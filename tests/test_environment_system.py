from __future__ import annotations

from typing import cast

import pytest

from mobilitylab.core import EntityId, RunContext, Simulation, State
from mobilitylab.environment import (
    EnvironmentBuilder,
    LocationRef,
    MovementIntent,
    ObservationRequest,
    RouteNotFoundError,
    RouteRequest,
    SimpleNetworkRouter,
)
from mobilitylab.scenario import (
    AreaSpec,
    BoundingBox,
    CoordinateReference,
    FacilitiesSpec,
    FacilitySpec,
    GridCellSpec,
    GridLayerSpec,
    GridLayerType,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PointSpec,
    PreparedScenario,
    ScenarioSpec,
    SpatialLayersSpec,
)


def build_environment_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="environment_commute_test",
            version="2026.06",
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="home", x=0.0, y=0.0),
                NetworkNodeSpec(node_id="main", x=1.0, y=0.0),
                NetworkNodeSpec(node_id="workplace", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="home-main",
                    from_node_id="home",
                    to_node_id="main",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="main-work",
                    from_node_id="main",
                    to_node_id="workplace",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="home-work",
                    from_node_id="home",
                    to_node_id="workplace",
                    length_meters=10.0,
                    allowed_modes=("walk",),
                ),
            ),
            coordinate_system="local-planar",
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="library",
                    facility_type="library",
                    location_id="main",
                    capacity=120,
                ),
                FacilitySpec(
                    facility_id="workplace-a",
                    facility_type="workplace",
                    location_id="workplace",
                    capacity=80,
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
        ),
        spatial_layers=SpatialLayersSpec(
            coordinate_reference=CoordinateReference(
                crs_id="local-planar",
                units="meters",
            ),
            extent=BoundingBox(min_x=0.0, min_y=0.0, max_x=3.0, max_y=1.0),
            areas=(
                AreaSpec(area_id="area:home", area_type="residential"),
                AreaSpec(area_id="area:work", area_type="workplace"),
            ),
            grid_layers=(
                GridLayerSpec(
                    layer_id="grid:walkability",
                    grid_type=GridLayerType.REGULAR_SQUARE,
                    extent=BoundingBox(
                        min_x=0.0,
                        min_y=0.0,
                        max_x=3.0,
                        max_y=1.0,
                    ),
                    cell_size_meters=1.0,
                    cells=(
                        GridCellSpec(
                            cell_id="grid:walkability:0:0",
                            row=0,
                            column=0,
                            area_id="area:home",
                            centroid=PointSpec(0.5, 0.5),
                        ),
                        GridCellSpec(
                            cell_id="grid:walkability:0:1",
                            row=0,
                            column=1,
                            centroid=PointSpec(1.5, 0.5),
                        ),
                        GridCellSpec(
                            cell_id="grid:walkability:0:2",
                            row=0,
                            column=2,
                            area_id="area:work",
                            centroid=PointSpec(2.5, 0.5),
                        ),
                    ),
                    initial_property_layers={
                        "walkability": {
                            "default": 1.0,
                            "cells": {"grid:walkability:0:2": 0.8},
                        },
                    },
                ),
            ),
        ),
    )


def test_environment_builder_installs_runtime_world_into_simulation() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    simulation = Simulation(seed=1, simulation_id="environment-test")
    simulation.add_initializer(environment.create_initializer())

    snapshot = simulation.initialize()

    environment_state = snapshot.entities["environment"]
    world_state = cast(State, environment_state["world"])
    network_state = cast(State, world_state["network"])
    facilities_state = cast(State, world_state["facilities"])
    spatial_layers_state = cast(State, world_state["spatial_layers"])

    assert environment_state["entity_type"] == "environment"
    assert network_state["node_count"] == 3
    assert facilities_state["facility_count"] == 2
    assert spatial_layers_state["area_count"] == 2
    assert spatial_layers_state["grid_layer_count"] == 1
    assert environment.world.mobility_mode_ids() == ("walk",)

    topics = [str(record["topic"]) for record in snapshot.event_trace]
    assert topics == ["simulation.initialized", "environment.initialized"]


def test_runtime_spatial_layers_resolve_regular_square_cells() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    home_position = environment.world.network.get_node("home").position
    work_position = environment.world.network.get_node("workplace").position

    assert home_position is not None
    assert work_position is not None

    home_cell = environment.world.spatial_layers.cell_at(
        "grid:walkability",
        home_position,
    )
    work_cell = environment.world.spatial_layers.cell_at(
        "grid:walkability",
        work_position,
    )

    assert home_cell is not None
    assert home_cell.cell_id == "grid:walkability:0:0"
    assert home_cell.area_id == "area:home"
    assert work_cell is not None
    assert work_cell.cell_id == "grid:walkability:0:2"
    assert environment.world.spatial_layers.layer_values_for_cell(
        "grid:walkability",
        "grid:walkability:0:2",
    ) == {"walkability": 0.8}


def test_simple_router_is_separate_and_respects_runtime_link_state() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    router = SimpleNetworkRouter()
    request = RouteRequest(
        origin=LocationRef.node("home"),
        destination=LocationRef.facility("workplace-a"),
        mode="walk",
        departure_time=0,
        agent_id=EntityId("worker-1"),
    )

    route = router.route(request, environment.world)

    assert [leg.link_id for leg in route.legs] == [
        "home-main",
        "main-work",
    ]
    assert route.total_travel_time_seconds == 2

    environment.world.close_link("main-work")
    rerouted = router.route(request, environment.world)

    assert [leg.link_id for leg in rerouted.legs] == ["home-work"]

    environment.world.close_link("home-work")
    with pytest.raises(RouteNotFoundError):
        router.route(request, environment.world)


def test_movement_kernel_advances_agent_location_and_emits_events() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    agent_id = EntityId("worker-1")
    simulation = Simulation(seed=2, simulation_id="movement-test")

    def install_and_start(context: RunContext) -> None:
        environment.install(context)
        environment.world.set_agent_location(agent_id, LocationRef.node("home"))
        environment.start_movement(
            MovementIntent(
                agent_id=agent_id,
                destination=LocationRef.facility("workplace-a"),
                mode="walk",
                movement_id="morning-trip",
            ),
            context,
        )

    simulation.add_initializer(install_and_start)

    snapshot = simulation.run()

    assert snapshot.time == 2
    assert environment.world.get_agent_location(agent_id) == LocationRef.facility(
        "workplace-a"
    )
    assert environment.movement_kernel.active_count == 0

    topics = [str(record["topic"]) for record in snapshot.event_trace]
    assert topics == [
        "simulation.initialized",
        "environment.initialized",
        "movement.started",
        "simulation.started",
        "movement.arrived",
        "simulation.completed",
    ]


def test_observation_service_returns_controlled_agent_view() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    agent_id = EntityId("worker-1")
    simulation = Simulation(seed=3)
    simulation.add_initializer(environment.create_initializer())
    simulation.initialize()
    environment.world.set_agent_location(agent_id, LocationRef.node("home"))

    observation = environment.observe(
        ObservationRequest(agent_id=agent_id, max_facilities=1),
        simulation.context,
    )

    assert observation.agent_id == agent_id
    assert observation.location == LocationRef.node("home")
    assert observation.available_modes == ("walk",)
    assert [facility.facility_id for facility in observation.nearby_facilities] == [
        "library"
    ]
    assert observation.media_refs == ()
    grid_cells = cast(list[State], observation.spatial_context["grid_cells"])
    areas = cast(list[State], observation.spatial_context["areas"])
    assert grid_cells[0]["cell_id"] == "grid:walkability:0:0"
    assert grid_cells[0]["area_id"] == "area:home"
    assert areas[0]["area_id"] == "area:home"


def test_observation_spatial_context_updates_after_network_movement() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    agent_id = EntityId("worker-1")
    simulation = Simulation(seed=4, simulation_id="movement-spatial-test")

    def install_and_start(context: RunContext) -> None:
        environment.install(context)
        environment.world.set_agent_location(agent_id, LocationRef.node("home"))
        environment.start_movement(
            MovementIntent(
                agent_id=agent_id,
                destination=LocationRef.facility("workplace-a"),
                mode="walk",
                movement_id="spatial-trip",
            ),
            context,
        )

    simulation.add_initializer(install_and_start)
    simulation.run()

    observation = environment.observe(
        ObservationRequest(agent_id=agent_id),
        simulation.context,
    )

    grid_cells = cast(list[State], observation.spatial_context["grid_cells"])
    layer_values = cast(State, observation.spatial_context["layer_values"])
    walkability_values = cast(State, layer_values["grid:walkability"])

    assert observation.location == LocationRef.facility("workplace-a")
    assert grid_cells[0]["cell_id"] == "grid:walkability:0:2"
    assert grid_cells[0]["area_id"] == "area:work"
    assert walkability_values["walkability"] == 0.8
