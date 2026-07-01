from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from random import Random
from typing import TypeAlias

from mobilitylab.core.clock import Clock
from mobilitylab.core.entities import EntityId, EntityRegistry, JsonValue
from mobilitylab.core.events import Event, EventBus
from mobilitylab.core.scheduler import (
    RecurringTask,
    ScheduledCallback,
    ScheduledTask,
    Scheduler,
)
from mobilitylab.core.snapshots import Snapshot

Initializer: TypeAlias = Callable[["RunContext"], None]


class SimulationStatus(StrEnum):
    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


@dataclass(frozen=True, slots=True)
class RunContext:
    """Shared deterministic runtime context passed to scheduled actions."""

    simulation_id: str
    seed: int
    clock: Clock
    rng: Random
    event_bus: EventBus
    entities: EntityRegistry
    scheduler: Scheduler

    def emit(
        self,
        topic: str,
        payload: dict[str, JsonValue] | None = None,
        *,
        source: EntityId | None = None,
    ) -> Event:
        return self.event_bus.emit(
            Event(
                time=self.clock.time,
                topic=topic,
                payload=payload or {},
                source=source,
            )
        )

    def schedule(
        self,
        delay: int,
        callback: ScheduledCallback,
        *,
        priority: int = 0,
        label: str | None = None,
    ) -> ScheduledTask:
        if delay < 0:
            msg = "delay must be non-negative"
            raise ValueError(msg)
        return self.schedule_at(
            self.clock.time + delay,
            callback,
            priority=priority,
            label=label,
        )

    def schedule_at(
        self,
        time: int,
        callback: ScheduledCallback,
        *,
        priority: int = 0,
        label: str | None = None,
    ) -> ScheduledTask:
        if time < self.clock.time:
            msg = f"cannot schedule callback in the past: {time} < {self.clock.time}"
            raise ValueError(msg)
        return self.scheduler.schedule(
            time,
            callback,
            priority=priority,
            label=label,
        )

    def schedule_every(
        self,
        interval_seconds: int,
        callback: ScheduledCallback,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        count: int | None = None,
        priority: int = 0,
        label: str | None = None,
    ) -> RecurringTask:
        if interval_seconds <= 0:
            msg = "interval_seconds must be positive"
            raise ValueError(msg)
        if count is not None and count < 1:
            msg = "count must be positive"
            raise ValueError(msg)

        first_time = self.clock.time + interval_seconds
        if start_time is not None:
            first_time = start_time
        if first_time < self.clock.time:
            msg = (
                "cannot schedule callback in the past: "
                f"{first_time} < {self.clock.time}"
            )
            raise ValueError(msg)
        if end_time is not None and end_time < first_time:
            msg = "end_time must be greater than or equal to the first execution time"
            raise ValueError(msg)

        recurring = RecurringTask(
            interval_seconds=interval_seconds,
            label=label,
        )
        runs_completed = 0

        def invoke(inner_context: RunContext) -> None:
            nonlocal runs_completed
            if recurring.cancelled:
                return

            runs_completed += 1
            callback(inner_context)

            if recurring.cancelled:
                return
            if count is not None and runs_completed >= count:
                return

            next_time = inner_context.clock.time + interval_seconds
            if end_time is not None and next_time > end_time:
                return

            recurring.set_next_task(
                inner_context.schedule_at(
                    next_time,
                    invoke,
                    priority=priority,
                    label=label,
                )
            )

        recurring.set_next_task(
            self.schedule_at(
                first_time,
                invoke,
                priority=priority,
                label=label,
            )
        )
        return recurring


class Simulation:
    """Small deterministic simulation runtime."""

    def __init__(
        self,
        *,
        seed: int,
        simulation_id: str = "simulation",
        start_time: int = 0,
    ) -> None:
        self.simulation_id = simulation_id
        self.seed = seed
        self.clock = Clock(start_time)
        self.rng = Random(seed)
        self.event_bus = EventBus()
        self.entities = EntityRegistry()
        self.scheduler = Scheduler()
        self.context = RunContext(
            simulation_id=simulation_id,
            seed=seed,
            clock=self.clock,
            rng=self.rng,
            event_bus=self.event_bus,
            entities=self.entities,
            scheduler=self.scheduler,
        )
        self._status = SimulationStatus.CREATED
        self._initializers: list[Initializer] = []

    @property
    def status(self) -> SimulationStatus:
        return self._status

    def add_initializer(self, initializer: Initializer) -> None:
        if self._status is not SimulationStatus.CREATED:
            msg = "initializers can only be added before initialization"
            raise RuntimeError(msg)
        self._initializers.append(initializer)

    def initialize(self) -> Snapshot:
        if self._status is not SimulationStatus.CREATED:
            msg = f"cannot initialize simulation from status {self._status.value}"
            raise RuntimeError(msg)
        self._status = SimulationStatus.INITIALIZED
        self.context.emit(
            "simulation.initialized",
            {
                "simulation_id": self.simulation_id,
                "seed": self.seed,
            },
        )
        for initializer in self._initializers:
            initializer(self.context)
        return self.snapshot()

    def run(
        self,
        *,
        until: int | None = None,
        max_steps: int | None = None,
    ) -> Snapshot:
        if until is not None and until < self.clock.time:
            msg = f"until must be >= current time {self.clock.time}"
            raise ValueError(msg)
        if max_steps is not None and max_steps < 0:
            msg = "max_steps must be non-negative"
            raise ValueError(msg)
        if self._status is SimulationStatus.CREATED:
            self.initialize()
        if self._status not in {
            SimulationStatus.INITIALIZED,
            SimulationStatus.PAUSED,
        }:
            msg = f"cannot run simulation from status {self._status.value}"
            raise RuntimeError(msg)

        previous_status = self._status
        self._status = SimulationStatus.RUNNING
        self.context.emit(
            "simulation.started"
            if previous_status is SimulationStatus.INITIALIZED
            else "simulation.resumed",
            {"simulation_id": self.simulation_id},
        )

        processed_steps = 0
        while self._status is SimulationStatus.RUNNING:
            if max_steps is not None and processed_steps >= max_steps:
                self.pause()
                break

            next_time = self.scheduler.peek_next_time()
            if next_time is None:
                self._complete()
                break
            if until is not None and next_time > until:
                self.clock.advance_to(until)
                self.pause()
                break

            scheduled = self.scheduler.pop_next()
            if scheduled is None:
                self._complete()
                break
            self.clock.advance_to(scheduled.time)
            scheduled.callback(self.context)
            processed_steps += 1

        return self.snapshot()

    def pause(self) -> Snapshot:
        if self._status is not SimulationStatus.RUNNING:
            msg = f"cannot pause simulation from status {self._status.value}"
            raise RuntimeError(msg)
        self._status = SimulationStatus.PAUSED
        self.context.emit(
            "simulation.paused",
            {"simulation_id": self.simulation_id},
        )
        return self.snapshot()

    def resume(
        self,
        *,
        until: int | None = None,
        max_steps: int | None = None,
    ) -> Snapshot:
        if self._status is not SimulationStatus.PAUSED:
            msg = f"cannot resume simulation from status {self._status.value}"
            raise RuntimeError(msg)
        return self.run(until=until, max_steps=max_steps)

    def stop(self) -> Snapshot:
        if self._status in {SimulationStatus.STOPPED, SimulationStatus.COMPLETED}:
            return self.snapshot()
        self._status = SimulationStatus.STOPPED
        self.context.emit(
            "simulation.stopped",
            {"simulation_id": self.simulation_id},
        )
        return self.snapshot()

    def snapshot(self) -> Snapshot:
        return Snapshot(
            time=self.clock.time,
            status=self._status.value,
            seed=self.seed,
            entities=self.entities.snapshot(),
            event_trace=self.event_bus.records(),
            pending_tasks=self.scheduler.pending_count(),
        )

    def checkpoint(self) -> Snapshot:
        return self.snapshot()

    def event_trace(self) -> tuple[dict[str, JsonValue], ...]:
        return self.event_bus.records()

    def _complete(self) -> None:
        self._status = SimulationStatus.COMPLETED
        self.context.emit(
            "simulation.completed",
            {"simulation_id": self.simulation_id},
        )
