# 0008 Service Backend Contracts

## Status

Accepted

## Context

CampusSociety needs replaceable external capabilities without coupling provider
details to core simulation semantics. The existing layers already define
scenario loading, environment routing and movement, agent behavior,
experiments, and visualization artifacts. Services should support these layers
without becoming a second runtime or a place for domain logic.

The storage, data, and export backend families are expected later, but they are
not necessary for the current MVP.

## Decision

Create a services MVP centered on thin backend contracts:

- `services.llm` owns provider-neutral LLM requests, responses, prompt
  rendering, cache, retry, and deterministic test clients.
- `services.routing` owns wrappers around environment routing contracts, such
  as deterministic route caching.
- `services.config` and `services.registry` provide explicit per-run service
  wiring through `ServiceConfig`, `ServiceBundle`, and `ServiceRegistry`.
- `services.storage`, `services.data`, and `services.export` remain documented
  placeholders until concrete backends are needed.

The agent layer uses `CognitiveBehavior` for cognition-backed decisions. The
name `LLM` is reserved for provider/backend service contracts such as
`LLMClient`.

## Consequences

LLM provider calls, retries, cache keys, and token usage can evolve without
changing agent runtime semantics.

Routing backends can be wrapped or replaced without moving the movement kernel
out of the environment layer.

Storage, data connector, and export implementation work is deferred without
blocking the framework boundary.
