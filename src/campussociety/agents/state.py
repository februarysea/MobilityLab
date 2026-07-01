from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from campussociety.agents._utils import copy_json_mapping, require_non_negative
from campussociety.core.entities import JsonValue


class AgentLifecycleStatus(StrEnum):
    """Runtime lifecycle state for a simulated agent."""

    IDLE = "idle"
    WAITING = "waiting"
    IN_ACTIVITY = "in_activity"
    TRAVELING = "traveling"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class AgentState:
    """Mutable runtime state owned by the agent layer.

    Physical location is intentionally not stored here. The authoritative
    location lives in the environment runtime world.
    """

    lifecycle_status: AgentLifecycleStatus = AgentLifecycleStatus.IDLE
    current_plan_element_index: int = 0
    current_activity_id: str | None = None
    current_activity_end_time: int | None = None
    current_trip_id: str | None = None
    last_decision_time: int | None = None
    fatigue: float = 0.0
    satisfaction: float = 0.0
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_negative(
            self.current_plan_element_index,
            "current_plan_element_index",
        )
        if self.current_activity_end_time is not None:
            require_non_negative(
                self.current_activity_end_time,
                "current_activity_end_time",
            )
        if self.last_decision_time is not None:
            require_non_negative(self.last_decision_time, "last_decision_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "lifecycle_status": self.lifecycle_status.value,
            "current_plan_element_index": self.current_plan_element_index,
            "current_activity_id": self.current_activity_id,
            "current_activity_end_time": self.current_activity_end_time,
            "current_trip_id": self.current_trip_id,
            "last_decision_time": self.last_decision_time,
            "fatigue": self.fatigue,
            "satisfaction": self.satisfaction,
            "attributes": copy_json_mapping(self.attributes),
        }

    def copy(self) -> AgentState:
        return AgentState(
            lifecycle_status=self.lifecycle_status,
            current_plan_element_index=self.current_plan_element_index,
            current_activity_id=self.current_activity_id,
            current_activity_end_time=self.current_activity_end_time,
            current_trip_id=self.current_trip_id,
            last_decision_time=self.last_decision_time,
            fatigue=self.fatigue,
            satisfaction=self.satisfaction,
            attributes=self.attributes,
        )
