from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from campussociety.core.entities import EntityId, JsonValue
from campussociety.environment._utils import (
    copy_json_mapping,
    require_non_empty,
    require_positive,
)
from campussociety.environment.facilities import RuntimeFacility
from campussociety.environment.spatial import LocationRef, Position

if TYPE_CHECKING:
    from campussociety.environment.world import RuntimeWorld


@dataclass(frozen=True, slots=True)
class ObservationRequest:
    """Readonly request for an agent-facing environment observation."""

    agent_id: EntityId
    max_facilities: int = 10
    facility_types: tuple[str, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(str(self.agent_id), "agent_id")
        require_positive(self.max_facilities, "max_facilities")
        object.__setattr__(self, "facility_types", tuple(self.facility_types))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "agent_id": str(self.agent_id),
            "max_facilities": self.max_facilities,
            "facility_types": list(self.facility_types),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class ObservedFacility:
    """Facility summary exposed through the observation API."""

    facility_id: str
    facility_type: str
    open: bool
    occupancy: int
    capacity: int | None = None
    distance_meters: float | None = None

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "facility_id": self.facility_id,
            "facility_type": self.facility_type,
            "open": self.open,
            "occupancy": self.occupancy,
            "capacity": self.capacity,
            "distance_meters": self.distance_meters,
        }


@dataclass(frozen=True, slots=True)
class AgentObservation:
    """Controlled readonly view of the environment for one agent."""

    agent_id: EntityId
    time: int
    location: LocationRef
    available_modes: tuple[str, ...] = ()
    nearby_facilities: tuple[ObservedFacility, ...] = ()
    media_refs: tuple[str, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "available_modes", tuple(self.available_modes))
        object.__setattr__(
            self,
            "nearby_facilities",
            tuple(self.nearby_facilities),
        )
        object.__setattr__(self, "media_refs", tuple(self.media_refs))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "agent_id": str(self.agent_id),
            "time": self.time,
            "location": self.location.to_record(),
            "available_modes": list(self.available_modes),
            "nearby_facilities": [
                facility.to_record() for facility in self.nearby_facilities
            ],
            "media_refs": list(self.media_refs),
            "attributes": copy_json_mapping(self.attributes),
        }


class ObservationService:
    """Produces agent-facing readonly observations from RuntimeWorld."""

    def observe(
        self,
        request: ObservationRequest,
        world: RuntimeWorld,
        *,
        time: int,
    ) -> AgentObservation:
        location = world.get_agent_location(request.agent_id)
        return AgentObservation(
            agent_id=request.agent_id,
            time=time,
            location=location,
            available_modes=world.mobility_mode_ids(),
            nearby_facilities=self._nearby_facilities(
                request,
                world,
                location=location,
            ),
            media_refs=(),
        )

    def _nearby_facilities(
        self,
        request: ObservationRequest,
        world: RuntimeWorld,
        *,
        location: LocationRef,
    ) -> tuple[ObservedFacility, ...]:
        allowed_types = set(request.facility_types)
        origin_position = world.position_for_location(location)
        observed: list[ObservedFacility] = []
        for facility in world.facilities.values():
            if allowed_types and facility.facility_type not in allowed_types:
                continue
            observed.append(
                self._observe_facility(
                    facility,
                    world,
                    origin_position=origin_position,
                )
            )
        observed.sort(
            key=lambda item: (
                item.distance_meters is None,
                0.0 if item.distance_meters is None else item.distance_meters,
                item.facility_id,
            )
        )
        return tuple(observed[: request.max_facilities])

    def _observe_facility(
        self,
        facility: RuntimeFacility,
        world: RuntimeWorld,
        *,
        origin_position: Position | None,
    ) -> ObservedFacility:
        facility_position = world.position_for_facility(facility)
        distance = None
        if origin_position is not None and facility_position is not None:
            distance = origin_position.distance_to(facility_position)
        return ObservedFacility(
            facility_id=facility.facility_id,
            facility_type=facility.facility_type,
            open=facility.state.open,
            occupancy=facility.state.occupancy,
            capacity=facility.capacity,
            distance_meters=distance,
        )
