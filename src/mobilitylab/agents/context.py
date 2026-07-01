from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from random import Random
from typing import TYPE_CHECKING

from mobilitylab.agents._utils import copy_json_mapping
from mobilitylab.agents.plans import AgentPlan
from mobilitylab.agents.profile import AgentProfile
from mobilitylab.agents.state import AgentState
from mobilitylab.core.entities import EntityId, JsonValue
from mobilitylab.core.events import Event
from mobilitylab.environment.observation import AgentObservation

if TYPE_CHECKING:
    from mobilitylab.agents.cognition.state import CognitiveState


@dataclass(frozen=True, slots=True)
class DecisionContext:
    """Readonly input passed to an agent behavior model."""

    agent_id: EntityId
    time: int
    profile: AgentProfile
    state: AgentState
    selected_plan: AgentPlan | None
    observation: AgentObservation
    rng: Random
    recent_events: tuple[Event, ...] = ()
    cognition_state: CognitiveState | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "recent_events", tuple(self.recent_events))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "agent_id": str(self.agent_id),
            "time": self.time,
            "profile": self.profile.to_record(),
            "state": self.state.to_record(),
            "selected_plan": None
            if self.selected_plan is None
            else self.selected_plan.to_record(),
            "observation": self.observation.to_record(),
            "recent_event_count": len(self.recent_events),
            "has_cognition_state": self.cognition_state is not None,
            "attributes": copy_json_mapping(self.attributes),
        }
