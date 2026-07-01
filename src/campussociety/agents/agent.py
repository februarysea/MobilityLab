from __future__ import annotations

from dataclasses import dataclass

from campussociety.agents.behavior.base import BehaviorModel
from campussociety.agents.cognition.state import CognitiveState
from campussociety.agents.context import DecisionContext
from campussociety.agents.decisions import AgentDecision
from campussociety.agents.plans import AgentPlan
from campussociety.agents.profile import AgentProfile
from campussociety.agents.state import AgentState
from campussociety.core.entities import EntityId, State


@dataclass(slots=True)
class RuntimeAgent:
    """Runtime agent entity with replaceable behavior."""

    id: EntityId
    agent_type: str
    profile: AgentProfile
    state: AgentState
    behavior_model: BehaviorModel
    selected_plan: AgentPlan | None = None
    cognition_state: CognitiveState | None = None

    def decide(self, context: DecisionContext) -> AgentDecision:
        return self.behavior_model.decide(context)

    def snapshot_state(self) -> State:
        return {
            "entity_type": "agent",
            "schema": "campussociety.agent.runtime.v1",
            "agent_id": str(self.id),
            "agent_type": self.agent_type,
            "profile": self.profile.to_record(),
            "state": self.state.to_record(),
            "selected_plan": None
            if self.selected_plan is None
            else self.selected_plan.to_record(),
            "behavior_id": self.behavior_model.behavior_id,
            "cognition_state": None
            if self.cognition_state is None
            else self.cognition_state.to_record(),
        }
