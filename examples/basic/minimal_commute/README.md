# Minimal Commute

This is the smallest complete MobilityLab mobility simulation example.

It defines:

- a local walking network
- home and workplace facilities
- two worker agents
- one work activity plan per agent
- one deterministic experiment run

Running the example writes experiment artifacts and visualization-ready datasets
under `examples/basic/minimal_commute/runs/minimal-commute/`.

```bash
uv run python -m examples.basic.minimal_commute.run
```

The run exercises the current MVP stack:

```text
Scenario -> Environment -> AgentSystem -> ExperimentRunner -> Artifacts
```

