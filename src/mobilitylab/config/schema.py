from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias, cast

from mobilitylab.config.errors import ConfigValidationError
from mobilitylab.core.entities import JsonValue

MOBILITYLAB_CONFIG_SCHEMA_VERSION = "mobilitylab.config.v1"

RawMapping: TypeAlias = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class DataSourceSchema:
    source_id: str
    source_type: str
    path: Path | None = None
    schema_version: str | None = None
    options: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ScenarioSchema:
    scenario_id: str
    version: str
    variant_id: str = "baseline"
    data_sources: tuple[DataSourceSchema, ...] = ()
    policy_defaults: Mapping[str, JsonValue] = field(default_factory=dict)
    initial_assumptions: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ActivitySchema:
    activity_id: str
    activity_type: str
    start_time: int | None = None
    end_time: int | None = None
    location_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PlanSchema:
    plan_id: str
    activities: tuple[ActivitySchema, ...] = ()
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentSchema:
    agent_id: str
    agent_type: str = "agent"
    profile: Mapping[str, JsonValue] = field(default_factory=dict)
    initial_state: Mapping[str, JsonValue] = field(default_factory=dict)
    plans: tuple[PlanSchema, ...] = ()
    policy_id: str | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PopulationSchema:
    agents: tuple[AgentSchema, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NetworkNodeSchema:
    node_id: str
    x: float | None = None
    y: float | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NetworkLinkSchema:
    link_id: str
    from_node_id: str
    to_node_id: str
    length_meters: float | None = None
    allowed_modes: tuple[str, ...] = ()
    bidirectional: bool | None = None
    base_speed_mps: float | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NetworkSchema:
    nodes: tuple[NetworkNodeSchema, ...] = ()
    links: tuple[NetworkLinkSchema, ...] = ()
    coordinate_system: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FacilitySchema:
    facility_id: str
    facility_type: str
    location_id: str | None = None
    capacity: int | None = None
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FacilitiesSchema:
    facilities: tuple[FacilitySchema, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MobilityModeSchema:
    mode_id: str
    mode_type: str
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MobilitySupplySchema:
    modes: tuple[MobilityModeSchema, ...] = ()
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RunSchema:
    run_id: str
    seed: int
    start_time: int = 0
    until: int | None = None
    max_steps: int | None = None
    output_root: Path | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OutputSchema:
    output_root: Path | None = None
    overwrite: bool = False
    write_manifest: bool = True
    write_events: bool = True
    write_metrics: bool = True
    write_final_snapshot: bool = True
    write_scenario_summary: bool = True


@dataclass(frozen=True, slots=True)
class TraceSchema:
    enabled: bool = True
    included_topics: tuple[str, ...] = ("*",)
    excluded_topics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MetricSchema:
    enabled: bool = True
    include_run_summary: bool = True
    include_event_counts: bool = True
    include_agent_summary: bool = True
    include_movement_summary: bool = True


@dataclass(frozen=True, slots=True)
class ReplaySchema:
    enabled: bool = True
    write_timeline: bool = True


@dataclass(frozen=True, slots=True)
class MobilityLabConfigSchema:
    """User-facing configuration document after YAML has been normalized."""

    schema_version: str
    scenario: ScenarioSchema
    run: RunSchema
    population: PopulationSchema = field(default_factory=PopulationSchema)
    network: NetworkSchema = field(default_factory=NetworkSchema)
    facilities: FacilitiesSchema = field(default_factory=FacilitiesSchema)
    mobility_supply: MobilitySupplySchema = field(default_factory=MobilitySupplySchema)
    output: OutputSchema = field(default_factory=OutputSchema)
    trace: TraceSchema = field(default_factory=TraceSchema)
    metrics: MetricSchema = field(default_factory=MetricSchema)
    replay: ReplaySchema = field(default_factory=ReplaySchema)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: RawMapping) -> MobilityLabConfigSchema:
        schema_version = _string(
            _value(raw, "schema_version", "schema_version"),
            "schema_version",
            default=MOBILITYLAB_CONFIG_SCHEMA_VERSION,
        )
        return cls(
            schema_version=schema_version,
            scenario=_scenario_schema(_required_mapping(raw, "scenario")),
            run=_run_schema(_required_mapping(raw, "run")),
            population=_population_schema(_optional_section(raw, "population")),
            network=_network_schema(_optional_section(raw, "network")),
            facilities=_facilities_schema(_optional_section(raw, "facilities")),
            mobility_supply=_mobility_supply_schema(
                _optional_section(raw, "mobility_supply"),
            ),
            output=_output_schema(_optional_section(raw, "output")),
            trace=_trace_schema(_optional_section(raw, "trace")),
            metrics=_metric_schema(_optional_section(raw, "metrics")),
            replay=_replay_schema(_optional_section(raw, "replay")),
            metadata=_json_mapping(_optional_section(raw, "metadata"), "metadata"),
        )


def _scenario_schema(raw: RawMapping) -> ScenarioSchema:
    data_sources = tuple(
        _data_source_schema(item, f"scenario.data_sources[{index}]")
        for index, item in enumerate(
            _sequence(raw.get("data_sources"), "scenario.data_sources")
        )
    )
    return ScenarioSchema(
        scenario_id=_string(_value(raw, "scenario_id", "id"), "scenario.scenario_id"),
        version=_string(_value(raw, "version"), "scenario.version"),
        variant_id=_string(
            _value(raw, "variant_id"),
            "scenario.variant_id",
            default="baseline",
        ),
        data_sources=data_sources,
        policy_defaults=_json_mapping(
            _optional_section(raw, "policy_defaults"),
            "scenario.policy_defaults",
        ),
        initial_assumptions=_json_mapping(
            _optional_section(raw, "initial_assumptions"),
            "scenario.initial_assumptions",
        ),
        metadata=_json_mapping(_optional_section(raw, "metadata"), "scenario.metadata"),
    )


def _data_source_schema(raw_value: object, path: str) -> DataSourceSchema:
    raw = _mapping(raw_value, path)
    return DataSourceSchema(
        source_id=_string(_value(raw, "source_id", "id"), f"{path}.source_id"),
        source_type=_string(_value(raw, "source_type", "type"), f"{path}.source_type"),
        path=_optional_path(raw.get("path"), f"{path}.path"),
        schema_version=_optional_string(
            raw.get("schema_version"), f"{path}.schema_version"
        ),
        options=_json_mapping(_optional_section(raw, "options"), f"{path}.options"),
    )


def _population_schema(raw: RawMapping) -> PopulationSchema:
    agents = tuple(
        _agent_schema(item, f"population.agents[{index}]")
        for index, item in enumerate(_sequence(raw.get("agents"), "population.agents"))
    )
    return PopulationSchema(
        agents=agents,
        metadata=_json_mapping(
            _optional_section(raw, "metadata"), "population.metadata"
        ),
    )


def _agent_schema(raw_value: object, path: str) -> AgentSchema:
    raw = _mapping(raw_value, path)
    return AgentSchema(
        agent_id=_string(_value(raw, "agent_id", "id"), f"{path}.agent_id"),
        agent_type=_string(
            _value(raw, "agent_type", "type"),
            f"{path}.agent_type",
            default="agent",
        ),
        profile=_json_mapping(_optional_section(raw, "profile"), f"{path}.profile"),
        initial_state=_json_mapping(
            _optional_section(raw, "initial_state"),
            f"{path}.initial_state",
        ),
        plans=_plans_schema(raw, path),
        policy_id=_optional_string(raw.get("policy_id"), f"{path}.policy_id"),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _plans_schema(raw: RawMapping, path: str) -> tuple[PlanSchema, ...]:
    if "plans" in raw:
        return tuple(
            _plan_schema(item, f"{path}.plans[{index}]")
            for index, item in enumerate(_sequence(raw.get("plans"), f"{path}.plans"))
        )
    if "plan" not in raw:
        return ()
    plan_value = raw["plan"]
    if isinstance(plan_value, list):
        return (
            PlanSchema(
                plan_id="default",
                activities=tuple(
                    _activity_schema(item, f"{path}.plan[{index}]")
                    for index, item in enumerate(plan_value)
                ),
            ),
        )
    return (_plan_schema(plan_value, f"{path}.plan"),)


def _plan_schema(raw_value: object, path: str) -> PlanSchema:
    raw = _mapping(raw_value, path)
    return PlanSchema(
        plan_id=_string(
            _value(raw, "plan_id", "id"), f"{path}.plan_id", default="default"
        ),
        activities=tuple(
            _activity_schema(item, f"{path}.activities[{index}]")
            for index, item in enumerate(
                _sequence(raw.get("activities"), f"{path}.activities")
            )
        ),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _activity_schema(raw_value: object, path: str) -> ActivitySchema:
    raw = _mapping(raw_value, path)
    activity_type_value = _value(raw, "activity_type", "type", "activity")
    return ActivitySchema(
        activity_id=_string(_value(raw, "activity_id", "id"), f"{path}.activity_id"),
        activity_type=_string(activity_type_value, f"{path}.activity_type"),
        start_time=_optional_int(raw.get("start_time"), f"{path}.start_time"),
        end_time=_optional_int(raw.get("end_time"), f"{path}.end_time"),
        location_id=_optional_string(
            _value(raw, "location_id", "location"),
            f"{path}.location_id",
        ),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _network_schema(raw: RawMapping) -> NetworkSchema:
    return NetworkSchema(
        nodes=tuple(
            _network_node_schema(item, f"network.nodes[{index}]")
            for index, item in enumerate(_sequence(raw.get("nodes"), "network.nodes"))
        ),
        links=tuple(
            _network_link_schema(item, f"network.links[{index}]")
            for index, item in enumerate(_sequence(raw.get("links"), "network.links"))
        ),
        coordinate_system=_optional_string(
            raw.get("coordinate_system"),
            "network.coordinate_system",
        ),
        metadata=_json_mapping(_optional_section(raw, "metadata"), "network.metadata"),
    )


def _network_node_schema(raw_value: object, path: str) -> NetworkNodeSchema:
    raw = _mapping(raw_value, path)
    return NetworkNodeSchema(
        node_id=_string(_value(raw, "node_id", "id"), f"{path}.node_id"),
        x=_optional_float(raw.get("x"), f"{path}.x"),
        y=_optional_float(raw.get("y"), f"{path}.y"),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _network_link_schema(raw_value: object, path: str) -> NetworkLinkSchema:
    raw = _mapping(raw_value, path)
    return NetworkLinkSchema(
        link_id=_string(_value(raw, "link_id", "id"), f"{path}.link_id"),
        from_node_id=_string(
            _value(raw, "from_node_id", "from"),
            f"{path}.from_node_id",
        ),
        to_node_id=_string(_value(raw, "to_node_id", "to"), f"{path}.to_node_id"),
        length_meters=_optional_float(
            raw.get("length_meters"), f"{path}.length_meters"
        ),
        allowed_modes=_string_tuple(
            _value(raw, "allowed_modes", "modes"),
            f"{path}.allowed_modes",
        ),
        bidirectional=_optional_bool(raw.get("bidirectional"), f"{path}.bidirectional"),
        base_speed_mps=_optional_float(
            raw.get("base_speed_mps"), f"{path}.base_speed_mps"
        ),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _facilities_schema(raw: RawMapping) -> FacilitiesSchema:
    facilities_value: object = raw.get("facilities", raw.get("items", []))
    if isinstance(facilities_value, Mapping):
        facilities_value = [facilities_value]
    return FacilitiesSchema(
        facilities=tuple(
            _facility_schema(item, f"facilities.facilities[{index}]")
            for index, item in enumerate(
                _sequence(facilities_value, "facilities.facilities")
            )
        ),
        metadata=_json_mapping(
            _optional_section(raw, "metadata"), "facilities.metadata"
        ),
    )


def _facility_schema(raw_value: object, path: str) -> FacilitySchema:
    raw = _mapping(raw_value, path)
    return FacilitySchema(
        facility_id=_string(_value(raw, "facility_id", "id"), f"{path}.facility_id"),
        facility_type=_string(
            _value(raw, "facility_type", "type"), f"{path}.facility_type"
        ),
        location_id=_optional_string(
            _value(raw, "location_id", "location"),
            f"{path}.location_id",
        ),
        capacity=_optional_int(raw.get("capacity"), f"{path}.capacity"),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _mobility_supply_schema(raw: RawMapping) -> MobilitySupplySchema:
    return MobilitySupplySchema(
        modes=tuple(
            _mobility_mode_schema(item, f"mobility_supply.modes[{index}]")
            for index, item in enumerate(
                _sequence(raw.get("modes"), "mobility_supply.modes")
            )
        ),
        metadata=_json_mapping(
            _optional_section(raw, "metadata"),
            "mobility_supply.metadata",
        ),
    )


def _mobility_mode_schema(raw_value: object, path: str) -> MobilityModeSchema:
    raw = _mapping(raw_value, path)
    return MobilityModeSchema(
        mode_id=_string(_value(raw, "mode_id", "id"), f"{path}.mode_id"),
        mode_type=_string(_value(raw, "mode_type", "type"), f"{path}.mode_type"),
        attributes=_json_mapping(
            _optional_section(raw, "attributes"), f"{path}.attributes"
        ),
    )


def _run_schema(raw: RawMapping) -> RunSchema:
    return RunSchema(
        run_id=_string(_value(raw, "run_id", "id"), "run.run_id"),
        seed=_int(_value(raw, "seed"), "run.seed"),
        start_time=_int(raw.get("start_time"), "run.start_time", default=0),
        until=_optional_int(raw.get("until"), "run.until"),
        max_steps=_optional_int(raw.get("max_steps"), "run.max_steps"),
        output_root=_optional_path(raw.get("output_root"), "run.output_root"),
        metadata=_json_mapping(_optional_section(raw, "metadata"), "run.metadata"),
    )


def _output_schema(raw: RawMapping) -> OutputSchema:
    return OutputSchema(
        output_root=_optional_path(raw.get("output_root"), "output.output_root"),
        overwrite=_bool(raw.get("overwrite"), "output.overwrite", default=False),
        write_manifest=_bool(
            raw.get("write_manifest"),
            "output.write_manifest",
            default=True,
        ),
        write_events=_bool(
            raw.get("write_events"), "output.write_events", default=True
        ),
        write_metrics=_bool(
            raw.get("write_metrics"), "output.write_metrics", default=True
        ),
        write_final_snapshot=_bool(
            raw.get("write_final_snapshot"),
            "output.write_final_snapshot",
            default=True,
        ),
        write_scenario_summary=_bool(
            raw.get("write_scenario_summary"),
            "output.write_scenario_summary",
            default=True,
        ),
    )


def _trace_schema(raw: RawMapping) -> TraceSchema:
    return TraceSchema(
        enabled=_bool(raw.get("enabled"), "trace.enabled", default=True),
        included_topics=_string_tuple(
            raw.get("included_topics", ["*"]),
            "trace.included_topics",
        ),
        excluded_topics=_string_tuple(
            raw.get("excluded_topics", []),
            "trace.excluded_topics",
        ),
    )


def _metric_schema(raw: RawMapping) -> MetricSchema:
    return MetricSchema(
        enabled=_bool(raw.get("enabled"), "metrics.enabled", default=True),
        include_run_summary=_bool(
            raw.get("include_run_summary"),
            "metrics.include_run_summary",
            default=True,
        ),
        include_event_counts=_bool(
            raw.get("include_event_counts"),
            "metrics.include_event_counts",
            default=True,
        ),
        include_agent_summary=_bool(
            raw.get("include_agent_summary"),
            "metrics.include_agent_summary",
            default=True,
        ),
        include_movement_summary=_bool(
            raw.get("include_movement_summary"),
            "metrics.include_movement_summary",
            default=True,
        ),
    )


def _replay_schema(raw: RawMapping) -> ReplaySchema:
    return ReplaySchema(
        enabled=_bool(raw.get("enabled"), "replay.enabled", default=True),
        write_timeline=_bool(
            raw.get("write_timeline"),
            "replay.write_timeline",
            default=True,
        ),
    )


def _required_mapping(raw: RawMapping, key: str) -> RawMapping:
    if key not in raw:
        msg = f"{key} is required"
        raise ConfigValidationError(msg)
    return _mapping(raw[key], key)


def _optional_section(raw: RawMapping, key: str) -> RawMapping:
    value = raw.get(key)
    if value is None:
        return {}
    return _mapping(value, key)


def _mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        msg = f"{path} must be a mapping"
        raise ConfigValidationError(msg)
    raw_mapping = cast(Mapping[object, object], value)
    result: dict[str, object] = {}
    for key, item in raw_mapping.items():
        if not isinstance(key, str):
            msg = f"{path} contains non-string key: {key!r}"
            raise ConfigValidationError(msg)
        result[key] = item
    return result


def _sequence(value: object, path: str) -> list[object]:
    if value is None:
        return []
    if not isinstance(value, list):
        msg = f"{path} must be a list"
        raise ConfigValidationError(msg)
    return value


def _value(raw: RawMapping, *keys: str) -> object:
    for key in keys:
        if key in raw:
            return raw[key]
    return None


def _string(value: object, path: str, *, default: str | None = None) -> str:
    if value is None:
        if default is not None:
            return default
        msg = f"{path} is required"
        raise ConfigValidationError(msg)
    if not isinstance(value, str) or value == "":
        msg = f"{path} must be a non-empty string"
        raise ConfigValidationError(msg)
    return value


def _optional_string(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _string(value, path)


def _int(value: object, path: str, *, default: int | None = None) -> int:
    if value is None:
        if default is not None:
            return default
        msg = f"{path} is required"
        raise ConfigValidationError(msg)
    if isinstance(value, bool) or not isinstance(value, int):
        msg = f"{path} must be an integer"
        raise ConfigValidationError(msg)
    return value


def _optional_int(value: object, path: str) -> int | None:
    if value is None:
        return None
    return _int(value, path)


def _optional_float(value: object, path: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{path} must be a number"
        raise ConfigValidationError(msg)
    return float(value)


def _bool(value: object, path: str, *, default: bool) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        msg = f"{path} must be a boolean"
        raise ConfigValidationError(msg)
    return value


def _optional_bool(value: object, path: str) -> bool | None:
    if value is None:
        return None
    return _bool(value, path, default=False)


def _optional_path(value: object, path: str) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or value == "":
        msg = f"{path} must be a non-empty path string"
        raise ConfigValidationError(msg)
    return Path(value)


def _string_tuple(value: object, path: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, list):
        msg = f"{path} must be a string or list of strings"
        raise ConfigValidationError(msg)
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or item == "":
            msg = f"{path}[{index}] must be a non-empty string"
            raise ConfigValidationError(msg)
        result.append(item)
    return tuple(result)


def _json_mapping(raw: RawMapping, path: str) -> dict[str, JsonValue]:
    return {key: _json_value(value, f"{path}.{key}") for key, value in raw.items()}


def _json_value(value: object, path: str) -> JsonValue:
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list):
        return [
            _json_value(item, f"{path}[{index}]") for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        raw_mapping = cast(Mapping[object, object], value)
        result: dict[str, JsonValue] = {}
        for key, item in raw_mapping.items():
            if not isinstance(key, str):
                msg = f"{path} contains non-string key: {key!r}"
                raise ConfigValidationError(msg)
            result[key] = _json_value(item, f"{path}.{key}")
        return result
    msg = f"{path} must be JSON-compatible"
    raise ConfigValidationError(msg)
