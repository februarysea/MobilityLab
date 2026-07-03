# Changelog

All notable project changes are recorded here.

## Unreleased

- Fixed visualization dev server run artifact serving so relative
  `MOBILITYLAB_RUN_DIR` values resolve from the npm invocation directory,
  missing `/run-artifacts` files return 404 instead of the Vite HTML shell, and
  configured run artifact failures no longer silently fall back to sample data.
- Fixed the replay viewer dashboard layout and initial map framing so the
  minimal commute network, facilities, metrics, events, and timeline fit in a
  usable default desktop viewport while preserving mobile vertical layout.
- Added a configuration layer that loads YAML user configs, normalizes them
  through schema objects, validates cross-section references, and compiles them
  into `PreparedScenario` and `RunConfig`.
- Added a runnable `examples/basic/minimal_commute` reference example that
  builds a minimal commute scenario, runs the experiment stack, and exports
  visualization-ready datasets.
- Renamed the project and Python package from CampusSociety/campussociety to
  MobilityLab/mobilitylab.
- Updated the project guide to clarify the mobility-first transport scope,
  spatial-overlay boundaries, current MVP capability boundary, and transport
  benchmark progression.
- Added environment runtime spatial overlays that compile scenario spatial
  layers into runtime areas, grid layers, grid cells, property-layer context,
  and controlled observation output.
- Added scenario spatial-layer contracts for coordinate references, semantic
  areas, optional grid overlays, static grid cells, and spatial index
  declarations.
- Reoriented the initial project testbeds from campus-specific scenarios to
  public U.S. data ABM and mobility experiments, with an ADR documenting the
  pivot.
- Added a services MVP with provider-neutral LLM request/response contracts,
  prompt rendering, deterministic LLM test client, LLM cache/retry wrappers,
  routing cache wrapper, and a thin service bundle.
- Renamed agent-layer `LLMBehavior` to `CognitiveBehavior` to keep LLM provider
  services distinct from cognition-backed agent behavior.
- Added a visualization MVP with artifact readers, dataset catalog contracts,
  GeoJSON export, replay/trace query helpers, dashboard specs, and a thin
  React/Vite/deck.gl replay viewer shell.
- Added an experiment run orchestration MVP with single-run configs,
  simulation assembly, run listeners, event trace export, built-in metrics,
  replay artifacts, run artifacts, and structured run results.
- Added an agent runtime MVP with `RuntimeAgent`, structured agent plans and
  decisions, replaceable behavior models, optional cognition state, and an
  `AgentSystem` that connects observations, decisions, movement requests, and
  event traces.
- Added deterministic batched agent activation with serial and threaded
  decision executor contracts so agent decisions can be parallelized before
  ordered runtime application.
- Added an environment runtime MVP with `RuntimeWorld`, deterministic routing
  contracts, a movement kernel, controlled observations, and simulation
  installation support.
- Added a scenario system MVP with scenario configs, normalized specs, variants,
  prepared scenarios, loader contracts, world/population specs, and core
  initializers.
- Initialized the project repository structure and Python tooling baseline.
- Added a deterministic simulation core with clock, scheduler, event bus,
  entity registry, lifecycle runtime, snapshots, and tests.
- Added integer-second core time constants, cancellable scheduled tasks,
  recurring callbacks, scheduler compaction, and sequenced event records.
