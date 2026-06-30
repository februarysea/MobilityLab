from __future__ import annotations

from typing import cast

import pytest

from campussociety.core import EntityId, RunContext, Simulation, State
from campussociety.environment import (
    EnvironmentBuilder,
    LocationRef,
    MovementIntent,
    ObservationRequest,
    RouteNotFoundError,
    RouteRequest,
    SimpleNetworkRouter,
)
from campussociety.scenario import (
    FacilitiesSpec,
    FacilitySpec,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PreparedScenario,
    ScenarioSpec,
)


def build_environment_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="campus_environment_test",
            version="2026.06",
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="gate", x=0.0, y=0.0),
                NetworkNodeSpec(node_id="quad", x=1.0, y=0.0),
                NetworkNodeSpec(node_id="classroom", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="gate-quad",
                    from_node_id="gate",
                    to_node_id="quad",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="quad-classroom",
                    from_node_id="quad",
                    to_node_id="classroom",
                    length_meters=1.4,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="gate-classroom",
                    from_node_id="gate",
                    to_node_id="classroom",
                    length_meters=10.0,
                    allowed_modes=("walk",),
                ),
            ),
            coordinate_system="local-campus",
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="library",
                    facility_type="library",
                    location_id="quad",
                    capacity=120,
                ),
                FacilitySpec(
                    facility_id="classroom-a",
                    facility_type="classroom",
                    location_id="classroom",
                    capacity=80,
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
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

    assert environment_state["entity_type"] == "environment"
    assert network_state["node_count"] == 3
    assert facilities_state["facility_count"] == 2
    assert environment.world.mobility_mode_ids() == ("walk",)

    topics = [str(record["topic"]) for record in snapshot.event_trace]
    assert topics == ["simulation.initialized", "environment.initialized"]


def test_simple_router_is_separate_and_respects_runtime_link_state() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    router = SimpleNetworkRouter()
    request = RouteRequest(
        origin=LocationRef.node("gate"),
        destination=LocationRef.facility("classroom-a"),
        mode="walk",
        departure_time=0,
        agent_id=EntityId("student-1"),
    )

    route = router.route(request, environment.world)

    assert [leg.link_id for leg in route.legs] == [
        "gate-quad",
        "quad-classroom",
    ]
    assert route.total_travel_time_seconds == 2

    environment.world.close_link("quad-classroom")
    rerouted = router.route(request, environment.world)

    assert [leg.link_id for leg in rerouted.legs] == ["gate-classroom"]

    environment.world.close_link("gate-classroom")
    with pytest.raises(RouteNotFoundError):
        router.route(request, environment.world)


def test_movement_kernel_advances_agent_location_and_emits_events() -> None:
    environment = EnvironmentBuilder().build(build_environment_scenario())
    agent_id = EntityId("student-1")
    simulation = Simulation(seed=2, simulation_id="movement-test")

    def install_and_start(context: RunContext) -> None:
        environment.install(context)
        environment.world.set_agent_location(agent_id, LocationRef.node("gate"))
        environment.start_movement(
            MovementIntent(
                agent_id=agent_id,
                destination=LocationRef.facility("classroom-a"),
                mode="walk",
                movement_id="morning-trip",
            ),
            context,
        )

    simulation.add_initializer(install_and_start)

    snapshot = simulation.run()

    assert snapshot.time == 2
    assert environment.world.get_agent_location(agent_id) == LocationRef.facility(
        "classroom-a"
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
    agent_id = EntityId("student-1")
    simulation = Simulation(seed=3)
    simulation.add_initializer(environment.create_initializer())
    simulation.initialize()
    environment.world.set_agent_location(agent_id, LocationRef.node("gate"))

    observation = environment.observe(
        ObservationRequest(agent_id=agent_id, max_facilities=1),
        simulation.context,
    )

    assert observation.agent_id == agent_id
    assert observation.location == LocationRef.node("gate")
    assert observation.available_modes == ("walk",)
    assert [facility.facility_id for facility in observation.nearby_facilities] == [
        "library"
    ]
    assert observation.media_refs == ()
