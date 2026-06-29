# 0001 Project Architecture

## Status

Accepted

## Context

CampusSociety needs to support traditional ABM policies, LLM-driven policies,
and hybrid policies without coupling provider calls to the simulation runtime.
The first scenario is campus-scale, but the framework should keep city-scale
extension points open from the start.

## Decision

Use a layered package structure with separate modules for core simulation,
agents, environment, scenarios, experiments, visualization, services, and
adapters.

The core package owns runtime primitives and deterministic execution contracts.
Domain-specific concepts live in scenario adapters. External capabilities such
as LLM providers, routing backends, storage, and exports live behind service
interfaces.

## Consequences

- Core code stays independent of campus, city, and LLM provider details.
- Scenarios configure agents and environments rather than owning experiment
  metrics.
- Experiments own run configuration, reproducibility metadata, traces, and
  metrics.
- Visualization consumes snapshots, traces, metrics, and scenario metadata
  without mutating simulation state.
- Additional adapters and service backends can be introduced without changing
  core simulation semantics.

