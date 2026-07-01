from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from mobilitylab.core.entities import JsonValue, copy_state

VISUALIZATION_MANIFEST_SCHEMA_VERSION = "mobilitylab.visualization.manifest.v1"


class DatasetCapability(StrEnum):
    """Display or query capability advertised by a visualization dataset."""

    NETWORK_GEOMETRY = "network_geometry"
    FACILITY_POINTS = "facility_points"
    REPLAY_FRAMES = "replay_frames"
    EVENT_TIMELINE = "event_timeline"
    METRIC_SUMMARY = "metric_summary"
    TRACE_EVENTS = "trace_events"


@dataclass(frozen=True, slots=True)
class ColumnSpec:
    """Column-level semantics for UI and notebook consumers."""

    name: str
    logical_type: str
    role: str | None = None
    unit: str | None = None
    required: bool = True
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "name")
        _require_non_empty(self.logical_type, "logical_type")
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "logical_type": self.logical_type,
            "role": self.role,
            "unit": self.unit,
            "required": self.required,
            "metadata": copy_state(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VisualizationDataset:
    """One dataset that can be consumed by a visualization surface."""

    dataset_id: str
    title: str
    kind: str
    path: str
    format: str
    capabilities: tuple[DatasetCapability, ...] = ()
    columns: tuple[ColumnSpec, ...] = ()
    time_key: str | None = None
    entity_key: str | None = None
    geometry_key: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = "mobilitylab.visualization.dataset.v1"

    def __post_init__(self) -> None:
        for field_name, value in {
            "dataset_id": self.dataset_id,
            "title": self.title,
            "kind": self.kind,
            "path": self.path,
            "format": self.format,
            "schema": self.schema,
        }.items():
            _require_non_empty(value, field_name)
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def has_capability(self, capability: DatasetCapability) -> bool:
        return capability in self.capabilities

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "dataset_id": self.dataset_id,
            "title": self.title,
            "kind": self.kind,
            "path": self.path,
            "format": self.format,
            "capabilities": [capability.value for capability in self.capabilities],
            "columns": [column.to_record() for column in self.columns],
            "time_key": self.time_key,
            "entity_key": self.entity_key,
            "geometry_key": self.geometry_key,
            "metadata": copy_state(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class DatasetCatalog:
    """Deterministic dataset registry for one visualization export."""

    datasets: tuple[VisualizationDataset, ...] = ()
    schema: str = "mobilitylab.visualization.dataset_catalog.v1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "datasets", tuple(self.datasets))
        seen: set[str] = set()
        for dataset in self.datasets:
            if dataset.dataset_id in seen:
                msg = f"duplicate visualization dataset: {dataset.dataset_id}"
                raise ValueError(msg)
            seen.add(dataset.dataset_id)

    def get(self, dataset_id: str) -> VisualizationDataset:
        for dataset in self.datasets:
            if dataset.dataset_id == dataset_id:
                return dataset
        msg = f"unknown visualization dataset: {dataset_id}"
        raise KeyError(msg)

    def with_dataset(self, dataset: VisualizationDataset) -> DatasetCatalog:
        return DatasetCatalog((*self.datasets, dataset), schema=self.schema)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "datasets": [dataset.to_record() for dataset in self.datasets],
        }


@dataclass(frozen=True, slots=True)
class VisualizationManifest:
    """Entrypoint consumed by web, notebook, and report visualization clients."""

    run_id: str
    scenario_id: str
    scenario_version: str
    variant_id: str
    final_time: int
    catalog: DatasetCatalog
    dashboards: tuple[Mapping[str, JsonValue], ...] = ()
    source_artifacts: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = VISUALIZATION_MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field_name, value in {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "variant_id": self.variant_id,
            "schema": self.schema,
        }.items():
            _require_non_empty(value, field_name)
        if self.final_time < 0:
            msg = "final_time must be non-negative"
            raise ValueError(msg)
        object.__setattr__(
            self,
            "dashboards",
            tuple(copy_state(dashboard) for dashboard in self.dashboards),
        )
        object.__setattr__(self, "source_artifacts", copy_state(self.source_artifacts))
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "variant_id": self.variant_id,
            "final_time": self.final_time,
            "catalog": self.catalog.to_record(),
            "dashboards": [copy_state(dashboard) for dashboard in self.dashboards],
            "source_artifacts": copy_state(self.source_artifacts),
            "metadata": copy_state(self.metadata),
        }


def catalog_from_iterable(
    datasets: Iterable[VisualizationDataset],
) -> DatasetCatalog:
    return DatasetCatalog(tuple(datasets))


def _require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)
