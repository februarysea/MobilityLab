from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest

from campussociety.core import (
    EntityId,
    RunContext,
    Simulation,
    SimulationStatus,
    State,
)


@dataclass
class CounterEntity:
    id: EntityId
    value: int = 0

    def snapshot_state(self) -> State:
        return {"value": self.value}


def build_counter_simulation(seed: int) -> Simulation:
    simulation = Simulation(seed=seed, simulation_id="counter-sim")

    def setup(context: RunContext) -> None:
        counter = CounterEntity(id=EntityId("counter"))
        context.entities.register(counter)

        def add_fixed(inner_context: RunContext) -> None:
            entity = cast(
                CounterEntity,
                inner_context.entities.get(EntityId("counter")),
            )
            entity.value += 1
            inner_context.emit(
                "counter.fixed",
                {"value": entity.value},
                source=entity.id,
            )

        def add_random(inner_context: RunContext) -> None:
            entity = cast(
                CounterEntity,
                inner_context.entities.get(EntityId("counter")),
            )
            entity.value += inner_context.rng.randint(1, 10)
            inner_context.emit(
                "counter.random",
                {"value": entity.value},
                source=entity.id,
            )

        context.schedule(delay=2, callback=add_random, label="random")
        context.schedule(delay=1, callback=add_fixed, label="fixed")

    simulation.add_initializer(setup)
    return simulation


def test_simulation_run_is_deterministic_for_same_seed() -> None:
    first = build_counter_simulation(seed=42).run()
    second = build_counter_simulation(seed=42).run()

    assert first.to_record() == second.to_record()
    assert first.status == SimulationStatus.COMPLETED.value
    assert first.time == 2
    assert first.pending_tasks == 0
    assert first.entities["counter"]["value"] == second.entities["counter"]["value"]

    topics = [str(record["topic"]) for record in first.event_trace]
    assert topics == [
        "simulation.initialized",
        "simulation.started",
        "counter.fixed",
        "counter.random",
        "simulation.completed",
    ]
    sequences = [record["sequence"] for record in first.event_trace]
    assert sequences == [1, 2, 3, 4, 5]


def test_simulation_can_pause_at_time_bound_and_resume() -> None:
    simulation = Simulation(seed=7, simulation_id="pause-resume")

    def setup(context: RunContext) -> None:
        def marker(inner_context: RunContext) -> None:
            inner_context.emit("marker", {"time": inner_context.clock.time})

        context.schedule(delay=10, callback=marker, label="marker")

    simulation.add_initializer(setup)

    paused = simulation.run(until=5)
    assert paused.status == SimulationStatus.PAUSED.value
    assert paused.time == 5
    assert paused.pending_tasks == 1

    completed = simulation.resume()
    assert completed.status == SimulationStatus.COMPLETED.value
    assert completed.time == 10
    assert completed.pending_tasks == 0

    topics = [str(record["topic"]) for record in completed.event_trace]
    assert topics == [
        "simulation.initialized",
        "simulation.started",
        "simulation.paused",
        "simulation.resumed",
        "marker",
        "simulation.completed",
    ]


def test_simulation_can_stop_and_checkpoint() -> None:
    simulation = Simulation(seed=11, simulation_id="stop")

    initialized = simulation.initialize()
    assert initialized.status == SimulationStatus.INITIALIZED.value

    stopped = simulation.stop()
    assert stopped.status == SimulationStatus.STOPPED.value
    assert stopped.to_record() == simulation.checkpoint().to_record()

    with pytest.raises(RuntimeError, match="cannot run"):
        simulation.run()


def test_simulation_runs_recurring_callbacks_with_count() -> None:
    simulation = Simulation(seed=1, simulation_id="recurring")
    times: list[int] = []

    def setup(context: RunContext) -> None:
        def tick(inner_context: RunContext) -> None:
            times.append(inner_context.clock.time)
            inner_context.emit("tick", {"time": inner_context.clock.time})

        context.schedule_every(
            interval_seconds=5,
            callback=tick,
            count=3,
            label="tick",
        )

    simulation.add_initializer(setup)

    completed = simulation.run()

    assert completed.status == SimulationStatus.COMPLETED.value
    assert completed.time == 15
    assert completed.pending_tasks == 0
    assert times == [5, 10, 15]


def test_recurring_callbacks_can_be_cancelled() -> None:
    simulation = Simulation(seed=1, simulation_id="cancel-recurring")
    times: list[int] = []

    def setup(context: RunContext) -> None:
        recurring = None

        def tick(inner_context: RunContext) -> None:
            nonlocal recurring
            times.append(inner_context.clock.time)
            if len(times) == 2:
                assert recurring is not None
                recurring.cancel()

        recurring = context.schedule_every(
            interval_seconds=5,
            callback=tick,
            label="tick",
        )

    simulation.add_initializer(setup)

    completed = simulation.run(until=30)

    assert completed.status == SimulationStatus.COMPLETED.value
    assert completed.time == 10
    assert times == [5, 10]
