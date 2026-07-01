# 0006 Experiment Run Orchestration

## Status

Accepted

## Context

CampusSociety now has MVP implementations for simulation core, scenarios,
environment runtime, and agents. The next layer needs to run those components
as reproducible experiments without moving scenario data ownership, movement
semantics, or agent behavior into an experiment script.

Scenario describes what world is simulated. Experiment describes how one run is
configured, executed, recorded, and evaluated.

## Decision

The experiment MVP is a single-run orchestration layer. It introduces:

- `RunConfig` for one deterministic simulation run
- `SimulationAssembler` to compose scenario, environment, agents, and core
  simulation initializers
- `SingleRunRunner` / `ExperimentRunner` to execute one run
- `RunListener` hooks for experiment-level orchestration events
- `EventTraceCollector` and `DefaultMetricCollector`
- `ReplayManifest`, `ReplayFrame`, and `ReplayBuilder` for visualization-ready
  replay inputs
- `RunDirectory`, `ArtifactPaths`, and `RunArtifactWriter` for JSON/JSONL
  artifacts
- `RunResult` for structured run output

Experiment does not define scenario contents, runtime movement semantics, agent
decision semantics, storage backends, visualization, or batch design expansion.

## Consequences

Single-run execution is reproducible from run config, scenario version, variant,
seed, and emitted artifacts.

The layer can later grow batch designs, parallel run execution, richer metrics,
LLM audit sinks, checkpointing, and richer replay state reconstruction without
changing core, scenario, environment, or agent responsibilities.

For now, run artifacts use local JSON and JSONL files to keep the MVP
dependency-free and inspectable. Replay artifacts are an entrypoint manifest
plus a timeline JSONL file grouped by simulation time.
