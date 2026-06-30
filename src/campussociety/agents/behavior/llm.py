from __future__ import annotations

from dataclasses import dataclass, field

from campussociety.agents.cognition.direct import DirectReasoning
from campussociety.agents.cognition.reasoning import ReasoningStrategy
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision, NoOpDecision


@dataclass(frozen=True, slots=True)
class LLMBehavior:
    """LLM-backed behavior shell with pluggable reasoning strategy."""

    behavior_id: str = "llm"
    reasoning_strategy: ReasoningStrategy = field(default_factory=DirectReasoning)

    def decide(self, context: DecisionContext) -> AgentDecision:
        if context.cognition_state is None:
            return NoOpDecision(
                agent_id=context.agent_id,
                reason="llm behavior requires cognition state",
            )
        return self.reasoning_strategy.reason(context, context.cognition_state)
