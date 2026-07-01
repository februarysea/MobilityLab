# CampusSociety Project Guide

## Project Scope

CampusSociety is a simulation framework for LLM-driven, traditional, and
hybrid agent-based mobility simulation.

The first testbeds use openly available U.S. public datasets for classic ABM
and mobility experiments. The architecture remains compatible with larger
regional and city-scale scenarios from the start.

## Architecture Principles

- Keep the full simulation architecture in place.
- Start each layer with the smallest useful implementation.
- Keep domain-specific logic out of the framework core.
- Support traditional ABM, LLM-driven agents, and hybrid policies.
- Keep simulation execution deterministic and reproducible.
- Record structured traces for debugging, evaluation, and replay.
- Treat LLM calls as policy/service behavior, not simulation-core behavior.
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

- `core/` contains no scenario-specific concepts.
- `core/` contains no geography-specific concepts.
- `core/` contains no LLM provider calls.
- `core/` exposes stable contracts for agents, environment, scenarios, and
  experiments.

### 2. Agent System

Purpose: agent definitions, state, behavior, and interaction.

Responsibilities:

- agent profile: role, demographics, preferences, budget, mobility access
- agent state: location, current activity, schedule, trip status, fatigue,
  satisfaction
- agent plans: daily activity plans, trip plans, fallback plans
- behavior models: rule-based, discrete-choice, cognition-backed, or hybrid
  decision making
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

### 3. Environment System

Purpose: external world, mobility supply, and observable context.

Responsibilities:

- spatial network: walking, cycling, vehicle, and future multimodal networks
- places and facilities: homes, workplaces, schools, shops, stations, parking
  areas, and public facilities
- mobility supply: buses, shared bikes, parking, road capacity, service
  frequency
- dynamic environment: weather, congestion, closures, incidents, facility
  opening status
- routing and travel cost queries
- perception API for agents
- future multimodal context: street-view images and environment media

Rules:

- Agents access environment state through observation/perception APIs.
- Agents do not read unrestricted global state.
- Routing cost depends on current environment state.
- Routing can be implemented internally or delegated to a routing service.

### 4. Scenario System

Purpose: define what world is simulated.

Responsibilities:

- load scenario data
- construct initial world state
- construct agent population
- define initial schedules and activity demand
- define available mobility modes and facilities
- define baseline policies and constraints
- define scenario variants

Initial public-data scenario examples:

- Census TIGER/Line geography
- ACS or ACS PUMS demographic inputs
- LEHD/LODES origin-destination flows
- NHTS travel behavior priors
- GTFS transit feeds
- EPA Smart Location Database indicators
- OSM or other routable network inputs when appropriate

Classic ABM experiment examples:

- Schelling-style residential sorting
- commuting flow and departure-time simulation
- activity schedule simulation
- mode-choice baseline comparison
- accessibility or transit service interventions
- road, facility, or service disruption scenarios

Rules:

- Scenario defines what to simulate.
- Scenario does not own experiment metrics.
- Scenario does not decide run counts.
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

Example metrics:

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
- Scenario does not depend on experiment.
- Metrics and traces are reproducible from run config, seed, scenario version,
  and policy version.

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
- Visualization does not mutate simulation state.
- Visualization does not define simulation semantics.
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
- Routing engines are swappable: NetworkX, OSRM, SUMO, MATSim, or future
  backends.
- Storage backends are swappable: local files, SQLite, Parquet, Postgres, or
  future systems.
- Services do not define simulation semantics.

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
  -> Services for routing/data backends

Visualization & Interface System
  -> Scenario metadata
  -> Environment geometry
  -> Experiment traces, metrics, and snapshots
  -> Services for storage/export backends

Core
  -> no domain-specific layer
```

Rules:

- Core does not depend on Agent, Environment, Scenario, Experiment, or LLM.
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
    behavior/
    cognition/
    perception.py
    memory.py
    interactions.py

  environment/
    world.py
    network.py
    places.py
    mobility_supply.py
    routing.py
    dynamics.py
    observation.py

  scenario/
    base.py
    loaders.py
    population.py
    variants.py

  experiments/
    runner.py
    config.py
    metrics.py
    traces.py
    replay.py
    export.py

  visualization/
    datasets.py
    maps.py
    replay.py
    dashboards.py
    trace_inspector.py
    figures.py
    web.py

  services/
    llm/
    routing/
    storage/
    data/
    export/

  adapters/
    us/
      README.md

    census/
      README.md

    lodes/
      README.md

    nhts/
      README.md

    gtfs/
      README.md

    epa/
      README.md
```

## Initial Public-data ABM Testbed Scope

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

Initial experiments:

- Schelling-style residential sorting
- LODES-informed commuting simulation
- NHTS-informed mode and departure-time choice
- activity schedule simulation
- transit accessibility or service-frequency interventions
- road closure, facility disruption, or pricing interventions

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
- The movement kernel does not call the LLM at every simulation step.

## Reproducibility Requirements

Every run records:

- scenario id and version
- experiment id
- random seed
- policy backend and version
- LLM model and prompt version, if used
- LLM input summary
- LLM structured output
- validation result
- action executed by the simulation
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
- `Policy`
- `Observation`
- `Event`

Public-data and scenario adapter names:

- `CensusTract`
- `BlockGroup`
- `ODFlow`
- `SyntheticPerson`
- `Home`
- `Workplace`
- `TransitStop`

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
- Do not use `CHANGELOG.md` for implementation notes that are only useful
  during a single coding session.

ADR rules:

- Create an ADR when a decision changes architecture, long-term interfaces, data
  contracts, experiment methodology, or provider/backend strategy.
- Use sequential filenames: `0001-title.md`, `0002-title.md`.
- Use this structure: `Status`, `Context`, `Decision`, `Consequences`.
- Keep accepted decisions stable. Add a new ADR to supersede an old decision.
