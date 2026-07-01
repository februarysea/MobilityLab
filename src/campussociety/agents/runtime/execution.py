from __future__ import annotations

from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from campussociety.agents.agent import RuntimeAgent
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision
from campussociety.core.entities import EntityId


@dataclass(frozen=True, slots=True)
class AgentDecisionRequest:
    """One pure decision request prepared from a runtime snapshot."""

    sequence: int
    agent: RuntimeAgent
    context: DecisionContext

    @property
    def agent_id(self) -> EntityId:
        return self.agent.id

    def decide(self) -> AgentDecision:
        return self.agent.decide(self.context)


@dataclass(frozen=True, slots=True)
class AgentDecisionResult:
    """Decision returned by an executor before deterministic application."""

    sequence: int
    agent_id: EntityId
    decision: AgentDecision


@runtime_checkable
class DecisionExecutor(Protocol):
    """Executes prepared agent decision requests.

    Executors may run requests sequentially or concurrently, but must return
    results sorted by request sequence and must not apply decisions to the
    runtime world.
    """

    @property
    def executor_id(self) -> str: ...

    def decide(
        self,
        requests: Sequence[AgentDecisionRequest],
    ) -> tuple[AgentDecisionResult, ...]: ...


@dataclass(frozen=True, slots=True)
class SerialDecisionExecutor:
    """Deterministic in-process decision executor."""

    executor_id: str = "serial"

    def decide(
        self,
        requests: Sequence[AgentDecisionRequest],
    ) -> tuple[AgentDecisionResult, ...]:
        return tuple(_decide_one(request) for request in requests)


@dataclass(frozen=True, slots=True)
class ThreadedDecisionExecutor:
    """Threaded executor for IO-bound or LLM-backed decision models."""

    max_workers: int | None = None
    executor_id: str = "threaded"

    def decide(
        self,
        requests: Sequence[AgentDecisionRequest],
    ) -> tuple[AgentDecisionResult, ...]:
        if not requests:
            return ()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(_decide_one, request) for request in requests]
            results = tuple(future.result() for future in futures)
        return tuple(sorted(results, key=lambda result: result.sequence))


def _decide_one(request: AgentDecisionRequest) -> AgentDecisionResult:
    return AgentDecisionResult(
        sequence=request.sequence,
        agent_id=request.agent_id,
        decision=request.decide(),
    )
