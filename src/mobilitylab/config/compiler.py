from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mobilitylab.config.schema import (
    MobilityLabConfigSchema,
    NetworkLinkSchema,
)
from mobilitylab.config.validate import validate_config
from mobilitylab.core.entities import JsonValue
from mobilitylab.experiments import (
    MetricConfig,
    OutputConfig,
    ReplayConfig,
    RunConfig,
    TraceConfig,
)
from mobilitylab.scenario import (
    ActivitySpec,
    AgentSpec,
    DataSource,
    FacilitiesSpec,
    FacilitySpec,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PlanSpec,
    PopulationSpec,
    PreparedScenario,
    ScenarioSpec,
)


@dataclass(frozen=True, slots=True)
class ExperimentConfigBundle:
    """Compiled user configuration ready for experiment assembly."""

    scenario: PreparedScenario
    run_config: RunConfig


def compile_config(
    config: MobilityLabConfigSchema,
    *,
    base_path: Path | None = None,
) -> ExperimentConfigBundle:
    """Compile a validated config schema into framework runtime contracts."""

    validate_config(config)
    scenario_spec = ScenarioSpec(
        scenario_id=config.scenario.scenario_id,
        version=config.scenario.version,
        variant_id=config.scenario.variant_id,
        data_sources=tuple(
            DataSource(
                source_id=source.source_id,
                source_type=source.source_type,
                path=_resolve_path(source.path, base_path),
                schema_version=source.schema_version,
                options=source.options,
            )
            for source in config.scenario.data_sources
        ),
        policy_defaults=config.scenario.policy_defaults,
        initial_assumptions=config.scenario.initial_assumptions,
        metadata=config.scenario.metadata,
    )
    prepared = PreparedScenario(
        spec=scenario_spec,
        population=PopulationSpec(
            agents=tuple(
                AgentSpec(
                    agent_id=agent.agent_id,
                    agent_type=agent.agent_type,
                    profile=agent.profile,
                    initial_state=agent.initial_state,
                    plans=tuple(
                        PlanSpec(
                            plan_id=plan.plan_id,
                            activities=tuple(
                                ActivitySpec(
                                    activity_id=activity.activity_id,
                                    activity_type=activity.activity_type,
                                    start_time=activity.start_time,
                                    end_time=activity.end_time,
                                    location_id=activity.location_id,
                                    attributes=activity.attributes,
                                )
                                for activity in plan.activities
                            ),
                            attributes=plan.attributes,
                        )
                        for plan in agent.plans
                    ),
                    policy_id=agent.policy_id,
                    attributes=agent.attributes,
                )
                for agent in config.population.agents
            ),
            metadata=config.population.metadata,
        ),
        network=NetworkSpec(
            nodes=tuple(
                NetworkNodeSpec(
                    node_id=node.node_id,
                    x=node.x,
                    y=node.y,
                    attributes=node.attributes,
                )
                for node in config.network.nodes
            ),
            links=tuple(_compile_network_link(link) for link in config.network.links),
            coordinate_system=config.network.coordinate_system,
            metadata=config.network.metadata,
        ),
        facilities=FacilitiesSpec(
            facilities=tuple(
                FacilitySpec(
                    facility_id=facility.facility_id,
                    facility_type=facility.facility_type,
                    location_id=facility.location_id,
                    capacity=facility.capacity,
                    attributes=facility.attributes,
                )
                for facility in config.facilities.facilities
            ),
            metadata=config.facilities.metadata,
        ),
        mobility_supply=MobilitySupplySpec(
            modes=tuple(
                MobilityModeSpec(
                    mode_id=mode.mode_id,
                    mode_type=mode.mode_type,
                    attributes=mode.attributes,
                )
                for mode in config.mobility_supply.modes
            ),
            metadata=config.mobility_supply.metadata,
        ),
        metadata=config.metadata,
    )
    run_config = RunConfig(
        run_id=config.run.run_id,
        scenario=scenario_spec,
        seed=config.run.seed,
        start_time=config.run.start_time,
        until=config.run.until,
        max_steps=config.run.max_steps,
        output=OutputConfig(
            output_root=_output_root(config, base_path),
            overwrite=config.output.overwrite,
            write_manifest=config.output.write_manifest,
            write_events=config.output.write_events,
            write_metrics=config.output.write_metrics,
            write_final_snapshot=config.output.write_final_snapshot,
            write_scenario_summary=config.output.write_scenario_summary,
        ),
        trace=TraceConfig(
            enabled=config.trace.enabled,
            included_topics=config.trace.included_topics,
            excluded_topics=config.trace.excluded_topics,
        ),
        metrics=MetricConfig(
            enabled=config.metrics.enabled,
            include_run_summary=config.metrics.include_run_summary,
            include_event_counts=config.metrics.include_event_counts,
            include_agent_summary=config.metrics.include_agent_summary,
            include_movement_summary=config.metrics.include_movement_summary,
        ),
        replay=ReplayConfig(
            enabled=config.replay.enabled,
            write_timeline=config.replay.write_timeline,
        ),
        metadata=config.run.metadata,
    )
    return ExperimentConfigBundle(scenario=prepared, run_config=run_config)


def _compile_network_link(link: NetworkLinkSchema) -> NetworkLinkSpec:
    attributes = dict(link.attributes)
    _set_if_present(attributes, "bidirectional", link.bidirectional)
    _set_if_present(attributes, "base_speed_mps", link.base_speed_mps)
    return NetworkLinkSpec(
        link_id=link.link_id,
        from_node_id=link.from_node_id,
        to_node_id=link.to_node_id,
        length_meters=link.length_meters,
        allowed_modes=link.allowed_modes,
        attributes=attributes,
    )


def _set_if_present(
    mapping: dict[str, JsonValue],
    key: str,
    value: bool | float | None,
) -> None:
    if value is not None:
        mapping[key] = value


def _output_root(config: MobilityLabConfigSchema, base_path: Path | None) -> Path:
    path = config.output.output_root or config.run.output_root or Path("runs")
    return _resolve_path(path, base_path) or Path("runs")


def _resolve_path(path: Path | None, base_path: Path | None) -> Path | None:
    if path is None:
        return None
    if path.is_absolute() or base_path is None:
        return path
    return base_path / path
