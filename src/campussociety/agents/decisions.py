from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, runtime_checkable

from campussociety.agents._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
)
from campussociety.core.entities import EntityId, JsonValue
from campussociety.environment.spatial import LocationRef


class AgentDecisionType(StrEnum):
    """Structured decision categories emitted by behavior models."""

    NO_OP = "no_op"
    WAIT = "wait"
    START_ACTIVITY = "start_activity"
    END_ACTIVITY = "end_activity"
    START_TRIP = "start_trip"
    REPLAN = "replan"
    COMMUNICATE = "communicate"


@runtime_checkable
class AgentDecision(Protocol):
    """Common protocol for all agent decisions."""

    @property
    def agent_id(self) -> EntityId: ...

    @property
    def reason(self) -> str | None: ...

    @property
    def attributes(self) -> Mapping[str, JsonValue]: ...

    @property
    def decision_type(self) -> AgentDecisionType: ...

    def to_record(self) -> dict[str, JsonValue]: ...


@dataclass(frozen=True, slots=True)
class NoOpDecision:
    agent_id: EntityId
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.NO_OP

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return _base_record(self)


@dataclass(frozen=True, slots=True)
class WaitDecision:
    agent_id: EntityId
    until_time: int
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.WAIT

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_negative(self.until_time, "until_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        record = _base_record(self)
        record["until_time"] = self.until_time
        return record


@dataclass(frozen=True, slots=True)
class StartActivityDecision:
    agent_id: EntityId
    activity_id: str
    activity_type: str
    location: LocationRef | None = None
    start_time: int | None = None
    end_time: int | None = None
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.START_ACTIVITY

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_empty(self.activity_id, "activity_id")
        require_non_empty(self.activity_type, "activity_type")
        if self.start_time is not None:
            require_non_negative(self.start_time, "start_time")
        if self.end_time is not None:
            require_non_negative(self.end_time, "end_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        record = _base_record(self)
        record.update(
            {
                "activity_id": self.activity_id,
                "activity_type": self.activity_type,
                "location": None
                if self.location is None
                else self.location.to_record(),
                "start_time": self.start_time,
                "end_time": self.end_time,
            }
        )
        return record


@dataclass(frozen=True, slots=True)
class EndActivityDecision:
    agent_id: EntityId
    activity_id: str
    end_time: int | None = None
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.END_ACTIVITY

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_empty(self.activity_id, "activity_id")
        if self.end_time is not None:
            require_non_negative(self.end_time, "end_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        record = _base_record(self)
        record["activity_id"] = self.activity_id
        record["end_time"] = self.end_time
        return record


@dataclass(frozen=True, slots=True)
class StartTripDecision:
    agent_id: EntityId
    destination: LocationRef
    mode: str
    origin: LocationRef | None = None
    departure_time: int | None = None
    movement_id: str | None = None
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.START_TRIP

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_empty(self.mode, "mode")
        if self.departure_time is not None:
            require_non_negative(self.departure_time, "departure_time")
        if self.movement_id is not None:
            require_non_empty(self.movement_id, "movement_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        record = _base_record(self)
        record.update(
            {
                "origin": None if self.origin is None else self.origin.to_record(),
                "destination": self.destination.to_record(),
                "mode": self.mode,
                "departure_time": self.departure_time,
                "movement_id": self.movement_id,
            }
        )
        return record


@dataclass(frozen=True, slots=True)
class ReplanDecision:
    agent_id: EntityId
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.REPLAN

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return _base_record(self)


@dataclass(frozen=True, slots=True)
class CommunicateDecision:
    agent_id: EntityId
    recipient_id: EntityId
    message: str
    reason: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    @property
    def decision_type(self) -> AgentDecisionType:
        return AgentDecisionType.COMMUNICATE

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_non_empty(str(self.recipient_id), "recipient_id")
        require_non_empty(self.message, "message")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        record = _base_record(self)
        record["recipient_id"] = str(self.recipient_id)
        record["message"] = self.message
        return record


def _base_record(decision: AgentDecision) -> dict[str, JsonValue]:
    return {
        "agent_id": str(decision.agent_id),
        "decision_type": decision.decision_type.value,
        "reason": decision.reason,
        "attributes": copy_json_mapping(decision.attributes),
    }
