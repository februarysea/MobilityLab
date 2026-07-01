from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from campussociety.core.entities import JsonValue, copy_state
from campussociety.core.snapshots import Snapshot
from campussociety.experiments.config import TraceConfig


@dataclass(frozen=True, slots=True)
class TraceRecord:
    """Experiment-layer event trace record."""

    event: Mapping[str, JsonValue]

    def __post_init__(self) -> None:
        object.__setattr__(self, "event", copy_state(self.event))

    def to_record(self) -> dict[str, JsonValue]:
        return copy_state(self.event)


@dataclass(frozen=True, slots=True)
class EventTraceCollector:
    """Extracts a filtered event trace from a completed snapshot."""

    config: TraceConfig = TraceConfig()

    def collect(self, snapshot: Snapshot) -> tuple[TraceRecord, ...]:
        if not self.config.enabled:
            return ()
        return tuple(
            TraceRecord(record)
            for record in snapshot.event_trace
            if self._include(record)
        )

    def _include(self, record: Mapping[str, JsonValue]) -> bool:
        raw_topic = record.get("topic")
        if not isinstance(raw_topic, str):
            return False
        if raw_topic in self.config.excluded_topics:
            return False
        if "*" in self.config.included_topics:
            return True
        return raw_topic in self.config.included_topics
