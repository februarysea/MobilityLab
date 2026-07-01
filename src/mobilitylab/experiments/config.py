from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from mobilitylab.core.entities import JsonValue, copy_state
from mobilitylab.scenario.base import ScenarioSpec
from mobilitylab.scenario.config import ScenarioConfig
from mobilitylab.scenario.variants import ScenarioVariantSpec

EXPERIMENT_RUN_CONFIG_SCHEMA_VERSION = "mobilitylab.experiment.run_config.v1"


def _copy_json_mapping(mapping: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return copy_state(mapping)


def _require_non_empty(value: str, field_name: str) -> None:
    if value == "":
        msg = f"{field_name} must not be empty"
        raise ValueError(msg)


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        msg = f"{field_name} must be non-negative"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """User-facing artifact output settings for one run."""

    output_root: Path = Path("runs")
    overwrite: bool = False
    write_manifest: bool = True
    write_events: bool = True
    write_metrics: bool = True
    write_final_snapshot: bool = True
    write_scenario_summary: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "output_root", Path(self.output_root))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "output_root": str(self.output_root),
            "overwrite": self.overwrite,
            "write_manifest": self.write_manifest,
            "write_events": self.write_events,
            "write_metrics": self.write_metrics,
            "write_final_snapshot": self.write_final_snapshot,
            "write_scenario_summary": self.write_scenario_summary,
        }


@dataclass(frozen=True, slots=True)
class TraceConfig:
    """Controls how the event trace is exported for a run."""

    enabled: bool = True
    included_topics: tuple[str, ...] = ("*",)
    excluded_topics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "included_topics", tuple(self.included_topics))
        object.__setattr__(self, "excluded_topics", tuple(self.excluded_topics))
        for topic in (*self.included_topics, *self.excluded_topics):
            _require_non_empty(topic, "trace topic")

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "enabled": self.enabled,
            "included_topics": list(self.included_topics),
            "excluded_topics": list(self.excluded_topics),
        }


@dataclass(frozen=True, slots=True)
class MetricConfig:
    """Controls built-in metric extraction for a run."""

    enabled: bool = True
    include_run_summary: bool = True
    include_event_counts: bool = True
    include_agent_summary: bool = True
    include_movement_summary: bool = True

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "enabled": self.enabled,
            "include_run_summary": self.include_run_summary,
            "include_event_counts": self.include_event_counts,
            "include_agent_summary": self.include_agent_summary,
            "include_movement_summary": self.include_movement_summary,
        }


@dataclass(frozen=True, slots=True)
class ReplayConfig:
    """Controls visualization-ready replay artifact generation."""

    enabled: bool = True
    write_timeline: bool = True

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "enabled": self.enabled,
            "write_timeline": self.write_timeline,
        }


@dataclass(frozen=True, slots=True)
class RunConfig:
    """Normalized configuration for one deterministic simulation run."""

    run_id: str
    scenario: ScenarioConfig | ScenarioSpec
    seed: int
    variant: ScenarioVariantSpec | None = None
    start_time: int = 0
    until: int | None = None
    max_steps: int | None = None
    output: OutputConfig = field(default_factory=OutputConfig)
    trace: TraceConfig = field(default_factory=TraceConfig)
    metrics: MetricConfig = field(default_factory=MetricConfig)
    replay: ReplayConfig = field(default_factory=ReplayConfig)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema_version: str = EXPERIMENT_RUN_CONFIG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_non_empty(self.run_id, "run_id")
        _require_non_empty(self.schema_version, "schema_version")
        _require_non_negative(self.seed, "seed")
        _require_non_negative(self.start_time, "start_time")
        if self.until is not None:
            _require_non_negative(self.until, "until")
            if self.until < self.start_time:
                msg = "until must be greater than or equal to start_time"
                raise ValueError(msg)
        if self.max_steps is not None:
            _require_non_negative(self.max_steps, "max_steps")
        object.__setattr__(self, "metadata", _copy_json_mapping(self.metadata))

    @property
    def run_dir(self) -> Path:
        return self.output.output_root / self.run_id

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "scenario": self._scenario_to_record(),
            "seed": self.seed,
            "variant": None if self.variant is None else self.variant.to_record(),
            "start_time": self.start_time,
            "until": self.until,
            "max_steps": self.max_steps,
            "output": self.output.to_record(),
            "trace": self.trace.to_record(),
            "metrics": self.metrics.to_record(),
            "replay": self.replay.to_record(),
            "metadata": _copy_json_mapping(self.metadata),
        }

    def _scenario_to_record(self) -> dict[str, JsonValue]:
        if isinstance(self.scenario, ScenarioSpec):
            return {
                "kind": "scenario_spec",
                "value": self.scenario.to_record(),
            }
        return {
            "kind": "scenario_config",
            "value": {
                "data_root": str(self.scenario.data_root),
                "input_paths": {
                    key: str(path) for key, path in self.scenario.input_paths.items()
                },
                "schema_version": self.scenario.schema_version,
                "default_variant": self.scenario.default_variant,
                "coordinate_system": self.scenario.coordinate_system,
                "loader_options": _copy_json_mapping(self.scenario.loader_options),
            },
        }
