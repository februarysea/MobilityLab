from __future__ import annotations

from dataclasses import dataclass, field

from mobilitylab.agents.cognition.direct import DirectReasoning
from mobilitylab.agents.cognition.reasoning import ReasoningStrategy
from mobilitylab.agents.context import DecisionContext
from mobilitylab.agents.decisions import AgentDecision, NoOpDecision


@dataclass(frozen=True, slots=True)
class CognitiveBehavior:
    """Cognition-backed behavior shell with pluggable reasoning strategy."""

    behavior_id: str = "cognitive"
    reasoning_strategy: ReasoningStrategy = field(default_factory=DirectReasoning)

    def decide(self, context: DecisionContext) -> AgentDecision:
        if context.cognition_state is None:
            return NoOpDecision(
                agent_id=context.agent_id,
                reason="cognitive behavior requires cognition state",
            )
        return self.reasoning_strategy.reason(context, context.cognition_state)
