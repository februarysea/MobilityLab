# 0010 Scenario Spatial Layer Contracts

## Status

Accepted

## Context

MobilityLab needs spatial declarations for campus-scale and public-data ABM
scenarios. The project must support semantic areas, facilities, networks, and
optional grid overlays without moving mutable runtime state into the scenario
layer.

Reference systems point to the same boundary: Mesa grids are runtime model
state, AgentSociety keeps static AOI/POI map data separate from dynamic person
state, and MATSim keeps network/facilities in scenario while spatial indexes
and grid-like zone systems support queries and aggregation.

## Decision

Add a scenario-level spatial declaration layer.

Scenario spatial contracts include coordinate references, bounding boxes,
semantic areas, optional grid overlays, static grid cells, static initial
property layers, and preferred spatial index declarations.

Do not store runtime occupancy, agent positions, congestion, closures, mutable
messages, or query caches in scenario spatial specs. Those belong to the
environment runtime and movement kernel.

## Consequences

- Scenario loaders can describe AOI/zone/cell/facility context without owning
  runtime movement or observation behavior.
- Grid layers are optional overlays for aggregation, heatmaps, sampling, and
  spatial indexing rather than the main semantic model.
- Environment adapters can compile scenario spatial declarations into runtime
  indexes and controlled observation APIs.
- Future city-scale adapters can use regular square grids, H3 grids, custom
  cells, or semantic zones behind the same scenario contract.
