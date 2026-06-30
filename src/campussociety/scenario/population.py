from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue, State
from campussociety.scenario._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
    require_unique,
)
from campussociety.scenario.errors import ScenarioValidationError


@dataclass(frozen=True, slots=True)
class ActivitySpec:
    """Planned activity demand for an agent."""

    activity_id: str
    activity_type: str
    start_time: int | None = None
    end_time: int | None = None
    location_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.activity_id, "activity_id")
        require_non_empty(self.activity_type, "activity_type")
        if self.start_time is not None:
            require_non_negative(self.start_time, "start_time")
        if self.end_time is not None:
            require_non_negative(self.end_time, "end_time")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.end_time < self.start_time
        ):
            msg = "end_time must be greater than or equal to start_time"
            raise ScenarioValidationError(msg)
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location_id": self.location_id,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class PlanSpec:
    """Ordered activity plan for an agent."""

    plan_id: str
    activities: tuple[ActivitySpec, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.plan_id, "plan_id")
        object.__setattr__(self, "activities", tuple(self.activities))
        require_unique(
            (activity.activity_id for activity in self.activities),
            "activities",
        )
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "plan_id": self.plan_id,
            "activities": [activity.to_record() for activity in self.activities],
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Scenario-level agent declaration before behavior is attached."""

    agent_id: str
    agent_type: str = "agent"
    profile: Mapping[str, JsonValue] = field(default_factory=dict)
    initial_state: Mapping[str, JsonValue] = field(default_factory=dict)
    plans: tuple[PlanSpec, ...] = ()
    policy_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.agent_id, "agent_id")
        require_non_empty(self.agent_type, "agent_type")
        object.__setattr__(self, "profile", copy_json_mapping(self.profile))
        object.__setattr__(self, "initial_state", copy_json_mapping(self.initial_state))
        object.__setattr__(self, "plans", tuple(self.plans))
        require_unique((plan.plan_id for plan in self.plans), "plans")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "profile": copy_json_mapping(self.profile),
            "initial_state": copy_json_mapping(self.initial_state),
            "plans": [plan.to_record() for plan in self.plans],
            "policy_id": self.policy_id,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class PopulationSpec:
    """Synthetic or observed population loaded by a scenario."""

    agents: tuple[AgentSpec, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "agents", tuple(self.agents))
        require_unique((agent.agent_id for agent in self.agents), "agents")
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def size(self) -> int:
        return len(self.agents)

    def agent_ids(self) -> tuple[str, ...]:
        return tuple(agent.agent_id for agent in self.agents)

    def to_record(self) -> State:
        return {
            "agents": [agent.to_record() for agent in self.agents],
            "metadata": copy_json_mapping(self.metadata),
        }
