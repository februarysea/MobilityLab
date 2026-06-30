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
class NetworkNodeSpec:
    """Scenario-level spatial network node."""

    node_id: str
    x: float | None = None
    y: float | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.node_id, "node_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "node_id": self.node_id,
            "x": self.x,
            "y": self.y,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class NetworkLinkSpec:
    """Scenario-level directed or undirected network link."""

    link_id: str
    from_node_id: str
    to_node_id: str
    length_meters: float | None = None
    allowed_modes: tuple[str, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.link_id, "link_id")
        require_non_empty(self.from_node_id, "from_node_id")
        require_non_empty(self.to_node_id, "to_node_id")
        if self.length_meters is not None:
            require_non_negative(self.length_meters, "length_meters")
        object.__setattr__(self, "allowed_modes", tuple(self.allowed_modes))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "link_id": self.link_id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "length_meters": self.length_meters,
            "allowed_modes": list(self.allowed_modes),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class NetworkSpec:
    """Network supply loaded by a scenario."""

    nodes: tuple[NetworkNodeSpec, ...] = ()
    links: tuple[NetworkLinkSpec, ...] = ()
    coordinate_system: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "links", tuple(self.links))
        require_unique((node.node_id for node in self.nodes), "nodes")
        require_unique((link.link_id for link in self.links), "links")
        node_ids = {node.node_id for node in self.nodes}
        missing_endpoints = tuple(
            sorted(
                {
                    endpoint
                    for link in self.links
                    for endpoint in (link.from_node_id, link.to_node_id)
                    if endpoint not in node_ids
                }
            )
        )
        if missing_endpoints:
            msg = "links reference unknown node ids: " + ", ".join(missing_endpoints)
            raise ScenarioValidationError(msg)
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def node_count(self) -> int:
        return len(self.nodes)

    @property
    def link_count(self) -> int:
        return len(self.links)

    def to_record(self) -> State:
        return {
            "nodes": [node.to_record() for node in self.nodes],
            "links": [link.to_record() for link in self.links],
            "coordinate_system": self.coordinate_system,
            "metadata": copy_json_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class FacilitySpec:
    """Scenario-level place or facility declaration."""

    facility_id: str
    facility_type: str
    location_id: str | None = None
    capacity: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.facility_id, "facility_id")
        require_non_empty(self.facility_type, "facility_type")
        if self.capacity is not None:
            require_non_negative(self.capacity, "capacity")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "facility_id": self.facility_id,
            "facility_type": self.facility_type,
            "location_id": self.location_id,
            "capacity": self.capacity,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class FacilitiesSpec:
    """Facility inventory loaded by a scenario."""

    facilities: tuple[FacilitySpec, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "facilities", tuple(self.facilities))
        require_unique(
            (facility.facility_id for facility in self.facilities),
            "facilities",
        )
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def size(self) -> int:
        return len(self.facilities)

    def to_record(self) -> State:
        return {
            "facilities": [facility.to_record() for facility in self.facilities],
            "metadata": copy_json_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class MobilityModeSpec:
    """Available mobility mode or supply class."""

    mode_id: str
    mode_type: str
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.mode_id, "mode_id")
        require_non_empty(self.mode_type, "mode_type")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "mode_id": self.mode_id,
            "mode_type": self.mode_type,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class MobilitySupplySpec:
    """Mobility supply loaded by a scenario."""

    modes: tuple[MobilityModeSpec, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "modes", tuple(self.modes))
        require_unique((mode.mode_id for mode in self.modes), "modes")
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def mode_count(self) -> int:
        return len(self.modes)

    def to_record(self) -> State:
        return {
            "modes": [mode.to_record() for mode in self.modes],
            "metadata": copy_json_mapping(self.metadata),
        }
