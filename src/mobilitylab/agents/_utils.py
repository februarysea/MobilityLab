from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy

from mobilitylab.agents.errors import AgentValidationError
from mobilitylab.core.entities import JsonValue


def copy_json_mapping(values: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return deepcopy(dict(values))


def require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise AgentValidationError(msg)


def require_non_negative(value: int | float, field_name: str) -> None:
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise AgentValidationError(msg)


def require_unique(values: Iterable[object], field_name: str) -> None:
    seen: set[object] = set()
    for value in values:
        if value in seen:
            msg = f"{field_name} contains duplicate value: {value}"
            raise AgentValidationError(msg)
        seen.add(value)
