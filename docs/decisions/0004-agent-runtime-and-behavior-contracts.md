# 0004 Agent Runtime and Behavior Contracts

## Status

Accepted

## Context

CampusSociety needs to support traditional agent-based simulation,
LLM-driven behavior, and hybrid behavior without making LLM cognition part of
the simulation core. The project also needs to keep policy and intervention
logic distinct from agent decision mechanisms.

The simulation core already owns deterministic time, scheduling, events, and
snapshots. The scenario layer owns initial population and plans. The environment
layer owns physical world state, controlled observations, routing, and the
movement kernel.

## Decision

The agent layer uses `RuntimeAgent` as the stable runtime entity. The agent's
decision mechanism is attached as a replaceable `BehaviorModel`.

Agent behavior implementations include deterministic rule-based behavior,
future discrete-choice behavior, LLM-backed behavior, and hybrid behavior. The
agent layer does not use `Policy` as the decision mechanism name; policy remains
reserved for interventions, governance rules, and experiment policy settings.

LLM and hybrid behavior can use optional cognition components:

- `CognitiveState`
- `MemoryStore`
- `ReasoningStrategy`
- `LLMAuditRecord`

Rule-based and discrete-choice behavior do not require cognition state.

All behavior implementations return a structured `AgentDecision`. The
`AgentSystem` validates and executes decisions, calls environment observation
APIs, requests movement through the environment movement kernel, and records
events through the core event bus.

Agent physical location remains authoritative in `RuntimeWorld`, not in
`AgentState`.

## Consequences

Traditional ABM agents stay lightweight and deterministic.

LLM-backed agents can swap reasoning strategies such as direct decision,
ReAct-style reasoning, or reflection without changing the runtime agent class.

Experiments can compare behavior models over the same population and scenario.

Movement execution remains deterministic and outside the agent decision model.
