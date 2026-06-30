# 0002 Scenario System Contracts

## Status

Accepted

## Context

CampusSociety needs a scenario layer that defines what world is simulated
without taking ownership of experiment execution, metrics, or framework core
runtime semantics. The first adapter is campus-scale, but the contracts should
remain useful for city-scale scenarios and future data loaders.

Scenario data must be reproducible from explicit inputs, variants, and versions.
The core simulation already exposes deterministic initialization through
`Simulation.add_initializer()` and `RunContext`, so scenario installation should
use those contracts instead of expanding core with domain-specific concepts.

## Decision

Define the framework scenario MVP around these contracts:

- `ScenarioConfig` for user-facing loader configuration such as data roots,
  input paths, schema versions, default variants, coordinate systems, and loader
  options.
- `ScenarioSpec` for normalized scenario declarations containing scenario id,
  version, variant id, data sources, policy defaults, assumptions, and metadata.
- `ScenarioVariantSpec` for thin baseline deltas such as overrides and
  deterministic scheduled scenario events.
- `PreparedScenario` for loaded and validated scenario data containing
  population, network, facilities, mobility supply, metadata, optional initial
  core entities, and an initializer factory.
- `ScenarioLoader` as the protocol that converts config or spec input into a
  `PreparedScenario`.
- `ScenarioInitializer` as a `Callable[[RunContext], None]` that installs a
  prepared scenario into a core `Simulation`.

Keep campus-specific loading and data interpretation in campus adapters. Keep
experiment run counts, metrics, traces, output paths, and LLM provider details
outside the scenario layer.

## Consequences

- Normal runs can use the implicit `baseline` variant while counterfactual runs
  record their variant id and scheduled effects explicitly.
- Prepared scenarios can be loaded and validated before simulation execution,
  making scenario preparation testable without running a simulation.
- Scenario installation uses core contracts without adding campus, city,
  routing, policy, or LLM concepts to the core runtime.
- Future campus and city adapters can implement their own loaders while sharing
  the same framework-level scenario contracts.
