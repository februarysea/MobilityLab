# Minimal Commute

This is the smallest complete MobilityLab mobility simulation example.

It defines:

- a local walking network
- home and workplace facilities
- two worker agents
- one work activity plan per agent
- one deterministic experiment run

The YAML entry point is the recommended user-facing path:

```bash
uv run python -m examples.basic.minimal_commute.run_from_config
```

The same scenario is also available as Python API construction:

```bash
uv run python -m examples.basic.minimal_commute.run
```

Both commands write experiment artifacts and visualization-ready datasets under
`examples/basic/minimal_commute/runs/minimal-commute/`.

## Visualization

The run exports a visualization manifest plus network, facility, replay,
metrics, and trace datasets:

```text
examples/basic/minimal_commute/runs/minimal-commute/
  visualization_manifest.json
  datasets/
    network.geojson
    facilities.geojson
    replay_frames.jsonl
    metrics.json
    trace_events.jsonl
```

Open the viewer against this run directory:

```bash
MOBILITYLAB_RUN_DIR=examples/basic/minimal_commute/runs/minimal-commute \
npm --prefix apps/visualization run dev
```

The relative run directory is resolved from the directory where you invoke the
`npm` command. Run the command above from the repository root.

If frontend dependencies are not installed yet:

```bash
npm --prefix apps/visualization install
```

The run exercises the current MVP stack:

```text
YAML/Python -> PreparedScenario + RunConfig -> ExperimentRunner -> Artifacts
```
