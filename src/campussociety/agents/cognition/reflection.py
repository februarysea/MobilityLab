from __future__ import annotations

from dataclasses import dataclass

from campussociety.agents.cognition.state import CognitiveState
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision, NoOpDecision


@dataclass(frozen=True, slots=True)
class ReflectionReasoning:
    """Placeholder for reflection-first LLM reasoning."""

    strategy_id: str = "reflection"

    def reason(
        self,
        context: DecisionContext,
        cognition_state: CognitiveState,
    ) -> AgentDecision:
        return NoOpDecision(
            agent_id=context.agent_id,
            reason="reflection reasoning is not connected to an LLM service",
        )
