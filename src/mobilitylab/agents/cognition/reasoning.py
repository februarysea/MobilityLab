from __future__ import annotations

from typing import Protocol, runtime_checkable

from mobilitylab.agents.cognition.state import CognitiveState
from mobilitylab.agents.context import DecisionContext
from mobilitylab.agents.decisions import AgentDecision


@runtime_checkable
class ReasoningStrategy(Protocol):
    """Pluggable reasoning strategy used inside cognition-backed behavior."""

    @property
    def strategy_id(self) -> str: ...

    def reason(
        self,
        context: DecisionContext,
        cognition_state: CognitiveState,
    ) -> AgentDecision: ...
