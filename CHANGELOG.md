# Changelog

All notable project changes are recorded here.

## Unreleased

- Added an agent runtime MVP with `RuntimeAgent`, structured agent plans and
  decisions, replaceable behavior models, optional cognition state, and an
  `AgentSystem` that connects observations, decisions, movement requests, and
  event traces.
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
