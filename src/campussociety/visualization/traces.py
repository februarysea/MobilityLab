from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue, copy_state


@dataclass(frozen=True, slots=True)
class TraceQuery:
    """Filter for event trace inspection."""

    topic: str | None = None
    agent_id: str | None = None
    movement_id: str | None = None
    start_time: int | None = None
    end_time: int | None = None


@dataclass(frozen=True, slots=True)
class TraceEventIndex:
    """Small readonly query helper for exported event traces."""

    events: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        events = tuple(sorted((copy_state(event) for event in self.events), key=_key))
        object.__setattr__(self, "events", events)

    def query(self, query: TraceQuery) -> tuple[Mapping[str, JsonValue], ...]:
        return tuple(event for event in self.events if _matches(event, query))

    def topics(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {
                    topic
                    for event in self.events
                    if isinstance(topic := event.get("topic"), str)
                }
            )
        )


def _matches(event: Mapping[str, JsonValue], query: TraceQuery) -> bool:
    raw_time = event.get("time")
    time = raw_time if isinstance(raw_time, int) else None
    if query.start_time is not None and (time is None or time < query.start_time):
        return False
    if query.end_time is not None and (time is None or time > query.end_time):
        return False
    if query.topic is not None and event.get("topic") != query.topic:
        return False
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return query.agent_id is None and query.movement_id is None
    if query.agent_id is not None and payload.get("agent_id") != query.agent_id:
        return False
    return not (
        query.movement_id is not None
        and payload.get("movement_id") != query.movement_id
    )


def _key(event: Mapping[str, JsonValue]) -> tuple[int, int]:
    raw_time = event.get("time")
    raw_sequence = event.get("sequence")
    time = raw_time if isinstance(raw_time, int) else 0
    sequence = raw_sequence if isinstance(raw_sequence, int) else 0
    return (time, sequence)
