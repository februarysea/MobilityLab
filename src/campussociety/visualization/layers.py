from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from campussociety.core.entities import JsonValue, copy_state


class LayerType(StrEnum):
    """Visualization layer families understood by viewer clients."""

    NETWORK = "network"
    FACILITIES = "facilities"
    REPLAY_EVENTS = "replay_events"
    METRICS = "metrics"
    TRACE = "trace"


@dataclass(frozen=True, slots=True)
class LayerSpec:
    """Declarative layer configuration independent of a concrete renderer."""

    layer_id: str
    title: str
    layer_type: LayerType
    dataset_id: str
    visible: bool = True
    encoding: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = "campussociety.visualization.layer.v1"

    def __post_init__(self) -> None:
        for field_name, value in {
            "layer_id": self.layer_id,
            "title": self.title,
            "dataset_id": self.dataset_id,
            "schema": self.schema,
        }.items():
            if value == "":
                msg = f"{field_name} must not be empty"
                raise ValueError(msg)
        object.__setattr__(self, "encoding", copy_state(self.encoding))
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "layer_id": self.layer_id,
            "title": self.title,
            "layer_type": self.layer_type.value,
            "dataset_id": self.dataset_id,
            "visible": self.visible,
            "encoding": copy_state(self.encoding),
            "metadata": copy_state(self.metadata),
        }
