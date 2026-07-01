from __future__ import annotations

from dataclasses import dataclass, field

from mobilitylab.agents.behavior.base import BehaviorModel
from mobilitylab.agents.behavior.cognitive import CognitiveBehavior
from mobilitylab.agents.behavior.rule_based import RuleBasedBehavior
from mobilitylab.agents.context import DecisionContext
from mobilitylab.agents.decisions import AgentDecision, AgentDecisionType


@dataclass(frozen=True, slots=True)
class HybridBehavior:
    """Rule-first behavior with an optional cognition-backed fallback."""

    behavior_id: str = "hybrid"
    primary: BehaviorModel = field(default_factory=RuleBasedBehavior)
    fallback: BehaviorModel = field(default_factory=CognitiveBehavior)

    def decide(self, context: DecisionContext) -> AgentDecision:
        decision = self.primary.decide(context)
        if decision.decision_type is AgentDecisionType.REPLAN:
            return self.fallback.decide(context)
        return decision
