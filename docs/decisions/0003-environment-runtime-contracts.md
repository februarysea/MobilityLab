# 0003 Environment Runtime Contracts

## Status

Accepted

## Context

CampusSociety now has a deterministic simulation core and a scenario system that
loads static world declarations. The next layer needs to turn a prepared
scenario into a runtime world that agents can observe and move through.

Reference implementations separate these concerns in different ways:

- Mesa offers useful space, network, occupancy, and neighborhood query patterns,
  but often lets agents directly read or mutate the model environment.
- AgentSociety v2 uses controlled environment tools and observations, but its
  code-generation router and large mobility space are too heavy for the
  framework core.
- MATSim separates static scenario supply, routing queries, mobsim execution,
  and event traces. Its QSim is too complex for the first campus MVP, but the
  routing-versus-execution boundary is important.

The environment MVP must define the movement kernel early because movement is a
central runtime behavior, not a later visualization or experiment concern.

## Decision

Environment is the runtime world layer installed into a core `Simulation`.

The MVP contains four primary contracts:

- `RuntimeWorld`: authoritative runtime state for network links, facilities,
  mobility modes, agent physical locations, and basic deterministic queries.
- `RoutingService`: readonly route calculation contract. Routing consumes the
  current `RuntimeWorld` and returns a `Route`; it does not mutate runtime state.
- `MovementKernel`: deterministic movement executor. It consumes
  `MovementIntent`, obtains a route, advances active movements by simulation
  time, updates `RuntimeWorld`, and emits structured movement events.
- `ObservationService`: readonly agent-facing view over `RuntimeWorld`.

The initial implementation keeps routing backend replacement explicit through a
`RoutingService` protocol and provides a small deterministic
`SimpleNetworkRouter`.

`Environment` itself is registered as a core entity so core snapshots can
capture runtime world and movement state without adding domain concepts to
`core/`.

The MVP intentionally does not include:

- a separate `ChangeApplier`;
- street-view or media loading;
- transit vehicle simulation;
- congestion or queue dynamics;
- LLM rendering or LLM calls.

Runtime changes such as link closures or facility capacity updates are currently
explicit `RuntimeWorld` methods. A future `ChangeApplier` can be introduced when
scenario variants and experiment interventions need a common change-record
contract.

Street-view and media remain observation-layer extension points. They may later
be exposed as media references through observations, but they do not belong in
the movement kernel.

## Consequences

The environment layer has a clear state and mutation boundary:

- Scenario defines the initial world and demand.
- Environment owns runtime world state, movement execution, and observations.
- Routing is replaceable and remains readonly.
- Movement is the only default mechanism that changes agent physical location.
- Agents should consume `ObservationService` output rather than unrestricted
  runtime world internals.
- Core remains domain-free and only supplies clock, scheduler, events, entities,
  and snapshots.

This keeps the campus MVP small while preserving a future path to richer routing
backends, street-view observations, transit supply, interventions, and more
MATSim-like movement engines.
