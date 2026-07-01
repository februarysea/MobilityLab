from __future__ import annotations

from dataclasses import dataclass

from mobilitylab.agents.cognition.state import CognitiveState
from mobilitylab.agents.context import DecisionContext
from mobilitylab.agents.decisions import AgentDecision, NoOpDecision


@dataclass(frozen=True, slots=True)
class DirectReasoning:
    """Placeholder direct reasoning strategy for future LLM integration."""

    strategy_id: str = "direct"

    def reason(
        self,
        context: DecisionContext,
        cognition_state: CognitiveState,
    ) -> AgentDecision:
        return NoOpDecision(
            agent_id=context.agent_id,
            reason="direct reasoning is not connected to an LLM service",
        )
