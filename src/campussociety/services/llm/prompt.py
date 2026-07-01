from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue, State, copy_state
from campussociety.services.llm.types import LLMMessage


class _SafeFormatDict(dict[str, object]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """Versioned prompt template owned outside the simulation core."""

    template_id: str
    version: str
    text: str
    role: str = "user"
    default_values: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.template_id == "":
            msg = "template_id must not be empty"
            raise ValueError(msg)
        if self.version == "":
            msg = "version must not be empty"
            raise ValueError(msg)
        if self.role == "":
            msg = "role must not be empty"
            raise ValueError(msg)
        object.__setattr__(self, "default_values", copy_state(self.default_values))

    @property
    def prompt_version(self) -> str:
        return f"{self.template_id}:{self.version}"

    def render(self, values: Mapping[str, JsonValue] | None = None) -> LLMMessage:
        merged: State = copy_state(self.default_values)
        if values is not None:
            merged.update(copy_state(values))
        formatted = self.text.format_map(_SafeFormatDict(merged))
        return LLMMessage(
            role=self.role,
            content=formatted,
            metadata={
                "template_id": self.template_id,
                "version": self.version,
            },
        )


class PromptRenderer:
    """Small prompt template registry."""

    def __init__(self, templates: tuple[PromptTemplate, ...] = ()) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        for template in templates:
            self.add_template(template)

    def add_template(self, template: PromptTemplate) -> None:
        if template.template_id in self._templates:
            msg = f"prompt template already exists: {template.template_id}"
            raise ValueError(msg)
        self._templates[template.template_id] = template

    def get(self, template_id: str) -> PromptTemplate:
        try:
            return self._templates[template_id]
        except KeyError as exc:
            msg = f"unknown prompt template: {template_id}"
            raise KeyError(msg) from exc

    def render(
        self,
        template_id: str,
        values: Mapping[str, JsonValue] | None = None,
    ) -> LLMMessage:
        return self.get(template_id).render(values)
