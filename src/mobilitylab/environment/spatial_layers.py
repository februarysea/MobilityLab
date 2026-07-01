from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from math import floor

from mobilitylab.core.entities import JsonValue, State
from mobilitylab.environment._utils import copy_json_mapping, require_non_empty
from mobilitylab.environment.errors import EnvironmentValidationError
from mobilitylab.environment.spatial import Position
from mobilitylab.scenario.spatial import (
    AreaSpec,
    BoundingBox,
    GridCellSpec,
    GridLayerSpec,
    GridLayerType,
    PointSpec,
    SpatialLayersSpec,
)


def _position_from_point(point: PointSpec | None) -> Position | None:
    if point is None:
        return None
    return Position(point.x, point.y, point.z)


@dataclass(frozen=True, slots=True)
class RuntimeBoundingBox:
    """Runtime axis-aligned extent for spatial overlay queries."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    min_z: float | None = None
    max_z: float | None = None

    @classmethod
    def from_spec(cls, spec: BoundingBox) -> RuntimeBoundingBox:
        return cls(
            min_x=spec.min_x,
            min_y=spec.min_y,
            max_x=spec.max_x,
            max_y=spec.max_y,
            min_z=spec.min_z,
            max_z=spec.max_z,
        )

    def contains(self, position: Position) -> bool:
        if not (self.min_x <= position.x <= self.max_x):
            return False
        if not (self.min_y <= position.y <= self.max_y):
            return False
        if position.z is None:
            return True
        if self.min_z is not None and position.z < self.min_z:
            return False
        return not (self.max_z is not None and position.z > self.max_z)

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
class RuntimeArea:
    """Runtime semantic area, zone, or AOI declaration."""

    area_id: str
    area_type: str
    name: str | None = None
    centroid: Position | None = None
    parent_area_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.area_id, "area_id")
        require_non_empty(self.area_type, "area_type")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    @classmethod
    def from_spec(cls, spec: AreaSpec) -> RuntimeArea:
        return cls(
            area_id=spec.area_id,
            area_type=spec.area_type,
            name=spec.name,
            centroid=_position_from_point(spec.centroid),
            parent_area_id=spec.parent_area_id,
            attributes=spec.attributes,
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "area_id": self.area_id,
            "area_type": self.area_type,
            "name": self.name,
            "centroid": None if self.centroid is None else self.centroid.to_record(),
            "parent_area_id": self.parent_area_id,
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(frozen=True, slots=True)
class RuntimeGridCell:
    """Runtime grid cell used for overlay queries and observation context."""

    layer_id: str
    cell_id: str
    row: int | None = None
    column: int | None = None
    area_id: str | None = None
    centroid: Position | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)
    generated: bool = False

    def __post_init__(self) -> None:
        require_non_empty(self.layer_id, "layer_id")
        require_non_empty(self.cell_id, "cell_id")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    @classmethod
    def from_spec(cls, layer_id: str, spec: GridCellSpec) -> RuntimeGridCell:
        return cls(
            layer_id=layer_id,
            cell_id=spec.cell_id,
            row=spec.row,
            column=spec.column,
            area_id=spec.area_id,
            centroid=_position_from_point(spec.centroid),
            attributes=spec.attributes,
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "layer_id": self.layer_id,
            "cell_id": self.cell_id,
            "row": self.row,
            "column": self.column,
            "area_id": self.area_id,
            "centroid": None if self.centroid is None else self.centroid.to_record(),
            "attributes": copy_json_mapping(self.attributes),
            "generated": self.generated,
        }


class RuntimeLayerStore:
    """Runtime values for grid property layers."""

    def __init__(
        self,
        initial_property_layers: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self._layers = copy_json_mapping(initial_property_layers or {})
        self._cell_values: dict[str, dict[str, JsonValue]] = {}

    def layer_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._layers))

    def set_cell_value(
        self,
        property_id: str,
        cell_id: str,
        value: JsonValue,
    ) -> None:
        require_non_empty(property_id, "property_id")
        require_non_empty(cell_id, "cell_id")
        self._cell_values.setdefault(property_id, {})[cell_id] = value

    def values_for_cell(self, cell_id: str) -> dict[str, JsonValue]:
        return {
            property_id: value
            for property_id in self.layer_ids()
            if (value := self.value_for_cell(property_id, cell_id)) is not None
        }

    def value_for_cell(self, property_id: str, cell_id: str) -> JsonValue:
        if property_id in self._cell_values:
            cell_values = self._cell_values[property_id]
            if cell_id in cell_values:
                return cell_values[cell_id]

        layer_value = self._layers.get(property_id)
        if not isinstance(layer_value, dict):
            return layer_value

        direct_value = layer_value.get(cell_id)
        if direct_value is not None:
            return direct_value

        cells_value = layer_value.get("cells")
        if isinstance(cells_value, dict):
            cell_value = cells_value.get(cell_id)
            if cell_value is not None:
                return cell_value

        return layer_value.get("default")

    def to_record(self) -> State:
        record: State = copy_json_mapping(self._layers)
        if self._cell_values:
            record["runtime_cell_values"] = {
                property_id: copy_json_mapping(values)
                for property_id, values in sorted(self._cell_values.items())
            }
        return record


class RuntimeGridLayer:
    """Runtime grid overlay compiled from a scenario grid layer."""

    def __init__(
        self,
        *,
        layer_id: str,
        grid_type: GridLayerType,
        extent: RuntimeBoundingBox | None = None,
        cell_size_meters: float | None = None,
        resolution: int | None = None,
        topology: str | None = None,
        cells: Iterable[RuntimeGridCell] = (),
        layer_store: RuntimeLayerStore | None = None,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        require_non_empty(layer_id, "layer_id")
        self.layer_id = layer_id
        self.grid_type = grid_type
        self.extent = extent
        self.cell_size_meters = cell_size_meters
        self.resolution = resolution
        self.topology = topology
        self.layer_store = layer_store or RuntimeLayerStore()
        self.metadata = copy_json_mapping(metadata or {})
        self._cells_by_id: dict[str, RuntimeGridCell] = {}
        self._cells_by_coordinate: dict[tuple[int, int], RuntimeGridCell] = {}
        for cell in cells:
            self.add_cell(cell)

    @classmethod
    def from_spec(cls, spec: GridLayerSpec) -> RuntimeGridLayer:
        return cls(
            layer_id=spec.layer_id,
            grid_type=spec.grid_type,
            extent=(
                RuntimeBoundingBox.from_spec(spec.extent)
                if spec.extent is not None
                else None
            ),
            cell_size_meters=spec.cell_size_meters,
            resolution=spec.resolution,
            topology=spec.topology,
            cells=(
                RuntimeGridCell.from_spec(spec.layer_id, cell) for cell in spec.cells
            ),
            layer_store=RuntimeLayerStore(spec.initial_property_layers),
            metadata=spec.metadata,
        )

    @property
    def cell_count(self) -> int:
        return len(self._cells_by_id)

    def add_cell(self, cell: RuntimeGridCell) -> None:
        if cell.layer_id != self.layer_id:
            msg = f"cell layer mismatch: {cell.layer_id} != {self.layer_id}"
            raise EnvironmentValidationError(msg)
        if cell.cell_id in self._cells_by_id:
            msg = f"grid cell already exists: {cell.cell_id}"
            raise EnvironmentValidationError(msg)
        self._cells_by_id[cell.cell_id] = cell
        if cell.row is not None and cell.column is not None:
            self._cells_by_coordinate[(cell.row, cell.column)] = cell

    def cell_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._cells_by_id))

    def cells(self) -> tuple[RuntimeGridCell, ...]:
        return tuple(self._cells_by_id[cell_id] for cell_id in self.cell_ids())

    def get_cell(self, cell_id: str) -> RuntimeGridCell:
        try:
            return self._cells_by_id[cell_id]
        except KeyError as exc:
            msg = f"unknown grid cell: {cell_id}"
            raise KeyError(msg) from exc

    def cell_at(self, position: Position) -> RuntimeGridCell | None:
        if self.grid_type is GridLayerType.REGULAR_SQUARE:
            return self._regular_square_cell_at(position)
        return self._nearest_explicit_cell(position)

    def layer_values_for_cell(self, cell_id: str) -> dict[str, JsonValue]:
        return self.layer_store.values_for_cell(cell_id)

    def layer_values_at(self, position: Position) -> dict[str, JsonValue]:
        cell = self.cell_at(position)
        if cell is None:
            return {}
        return self.layer_values_for_cell(cell.cell_id)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "layer_id": self.layer_id,
            "grid_type": self.grid_type.value,
            "extent": None if self.extent is None else self.extent.to_record(),
            "cell_size_meters": self.cell_size_meters,
            "resolution": self.resolution,
            "topology": self.topology,
            "cell_count": self.cell_count,
            "cells": [cell.to_record() for cell in self.cells()],
            "property_layers": self.layer_store.to_record(),
            "metadata": copy_json_mapping(self.metadata),
        }

    def _regular_square_cell_at(self, position: Position) -> RuntimeGridCell | None:
        if self.extent is None or self.cell_size_meters is None:
            return self._nearest_explicit_cell(position)
        if not self.extent.contains(position):
            return None

        width = self.extent.max_x - self.extent.min_x
        height = self.extent.max_y - self.extent.min_y
        max_column = max(0, int(width / self.cell_size_meters) - 1)
        max_row = max(0, int(height / self.cell_size_meters) - 1)
        column = min(
            max_column,
            max(0, floor((position.x - self.extent.min_x) / self.cell_size_meters)),
        )
        row = min(
            max_row,
            max(0, floor((position.y - self.extent.min_y) / self.cell_size_meters)),
        )

        explicit_cell = self._cells_by_coordinate.get((row, column))
        if explicit_cell is not None:
            return explicit_cell

        centroid = Position(
            self.extent.min_x + (column + 0.5) * self.cell_size_meters,
            self.extent.min_y + (row + 0.5) * self.cell_size_meters,
        )
        return RuntimeGridCell(
            layer_id=self.layer_id,
            cell_id=f"{self.layer_id}:{row}:{column}",
            row=row,
            column=column,
            centroid=centroid,
            generated=True,
        )

    def _nearest_explicit_cell(self, position: Position) -> RuntimeGridCell | None:
        candidates = tuple(cell for cell in self.cells() if cell.centroid is not None)
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda cell: (
                position.distance_to(cell.centroid)
                if cell.centroid is not None
                else float("inf"),
                cell.cell_id,
            ),
        )


class RuntimeSpatialLayers:
    """Runtime spatial overlays compiled from scenario spatial declarations."""

    def __init__(
        self,
        *,
        coordinate_reference: Mapping[str, JsonValue] | None = None,
        extent: RuntimeBoundingBox | None = None,
        areas: Iterable[RuntimeArea] = (),
        grid_layers: Iterable[RuntimeGridLayer] = (),
        spatial_indexes: tuple[Mapping[str, JsonValue], ...] = (),
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self.coordinate_reference = (
            None
            if coordinate_reference is None
            else copy_json_mapping(coordinate_reference)
        )
        self.extent = extent
        self.metadata = copy_json_mapping(metadata or {})
        self.spatial_indexes = tuple(
            copy_json_mapping(index) for index in spatial_indexes
        )
        self._areas: dict[str, RuntimeArea] = {}
        self._grid_layers: dict[str, RuntimeGridLayer] = {}
        for area in areas:
            self.add_area(area)
        for layer in grid_layers:
            self.add_grid_layer(layer)

    @classmethod
    def empty(cls) -> RuntimeSpatialLayers:
        return cls()

    @classmethod
    def from_spec(cls, spec: SpatialLayersSpec) -> RuntimeSpatialLayers:
        return cls(
            coordinate_reference=(
                spec.coordinate_reference.to_record()
                if spec.coordinate_reference is not None
                else None
            ),
            extent=(
                RuntimeBoundingBox.from_spec(spec.extent)
                if spec.extent is not None
                else None
            ),
            areas=(RuntimeArea.from_spec(area) for area in spec.areas),
            grid_layers=(
                RuntimeGridLayer.from_spec(layer) for layer in spec.grid_layers
            ),
            spatial_indexes=tuple(index.to_record() for index in spec.spatial_indexes),
            metadata=spec.metadata,
        )

    @property
    def area_count(self) -> int:
        return len(self._areas)

    @property
    def grid_layer_count(self) -> int:
        return len(self._grid_layers)

    @property
    def spatial_index_count(self) -> int:
        return len(self.spatial_indexes)

    def add_area(self, area: RuntimeArea) -> None:
        if area.area_id in self._areas:
            msg = f"area already exists: {area.area_id}"
            raise EnvironmentValidationError(msg)
        self._areas[area.area_id] = area

    def add_grid_layer(self, layer: RuntimeGridLayer) -> None:
        if layer.layer_id in self._grid_layers:
            msg = f"grid layer already exists: {layer.layer_id}"
            raise EnvironmentValidationError(msg)
        self._grid_layers[layer.layer_id] = layer

    def area_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._areas))

    def grid_layer_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._grid_layers))

    def areas(self) -> tuple[RuntimeArea, ...]:
        return tuple(self._areas[area_id] for area_id in self.area_ids())

    def grid_layers(self) -> tuple[RuntimeGridLayer, ...]:
        return tuple(self._grid_layers[layer_id] for layer_id in self.grid_layer_ids())

    def get_area(self, area_id: str) -> RuntimeArea:
        try:
            return self._areas[area_id]
        except KeyError as exc:
            msg = f"unknown area: {area_id}"
            raise KeyError(msg) from exc

    def get_grid_layer(self, layer_id: str) -> RuntimeGridLayer:
        try:
            return self._grid_layers[layer_id]
        except KeyError as exc:
            msg = f"unknown grid layer: {layer_id}"
            raise KeyError(msg) from exc

    def cell_at(
        self,
        layer_id: str,
        position: Position,
    ) -> RuntimeGridCell | None:
        return self.get_grid_layer(layer_id).cell_at(position)

    def cells_at(self, position: Position) -> tuple[RuntimeGridCell, ...]:
        cells: list[RuntimeGridCell] = []
        for layer in self.grid_layers():
            cell = layer.cell_at(position)
            if cell is not None:
                cells.append(cell)
        return tuple(cells)

    def layer_values_at(
        self,
        layer_id: str,
        position: Position,
    ) -> dict[str, JsonValue]:
        return self.get_grid_layer(layer_id).layer_values_at(position)

    def layer_values_for_cell(
        self,
        layer_id: str,
        cell_id: str,
    ) -> dict[str, JsonValue]:
        return self.get_grid_layer(layer_id).layer_values_for_cell(cell_id)

    def spatial_context_at(self, position: Position) -> State:
        grid_cell_records: list[JsonValue] = []
        layer_values: dict[str, JsonValue] = {}
        area_ids: set[str] = set()

        for layer in self.grid_layers():
            cell = layer.cell_at(position)
            if cell is None:
                continue
            values = layer.layer_values_for_cell(cell.cell_id)
            grid_cell_records.append(
                {
                    "layer_id": layer.layer_id,
                    "cell_id": cell.cell_id,
                    "row": cell.row,
                    "column": cell.column,
                    "area_id": cell.area_id,
                    "generated": cell.generated,
                    "layer_values": values,
                }
            )
            layer_values[layer.layer_id] = values
            if cell.area_id is not None:
                area_ids.add(cell.area_id)

        area_records: list[JsonValue] = [
            self._areas[area_id].to_record()
            for area_id in sorted(area_ids)
            if area_id in self._areas
        ]
        return {
            "grid_cells": grid_cell_records,
            "layer_values": layer_values,
            "areas": area_records,
        }

    def to_record(self) -> State:
        return {
            "coordinate_reference": self.coordinate_reference,
            "extent": None if self.extent is None else self.extent.to_record(),
            "area_count": self.area_count,
            "grid_layer_count": self.grid_layer_count,
            "spatial_index_count": self.spatial_index_count,
            "areas": [area.to_record() for area in self.areas()],
            "grid_layers": [layer.to_record() for layer in self.grid_layers()],
            "spatial_indexes": [dict(index) for index in self.spatial_indexes],
            "metadata": copy_json_mapping(self.metadata),
        }
