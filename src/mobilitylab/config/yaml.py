from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

import yaml

from mobilitylab.config.compiler import ExperimentConfigBundle, compile_config
from mobilitylab.config.errors import ConfigLoadError
from mobilitylab.config.schema import MobilityLabConfigSchema, RawMapping


def load_yaml_mapping(path: str | Path) -> dict[str, object]:
    """Load a YAML file as a string-keyed mapping."""

    config_path = Path(path)
    try:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        msg = f"cannot read config file: {config_path}"
        raise ConfigLoadError(msg) from exc
    except yaml.YAMLError as exc:
        msg = f"cannot parse YAML config file: {config_path}"
        raise ConfigLoadError(msg) from exc

    if loaded is None:
        msg = f"config file is empty: {config_path}"
        raise ConfigLoadError(msg)
    if not isinstance(loaded, Mapping):
        msg = f"config file must contain a mapping at top level: {config_path}"
        raise ConfigLoadError(msg)

    raw_mapping = cast(Mapping[object, object], loaded)
    result: dict[str, object] = {}
    for key, value in raw_mapping.items():
        if not isinstance(key, str):
            msg = f"config file contains non-string top-level key: {key!r}"
            raise ConfigLoadError(msg)
        result[key] = value
    return result


def load_config_schema(path: str | Path) -> MobilityLabConfigSchema:
    """Load a YAML file into the normalized config schema layer."""

    raw: RawMapping = load_yaml_mapping(path)
    return MobilityLabConfigSchema.from_mapping(raw)


def load_experiment_config(path: str | Path) -> ExperimentConfigBundle:
    """Load and compile a YAML experiment config into framework contracts."""

    config_path = Path(path)
    schema = load_config_schema(config_path)
    return compile_config(schema, base_path=config_path.parent)
