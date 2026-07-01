# 0011 Environment Spatial Overlay Runtime

## Status

Accepted

## Context

Scenario spatial-layer contracts now declare coordinate references, semantic
areas, optional grid overlays, grid cells, initial property layers, and spatial
index preferences. The environment runtime needs to consume those declarations
without changing the movement kernel into a grid-based movement engine.

Reference systems support this boundary: Mesa has grid/cell abstractions, but
their movement semantics are cell-to-cell transitions; AgentSociety and MATSim
primarily use spatial indexes and grid-like overlays for observation, matching,
aggregation, and analysis rather than as the core mobility execution substrate.

## Decision

Compile `PreparedScenario.spatial_layers` into environment runtime spatial
overlays.

The environment layer introduces `RuntimeSpatialLayers`, runtime areas, runtime
grid layers, runtime grid cells, and runtime layer values. These overlays answer
queries such as:

- which grid cell contains or best represents a position;
- which initial property-layer values apply to a cell;
- which semantic areas are associated with the observed grid context.

`RuntimeWorld` owns `spatial_layers` alongside network, facilities, mobility
modes, and agent locations. `ObservationService` exposes spatial context through
agent observations.

The movement kernel remains network-route based. Grid layers are not the default
movement engine.

## Consequences

- Scenario continues to own static spatial declarations.
- Environment owns runtime spatial overlay queries and mutable runtime layer
  values.
- Agent observations can include area/grid/property context without exposing
  unrestricted world state.
- Routing and movement can later consult spatial layers for cost modifiers, but
  route execution remains on the network unless a separate grid movement backend
  is introduced.
- H3, polygon containment, spatial tree backends, dynamic raster updates, media
  lookup, and grid movement remain future extensions.
