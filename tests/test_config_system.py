from __future__ import annotations

from pathlib import Path

import pytest

from mobilitylab.config import (
    ConfigValidationError,
    MobilityLabConfigSchema,
    compile_config,
    load_experiment_config,
)
from mobilitylab.experiments import ExperimentRunner, SimulationAssembler
from mobilitylab.scenario import InMemoryScenarioLoader


def test_yaml_config_compiles_and_runs_experiment(tmp_path: Path) -> None:
    config_path = tmp_path / "experiment.yaml"
    config_path.write_text(
        """
schema_version: mobilitylab.config.v1

scenario:
  id: config_runtime_test
  version: "2026.07"
  metadata:
    source: test-yaml

network:
  coordinate_system: local-planar
  nodes:
    - id: home
      x: 0
      y: 0
    - id: workplace
      x: 2
      y: 0
  links:
    - id: home-work
      from: home
      to: workplace
      length_meters: 2.8
      modes: [walk]
      bidirectional: true

facilities:
  facilities:
    - id: workplace-a
      type: workplace
      location: workplace
      capacity: 10

mobility_supply:
  modes:
    - id: walk
      type: active

population:
  agents:
    - id: worker-1
      type: worker
      profile:
        role: worker
        mobility_access: [walk]
      initial_state:
        location:
          kind: node
          id: home
      plans:
        - id: morning
          activities:
            - id: work-1
              activity: work
              start_time: 5
              end_time: 8
              location: workplace-a

run:
  id: yaml-run
  seed: 7
  metadata:
    source: config-system-test

output:
  output_root: runs
  overwrite: true

trace:
  enabled: true

metrics:
  enabled: true

replay:
  enabled: true
""",
        encoding="utf-8",
    )

    bundle = load_experiment_config(config_path)

    assert bundle.scenario.scenario_id == "config_runtime_test"
    assert bundle.scenario.population.size == 1
    assert bundle.scenario.network.link_count == 1
    assert bundle.scenario.network.links[0].attributes["bidirectional"] is True
    assert bundle.run_config.run_id == "yaml-run"
    assert bundle.run_config.output.output_root == tmp_path / "runs"

    runner = ExperimentRunner(
        assembler=SimulationAssembler(InMemoryScenarioLoader(bundle.scenario)),
    )
    result = runner.run(bundle.run_config)

    assert result.snapshot.status == "completed"
    assert result.snapshot.time == 8
    assert result.artifacts.run_dir == tmp_path / "runs" / "yaml-run"


def test_config_validation_reports_cross_section_references() -> None:
    config = MobilityLabConfigSchema.from_mapping(
        {
            "schema_version": "mobilitylab.config.v1",
            "scenario": {
                "id": "invalid_config",
                "version": "2026.07",
            },
            "network": {
                "nodes": [
                    {"id": "home"},
                ],
            },
            "facilities": {
                "facilities": [
                    {
                        "id": "home-a",
                        "type": "home",
                        "location": "home",
                    },
                ],
            },
            "mobility_supply": {
                "modes": [
                    {"id": "walk", "type": "active"},
                ],
            },
            "population": {
                "agents": [
                    {
                        "id": "worker-1",
                        "profile": {"mobility_access": ["walk"]},
                        "initial_state": {"location": "home-a"},
                        "plans": [
                            {
                                "id": "morning",
                                "activities": [
                                    {
                                        "id": "work-1",
                                        "activity": "work",
                                        "location": "missing-workplace",
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            "run": {
                "id": "bad-run",
                "seed": 1,
            },
        },
    )

    with pytest.raises(
        ConfigValidationError,
        match=r"activities\[0\]\.location_id references unknown",
    ):
        compile_config(config)
