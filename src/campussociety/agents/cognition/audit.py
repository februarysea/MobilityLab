from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.agents._utils import copy_json_mapping, require_non_empty
from campussociety.core.entities import JsonValue


@dataclass(frozen=True, slots=True)
class LLMAuditRecord:
    """Structured record for an LLM-backed decision attempt."""

    record_id: str
    time: int
    prompt_version: str
    model: str
    input_summary: Mapping[str, JsonValue] = field(default_factory=dict)
    structured_output: Mapping[str, JsonValue] = field(default_factory=dict)
    validation_result: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.record_id, "record_id")
        require_non_empty(self.prompt_version, "prompt_version")
        require_non_empty(self.model, "model")
        object.__setattr__(
            self,
            "input_summary",
            copy_json_mapping(self.input_summary),
        )
        object.__setattr__(
            self,
            "structured_output",
            copy_json_mapping(self.structured_output),
        )
        object.__setattr__(
            self,
            "validation_result",
            copy_json_mapping(self.validation_result),
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "record_id": self.record_id,
            "time": self.time,
            "prompt_version": self.prompt_version,
            "model": self.model,
            "input_summary": copy_json_mapping(self.input_summary),
            "structured_output": copy_json_mapping(self.structured_output),
            "validation_result": copy_json_mapping(self.validation_result),
        }
