# 0013 Configuration Layer

## Status

Accepted

## Context

MobilityLab needs a user-facing configuration entry point so users can run
small experiments without constructing every framework object in Python.
The configuration format should reduce user burden while preserving the
existing separation between simulation core, scenario contracts, environment
runtime, agent runtime, and experiment execution.

YAML is useful as an initial human-authored format, but it should not become a
runtime dependency of `core`, `environment`, `agents`, or `experiments`.

## Decision

Add a dedicated `mobilitylab.config` layer with this flow:

```text
YAML
  -> config schema objects
  -> validation
  -> compiler
  -> PreparedScenario + RunConfig
  -> ExperimentRunner
```

The config layer owns file-format parsing, user-facing aliases, schema version
checking, cross-section validation, and compilation into existing framework
contracts. Runtime layers continue to depend on `PreparedScenario`, `RunConfig`,
and other typed contracts rather than on YAML or raw mappings.

The first implementation supports the current MVP scenario and experiment
fields only: scenario metadata, population, network, facilities, mobility
supply, run timing, output, trace, metrics, and replay settings.

## Consequences

Users can start from YAML without learning every internal dataclass.
Future JSON, TOML, presets, public-data generators, batch sweeps, and policy
workflows can reuse the same schema/validation/compiler boundary.

The config layer adds one extra translation step, so it must stay thin and avoid
duplicating simulation semantics. Reusable simulation behavior still belongs in
scenario, environment, agents, experiments, visualization, or services.
