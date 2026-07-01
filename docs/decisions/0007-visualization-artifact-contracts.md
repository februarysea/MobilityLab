# Visualization Artifact Contracts

## Status

Accepted

## Context

CampusSociety needs replay, map, metrics, and trace views without allowing user
interfaces to redefine simulation semantics or mutate runtime state. The
experiment layer already writes run artifacts such as event traces, metrics,
snapshots, and replay timelines.

## Decision

The visualization layer consumes completed experiment run artifacts and exports
visualization-ready datasets. The first contract includes a
`visualization_manifest.json`, a dataset catalog, static GeoJSON for network and
facilities, replay frame JSONL, metric tables, trace event JSONL, and a
declarative replay dashboard spec.

The web viewer is a thin React/Vite/deck.gl client. It reads the visualization
manifest and datasets through HTTP and does not import or execute simulation
runtime code.

## Consequences

Visualization stays read-only and can serve web dashboards, notebooks, reports,
and future live views from the same artifact contracts. The MVP uses deck.gl
for map rendering from the start so later trajectory and geospatial layers can
reuse the same frontend renderer family. Live simulation control, backend APIs,
database-backed datasets, and batch experiment comparisons remain out of scope
for this decision.
