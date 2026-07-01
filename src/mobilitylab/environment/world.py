from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import TypeAlias

from mobilitylab.core.entities import EntityId, JsonValue, State
from mobilitylab.core.simulation import RunContext
from mobilitylab.environment._utils import copy_json_mapping, require_non_empty
from mobilitylab.environment.errors import EnvironmentValidationError
from mobilitylab.environment.facilities import FacilityStore, RuntimeFacility
from mobilitylab.environment.movement import MovementIntent, MovementKernel
from mobilitylab.environment.network import RuntimeNetwork
from mobilitylab.environment.observation import (
    AgentObservation,
    ObservationRequest,
    ObservationService,
)
from mobilitylab.environment.routing import RoutingService, SimpleNetworkRouter
from mobilitylab.environment.spatial import LocationKind, LocationRef, Position
from mobilitylab.environment.spatial_layers import RuntimeSpatialLayers
from mobilitylab.scenario.base import PreparedScenario

EnvironmentInitializer: TypeAlias = Callable[[RunContext], None]
DEFAULT_ENVIRONMENT_ID = EntityId("environment")


@dataclass(frozen=True, slots=True)
class MobilityMode:
    """Runtime mobility mode declaration."""

    mode_id: str
    mode_type: str
    attributes: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.mode_id, "mode_id")
        require_non_empty(self.mode_type, "mode_type")
        object.__setattr__(self, "attributes", copy_json_mapping(self.attributes))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "mode_id": self.mode_id,
            "mode_type": self.mode_type,
            "attributes": copy_json_mapping(self.attributes),
        }


class RuntimeWorld:
    """Authoritative runtime state source for the environment layer."""

    def __init__(
        self,
        *,
        network: RuntimeNetwork,
        facilities: FacilityStore,
        mobility_modes: tuple[MobilityMode, ...] = (),
        spatial_layers: RuntimeSpatialLayers | None = None,
        metadata: Mapping[str, JsonValue] | None = None,
    ) -> None:
        self.network = network
        self.facilities = facilities
        self.spatial_layers = spatial_layers or RuntimeSpatialLayers.empty()
        self.metadata = copy_json_mapping(metadata or {})
        self._mobility_modes: dict[str, MobilityMode] = {}
        self._agent_locations: dict[EntityId, LocationRef] = {}
        for mode in mobility_modes:
            self.add_mobility_mode(mode)

    @classmethod
    def from_prepared_scenario(cls, scenario: PreparedScenario) -> RuntimeWorld:
        network = RuntimeNetwork.from_spec(scenario.network)
        facilities = FacilityStore.from_spec(scenario.facilities, network=network)
        modes = tuple(
            MobilityMode(
                mode_id=mode.mode_id,
                mode_type=mode.mode_type,
                attributes=mode.attributes,
            )
            for mode in scenario.mobility_supply.modes
        )
        return cls(
            network=network,
            facilities=facilities,
            mobility_modes=modes,
            spatial_layers=RuntimeSpatialLayers.from_spec(scenario.spatial_layers),
            metadata={
                "scenario_id": scenario.scenario_id,
                "scenario_version": scenario.version,
                "variant_id": scenario.variant_id,
            },
        )

    def add_mobility_mode(self, mode: MobilityMode) -> None:
        if mode.mode_id in self._mobility_modes:
            msg = f"mobility mode already exists: {mode.mode_id}"
            raise EnvironmentValidationError(msg)
        self._mobility_modes[mode.mode_id] = mode

    def mobility_mode_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._mobility_modes))

    def mobility_modes(self) -> tuple[MobilityMode, ...]:
        return tuple(
            self._mobility_modes[mode_id] for mode_id in self.mobility_mode_ids()
        )

    def has_mobility_mode(self, mode_id: str) -> bool:
        return mode_id in self._mobility_modes

    def set_agent_location(
        self,
        agent_id: EntityId,
        location: LocationRef,
    ) -> None:
        require_non_empty(str(agent_id), "agent_id")
        self.validate_location(location)
        self._agent_locations[agent_id] = location

    def get_agent_location(self, agent_id: EntityId) -> LocationRef:
        try:
            return self._agent_locations[agent_id]
        except KeyError as exc:
            msg = f"unknown agent location: {agent_id}"
            raise KeyError(msg) from exc

    def has_agent_location(self, agent_id: EntityId) -> bool:
        return agent_id in self._agent_locations

    def agent_location_records(self) -> dict[str, JsonValue]:
        return {
            str(agent_id): self._agent_locations[agent_id].to_record()
            for agent_id in sorted(self._agent_locations, key=str)
        }

    def resolve_location_node(
        self,
        location: LocationRef,
        *,
        use_destination: bool = False,
    ) -> str:
        if location.kind is LocationKind.NODE:
            if not self.network.contains_node(location.id):
                msg = f"location references unknown node: {location.id}"
                raise EnvironmentValidationError(msg)
            return location.id
        if location.kind is LocationKind.FACILITY:
            facility = self.facilities.get(location.id)
            if facility.access_node_id is None:
                msg = f"facility has no access node: {location.id}"
                raise EnvironmentValidationError(msg)
            return facility.access_node_id
        if location.kind is LocationKind.LINK:
            link = self.network.get_link(location.id)
            return link.to_node_id if use_destination else link.from_node_id
        msg = f"cannot resolve route location to a network node: {location.id}"
        raise EnvironmentValidationError(msg)

    def validate_location(self, location: LocationRef) -> None:
        if location.kind is LocationKind.NODE:
            if not self.network.contains_node(location.id):
                msg = f"location references unknown node: {location.id}"
                raise EnvironmentValidationError(msg)
            return
        if location.kind is LocationKind.LINK:
            if not self.network.contains_link(location.id):
                msg = f"location references unknown link: {location.id}"
                raise EnvironmentValidationError(msg)
            return
        if location.kind is LocationKind.FACILITY:
            if not self.facilities.contains(location.id):
                msg = f"location references unknown facility: {location.id}"
                raise EnvironmentValidationError(msg)
            return
        if location.kind is LocationKind.ROUTE:
            return

    def position_for_location(self, location: LocationRef) -> Position | None:
        if location.position is not None:
            return location.position
        if location.kind is LocationKind.NODE:
            return self.network.get_node(location.id).position
        if location.kind is LocationKind.FACILITY:
            return self.position_for_facility(self.facilities.get(location.id))
        if location.kind is LocationKind.LINK:
            link = self.network.get_link(location.id)
            from_position = self.network.get_node(link.from_node_id).position
            to_position = self.network.get_node(link.to_node_id).position
            if from_position is None or to_position is None:
                return None
            return Position(
                (from_position.x + to_position.x) / 2,
                (from_position.y + to_position.y) / 2,
            )
        return None

    def position_for_facility(self, facility: RuntimeFacility) -> Position | None:
        if facility.position is not None:
            return facility.position
        if facility.access_node_id is None:
            return None
        return self.network.get_node(facility.access_node_id).position

    def close_link(self, link_id: str) -> None:
        self.network.set_link_open(link_id, False)

    def open_link(self, link_id: str) -> None:
        self.network.set_link_open(link_id, True)

    def spatial_context_for_location(self, location: LocationRef) -> State:
        position = self.position_for_location(location)
        if position is None:
            return {}
        return self.spatial_layers.spatial_context_at(position)

    def to_record(self) -> State:
        return {
            "schema": "mobilitylab.environment.runtime_world.v1",
            "network": self.network.to_record(),
            "facilities": self.facilities.to_record(),
            "mobility_modes": [mode.to_record() for mode in self.mobility_modes()],
            "spatial_layers": self.spatial_layers.to_record(),
            "agent_locations": self.agent_location_records(),
            "metadata": copy_json_mapping(self.metadata),
        }


class Environment:
    """Runtime environment facade installed into a core Simulation."""

    def __init__(
        self,
        *,
        world: RuntimeWorld,
        routing_service: RoutingService | None = None,
        observation_service: ObservationService | None = None,
        environment_id: EntityId = DEFAULT_ENVIRONMENT_ID,
        step_interval_seconds: int = 1,
    ) -> None:
        self._id = environment_id
        self.world = world
        self.routing_service = routing_service or SimpleNetworkRouter()
        self.observation_service = observation_service or ObservationService()
        self.movement_kernel = MovementKernel(
            world=world,
            routing_service=self.routing_service,
            step_interval_seconds=step_interval_seconds,
        )

    @property
    def id(self) -> EntityId:
        return self._id

    def create_initializer(
        self,
        *,
        register_entity: bool = True,
    ) -> EnvironmentInitializer:
        def initialize(context: RunContext) -> None:
            self.install(context, register_entity=register_entity)

        return initialize

    def install(
        self,
        context: RunContext,
        *,
        register_entity: bool = True,
    ) -> None:
        source: EntityId | None = None
        if register_entity:
            context.entities.register(self)
            source = self.id
        context.emit(
            "environment.initialized",
            {
                "environment_id": str(self.id),
                "network_nodes": self.world.network.node_count,
                "network_links": self.world.network.link_count,
                "facility_count": self.world.facilities.size,
                "mobility_modes": len(self.world.mobility_mode_ids()),
                "spatial_areas": self.world.spatial_layers.area_count,
                "grid_layers": self.world.spatial_layers.grid_layer_count,
                "spatial_indexes": self.world.spatial_layers.spatial_index_count,
            },
            source=source,
        )

    def start_movement(
        self,
        intent: MovementIntent,
        context: RunContext,
    ) -> None:
        self.movement_kernel.start_movement(intent, context)

    def observe(
        self,
        request: ObservationRequest,
        context: RunContext,
    ) -> AgentObservation:
        return self.observation_service.observe(
            request,
            self.world,
            time=context.clock.time,
        )

    def snapshot_state(self) -> State:
        return {
            "entity_type": "environment",
            "schema": "mobilitylab.environment.v1",
            "world": self.world.to_record(),
            "movement": self.movement_kernel.snapshot_state(),
        }


@dataclass(frozen=True, slots=True)
class EnvironmentBuilder:
    """Builds runtime environments from prepared scenarios."""

    environment_id: EntityId = DEFAULT_ENVIRONMENT_ID
    step_interval_seconds: int = 1

    def build(
        self,
        scenario: PreparedScenario,
        *,
        routing_service: RoutingService | None = None,
        observation_service: ObservationService | None = None,
    ) -> Environment:
        return Environment(
            world=RuntimeWorld.from_prepared_scenario(scenario),
            routing_service=routing_service,
            observation_service=observation_service,
            environment_id=self.environment_id,
            step_interval_seconds=self.step_interval_seconds,
        )
