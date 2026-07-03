from __future__ import annotations

from collections.abc import Iterable

from mobilitylab.config.errors import ConfigValidationError
from mobilitylab.config.schema import (
    MOBILITYLAB_CONFIG_SCHEMA_VERSION,
    AgentSchema,
    MobilityLabConfigSchema,
)


def validate_config(config: MobilityLabConfigSchema) -> None:
    """Validate cross-section references before compiling runtime contracts."""

    if config.schema_version != MOBILITYLAB_CONFIG_SCHEMA_VERSION:
        msg = (
            "unsupported config schema_version: "
            f"{config.schema_version!r}; expected {MOBILITYLAB_CONFIG_SCHEMA_VERSION!r}"
        )
        raise ConfigValidationError(msg)

    node_ids = {node.node_id for node in config.network.nodes}
    link_ids = {link.link_id for link in config.network.links}
    facility_ids = {facility.facility_id for facility in config.facilities.facilities}
    mode_ids = {mode.mode_id for mode in config.mobility_supply.modes}

    _require_unique((node.node_id for node in config.network.nodes), "network.nodes")
    _require_unique((link.link_id for link in config.network.links), "network.links")
    _require_unique(
        (facility.facility_id for facility in config.facilities.facilities),
        "facilities.facilities",
    )
    _require_unique(
        (mode.mode_id for mode in config.mobility_supply.modes),
        "mobility_supply.modes",
    )
    _require_unique(
        (agent.agent_id for agent in config.population.agents),
        "population.agents",
    )

    for index, link in enumerate(config.network.links):
        if link.from_node_id not in node_ids:
            msg = (
                f"network.links[{index}].from_node_id references unknown node: "
                f"{link.from_node_id}"
            )
            raise ConfigValidationError(msg)
        if link.to_node_id not in node_ids:
            msg = (
                f"network.links[{index}].to_node_id references unknown node: "
                f"{link.to_node_id}"
            )
            raise ConfigValidationError(msg)
        _validate_modes(
            link.allowed_modes,
            mode_ids,
            f"network.links[{index}].allowed_modes",
        )

    for index, facility in enumerate(config.facilities.facilities):
        if facility.location_id is not None and facility.location_id not in node_ids:
            msg = (
                f"facilities.facilities[{index}].location_id references unknown node: "
                f"{facility.location_id}"
            )
            raise ConfigValidationError(msg)

    for agent_index, agent in enumerate(config.population.agents):
        _validate_agent_locations(
            agent,
            agent_index=agent_index,
            facility_ids=facility_ids,
            node_ids=node_ids,
            link_ids=link_ids,
            mode_ids=mode_ids,
        )

    if config.run.until is not None and config.run.until < config.run.start_time:
        msg = "run.until must be greater than or equal to run.start_time"
        raise ConfigValidationError(msg)


def _validate_agent_locations(
    agent: AgentSchema,
    *,
    agent_index: int,
    facility_ids: set[str],
    node_ids: set[str],
    link_ids: set[str],
    mode_ids: set[str],
) -> None:
    mobility_access = agent.profile.get("mobility_access")
    if isinstance(mobility_access, list):
        _validate_modes(
            tuple(item for item in mobility_access if isinstance(item, str)),
            mode_ids,
            f"population.agents[{agent_index}].profile.mobility_access",
        )

    raw_location = (
        agent.initial_state.get("location")
        or agent.initial_state.get("initial_location")
        or agent.initial_state.get("location_id")
    )
    if raw_location is not None:
        _validate_location_value(
            raw_location,
            f"population.agents[{agent_index}].initial_state.location",
            facility_ids=facility_ids,
            node_ids=node_ids,
            link_ids=link_ids,
        )

    for plan_index, plan in enumerate(agent.plans):
        _require_unique(
            (activity.activity_id for activity in plan.activities),
            f"population.agents[{agent_index}].plans[{plan_index}].activities",
        )
        for activity_index, activity in enumerate(plan.activities):
            if activity.location_id is None:
                continue
            if (
                activity.location_id not in facility_ids
                and activity.location_id not in node_ids
            ):
                msg = (
                    "population.agents"
                    f"[{agent_index}].plans[{plan_index}]"
                    f".activities[{activity_index}].location_id references "
                    f"unknown facility or node: {activity.location_id}"
                )
                raise ConfigValidationError(msg)


def _validate_location_value(
    raw_location: object,
    path: str,
    *,
    facility_ids: set[str],
    node_ids: set[str],
    link_ids: set[str],
) -> None:
    if isinstance(raw_location, str):
        if raw_location in facility_ids or raw_location in node_ids:
            return
        msg = f"{path} references unknown facility or node: {raw_location}"
        raise ConfigValidationError(msg)
    if not isinstance(raw_location, dict):
        msg = f"{path} must be a location id or location mapping"
        raise ConfigValidationError(msg)
    raw_id = raw_location.get("id")
    raw_kind = raw_location.get("kind")
    if not isinstance(raw_id, str) or raw_id == "":
        msg = f"{path}.id must be a non-empty string"
        raise ConfigValidationError(msg)
    if raw_kind == "facility" and raw_id not in facility_ids:
        msg = f"{path}.id references unknown facility: {raw_id}"
        raise ConfigValidationError(msg)
    if raw_kind == "node" and raw_id not in node_ids:
        msg = f"{path}.id references unknown node: {raw_id}"
        raise ConfigValidationError(msg)
    if raw_kind == "link" and raw_id not in link_ids:
        msg = f"{path}.id references unknown link: {raw_id}"
        raise ConfigValidationError(msg)
    if raw_kind is None and raw_id not in facility_ids and raw_id not in node_ids:
        msg = f"{path}.id references unknown facility or node: {raw_id}"
        raise ConfigValidationError(msg)


def _validate_modes(values: tuple[str, ...], mode_ids: set[str], path: str) -> None:
    if not mode_ids:
        return
    missing = tuple(mode for mode in values if mode not in mode_ids)
    if missing:
        msg = f"{path} references unknown modes: {', '.join(missing)}"
        raise ConfigValidationError(msg)


def _require_unique(values: Iterable[str], path: str) -> None:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        else:
            seen.add(value)
    if repeated:
        msg = f"{path} contains duplicate ids: {', '.join(sorted(repeated))}"
        raise ConfigValidationError(msg)
