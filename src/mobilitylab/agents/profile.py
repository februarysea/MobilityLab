from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from mobilitylab.agents._utils import copy_json_mapping, require_non_empty
from mobilitylab.core.entities import JsonValue


@dataclass(frozen=True, slots=True)
class AgentProfile:
    """Stable or slowly changing description of a simulated agent."""

    role: str = "agent"
    demographics: Mapping[str, JsonValue] = field(default_factory=dict)
    preferences: Mapping[str, JsonValue] = field(default_factory=dict)
    mobility_access: tuple[str, ...] = ()
    constraints: Mapping[str, JsonValue] = field(default_factory=dict)
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.role, "role")
        object.__setattr__(self, "demographics", copy_json_mapping(self.demographics))
        object.__setattr__(self, "preferences", copy_json_mapping(self.preferences))
        object.__setattr__(self, "mobility_access", tuple(self.mobility_access))
        object.__setattr__(self, "constraints", copy_json_mapping(self.constraints))
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "role": self.role,
            "demographics": copy_json_mapping(self.demographics),
            "preferences": copy_json_mapping(self.preferences),
            "mobility_access": list(self.mobility_access),
            "constraints": copy_json_mapping(self.constraints),
            "attributes": copy_json_mapping(self.attributes),
        }
