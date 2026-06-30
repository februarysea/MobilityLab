from __future__ import annotations

from typing import Protocol, runtime_checkable

from campussociety.agents.cognition.state import CognitiveState
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision


@runtime_checkable
class ReasoningStrategy(Protocol):
    """Pluggable reasoning strategy used inside LLM-backed behavior."""

    @property
    def strategy_id(self) -> str: ...

    def reason(
        self,
        context: DecisionContext,
        cognition_state: CognitiveState,
    ) -> AgentDecision: ...
