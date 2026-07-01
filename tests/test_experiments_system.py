from __future__ import annotations

import json
from pathlib import Path

from campussociety.core import Snapshot
from campussociety.experiments import (
    AssembledRun,
    ExperimentRunner,
    OutputConfig,
    RunConfig,
    RunListener,
    RunResult,
    RunStatus,
    SimulationAssembler,
)
from campussociety.scenario import (
    ActivitySpec,
    AgentSpec,
    FacilitiesSpec,
    FacilitySpec,
    InMemoryScenarioLoader,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PlanSpec,
    PopulationSpec,
    PreparedScenario,
    ScenarioSpec,
)


def build_experiment_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="experiment_runtime_test",
            version="2026.07",
        ),
        population=PopulationSpec(
            agents=(
                AgentSpec(
                    agent_id="student-1",
                    agent_type="student",
                    profile={
                        "role": "student",
                        "mobility_access": ["walk"],
                    },
                    initial_state={
                        "location": {
                            "kind": "node",
                            "id": "gate",
                        },
                    },
                    plans=(
                        PlanSpec(
                            plan_id="morning",
                            activities=(
                                ActivitySpec(
                                    activity_id="class-1",
                                    activity_type="class",
                                    start_time=5,
                                    end_time=8,
                                    location_id="classroom-a",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="gate", x=0.0, y=0.0),
                NetworkNodeSpec(node_id="classroom", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="gate-classroom",
                    from_node_id="gate",
                    to_node_id="classroom",
                    length_meters=2.8,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
            ),
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="classroom-a",
                    facility_type="classroom",
                    location_id="classroom",
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
        ),
    )


def test_simulation_assembler_installs_scenario_environment_and_agents() -> None:
    scenario = build_experiment_scenario()
    assembler = SimulationAssembler(InMemoryScenarioLoader(scenario))
    config = RunConfig(
        run_id="assembly-test",
        scenario=scenario.spec,
        seed=42,
    )

    assembled = assembler.assemble(config)
    snapshot = assembled.simulation.initialize()

    assert assembled.scenario is scenario
    assert snapshot.entities["scenario:experiment_runtime_test"]["population_size"] == 1
    assert snapshot.entities["environment"]["entity_type"] == "environment"
    assert snapshot.entities["agents"]["entity_type"] == "agent_system"

    topics = [record["topic"] for record in snapshot.event_trace]
    assert topics == [
        "simulation.initialized",
        "scenario.initialized",
        "environment.initialized",
        "agents.initialized",
    ]


def test_experiment_runner_runs_and_writes_artifacts(tmp_path: Path) -> None:
    scenario = build_experiment_scenario()
    listener = RecordingRunListener()
    runner = ExperimentRunner(
        assembler=SimulationAssembler(InMemoryScenarioLoader(scenario)),
        listeners=(listener,),
    )
    config = RunConfig(
        run_id="single-run",
        scenario=scenario.spec,
        seed=7,
        output=OutputConfig(output_root=tmp_path),
    )

    result = runner.run(config)

    assert result.status is RunStatus.COMPLETED
    assert result.snapshot.status == "completed"
    assert result.snapshot.time == 8
    assert listener.events == [
        "started:single-run",
        "built:single-run",
        "before:single-run",
        "after:single-run:8",
        "completed:single-run",
    ]

    assert result.artifacts.run_dir == tmp_path / "single-run"
    assert result.artifacts.run_manifest.exists()
    assert result.artifacts.events.exists()
    assert result.artifacts.metrics.exists()
    assert result.artifacts.final_snapshot.exists()
    assert result.artifacts.scenario_summary.exists()
    assert result.artifacts.replay_manifest.exists()
    assert result.artifacts.replay_timeline.exists()

    manifest = json.loads(result.artifacts.run_manifest.read_text(encoding="utf-8"))
    assert manifest["run_config"]["run_id"] == "single-run"
    assert manifest["scenario"]["scenario_id"] == "experiment_runtime_test"
    assert manifest["artifacts"]["replay_manifest"] == str(
        result.artifacts.replay_manifest
    )

    event_lines = result.artifacts.events.read_text(encoding="utf-8").splitlines()
    event_topics = [json.loads(line)["topic"] for line in event_lines]
    assert "scenario.initialized" in event_topics
    assert "environment.initialized" in event_topics
    assert "agents.initialized" in event_topics
    assert "movement.arrived" in event_topics

    metrics = json.loads(result.artifacts.metrics.read_text(encoding="utf-8"))
    metric_names = {metric["name"] for metric in metrics["metrics"]}
    assert {
        "run.final_time",
        "run.event_count",
        "agents.count",
        "agents.lifecycle_status.completed.count",
        "movement.started.count",
        "movement.arrived.count",
        "movement.mode.walk.count",
    }.issubset(metric_names)

    replay_manifest = json.loads(
        result.artifacts.replay_manifest.read_text(encoding="utf-8")
    )
    assert replay_manifest["run_id"] == "single-run"
    assert replay_manifest["scenario_id"] == "experiment_runtime_test"
    assert replay_manifest["final_time"] == 8
    assert replay_manifest["frame_count"] > 0
    assert replay_manifest["artifacts"]["replay_timeline"] == str(
        result.artifacts.replay_timeline
    )

    replay_lines = result.artifacts.replay_timeline.read_text(
        encoding="utf-8"
    ).splitlines()
    replay_frames = [json.loads(line) for line in replay_lines]
    assert replay_frames == sorted(replay_frames, key=lambda frame: frame["time"])
    assert any(
        event["topic"] == "movement.arrived"
        for frame in replay_frames
        for event in frame["events"]
    )


class RecordingRunListener(RunListener):
    def __init__(self) -> None:
        self.events: list[str] = []

    def on_run_started(self, config: RunConfig) -> None:
        self.events.append(f"started:{config.run_id}")

    def on_simulation_built(self, assembled: AssembledRun) -> None:
        self.events.append(f"built:{assembled.config.run_id}")

    def on_before_simulation(self, assembled: AssembledRun) -> None:
        self.events.append(f"before:{assembled.config.run_id}")

    def on_after_simulation(self, assembled: AssembledRun, snapshot: Snapshot) -> None:
        self.events.append(f"after:{assembled.config.run_id}:{snapshot.time}")

    def on_run_completed(self, result: RunResult) -> None:
        self.events.append(f"completed:{result.run_id}")
