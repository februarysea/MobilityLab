from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy

from mobilitylab.core.entities import JsonValue
from mobilitylab.environment.errors import EnvironmentValidationError


def copy_json_mapping(mapping: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return deepcopy(dict(mapping))


def require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise EnvironmentValidationError(msg)


def require_non_negative(value: int | float, field_name: str) -> None:
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise EnvironmentValidationError(msg)


def require_positive(value: int | float, field_name: str) -> None:
    if value <= 0:
        msg = f"{field_name} must be positive"
        raise EnvironmentValidationError(msg)


def optional_float(
    attributes: Mapping[str, JsonValue],
    key: str,
) -> float | None:
    value = attributes.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{key} must be a number"
        raise EnvironmentValidationError(msg)
    return float(value)


def optional_bool(
    attributes: Mapping[str, JsonValue],
    key: str,
    *,
    default: bool = False,
) -> bool:
    value = attributes.get(key)
    if value is None:
        return default
    if not isinstance(value, bool):
        msg = f"{key} must be a boolean"
        raise EnvironmentValidationError(msg)
    return value
