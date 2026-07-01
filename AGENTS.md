# CampusSociety Project Guide

## Project Scope

CampusSociety is a simulation framework for traditional, agent-based,
LLM-driven, and hybrid mobility and transportation simulation.

The first implementation target is a mobility-first simulation foundation:
network-route movement, agent trip/activity execution, spatial context,
experiment traces, and reproducible transport benchmarks. Public U.S. datasets
enter through planned scenario adapters.

The architecture remains compatible with larger regional and city-scale
scenarios from the start.

## Architecture Principles

- Keep the full simulation architecture in place.
- Start each layer with the smallest useful implementation.
- Keep domain-specific logic out of the framework core.
- Support traditional transport models, agent-based mobility simulation,
  LLM-driven agents, and hybrid behavior models.
- Keep simulation execution deterministic and reproducible.
- Record structured traces for debugging, evaluation, and replay.
- Route LLM calls through policy/service behavior and keep the simulation core
  provider-neutral.
- Keep visualization and user interfaces separate from simulation execution.

## Logical Layers

### 1. Simulation Core

Purpose: runtime foundation.

Responsibilities:

- simulation lifecycle: initialize, run, pause, resume, stop
- clock and step/event scheduling
- event bus
- entity registry
- state snapshot and checkpoint
- deterministic random seed handling
- replay support
- plugin/adapter registration hooks

Core concepts:

- `Simulation`
- `Scheduler`
- `Clock`
- `Event`
- `Action`
- `Entity`
- `EntityId`
- `State`
- `Snapshot`
- `RunContext`

Rules:

- `core/` owns generic runtime contracts.
- Scenario, geography, and provider details live in outer layers.
- LLM provider calls live behind service contracts.
- `core/` exposes stable contracts for agents, environment, scenarios, and
  experiments.

### 2. Agent System

Purpose: agent definitions, state, behavior, and interaction.

Responsibilities:

- agent profile: role, demographics, preferences, budget, mobility access
- agent state: lifecycle status, current activity, current trip, plan progress,
  fatigue, satisfaction, and behavior-specific attributes
- agent plans: daily activity plans, trip plans, fallback plans
- behavior models: rule-based, discrete-choice, cognition-backed, or hybrid
  decisions for activity, mode, departure time, route preference, replanning, and
  communication
- agent perception: accessible environment observations
- agent memory: short-term and long-term experience
- agent interaction: communication, social influence, group travel, queue
  interaction

Behavior models:

- `RuleBasedBehavior`
- `DiscreteChoiceBehavior`
- `CognitiveBehavior`
- `HybridBehavior`

Rules:

- LLM provider calls live behind service contracts.
- Agent behavior models are swappable.
- Agent behavior depends on core contracts and controlled environment
  observations.
- Authoritative physical location belongs to the environment runtime world.
- Agent state stores lifecycle, plan, activity, trip, and behavior context.
- Agent behavior emits high-level decisions and intents; routing, movement,
  link occupancy, queueing, and vehicle/transit operations belong to the
  environment.
- Use `BehaviorModel` for agent decision mechanisms. Reserve `Policy` for
  experiment policy, governance constraints, pricing, closures, service changes,
  and other interventions.

### 3. Environment System

Purpose: external world, mobility supply, and observable context.

Responsibilities:

- runtime world: authoritative agent physical locations, network state,
  facilities, mobility modes, and runtime spatial overlays
- spatial network: walking, cycling, vehicle, and future multimodal networks
- places and facilities: homes, workplaces, schools, shops, stations, parking
  areas, and public facilities
- spatial overlays: semantic areas, grid layers, grid cells, property layers,
  and spatial context compiled from scenario declarations
- mobility supply: buses, shared bikes, parking, road capacity, service
  frequency
- dynamic environment: weather, congestion, closures, incidents, facility
  opening status
- routing and travel cost queries
- perception API for agents
- future multimodal context: street-view images and environment media

Rules:

- Agents access environment state through controlled observation/perception
  APIs.
- Current routing is deterministic network-route movement with fixed or manually
  adjusted link costs.
- Capacity, congestion, queueing, BPR/Vickrey dynamics, transit vehicles, and
  dynamic network loading are next-stage transport supply models.
- Grid layers are spatial overlays for aggregation, heatmaps, sampling,
  indexing, and observation context.
- Dedicated grid movement belongs in a separate movement backend when a model
  requires it.
- Routing can be implemented internally or delegated to a routing service.

### 4. Scenario System

Purpose: define what world is simulated.

Responsibilities:

- load scenario data
- construct initial world state
- construct agent population
- define initial schedules and activity demand
- define available mobility modes and facilities
- define static spatial declarations: coordinate reference, extent, semantic
  areas, optional grid overlays, grid cells, property layers, and spatial index
  preferences
- define baseline policies and constraints
- define scenario variants

Planned public-data scenario inputs:

- Census TIGER/Line geography
- ACS or ACS PUMS demographic inputs
- LEHD/LODES origin-destination flows
- NHTS travel behavior priors
- GTFS transit feeds
- EPA Smart Location Database indicators
- OSM or other routable network inputs when appropriate

Transportation benchmark and model targets:

- fixed-cost shortest-route commute and closure/accessibility experiments
- Pigou or parallel-route user-equilibrium examples
- Braess network intervention examples
- Vickrey bottleneck departure-time and queueing examples
- BPR link-performance static assignment and Sioux Falls-style benchmarks
- MATSim-style activity plans, scoring, replanning, and repeated iterations
- SUMO-style microscopic network execution through future adapters

Rules:

- Scenario defines what to simulate.
- Experiment owns metrics and run counts.
- Scenario owns static spatial declarations.
- Runtime occupancy, mutable congestion, agent positions, replay state, and
  spatial query caches belong to environment and experiment runtime layers.
- Dataset-specific and domain-specific logic lives in scenario adapters.

### 5. Experiment & Data Collection System

Purpose: define how simulations are run, compared, measured, and exported.

Responsibilities:

- select scenario and scenario variants
- configure run parameters
- configure random seeds
- run single simulations or batches
- compare baselines and LLM-driven policies
- collect metrics
- collect traces
- collect LLM prompt/response records
- support replay and audit
- export results for notebooks, dashboards, and reports

Current built-in metric scope:

- final simulation time
- event counts
- agent lifecycle counts
- movement event and mode counts

Target transportation metrics:

- arrival delay
- lateness rate
- average travel time
- mode share
- walking/cycling/bus usage
- congestion level
- queue length
- facility crowding
- satisfaction
- energy or carbon proxy
- LLM call count and cost
- policy intervention effect

Rules:

- Experiment defines how to run and evaluate.
- Experiment depends on scenario.
- Scenario stays upstream of experiment outputs.
- Metrics and traces are reproducible from run config, seed, scenario version,
  and policy version.
- Batch comparison, assignment/equilibrium loops, calibration, and repeated
  replanning iterations are experiment-layer responsibilities.

### 6. Visualization & Interface System

Purpose: present simulation state, experiment outputs, and analysis results.

Responsibilities:

- live simulation views
- replay views
- regional, neighborhood, and network map views
- agent trajectory visualization
- network and facility overlays
- congestion, queue, and crowding heatmaps
- mode share and travel-time charts
- experiment comparison dashboards
- prompt/decision trace inspection
- export-ready figures, tables, and report assets
- notebook, web, CLI, and API interfaces

Possible components:

- `MapView`
- `ReplayView`
- `Dashboard`
- `TraceInspector`
- `MetricsExplorer`
- `VisualizationDataset`
- `FigureExporter`
- `WebInterface`

Rules:

- Visualization consumes simulation state, traces, metrics, and scenario
  metadata.
- Visualization consumes state and artifacts through read-only data contracts.
- Simulation semantics stay in core, scenario, environment, agent, experiment,
  and service contracts.
- Experiment outputs should include visualization-ready data contracts.
- UI-specific models stay outside core, agent, environment, and scenario
  modules.

### 7. Services / Extensions

Purpose: external capabilities and replaceable backends.

Responsibilities:

- LLM provider access
- LLM prompt rendering
- structured output validation
- LLM cache and retry
- routing backend adapters
- storage backend adapters
- data connectors
- calibration and evaluation helpers
- frontend or report export backends when they are external integrations

Possible services:

- `LLMService`
- `RoutingService`
- `StorageService`
- `TraceStore`
- `MetricsStore`
- `DataConnector`
- `ExportService`

Rules:

- LLM provider details stay in services.
- Routing and simulation engines are planned to be swappable through service or
  adapter boundaries: NetworkX, OSRM, SUMO, MATSim, or future backends.
- Storage backends are swappable: local files, SQLite, Parquet, Postgres, or
  future systems.
- Simulation semantics stay in framework contracts; services provide replaceable
  external capabilities.

## Dependency Direction

```text
Experiment
  -> Scenario
  -> Core contracts
  -> Agent System
  -> Environment System
  -> Services

Agent System
  -> Core contracts
  -> Environment perception API
  -> Services for LLM or other policy backends

Environment System
  -> Core contracts
  -> Scenario contracts
  -> Services for routing/data backends

Visualization & Interface System
  -> Scenario metadata
  -> Environment geometry
  -> Experiment traces, metrics, and snapshots
  -> Services for storage/export backends

Core
  -> generic runtime contracts
```

Rules:

- Core stays upstream of Agent, Environment, Scenario, Experiment, and LLM
  provider layers.
- Scenario configures Agent and Environment.
- Experiment runs Scenario and collects data.
- Visualization consumes scenario metadata, traces, metrics, and snapshots.
- Services provide replaceable backends.

## Suggested Package Structure

```text
campussociety/
  core/
    clock.py
    scheduler.py
    events.py
    entities.py
    simulation.py
    snapshots.py

  agents/
    profile.py
    state.py
    plans.py
    decisions.py
    context.py
    behavior/
    cognition/
    runtime/

  environment/
    world.py
    network.py
    facilities.py
    movement.py
    routing.py
    spatial.py
    spatial_layers.py
    observation.py

  scenario/
    base.py
    config.py
    loaders.py
    population.py
    spatial.py
    world.py
    variants.py

  experiments/
    artifacts.py
    assembly.py
    config.py
    listeners.py
    metrics.py
    replay.py
    results.py
    runner.py
    traces.py

  visualization/
    datasets.py
    dashboards.py
    exporters.py
    geometry.py
    layers.py
    metrics.py
    readers.py
    replay.py
    traces.py

  services/
    llm/
    routing/
    storage/
    data/
    export/

  adapters/
    city/
      README.md
```

## Current MVP Boundary

Implemented:

- deterministic simulation core with scheduler, event bus, entity registry, and
  snapshots
- scenario specs for population, network, facilities, mobility supply, variants,
  and spatial layers
- environment runtime world with fixed-cost routing, deterministic movement,
  facilities, agent physical locations, and spatial overlay observations
- agent runtime for trip/activity plans and swappable behavior models
- single-run experiment orchestration with traces, basic metrics, replay, and
  artifacts
- visualization artifact export for network, facilities, replay frames,
  metrics, and trace events
- provider-neutral LLM service contracts, prompt rendering, cache/retry wrappers,
  and deterministic test clients

Roadmap capabilities:

- public-data download/connectors/loaders for Census, LODES, NHTS, GTFS, EPA,
  OSM, or Sioux Falls-style benchmark data
- first-class OD demand, OD matrix, demand expansion, or zone connectors
- flow-dependent link costs, BPR functions, queues, Vickrey bottleneck dynamics,
  dynamic network loading, or traffic assignment/equilibrium loops
- transit vehicle operations, schedules, headway/wait-time simulation, or
  microscopic car-following/lane models
- batch experiment comparison, calibration loops, and MATSim-style scoring and
  replanning iterations

## Mobility and Transport Testbed Scope

Initial public data inputs:

- Census TIGER/Line boundaries and roads
- ACS or ACS PUMS demographic records
- LEHD/LODES home-work OD flows
- NHTS travel behavior distributions
- GTFS transit service feeds
- EPA Smart Location Database indicators
- optional OSM-derived routable networks

Initial simulated entities:

- synthetic persons or households
- homes and residential zones
- workplaces and employment zones
- facilities and activity locations
- road, walking, cycling, and transit network elements
- transit stops and services
- zones, tracts, block groups, or other public-data geographies

Initial benchmark progression:

1. fixed-cost commute with shortest-route movement, closures, and accessibility
   metrics
2. OD demand and zone connector scenarios, including LODES-informed commuting
3. Pigou, parallel-route, and Braess network examples for route choice and
   intervention effects
4. BPR link-performance static assignment and Sioux Falls-style benchmarks
5. Vickrey bottleneck departure-time choice and queueing
6. activity-based daily schedules with NHTS or ATUS priors
7. MATSim-style scoring, replanning, and repeated iterations
8. GTFS transit supply and service-frequency interventions

Initial policies and behavior models:

- rule-based baseline
- simple discrete-choice baseline
- LLM-driven mode and departure-time choice
- hybrid policy with rule constraints and LLM fallback

LLM call timing:

- daily plan generation or adjustment
- pre-trip mode/departure/route preference decision
- replanning under abnormal events
- end-of-day memory update

Rules:

- Movement execution is deterministic.
- LLM calls happen in planning, decision, replanning, and memory phases.
- Grid layers support spatial context and aggregation. Cell-based traffic
  execution belongs in a dedicated grid movement backend.
- Routing, network loading, queues, transit operations, and traffic assignment
  stay outside agent behavior models.

## Reproducibility Requirements

Every run records:

- scenario id and version
- experiment id
- random seed
- behavior model and policy or intervention version
- LLM model and prompt version, if used
- LLM input summary
- LLM structured output
- validation result
- decision or movement intent executed by the simulation
- event trace
- metrics output

LLM response cache keys include:

- prompt version
- model
- structured context
- relevant generation parameters

## Naming Guidance

Framework-level names:

- `Agent`
- `Place`
- `Facility`
- `Network`
- `Mode`
- `Trip`
- `Activity`
- `BehaviorModel`
- `PolicyIntervention`
- `Observation`
- `Event`
- `Area`
- `Zone`
- `SpatialLayer`
- `GridLayer`

Public-data and scenario adapter names:

- `CensusTract`
- `BlockGroup`
- `ODFlow`
- `SyntheticPerson`
- `Home`
- `Workplace`
- `TransitStop`

Transport model names:

- `ODFlow`
- `ODMatrix`
- `RouteChoice`
- `LinkCostFunction`
- `NetworkLoading`
- `TrafficAssignment`

## Project Records

Use separate records for project history.

Files:

- `AGENTS.md`: project guide, architecture boundaries, coding rules, and
  collaboration rules
- `CHANGELOG.md`: chronological summary of user-visible or architecture-level
  changes
- `docs/decisions/`: Architecture Decision Records

Changelog rules:

- Add meaningful project changes under `## Unreleased`.
- Record architecture changes, new layers, major behavior changes, new
  dependencies, data format changes, and experiment protocol changes.
- Keep entries concise and factual.
- Keep single-session implementation notes out of `CHANGELOG.md`.

ADR rules:

- Create an ADR when a decision changes architecture, long-term interfaces, data
  contracts, experiment methodology, or provider/backend strategy.
- Use sequential filenames: `0001-title.md`, `0002-title.md`.
- Use this structure: `Status`, `Context`, `Decision`, `Consequences`.
- Keep accepted decisions stable. Add a new ADR to supersede an old decision.
- ADR 0009 supersedes older campus-first ADR language only for initial testbed
  scope; older ADRs remain valid for architecture boundaries until a newer ADR
  explicitly supersedes them.
