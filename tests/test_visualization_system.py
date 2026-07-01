from __future__ import annotations

import json
from pathlib import Path

from mobilitylab.experiments import (
    ExperimentRunner,
    OutputConfig,
    RunConfig,
    SimulationAssembler,
)
from mobilitylab.scenario import (
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
from mobilitylab.visualization import (
    DatasetCapability,
    ReplayTimeline,
    RunArtifactReader,
    TraceEventIndex,
    TraceQuery,
    VisualizationExporter,
)


def build_visualization_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="visualization_runtime_test",
            version="2026.07",
        ),
        population=PopulationSpec(
            agents=(
                AgentSpec(
                    agent_id="worker-1",
                    agent_type="worker",
                    profile={"role": "worker", "mobility_access": ["walk"]},
                    initial_state={"location": {"kind": "node", "id": "home"}},
                    plans=(
                        PlanSpec(
                            plan_id="morning",
                            activities=(
                                ActivitySpec(
                                    activity_id="work-1",
                                    activity_type="work",
                                    start_time=5,
                                    end_time=8,
                                    location_id="workplace-a",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="home", x=0.0, y=0.0),
                NetworkNodeSpec(node_id="workplace", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="home-work",
                    from_node_id="home",
                    to_node_id="workplace",
                    length_meters=2.8,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
            ),
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="workplace-a",
                    facility_type="workplace",
                    location_id="workplace",
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
        ),
    )


def test_visualization_exporter_writes_manifest_and_datasets(
    tmp_path: Path,
) -> None:
    scenario = build_visualization_scenario()
    runner = ExperimentRunner(
        assembler=SimulationAssembler(InMemoryScenarioLoader(scenario)),
    )
    result = runner.run(
        RunConfig(
            run_id="viz-run",
            scenario=scenario.spec,
            seed=11,
            output=OutputConfig(output_root=tmp_path),
        )
    )

    export = VisualizationExporter().export_run(result.artifacts.run_dir)

    assert export.manifest_path.exists()
    assert export.datasets_dir.exists()
    assert (export.datasets_dir / "network.geojson").exists()
    assert (export.datasets_dir / "facilities.geojson").exists()
    assert (export.datasets_dir / "replay_frames.jsonl").exists()
    assert (export.datasets_dir / "metrics.json").exists()
    assert (export.datasets_dir / "trace_events.jsonl").exists()

    manifest = json.loads(export.manifest_path.read_text(encoding="utf-8"))
    assert manifest["run_id"] == "viz-run"
    assert manifest["scenario_id"] == "visualization_runtime_test"
    dataset_ids = {dataset["dataset_id"] for dataset in manifest["catalog"]["datasets"]}
    assert dataset_ids == {
        "network",
        "facilities",
        "replay_frames",
        "metrics",
        "trace_events",
    }
    replay_dataset = export.manifest.catalog.get("replay_frames")
    assert replay_dataset.has_capability(DatasetCapability.REPLAY_FRAMES)
    assert manifest["dashboards"][0]["dashboard_id"] == "replay"

    network = json.loads(
        (export.datasets_dir / "network.geojson").read_text(encoding="utf-8")
    )
    network_feature_types = {
        feature["properties"]["feature_type"] for feature in network["features"]
    }
    assert {"network_node", "network_link"}.issubset(network_feature_types)

    facilities = json.loads(
        (export.datasets_dir / "facilities.geojson").read_text(encoding="utf-8")
    )
    assert facilities["features"][0]["properties"]["facility_id"] == "workplace-a"


def test_visualization_readers_support_replay_and_trace_queries(
    tmp_path: Path,
) -> None:
    scenario = build_visualization_scenario()
    runner = ExperimentRunner(
        assembler=SimulationAssembler(InMemoryScenarioLoader(scenario)),
    )
    result = runner.run(
        RunConfig(
            run_id="viz-query-run",
            scenario=scenario.spec,
            seed=12,
            output=OutputConfig(output_root=tmp_path),
        )
    )
    VisualizationExporter().export_run(result.artifacts.run_dir)
    reader = RunArtifactReader(result.artifacts.run_dir)

    replay_frames = reader.read_replay_frames()
    arrival_time: int | None = None
    for frame in replay_frames:
        events = frame.get("events")
        if not isinstance(events, list):
            continue
        if not any(
            isinstance(event, dict) and event.get("topic") == "movement.arrived"
            for event in events
        ):
            continue
        raw_time = frame.get("time")
        assert isinstance(raw_time, int)
        arrival_time = raw_time
        break
    assert arrival_time is not None
    timeline = ReplayTimeline.from_records(replay_frames)
    bundle = timeline.bundle_at(arrival_time)
    assert bundle.time == arrival_time
    assert any(event["topic"] == "movement.arrived" for event in bundle.events)

    trace_index = TraceEventIndex(reader.read_trace_events())
    movement_events = trace_index.query(
        TraceQuery(topic="movement.started", agent_id="worker-1")
    )
    assert len(movement_events) == 1
    assert "movement.started" in trace_index.topics()
