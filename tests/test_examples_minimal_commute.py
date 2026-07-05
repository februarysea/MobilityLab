from __future__ import annotations

import json
from pathlib import Path

from examples.basic.minimal_commute.run import MinimalCommuteResult, run_minimal_commute
from examples.basic.minimal_commute.run_from_config import (
    run_minimal_commute_from_config,
)


def test_minimal_commute_python_example_runs_full_experiment_stack(
    tmp_path: Path,
) -> None:
    result = run_minimal_commute(output_root=tmp_path)

    _assert_minimal_commute_result(result, tmp_path)


def test_minimal_commute_config_example_runs_full_experiment_stack(
    tmp_path: Path,
) -> None:
    result = run_minimal_commute_from_config(output_root=tmp_path)

    _assert_minimal_commute_result(result, tmp_path)


def _assert_minimal_commute_result(
    result: MinimalCommuteResult,
    output_root: Path,
) -> None:
    run = result.run
    visualization = result.visualization

    assert run.snapshot.status == "completed"
    assert run.snapshot.time == 55
    assert run.artifacts.run_dir == output_root / "minimal-commute"
    assert visualization.manifest_path.exists()

    metric_values = {metric.name: metric.value for metric in run.metrics}
    assert metric_values["scenario.population_size"] == 2
    assert metric_values["scenario.network_nodes"] == 4
    assert metric_values["scenario.network_links"] == 3
    assert metric_values["agents.lifecycle_status.completed.count"] == 2
    assert metric_values["movement.started.count"] == 2
    assert metric_values["movement.arrived.count"] == 2
    assert metric_values["movement.mode.walk.count"] == 2

    event_topics = [
        json.loads(line)["topic"]
        for line in run.artifacts.events.read_text(encoding="utf-8").splitlines()
    ]
    assert "scenario.initialized" in event_topics
    assert "environment.initialized" in event_topics
    assert "agents.initialized" in event_topics
    assert "movement.started" in event_topics
    assert "movement.arrived" in event_topics
    assert "activity.started" in event_topics
    assert "activity.ended" in event_topics

    assert (run.artifacts.run_dir / "datasets" / "network.geojson").exists()
    assert (run.artifacts.run_dir / "datasets" / "facilities.geojson").exists()
