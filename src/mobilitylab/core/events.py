from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TypeAlias

from mobilitylab.core.entities import EntityId, JsonValue, copy_state

EventHandler: TypeAlias = Callable[["Event"], None]


@dataclass(frozen=True, slots=True)
class Event:
    """Structured event emitted by the simulation runtime or domain adapters."""

    time: int
    topic: str
    payload: Mapping[str, JsonValue] = field(default_factory=dict)
    source: EntityId | None = None
    sequence: int | None = None
    schema_version: str = "core.event.v1"

    def __post_init__(self) -> None:
        if self.time < 0:
            msg = "event time must be non-negative"
            raise ValueError(msg)
        if self.topic == "":
            msg = "event topic must not be empty"
            raise ValueError(msg)
        if self.sequence is not None and self.sequence < 1:
            msg = "event sequence must be positive"
            raise ValueError(msg)
        if self.schema_version == "":
            msg = "event schema_version must not be empty"
            raise ValueError(msg)
        object.__setattr__(
            self,
            "payload",
            MappingProxyType(copy_state(self.payload)),
        )

    def with_sequence(self, sequence: int) -> Event:
        return Event(
            time=self.time,
            topic=self.topic,
            payload=self.payload,
            source=self.source,
            sequence=sequence,
            schema_version=self.schema_version,
        )

    def to_record(self) -> dict[str, JsonValue]:
        record: dict[str, JsonValue] = {
            "time": self.time,
            "sequence": self.sequence,
            "topic": self.topic,
            "schema_version": self.schema_version,
            "payload": copy_state(dict(self.payload)),
        }
        if self.source is not None:
            record["source"] = str(self.source)
        return record


class EventBus:
    """In-memory event bus with deterministic trace ordering."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._next_sequence = 1

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        if topic == "":
            msg = "topic must not be empty"
            raise ValueError(msg)
        self._subscribers[topic].append(handler)

    def emit(self, event: Event) -> Event:
        sequenced_event = event.with_sequence(self._next_sequence)
        self._next_sequence += 1
        self._events.append(sequenced_event)
        for handler in self._subscribers.get(sequenced_event.topic, ()):
            handler(sequenced_event)
        for handler in self._subscribers.get("*", ()):
            handler(sequenced_event)
        return sequenced_event

    def events(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def records(self) -> tuple[dict[str, JsonValue], ...]:
        return tuple(event.to_record() for event in self._events)

    def clear(self) -> None:
        self._events.clear()
        self._next_sequence = 1
