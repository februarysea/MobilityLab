from __future__ import annotations

from mobilitylab.scenario import (
    ActivitySpec,
    AgentSpec,
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


def build_minimal_commute_scenario() -> PreparedScenario:
    """Build a tiny deterministic home-to-work walking commute scenario."""

    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="minimal_commute",
            version="2026.07",
            metadata={
                "example": "basic/minimal_commute",
                "description": "Two workers walk from homes to a workplace.",
            },
        ),
        population=PopulationSpec(
            agents=(
                _worker_agent(
                    agent_id="worker-1",
                    home_facility_id="home-north",
                    work_start_time=20,
                    work_end_time=50,
                ),
                _worker_agent(
                    agent_id="worker-2",
                    home_facility_id="home-south",
                    work_start_time=25,
                    work_end_time=55,
                ),
            ),
            metadata={"source": "hand-authored example population"},
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="home-north-node", x=0.0, y=1.0),
                NetworkNodeSpec(node_id="home-south-node", x=0.0, y=-1.0),
                NetworkNodeSpec(node_id="main-street", x=1.0, y=0.0),
                NetworkNodeSpec(node_id="workplace-node", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="north-home-to-main",
                    from_node_id="home-north-node",
                    to_node_id="main-street",
                    length_meters=6.0,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="south-home-to-main",
                    from_node_id="home-south-node",
                    to_node_id="main-street",
                    length_meters=5.0,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
                NetworkLinkSpec(
                    link_id="main-to-work",
                    from_node_id="main-street",
                    to_node_id="workplace-node",
                    length_meters=8.0,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
            ),
            coordinate_system="local-planar",
            metadata={"description": "Toy walking network in local coordinates."},
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="home-north",
                    facility_type="home",
                    location_id="home-north-node",
                    capacity=1,
                ),
                FacilitySpec(
                    facility_id="home-south",
                    facility_type="home",
                    location_id="home-south-node",
                    capacity=1,
                ),
                FacilitySpec(
                    facility_id="workplace-a",
                    facility_type="workplace",
                    location_id="workplace-node",
                    capacity=20,
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(
                MobilityModeSpec(
                    mode_id="walk",
                    mode_type="active",
                    attributes={"description": "Fixed-speed walking mode."},
                ),
            ),
        ),
    )


def _worker_agent(
    *,
    agent_id: str,
    home_facility_id: str,
    work_start_time: int,
    work_end_time: int,
) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        agent_type="worker",
        profile={
            "role": "worker",
            "mobility_access": ["walk"],
        },
        initial_state={
            "location": {
                "kind": "facility",
                "id": home_facility_id,
            },
        },
        plans=(
            PlanSpec(
                plan_id="weekday-work",
                activities=(
                    ActivitySpec(
                        activity_id=f"{agent_id}-work",
                        activity_type="work",
                        start_time=work_start_time,
                        end_time=work_end_time,
                        location_id="workplace-a",
                    ),
                ),
            ),
        ),
    )
