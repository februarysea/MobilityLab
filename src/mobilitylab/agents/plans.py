from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TypeAlias

from mobilitylab.agents._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
    require_unique,
)
from mobilitylab.agents.errors import AgentValidationError
from mobilitylab.core.entities import JsonValue
from mobilitylab.environment.spatial import LocationRef


@dataclass(frozen=True, slots=True)
class ActivityPlan:
    """Planned activity demand for a runtime agent."""

    activity_id: str
    activity_type: str
    start_time: int | None = None
    end_time: int | None = None
    location: LocationRef | None = None
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
            raise AgentValidationError(msg)
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "element_type": "activity",
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": None if self.location is None else self.location.to_record(),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class TripPlan:
    """Planned trip demand.

    The environment movement kernel remains the source of truth for executed
    routes and travel times.
    """

    trip_id: str
    destination: LocationRef
    mode: str
    origin: LocationRef | None = None
    departure_time: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.trip_id, "trip_id")
        require_non_empty(self.mode, "mode")
        if self.departure_time is not None:
            require_non_negative(self.departure_time, "departure_time")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "element_type": "trip",
            "trip_id": self.trip_id,
            "origin": None if self.origin is None else self.origin.to_record(),
            "destination": self.destination.to_record(),
            "mode": self.mode,
            "departure_time": self.departure_time,
            "attributes": copy_json_mapping(self.attributes),
        }


PlanElement: TypeAlias = ActivityPlan | TripPlan


@dataclass(frozen=True, slots=True)
class AgentPlan:
    """Ordered intent data selected by a runtime agent."""

    plan_id: str
    elements: tuple[PlanElement, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.plan_id, "plan_id")
        object.__setattr__(self, "elements", tuple(self.elements))
        require_unique(
            (self._element_id(element) for element in self.elements),
            "elements",
        )
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    @property
    def size(self) -> int:
        return len(self.elements)

    def element_at(self, index: int) -> PlanElement | None:
        if index < 0:
            return None
        if index >= len(self.elements):
            return None
        return self.elements[index]

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "plan_id": self.plan_id,
            "elements": [element.to_record() for element in self.elements],
            "attributes": copy_json_mapping(self.attributes),
        }

    def _element_id(self, element: PlanElement) -> str:
        if isinstance(element, ActivityPlan):
            return f"activity:{element.activity_id}"
        return f"trip:{element.trip_id}"
