from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from mobilitylab.core.entities import JsonValue, copy_state
from mobilitylab.visualization.layers import LayerSpec, LayerType


class PanelType(StrEnum):
    """High-level viewer panel families."""

    MAP = "map"
    TIMELINE = "timeline"
    METRICS = "metrics"
    EVENTS = "events"


@dataclass(frozen=True, slots=True)
class PanelSpec:
    """A dashboard panel that points to datasets or layers."""

    panel_id: str
    title: str
    panel_type: PanelType
    dataset_ids: tuple[str, ...] = ()
    layer_ids: tuple[str, ...] = ()
    options: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = "mobilitylab.visualization.panel.v1"

    def __post_init__(self) -> None:
        for field_name, value in {
            "panel_id": self.panel_id,
            "title": self.title,
            "schema": self.schema,
        }.items():
            if value == "":
                msg = f"{field_name} must not be empty"
                raise ValueError(msg)
        object.__setattr__(self, "dataset_ids", tuple(self.dataset_ids))
        object.__setattr__(self, "layer_ids", tuple(self.layer_ids))
        object.__setattr__(self, "options", copy_state(self.options))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "panel_id": self.panel_id,
            "title": self.title,
            "panel_type": self.panel_type.value,
            "dataset_ids": list(self.dataset_ids),
            "layer_ids": list(self.layer_ids),
            "options": copy_state(self.options),
        }


@dataclass(frozen=True, slots=True)
class DashboardSpec:
    """Declarative dashboard layout independent of the frontend framework."""

    dashboard_id: str
    title: str
    panels: tuple[PanelSpec, ...]
    layers: tuple[LayerSpec, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = "mobilitylab.visualization.dashboard.v1"

    def __post_init__(self) -> None:
        for field_name, value in {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "schema": self.schema,
        }.items():
            if value == "":
                msg = f"{field_name} must not be empty"
                raise ValueError(msg)
        object.__setattr__(self, "panels", tuple(self.panels))
        object.__setattr__(self, "layers", tuple(self.layers))
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "panels": [panel.to_record() for panel in self.panels],
            "layers": [layer.to_record() for layer in self.layers],
            "metadata": copy_state(self.metadata),
        }


def default_replay_dashboard() -> DashboardSpec:
    """Build the MVP replay dashboard contract used by the viewer shell."""

    layers = (
        LayerSpec(
            layer_id="network",
            title="Network",
            layer_type=LayerType.NETWORK,
            dataset_id="network",
            encoding={
                "geometry": "LineString",
                "color": "#5b6573",
                "line_width": 2,
            },
        ),
        LayerSpec(
            layer_id="facilities",
            title="Facilities",
            layer_type=LayerType.FACILITIES,
            dataset_id="facilities",
            encoding={
                "geometry": "Point",
                "color": "#2f7d6d",
                "radius": 5,
            },
        ),
        LayerSpec(
            layer_id="replay_events",
            title="Replay Events",
            layer_type=LayerType.REPLAY_EVENTS,
            dataset_id="replay_frames",
        ),
        LayerSpec(
            layer_id="metrics",
            title="Metrics",
            layer_type=LayerType.METRICS,
            dataset_id="metrics",
        ),
        LayerSpec(
            layer_id="trace_events",
            title="Trace Events",
            layer_type=LayerType.TRACE,
            dataset_id="trace_events",
        ),
    )
    return DashboardSpec(
        dashboard_id="replay",
        title="Replay Dashboard",
        layers=layers,
        panels=(
            PanelSpec(
                panel_id="map",
                title="Map",
                panel_type=PanelType.MAP,
                dataset_ids=("network", "facilities"),
                layer_ids=("network", "facilities"),
            ),
            PanelSpec(
                panel_id="timeline",
                title="Timeline",
                panel_type=PanelType.TIMELINE,
                dataset_ids=("replay_frames",),
                layer_ids=("replay_events",),
            ),
            PanelSpec(
                panel_id="metrics",
                title="Metrics",
                panel_type=PanelType.METRICS,
                dataset_ids=("metrics",),
                layer_ids=("metrics",),
            ),
            PanelSpec(
                panel_id="events",
                title="Events",
                panel_type=PanelType.EVENTS,
                dataset_ids=("trace_events",),
                layer_ids=("trace_events",),
            ),
        ),
    )
