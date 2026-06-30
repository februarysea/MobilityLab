from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.agents._utils import copy_json_mapping, require_non_empty
from campussociety.core.entities import JsonValue


@dataclass(frozen=True, slots=True)
class MemoryEntry:
    """One memory item available to cognition-backed behavior."""

    entry_id: str
    time: int
    content: str
    tags: tuple[str, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.entry_id, "entry_id")
        require_non_empty(self.content, "content")
        object.__setattr__(self, "tags", tuple(self.tags))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "entry_id": self.entry_id,
            "time": self.time,
            "content": self.content,
            "tags": list(self.tags),
            "attributes": copy_json_mapping(self.attributes),
        }


@dataclass(slots=True)
class MemoryStore:
    """Small in-memory store for optional cognition state."""

    short_term: list[MemoryEntry] = field(default_factory=list)
    episodic: list[MemoryEntry] = field(default_factory=list)
    semantic: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.short_term = list(self.short_term)
        self.episodic = list(self.episodic)
        object.__setattr__(self, "semantic", copy_json_mapping(self.semantic))

    def append_short_term(self, entry: MemoryEntry) -> None:
        self.short_term.append(entry)

    def append_episodic(self, entry: MemoryEntry) -> None:
        self.episodic.append(entry)

    def recent_short_term(self, limit: int) -> tuple[MemoryEntry, ...]:
        if limit <= 0:
            return ()
        return tuple(self.short_term[-limit:])

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "short_term": [entry.to_record() for entry in self.short_term],
            "episodic": [entry.to_record() for entry in self.episodic],
            "semantic": copy_json_mapping(self.semantic),
        }
