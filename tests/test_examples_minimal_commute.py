from __future__ import annotations

import json
from pathlib import Path

from examples.basic.minimal_commute.run import run_minimal_commute


def test_minimal_commute_example_runs_full_experiment_stack(tmp_path: Path) -> None:
    result = run_minimal_commute(output_root=tmp_path)

    assert result.run.snapshot.status == "completed"
    assert result.run.snapshot.time == 55
    assert result.run.artifacts.run_dir == tmp_path / "minimal-commute"
    assert result.visualization.manifest_path.exists()

    metric_values = {metric.name: metric.value for metric in result.run.metrics}
    assert metric_values["scenario.population_size"] == 2
    assert metric_values["scenario.network_nodes"] == 4
    assert metric_values["scenario.network_links"] == 3
    assert metric_values["agents.lifecycle_status.completed.count"] == 2
    assert metric_values["movement.started.count"] == 2
    assert metric_values["movement.arrived.count"] == 2
    assert metric_values["movement.mode.walk.count"] == 2

    event_topics = [
        json.loads(line)["topic"]
        for line in result.run.artifacts.events.read_text(encoding="utf-8").splitlines()
    ]
    assert "scenario.initialized" in event_topics
    assert "environment.initialized" in event_topics
    assert "agents.initialized" in event_topics
    assert "movement.started" in event_topics
    assert "movement.arrived" in event_topics
    assert "activity.started" in event_topics
    assert "activity.ended" in event_topics

    assert (result.run.artifacts.run_dir / "datasets" / "network.geojson").exists()
    assert (result.run.artifacts.run_dir / "datasets" / "facilities.geojson").exists()
