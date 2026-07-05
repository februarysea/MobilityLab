# Minimal Commute Spec

## User Value

`basic/minimal_commute` is the smallest complete MobilityLab example. It shows
how to define a tiny mobility scenario, run a deterministic experiment, and
inspect the produced metrics, traces, replay artifacts, and visualization-ready
datasets.

The example is intended as the first reference project for new users before
traffic assignment, queueing, public-data, or LLM behavior examples are added.

## Framework Value

This example validates that the current MVP stack can connect:

- YAML configuration loading and compilation
- Python API scenario construction
- scenario specs for population, network, facilities, and mobility supply
- environment runtime world construction
- agent trip and activity execution
- experiment runner orchestration
- metrics, event traces, replay artifacts, and run artifacts
- visualization dataset export

## Model Definition

- Scenario id: `minimal_commute`
- Run id: `minimal-commute`
- Random seed: `7`
- Coordinate system: `local-planar`
- Mobility mode: `walk`
- Population: 2 worker agents
- Facilities: 2 homes and 1 workplace
- Network: 4 nodes and 3 bidirectional walking links
- Plans: each worker has one work activity at `workplace-a`

The first worker starts work at simulation time `20` and ends at `50`. The
second worker starts work at simulation time `25` and ends at `55`.

## Entry Points

Recommended user-facing YAML entry point:

```bash
uv run python -m examples.basic.minimal_commute.run_from_config
```

Python API construction entry point:

```bash
uv run python -m examples.basic.minimal_commute.run
```

Both entry points should produce the same run id, final simulation time,
metrics, replay artifacts, and visualization datasets.

## Expected Outputs

The run writes artifacts under:

```text
examples/basic/minimal_commute/runs/minimal-commute/
```

Expected run results:

- run status: `completed`
- final simulation time: `55` seconds
- completed agents: `2`
- movement started count: `2`
- movement arrived count: `2`
- walking movement count: `2`

Expected visualization files:

- `visualization_manifest.json`
- `datasets/network.geojson`
- `datasets/facilities.geojson`
- `datasets/replay_frames.jsonl`
- `datasets/metrics.json`
- `datasets/trace_events.jsonl`

Expected geometry:

- network dataset has 3 `LineString` link features
- network dataset has 4 `Point` node features
- facilities dataset has 3 facility point features

## Success Criteria

- The YAML entry point runs from the repository root.
- The Python API entry point runs from the repository root.
- `tests/test_examples_minimal_commute.py` passes.
- `make check` passes.
- The exported visualization manifest references all expected datasets through
  `catalog.datasets`.
- The replay viewer can load the completed run through `MOBILITYLAB_RUN_DIR`.

## Framework Gaps Exercised

This example is expected to remain small, but it has already exercised these
framework boundaries:

- config compilation into `PreparedScenario` and `RunConfig`
- deterministic experiment output directories
- visualization artifact export contracts
- visualization dev-server run artifact serving
- replay dashboard layout and local-coordinate map framing

## Follow-ups

- Add a closure or accessibility variant while keeping fixed link costs.
- Use this example as the baseline before implementing OD demand examples.
- Keep traffic assignment, congestion, queueing, and route-choice logic out of
  this basic example.
