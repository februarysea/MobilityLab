from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue
from campussociety.scenario._utils import (
    copy_json_mapping,
    require_non_empty,
    require_non_negative,
)

BASELINE_VARIANT_ID = "baseline"


@dataclass(frozen=True, slots=True)
class ScheduledScenarioEvent:
    """Event emitted by a prepared scenario at a deterministic simulation time."""

    time: int
    topic: str
    payload: Mapping[str, JsonValue] = field(default_factory=dict)
    source: str | None = None
    priority: int = 0
    label: str | None = None

    def __post_init__(self) -> None:
        require_non_negative(self.time, "time")
        require_non_empty(self.topic, "topic")
        object.__setattr__(self, "payload", copy_json_mapping(self.payload))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "time": self.time,
            "topic": self.topic,
            "payload": copy_json_mapping(self.payload),
            "source": self.source,
            "priority": self.priority,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class ScenarioVariantSpec:
    """Delta from a baseline scenario declaration."""

    variant_id: str = BASELINE_VARIANT_ID
    description: str = ""
    overrides: Mapping[str, JsonValue] = field(default_factory=dict)
    scheduled_events: tuple[ScheduledScenarioEvent, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.variant_id, "variant_id")
        object.__setattr__(self, "overrides", copy_json_mapping(self.overrides))
        object.__setattr__(self, "scheduled_events", tuple(self.scheduled_events))
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    @property
    def is_baseline(self) -> bool:
        return self.variant_id == BASELINE_VARIANT_ID

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "variant_id": self.variant_id,
            "description": self.description,
            "overrides": copy_json_mapping(self.overrides),
            "scheduled_events": [event.to_record() for event in self.scheduled_events],
            "metadata": copy_json_mapping(self.metadata),
        }


def baseline_variant() -> ScenarioVariantSpec:
    return ScenarioVariantSpec()
