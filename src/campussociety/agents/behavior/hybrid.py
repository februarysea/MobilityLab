from __future__ import annotations

from dataclasses import dataclass, field

from campussociety.agents.behavior.base import BehaviorModel
from campussociety.agents.behavior.llm import LLMBehavior
from campussociety.agents.behavior.rule_based import RuleBasedBehavior
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision, AgentDecisionType


@dataclass(frozen=True, slots=True)
class HybridBehavior:
    """Rule-first behavior with an optional cognition-backed fallback."""

    behavior_id: str = "hybrid"
    primary: BehaviorModel = field(default_factory=RuleBasedBehavior)
    fallback: BehaviorModel = field(default_factory=LLMBehavior)

    def decide(self, context: DecisionContext) -> AgentDecision:
        decision = self.primary.decide(context)
        if decision.decision_type is AgentDecisionType.REPLAN:
            return self.fallback.decide(context)
        return decision
