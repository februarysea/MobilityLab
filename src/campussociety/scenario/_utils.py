from __future__ import annotations

from collections.abc import Iterable, Mapping

from campussociety.core.entities import JsonValue, copy_state
from campussociety.scenario.errors import ScenarioValidationError


def copy_json_mapping(mapping: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return copy_state(mapping)


def require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise ScenarioValidationError(msg)


def require_non_negative(value: int | float, field_name: str) -> None:
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise ScenarioValidationError(msg)


def duplicates(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        else:
            seen.add(value)
    return tuple(sorted(repeated))


def require_unique(values: Iterable[str], field_name: str) -> None:
    repeated = duplicates(values)
    if repeated:
        msg = f"{field_name} contains duplicate ids: {', '.join(repeated)}"
        raise ScenarioValidationError(msg)
