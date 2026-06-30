from __future__ import annotations

from typing import cast

from campussociety.agents import (
    AgentLifecycleStatus,
    AgentSystemBuilder,
    CognitiveState,
    DirectReasoning,
    LLMBehavior,
    RuleBasedBehavior,
)
from campussociety.core import EntityId, Simulation, State
from campussociety.environment import EnvironmentBuilder, LocationRef
from campussociety.scenario import (
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


def build_agent_scenario() -> PreparedScenario:
    return PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="agent_runtime_test",
            version="2026.06",
        ),
        population=PopulationSpec(
            agents=(
                AgentSpec(
                    agent_id="student-1",
                    agent_type="student",
                    profile={
                        "role": "student",
                        "mobility_access": ["walk"],
                    },
                    initial_state={
                        "location": {
                            "kind": "node",
                            "id": "gate",
                        },
                    },
                    plans=(
                        PlanSpec(
                            plan_id="morning",
                            activities=(
                                ActivitySpec(
                                    activity_id="class-1",
                                    activity_type="class",
                                    start_time=5,
                                    end_time=8,
                                    location_id="classroom-a",
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        network=NetworkSpec(
            nodes=(
                NetworkNodeSpec(node_id="gate", x=0.0, y=0.0),
                NetworkNodeSpec(node_id="classroom", x=2.0, y=0.0),
            ),
            links=(
                NetworkLinkSpec(
                    link_id="gate-classroom",
                    from_node_id="gate",
                    to_node_id="classroom",
                    length_meters=2.8,
                    allowed_modes=("walk",),
                    attributes={"bidirectional": True},
                ),
            ),
        ),
        facilities=FacilitiesSpec(
            facilities=(
                FacilitySpec(
                    facility_id="classroom-a",
                    facility_type="classroom",
                    location_id="classroom",
                ),
            ),
        ),
        mobility_supply=MobilitySupplySpec(
            modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
        ),
    )


def test_agent_system_runs_plan_driven_agent_through_environment() -> None:
    scenario = build_agent_scenario()
    environment = EnvironmentBuilder().build(scenario)
    agent_system = AgentSystemBuilder().build(scenario, environment)
    simulation = Simulation(seed=7, simulation_id="agent-runtime")
    simulation.add_initializer(environment.create_initializer())
    simulation.add_initializer(agent_system.create_initializer())

    snapshot = simulation.run()

    agent_id = EntityId("student-1")
    assert snapshot.time == 8
    assert environment.world.get_agent_location(agent_id) == LocationRef.facility(
        "classroom-a"
    )
    agent = agent_system.agents.get(agent_id)
    assert agent.state.lifecycle_status is AgentLifecycleStatus.COMPLETED
    assert agent.state.current_plan_element_index == 2

    agent_system_state = snapshot.entities["agents"]
    agents_state = agent_system_state["agents"]
    assert isinstance(agents_state, dict)
    student_state = agents_state["student-1"]
    assert isinstance(student_state, dict)
    assert student_state["behavior_id"] == "rule_based"
    assert student_state["cognition_state"] is None

    topics = [str(record["topic"]) for record in snapshot.event_trace]
    assert "agent.decision" in topics
    assert "trip.requested" in topics
    assert "movement.arrived" in topics
    assert "activity.started" in topics
    assert "activity.ended" in topics

    decision_types = [
        cast(State, record["payload"])["decision_type"]
        for record in snapshot.event_trace
        if record["topic"] == "agent.decision"
    ]
    assert decision_types == [
        "start_trip",
        "wait",
        "start_activity",
        "no_op",
    ]


def test_builder_attaches_cognition_only_to_llm_backed_behavior() -> None:
    scenario = PreparedScenario(
        spec=ScenarioSpec(
            scenario_id="agent_cognition_test",
            version="2026.06",
        ),
        population=PopulationSpec(
            agents=(
                AgentSpec(agent_id="rule-agent", attributes={"behavior_id": "rule"}),
                AgentSpec(agent_id="llm-agent", attributes={"behavior_id": "llm"}),
            ),
        ),
    )
    environment = EnvironmentBuilder().build(scenario)
    agent_system = AgentSystemBuilder(
        default_initial_location=LocationRef.node("missing"),
    ).build(
        scenario,
        environment,
        behavior_models={
            "rule": RuleBasedBehavior(behavior_id="rule"),
            "llm": LLMBehavior(reasoning_strategy=DirectReasoning()),
        },
    )

    assert agent_system.agents.get(EntityId("rule-agent")).cognition_state is None
    assert isinstance(
        agent_system.agents.get(EntityId("llm-agent")).cognition_state,
        CognitiveState,
    )
