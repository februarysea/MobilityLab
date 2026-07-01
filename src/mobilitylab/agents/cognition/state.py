from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from mobilitylab.agents._utils import copy_json_mapping
from mobilitylab.agents.cognition.audit import LLMAuditRecord
from mobilitylab.agents.cognition.memory import MemoryStore
from mobilitylab.core.entities import JsonValue


@dataclass(slots=True)
class CognitiveState:
    """Optional cognition state for cognition-backed or hybrid behavior."""

    memory: MemoryStore = field(default_factory=MemoryStore)
    reasoning_state: Mapping[str, JsonValue] = field(default_factory=dict)
    audit_records: list[LLMAuditRecord] = field(default_factory=list)
    last_reflection_time: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.audit_records = list(self.audit_records)
        object.__setattr__(
            self,
            "reasoning_state",
            copy_json_mapping(self.reasoning_state),
        )
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def append_audit_record(self, record: LLMAuditRecord) -> None:
        self.audit_records.append(record)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "memory": self.memory.to_record(),
            "reasoning_state": copy_json_mapping(self.reasoning_state),
            "audit_records": [record.to_record() for record in self.audit_records],
            "last_reflection_time": self.last_reflection_time,
            "attributes": copy_json_mapping(self.attributes),
        }
