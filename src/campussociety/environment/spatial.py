from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import sqrt

from campussociety.core.entities import JsonValue
from campussociety.environment._utils import copy_json_mapping, require_non_empty


class LocationKind(StrEnum):
    """Runtime location reference kind."""

    NODE = "node"
    LINK = "link"
    FACILITY = "facility"
    ROUTE = "route"


@dataclass(frozen=True, slots=True)
class Position:
    """Coordinate position in the scenario coordinate system."""

    x: float
    y: float
    z: float | None = None

    def distance_to(self, other: Position) -> float:
        dz = 0.0 if self.z is None or other.z is None else self.z - other.z
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2 + dz**2)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }


@dataclass(frozen=True, slots=True)
class LocationRef:
    """Stable reference to a runtime location."""

    kind: LocationKind
    id: str
    position: Position | None = None
    detail: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.id, "id")
        object.__setattr__(self, "detail", copy_json_mapping(self.detail))

    @classmethod
    def node(cls, node_id: str) -> LocationRef:
        return cls(kind=LocationKind.NODE, id=node_id)

    @classmethod
    def link(cls, link_id: str) -> LocationRef:
        return cls(kind=LocationKind.LINK, id=link_id)

    @classmethod
    def facility(cls, facility_id: str) -> LocationRef:
        return cls(kind=LocationKind.FACILITY, id=facility_id)

    @classmethod
    def route(
        cls,
        movement_id: str,
        *,
        position: Position | None = None,
        detail: Mapping[str, JsonValue] | None = None,
    ) -> LocationRef:
        return cls(
            kind=LocationKind.ROUTE,
            id=movement_id,
            position=position,
            detail=detail or {},
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "kind": self.kind.value,
            "id": self.id,
            "position": None if self.position is None else self.position.to_record(),
            "detail": copy_json_mapping(self.detail),
        }
