from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from mobilitylab.core.entities import JsonValue, State, copy_state


@dataclass(frozen=True, slots=True)
class Snapshot:
    """Serializable capture of simulation runtime state."""

    time: int
    status: str
    seed: int
    entities: Mapping[str, State]
    event_trace: tuple[Mapping[str, JsonValue], ...]
    pending_tasks: int

    def __post_init__(self) -> None:
        entities = {
            entity_id: copy_state(state)
            for entity_id, state in sorted(self.entities.items())
        }
        event_trace = tuple(dict(record) for record in self.event_trace)
        object.__setattr__(self, "entities", MappingProxyType(entities))
        object.__setattr__(self, "event_trace", event_trace)

    def to_record(self) -> dict[str, JsonValue]:
        entities: dict[str, JsonValue] = {
            entity_id: copy_state(state) for entity_id, state in self.entities.items()
        }
        event_trace: list[JsonValue] = [dict(record) for record in self.event_trace]
        return {
            "time": self.time,
            "status": self.status,
            "seed": self.seed,
            "entities": entities,
            "event_trace": event_trace,
            "pending_tasks": self.pending_tasks,
        }
