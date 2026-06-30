from __future__ import annotations

from dataclasses import dataclass

from campussociety.agents.behavior.rule_based import RuleBasedBehavior
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision


@dataclass(frozen=True, slots=True)
class DiscreteChoiceBehavior:
    """Placeholder behavior slot for future discrete-choice models.

    Until a utility model is configured, this delegates to deterministic
    plan-following behavior so experiments have a working baseline path.
    """

    behavior_id: str = "discrete_choice"
    fallback: RuleBasedBehavior = RuleBasedBehavior()

    def decide(self, context: DecisionContext) -> AgentDecision:
        return self.fallback.decide(context)
