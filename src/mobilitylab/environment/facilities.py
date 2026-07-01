from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from mobilitylab.core.entities import JsonValue
from mobilitylab.environment._utils import (
    copy_json_mapping,
    optional_float,
    require_non_empty,
    require_non_negative,
)
from mobilitylab.environment.errors import EnvironmentValidationError
from mobilitylab.environment.network import RuntimeNetwork
from mobilitylab.environment.spatial import Position
from mobilitylab.scenario.world import FacilitiesSpec, FacilitySpec


@dataclass(slots=True)
class FacilityState:
    """Mutable runtime state for a facility."""

    open: bool = True
    occupancy: int = 0

    def __post_init__(self) -> None:
        require_non_negative(self.occupancy, "occupancy")

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "open": self.open,
            "occupancy": self.occupancy,
        }


@dataclass(slots=True)
class RuntimeFacility:
    """Runtime facility or place used by environment queries and movement."""

    facility_id: str
    facility_type: str
    access_node_id: str | None = None
    position: Position | None = None
    capacity: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)
    state: FacilityState = field(default_factory=FacilityState)

    def __post_init__(self) -> None:
        require_non_empty(self.facility_id, "facility_id")
        require_non_empty(self.facility_type, "facility_type")
        if self.capacity is not None:
            require_non_negative(self.capacity, "capacity")
        self.attributes = copy_json_mapping(self.attributes)

    @classmethod
    def from_spec(
        cls,
        spec: FacilitySpec,
        *,
        network: RuntimeNetwork,
    ) -> RuntimeFacility:
        access_node_id = spec.location_id
        if access_node_id is None and network.contains_node(spec.facility_id):
            access_node_id = spec.facility_id
        if access_node_id is not None and not network.contains_node(access_node_id):
            msg = (
                "facility references unknown access node: "
                f"{spec.facility_id} -> {access_node_id}"
            )
            raise EnvironmentValidationError(msg)

        x = optional_float(spec.attributes, "x")
        y = optional_float(spec.attributes, "y")
        position = Position(x, y) if x is not None and y is not None else None
        return cls(
            facility_id=spec.facility_id,
            facility_type=spec.facility_type,
            access_node_id=access_node_id,
            position=position,
            capacity=spec.capacity,
            attributes=spec.attributes,
        )

    def has_capacity_for_entry(self) -> bool:
        return self.capacity is None or self.state.occupancy < self.capacity

    def enter(self, count: int = 1) -> None:
        require_non_negative(count, "count")
        if self.capacity is not None and self.state.occupancy + count > self.capacity:
            msg = f"facility capacity exceeded: {self.facility_id}"
            raise EnvironmentValidationError(msg)
        self.state.occupancy += count

    def leave(self, count: int = 1) -> None:
        require_non_negative(count, "count")
        if self.state.occupancy - count < 0:
            msg = f"facility occupancy cannot be negative: {self.facility_id}"
            raise EnvironmentValidationError(msg)
        self.state.occupancy -= count

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "facility_id": self.facility_id,
            "facility_type": self.facility_type,
            "access_node_id": self.access_node_id,
            "position": None if self.position is None else self.position.to_record(),
            "capacity": self.capacity,
            "attributes": copy_json_mapping(self.attributes),
            "state": self.state.to_record(),
        }


class FacilityStore:
    """Runtime facility store with deterministic id ordering."""

    def __init__(
        self,
        facilities: Iterable[RuntimeFacility] = (),
        *,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self.metadata = copy_json_mapping(metadata or {})
        self._facilities: dict[str, RuntimeFacility] = {}
        for facility in facilities:
            self.add(facility)

    @classmethod
    def from_spec(
        cls,
        spec: FacilitiesSpec,
        *,
        network: RuntimeNetwork,
    ) -> FacilityStore:
        return cls(
            (
                RuntimeFacility.from_spec(facility, network=network)
                for facility in spec.facilities
            ),
            metadata=spec.metadata,
        )

    @property
    def size(self) -> int:
        return len(self._facilities)

    def add(self, facility: RuntimeFacility) -> None:
        if facility.facility_id in self._facilities:
            msg = f"facility already exists: {facility.facility_id}"
            raise EnvironmentValidationError(msg)
        self._facilities[facility.facility_id] = facility

    def contains(self, facility_id: str) -> bool:
        return facility_id in self._facilities

    def get(self, facility_id: str) -> RuntimeFacility:
        try:
            return self._facilities[facility_id]
        except KeyError as exc:
            msg = f"unknown facility: {facility_id}"
            raise KeyError(msg) from exc

    def facility_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._facilities))

    def values(self) -> tuple[RuntimeFacility, ...]:
        return tuple(
            self._facilities[facility_id] for facility_id in self.facility_ids()
        )

    def set_open(self, facility_id: str, open_: bool) -> None:
        self.get(facility_id).state.open = open_

    def set_capacity(self, facility_id: str, capacity: int | None) -> None:
        if capacity is not None:
            require_non_negative(capacity, "capacity")
        facility = self.get(facility_id)
        if capacity is not None and facility.state.occupancy > capacity:
            msg = f"capacity cannot be lower than current occupancy: {facility_id}"
            raise EnvironmentValidationError(msg)
        facility.capacity = capacity

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "facility_count": self.size,
            "facilities": [facility.to_record() for facility in self.values()],
            "metadata": copy_json_mapping(self.metadata),
        }
