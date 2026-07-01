# 0005 Agent Decision Parallelism

## Status

Accepted

## Context

MobilityLab agents may use lightweight rule-based behavior, discrete-choice
models, cognition-backed behavior, or hybrid behavior. Cognition-backed
decisions and some future choice models can be expensive enough to require
concurrent execution.

The simulation runtime still needs deterministic replay. The environment owns
authoritative physical state, and movement execution must remain deterministic.

## Decision

Agent activation is split into two phases:

- decision phase: build readonly `DecisionContext` objects and execute
  behavior models through a `DecisionExecutor`
- apply phase: emit decisions and apply them to the runtime world in stable
  agent-id order

The default executor is `SerialDecisionExecutor`. A `ThreadedDecisionExecutor`
is available for IO-bound or cognition-backed behavior. Executors must return
results in request sequence order and must not mutate the environment or core
runtime.

Agent activations scheduled for the same simulation time are batched by
`AgentSystem`. Each decision context receives an agent-specific deterministic
random generator derived from the simulation seed, simulation id, current time,
and agent id. This avoids shared RNG contention when decisions are executed
concurrently.

## Consequences

Rule-based behavior remains simple and deterministic.

Cognition-backed behavior can later run concurrently without changing
environment mutation semantics.

Runtime state changes, movement requests, and event emission remain ordered and
replayable.
