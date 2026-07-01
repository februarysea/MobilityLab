from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from mobilitylab.core.entities import JsonValue
from mobilitylab.scenario._utils import copy_json_mapping, require_non_empty

SCENARIO_CONFIG_SCHEMA_VERSION = "mobilitylab.scenario.config.v1"


@dataclass(frozen=True, slots=True)
class ScenarioConfig:
    """User-facing scenario loading configuration."""

    data_root: Path = Path(".")
    input_paths: Mapping[str, Path] = field(default_factory=dict)
    schema_version: str = SCENARIO_CONFIG_SCHEMA_VERSION
    default_variant: str = "baseline"
    coordinate_system: str | None = None
    loader_options: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.schema_version, "schema_version")
        require_non_empty(self.default_variant, "default_variant")
        normalized_paths: dict[str, Path] = {}
        for key, value in self.input_paths.items():
            require_non_empty(key, "input path key")
            normalized_paths[key] = Path(value)

        object.__setattr__(self, "data_root", Path(self.data_root))
        object.__setattr__(self, "input_paths", normalized_paths)
        object.__setattr__(
            self,
            "loader_options",
            copy_json_mapping(self.loader_options),
        )

    def resolve_input_path(self, key: str) -> Path:
        """Return an absolute-or-data-root-relative input path."""
        try:
            path = self.input_paths[key]
        except KeyError as exc:
            msg = f"unknown scenario input path: {key}"
            raise KeyError(msg) from exc

        if path.is_absolute():
            return path
        return self.data_root / path
