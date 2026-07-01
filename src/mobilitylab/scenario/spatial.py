from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from mobilitylab.core.entities import JsonValue, State
from mobilitylab.scenario._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
    require_unique,
)
from mobilitylab.scenario.errors import ScenarioValidationError


class SpatialGeometryType(StrEnum):
    """Declared geometry representation type."""

    POINT = "point"
    POLYGON = "polygon"
    MULTIPOLYGON = "multipolygon"
    SOURCE_REF = "source_ref"


class GridLayerType(StrEnum):
    """Declared grid layer type."""

    REGULAR_SQUARE = "regular_square"
    H3 = "h3"
    CUSTOM = "custom"


class SpatialIndexKind(StrEnum):
    """Preferred runtime spatial index kind for a spatial layer."""

    NONE = "none"
    STRTREE = "strtree"
    QUADTREE = "quadtree"
    H3 = "h3"


BUILTIN_SPATIAL_INDEX_TARGETS = frozenset(
    {
        "areas",
        "facilities",
        "network_nodes",
        "network_links",
    }
)


@dataclass(frozen=True, slots=True)
class CoordinateReference:
    """Scenario-level coordinate reference declaration."""

    crs_id: str
    authority: str | None = None
    epsg: int | None = None
    units: str | None = None
    description: str = ""
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.crs_id, "crs_id")
        if self.epsg is not None and self.epsg <= 0:
            msg = "epsg must be positive"
            raise ScenarioValidationError(msg)
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "crs_id": self.crs_id,
            "authority": self.authority,
            "epsg": self.epsg,
            "units": self.units,
            "description": self.description,
            "metadata": copy_json_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PointSpec:
    """Coordinate point in a scenario spatial layer."""

    x: float
    y: float
    z: float | None = None

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Axis-aligned spatial extent in the declared coordinate reference."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    min_z: float | None = None
    max_z: float | None = None

    def __post_init__(self) -> None:
        if self.max_x < self.min_x:
            msg = "max_x must be greater than or equal to min_x"
            raise ScenarioValidationError(msg)
        if self.max_y < self.min_y:
            msg = "max_y must be greater than or equal to min_y"
            raise ScenarioValidationError(msg)
        if (
            self.min_z is not None
            and self.max_z is not None
            and self.max_z < self.min_z
        ):
            msg = "max_z must be greater than or equal to min_z"
            raise ScenarioValidationError(msg)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "min_z": self.min_z,
            "max_z": self.max_z,
        }


@dataclass(frozen=True, slots=True)
class GeometrySpec:
    """Declared geometry payload or external geometry source reference."""

    geometry_type: SpatialGeometryType
    coordinates: JsonValue = None
    source_id: str | None = None
    source_layer: str | None = None
    properties: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.geometry_type is SpatialGeometryType.SOURCE_REF and (
            self.source_id is None or self.source_id == ""
        ):
            msg = "source_ref geometry requires source_id"
            raise ScenarioValidationError(msg)
        object.__setattr__(self, "properties", copy_json_mapping(self.properties))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "geometry_type": self.geometry_type.value,
            "coordinates": self.coordinates,
            "source_id": self.source_id,
            "source_layer": self.source_layer,
            "properties": copy_json_mapping(self.properties),
        }


@dataclass(frozen=True, slots=True)
class AreaSpec:
    """Semantic area, zone, or AOI declared by a scenario."""

    area_id: str
    area_type: str
    name: str | None = None
    centroid: PointSpec | None = None
    geometry: GeometrySpec | None = None
    parent_area_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.area_id, "area_id")
        require_non_empty(self.area_type, "area_type")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "area_id": self.area_id,
            "area_type": self.area_type,
            "name": self.name,
            "centroid": None if self.centroid is None else self.centroid.to_record(),
            "geometry": None if self.geometry is None else self.geometry.to_record(),
            "parent_area_id": self.parent_area_id,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class GridCellSpec:
    """Static cell declaration for a grid layer."""

    cell_id: str
    row: int | None = None
    column: int | None = None
    area_id: str | None = None
    centroid: PointSpec | None = None
    geometry: GeometrySpec | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.cell_id, "cell_id")
        if self.row is not None:
            require_non_negative(self.row, "row")
        if self.column is not None:
            require_non_negative(self.column, "column")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "cell_id": self.cell_id,
            "row": self.row,
            "column": self.column,
            "area_id": self.area_id,
            "centroid": None if self.centroid is None else self.centroid.to_record(),
            "geometry": None if self.geometry is None else self.geometry.to_record(),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class GridLayerSpec:
    """Declared grid overlay; runtime occupancy belongs to environment state."""

    layer_id: str
    grid_type: GridLayerType
    coordinate_reference: CoordinateReference | None = None
    extent: BoundingBox | None = None
    cell_size_meters: float | None = None
    resolution: int | None = None
    topology: str | None = None
    cells: tuple[GridCellSpec, ...] = ()
    initial_property_layers: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.layer_id, "layer_id")
        if self.cell_size_meters is not None and self.cell_size_meters <= 0:
            msg = "cell_size_meters must be positive"
            raise ScenarioValidationError(msg)
        if self.resolution is not None:
            require_non_negative(self.resolution, "resolution")
        object.__setattr__(self, "cells", tuple(self.cells))
        require_unique((cell.cell_id for cell in self.cells), "cells")
        object.__setattr__(
            self,
            "initial_property_layers",
            copy_json_mapping(self.initial_property_layers),
        )
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "layer_id": self.layer_id,
            "grid_type": self.grid_type.value,
            "coordinate_reference": (
                None
                if self.coordinate_reference is None
                else self.coordinate_reference.to_record()
            ),
            "extent": None if self.extent is None else self.extent.to_record(),
            "cell_size_meters": self.cell_size_meters,
            "resolution": self.resolution,
            "topology": self.topology,
            "cells": [cell.to_record() for cell in self.cells],
            "initial_property_layers": copy_json_mapping(self.initial_property_layers),
            "metadata": copy_json_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SpatialIndexSpec:
    """Preferred runtime index declaration for spatial queries."""

    index_id: str
    index_kind: SpatialIndexKind
    target_id: str
    target_kinds: tuple[str, ...] = ()
    options: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.index_id, "index_id")
        require_non_empty(self.target_id, "target_id")
        object.__setattr__(self, "target_kinds", tuple(self.target_kinds))
        object.__setattr__(self, "options", copy_json_mapping(self.options))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "index_id": self.index_id,
            "index_kind": self.index_kind.value,
            "target_id": self.target_id,
            "target_kinds": list(self.target_kinds),
            "options": copy_json_mapping(self.options),
        }


@dataclass(frozen=True, slots=True)
class SpatialLayersSpec:
    """Static spatial declarations loaded by a scenario."""

    coordinate_reference: CoordinateReference | None = None
    extent: BoundingBox | None = None
    areas: tuple[AreaSpec, ...] = ()
    grid_layers: tuple[GridLayerSpec, ...] = ()
    spatial_indexes: tuple[SpatialIndexSpec, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "areas", tuple(self.areas))
        object.__setattr__(self, "grid_layers", tuple(self.grid_layers))
        object.__setattr__(self, "spatial_indexes", tuple(self.spatial_indexes))
        require_unique((area.area_id for area in self.areas), "areas")
        require_unique((layer.layer_id for layer in self.grid_layers), "grid_layers")
        require_unique(
            (index.index_id for index in self.spatial_indexes),
            "spatial_indexes",
        )

        area_ids = {area.area_id for area in self.areas}
        missing_parent_ids = tuple(
            sorted(
                area.parent_area_id
                for area in self.areas
                if area.parent_area_id is not None
                and area.parent_area_id not in area_ids
            )
        )
        if missing_parent_ids:
            msg = "areas reference unknown parent ids: " + ", ".join(missing_parent_ids)
            raise ScenarioValidationError(msg)

        layer_ids = {layer.layer_id for layer in self.grid_layers}
        missing_target_ids = tuple(
            sorted(
                index.target_id
                for index in self.spatial_indexes
                if index.target_id not in layer_ids
                and index.target_id not in BUILTIN_SPATIAL_INDEX_TARGETS
            )
        )
        if missing_target_ids:
            msg = "spatial indexes reference unknown targets: " + ", ".join(
                missing_target_ids
            )
            raise ScenarioValidationError(msg)

        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def area_count(self) -> int:
        return len(self.areas)

    @property
    def grid_layer_count(self) -> int:
        return len(self.grid_layers)

    @property
    def spatial_index_count(self) -> int:
        return len(self.spatial_indexes)

    def to_record(self) -> State:
        return {
            "coordinate_reference": (
                None
                if self.coordinate_reference is None
                else self.coordinate_reference.to_record()
            ),
            "extent": None if self.extent is None else self.extent.to_record(),
            "areas": [area.to_record() for area in self.areas],
            "grid_layers": [layer.to_record() for layer in self.grid_layers],
            "spatial_indexes": [index.to_record() for index in self.spatial_indexes],
            "metadata": copy_json_mapping(self.metadata),
        }
