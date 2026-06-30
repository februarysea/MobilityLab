from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from campussociety.core.entities import EntityId, JsonValue
from campussociety.core.scheduler import ScheduledTask
from campussociety.core.simulation import RunContext
from campussociety.environment._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
    require_positive,
)
from campussociety.environment.errors import MovementError
from campussociety.environment.routing import Route, RouteRequest, RoutingService
from campussociety.environment.spatial import LocationRef

if TYPE_CHECKING:
    from campussociety.environment.world import RuntimeWorld


class MovementStatus(StrEnum):
    """Runtime movement lifecycle status."""

    ACTIVE = "active"
    ARRIVED = "arrived"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class MovementIntent:
    """Request to move an agent through the runtime environment."""

    agent_id: EntityId
    destination: LocationRef
    mode: str
    origin: LocationRef | None = None
    movement_id: str | None = None
    departure_time: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_empty(self.mode, "mode")
        if self.movement_id is not None:
            require_non_empty(self.movement_id, "movement_id")
        if self.departure_time is not None:
            require_non_negative(self.departure_time, "departure_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "agent_id": str(self.agent_id),
            "destination": self.destination.to_record(),
            "mode": self.mode,
            "origin": None if self.origin is None else self.origin.to_record(),
            "movement_id": self.movement_id,
            "departure_time": self.departure_time,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(slots=True)
class ActiveMovement:
    """Movement currently being advanced by the movement kernel."""

    movement_id: str
    agent_id: EntityId
    route: Route
    started_at: int
    last_updated_time: int
    elapsed_seconds: int = 0
    status: MovementStatus = MovementStatus.ACTIVE
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        require_non_empty(self.movement_id, "movement_id")
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_negative(self.started_at, "started_at")
        require_non_negative(self.last_updated_time, "last_updated_time")
        require_non_negative(self.elapsed_seconds, "elapsed_seconds")

    @property
    def progress_ratio(self) -> float:
        total = self.route.total_travel_time_seconds
        if total == 0:
            return 1.0
        return min(1.0, self.elapsed_seconds / total)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "movement_id": self.movement_id,
            "agent_id": str(self.agent_id),
            "route": self.route.to_record(),
            "started_at": self.started_at,
            "last_updated_time": self.last_updated_time,
            "elapsed_seconds": self.elapsed_seconds,
            "progress_ratio": self.progress_ratio,
            "status": self.status.value,
            "failure_reason": self.failure_reason,
        }


class MovementKernel:
    """Deterministic environment movement executor."""

    def __init__(
        self,
        *,
        world: RuntimeWorld,
        routing_service: RoutingService,
        step_interval_seconds: int = 1,
        emit_progress_events: bool = False,
    ) -> None:
        require_positive(step_interval_seconds, "step_interval_seconds")
        self._world = world
        self._routing_service = routing_service
        self.step_interval_seconds = step_interval_seconds
        self.emit_progress_events = emit_progress_events
        self._active: dict[str, ActiveMovement] = {}
        self._agent_to_movement: dict[EntityId, str] = {}
        self._next_sequence = 1
        self._scheduled_task: ScheduledTask | None = None

    @property
    def active_count(self) -> int:
        return len(self._active)

    def active_movements(self) -> tuple[ActiveMovement, ...]:
        return tuple(self._active[movement_id] for movement_id in sorted(self._active))

    def active_movement_for_agent(self, agent_id: EntityId) -> ActiveMovement | None:
        movement_id = self._agent_to_movement.get(agent_id)
        if movement_id is None:
            return None
        return self._active[movement_id]

    def start_movement(
        self,
        intent: MovementIntent,
        context: RunContext,
    ) -> ActiveMovement:
        if intent.agent_id in self._agent_to_movement:
            msg = f"agent already has an active movement: {intent.agent_id}"
            raise MovementError(msg)

        movement_id = intent.movement_id or self._new_movement_id(intent.agent_id)
        if movement_id in self._active:
            msg = f"movement already exists: {movement_id}"
            raise MovementError(msg)

        origin = intent.origin or self._world.get_agent_location(intent.agent_id)
        if intent.departure_time is None:
            departure_time = context.clock.time
        else:
            departure_time = intent.departure_time
        if departure_time < context.clock.time:
            msg = (
                "movement departure_time cannot be in the past: "
                f"{departure_time} < {context.clock.time}"
            )
            raise MovementError(msg)
        if departure_time > context.clock.time:
            msg = (
                "future movement starts should be scheduled by core: "
                f"{departure_time} > {context.clock.time}"
            )
            raise MovementError(msg)

        route = self._routing_service.route(
            RouteRequest(
                origin=origin,
                destination=intent.destination,
                mode=intent.mode,
                departure_time=departure_time,
                agent_id=intent.agent_id,
                attributes=intent.attributes,
            ),
            self._world,
        )
        movement = ActiveMovement(
            movement_id=movement_id,
            agent_id=intent.agent_id,
            route=route,
            started_at=context.clock.time,
            last_updated_time=context.clock.time,
        )
        self._active[movement_id] = movement
        self._agent_to_movement[intent.agent_id] = movement_id
        self._world.set_agent_location(
            intent.agent_id,
            LocationRef.route(
                movement_id,
                detail={
                    "status": MovementStatus.ACTIVE.value,
                    "progress_ratio": 0.0,
                },
            ),
        )
        context.emit(
            "movement.started",
            {
                "movement_id": movement_id,
                "agent_id": str(intent.agent_id),
                "mode": intent.mode,
                "route": route.to_record(),
            },
        )

        if route.total_travel_time_seconds == 0:
            self._arrive(movement, context)
        else:
            self._ensure_scheduled(context)
        return movement

    def step(self, context: RunContext) -> None:
        self._scheduled_task = None
        if not self._active:
            return

        for movement in self.active_movements():
            if movement.status is not MovementStatus.ACTIVE:
                continue
            if not self._route_still_traversable(movement):
                self.fail_movement(
                    movement.movement_id,
                    context,
                    reason="route became unavailable",
                )
                continue
            delta = max(0, context.clock.time - movement.last_updated_time)
            movement.elapsed_seconds += delta
            movement.last_updated_time = context.clock.time
            if movement.elapsed_seconds >= movement.route.total_travel_time_seconds:
                self._arrive(movement, context)
                continue

            self._world.set_agent_location(
                movement.agent_id,
                LocationRef.route(
                    movement.movement_id,
                    detail={
                        "status": MovementStatus.ACTIVE.value,
                        "progress_ratio": movement.progress_ratio,
                    },
                ),
            )
            if self.emit_progress_events:
                context.emit(
                    "movement.progressed",
                    {
                        "movement_id": movement.movement_id,
                        "agent_id": str(movement.agent_id),
                        "elapsed_seconds": movement.elapsed_seconds,
                        "progress_ratio": movement.progress_ratio,
                    },
                )

        self._ensure_scheduled(context)

    def fail_movement(
        self,
        movement_id: str,
        context: RunContext,
        *,
        reason: str,
    ) -> ActiveMovement:
        movement = self._active.get(movement_id)
        if movement is None:
            msg = f"unknown active movement: {movement_id}"
            raise KeyError(msg)
        movement.status = MovementStatus.FAILED
        movement.failure_reason = reason
        self._remove_active(movement)
        context.emit(
            "movement.failed",
            {
                "movement_id": movement.movement_id,
                "agent_id": str(movement.agent_id),
                "reason": reason,
            },
        )
        return movement

    def cancel_movement(
        self,
        movement_id: str,
        context: RunContext,
        *,
        reason: str = "cancelled",
    ) -> ActiveMovement:
        movement = self._active.get(movement_id)
        if movement is None:
            msg = f"unknown active movement: {movement_id}"
            raise KeyError(msg)
        movement.status = MovementStatus.CANCELLED
        movement.failure_reason = reason
        self._remove_active(movement)
        context.emit(
            "movement.cancelled",
            {
                "movement_id": movement.movement_id,
                "agent_id": str(movement.agent_id),
                "reason": reason,
            },
        )
        return movement

    def snapshot_state(self) -> dict[str, JsonValue]:
        return {
            "active_count": self.active_count,
            "active_movements": [
                movement.to_record() for movement in self.active_movements()
            ],
            "step_interval_seconds": self.step_interval_seconds,
            "emit_progress_events": self.emit_progress_events,
        }

    def _new_movement_id(self, agent_id: EntityId) -> str:
        movement_id = f"movement:{agent_id}:{self._next_sequence}"
        self._next_sequence += 1
        return movement_id

    def _ensure_scheduled(self, context: RunContext) -> None:
        if not self._active:
            return
        if self._scheduled_task is not None and not self._scheduled_task.cancelled:
            return
        self._scheduled_task = context.schedule(
            self.step_interval_seconds,
            self.step,
            label="environment.movement.step",
        )

    def _arrive(self, movement: ActiveMovement, context: RunContext) -> None:
        movement.status = MovementStatus.ARRIVED
        movement.elapsed_seconds = movement.route.total_travel_time_seconds
        movement.last_updated_time = context.clock.time
        self._world.set_agent_location(
            movement.agent_id,
            movement.route.request.destination,
        )
        self._remove_active(movement)
        context.emit(
            "movement.arrived",
            {
                "movement_id": movement.movement_id,
                "agent_id": str(movement.agent_id),
                "destination": movement.route.request.destination.to_record(),
                "travel_time_seconds": movement.route.total_travel_time_seconds,
            },
        )

    def _remove_active(self, movement: ActiveMovement) -> None:
        self._active.pop(movement.movement_id, None)
        self._agent_to_movement.pop(movement.agent_id, None)

    def _route_still_traversable(self, movement: ActiveMovement) -> bool:
        return all(
            self._world.network.is_link_traversable(leg.link_id, leg.mode)
            for leg in movement.route.legs
        )
