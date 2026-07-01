from __future__ import annotations

from pathlib import Path

import pytest

from campussociety.core import EntityId, Simulation
from campussociety.scenario import (
    ActivitySpec,
    AgentSpec,
    DataSource,
    FacilitiesSpec,
    FacilitySpec,
    InMemoryScenarioLoader,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PlanSpec,
    PopulationSpec,
    PreparedScenario,
    ScenarioConfig,
    ScenarioEntity,
    ScenarioSpec,
    ScenarioValidationError,
    ScenarioVariantSpec,
    ScheduledScenarioEvent,
)


def build_prepared_scenario() -> PreparedScenario:
    variant = ScenarioVariantSpec(
        variant_id="rainy_day",
        description="Rain begins after the first simulated minute.",
        overrides={"weather": {"condition": "rain"}},
        scheduled_events=(
            ScheduledScenarioEvent(
                time=60,
                topic="environment.weather.changed",
                payload={"condition": "rain"},
            ),
        ),
    )
    spec = ScenarioSpec(
        scenario_id="toy_commute_day",
        version="2026.06",
        data_sources=(
            DataSource(
                source_id="population",
                source_type="csv",
                path=Path("population.csv"),
            ),
        ),
        initial_assumptions={"day_type": "commute_day"},
    ).with_variant(variant)

    population = PopulationSpec(
        agents=(
            AgentSpec(
                agent_id="worker-1",
                agent_type="worker",
                profile={"role": "worker"},
                plans=(
                    PlanSpec(
                        plan_id="weekday",
                        activities=(
                            ActivitySpec(
                                activity_id="work-1",
                                activity_type="work",
                                start_time=8 * 3600,
                                end_time=9 * 3600,
                                location_id="workplace-a",
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    network = NetworkSpec(
        nodes=(
            NetworkNodeSpec(node_id="home"),
            NetworkNodeSpec(node_id="workplace-a"),
        ),
        links=(
            NetworkLinkSpec(
                link_id="walk-1",
                from_node_id="home",
                to_node_id="workplace-a",
                length_meters=300.0,
                allowed_modes=("walk",),
            ),
        ),
        coordinate_system="local-planar",
    )
    facilities = FacilitiesSpec(
        facilities=(
            FacilitySpec(
                facility_id="workplace-a",
                facility_type="workplace",
                capacity=80,
            ),
        ),
    )
    mobility_supply = MobilitySupplySpec(
        modes=(MobilityModeSpec(mode_id="walk", mode_type="active"),),
    )

    return PreparedScenario(
        spec=spec,
        population=population,
        network=network,
        facilities=facilities,
        mobility_supply=mobility_supply,
        variant=variant,
        metadata={"source": "unit-test"},
        initial_entities=(
            ScenarioEntity(
                id=EntityId("scenario-loader:marker"),
                entity_type="loader_marker",
                state={"ready": True},
            ),
        ),
    )


def test_scenario_config_resolves_input_paths() -> None:
    config = ScenarioConfig(
        data_root=Path("data/us_public"),
        input_paths={
            "population": Path("population.csv"),
            "network": Path("/tmp/network.json"),
        },
        loader_options={"scenario_id": "toy_commute_day"},
    )

    assert config.resolve_input_path("population") == Path(
        "data/us_public/population.csv"
    )
    assert config.resolve_input_path("network") == Path("/tmp/network.json")

    with pytest.raises(KeyError, match="unknown scenario input path"):
        config.resolve_input_path("missing")


def test_prepared_scenario_initializer_installs_into_core_simulation() -> None:
    prepared = build_prepared_scenario()
    simulation = Simulation(seed=123, simulation_id="scenario-test")
    simulation.add_initializer(prepared.create_initializer())

    initialized = simulation.initialize()

    assert initialized.pending_tasks == 1
    assert initialized.entities["scenario:toy_commute_day"]["population_size"] == 1
    assert initialized.entities["scenario:toy_commute_day"]["network_nodes"] == 2
    assert initialized.entities["scenario:toy_commute_day"]["facility_count"] == 1
    assert initialized.entities["scenario-loader:marker"]["ready"] is True

    completed = simulation.run()
    topics = [str(record["topic"]) for record in completed.event_trace]

    assert topics == [
        "simulation.initialized",
        "scenario.initialized",
        "simulation.started",
        "environment.weather.changed",
        "simulation.completed",
    ]
    assert completed.time == 60
    assert completed.pending_tasks == 0


def test_in_memory_loader_applies_variant_to_baseline_scenario() -> None:
    baseline_spec = ScenarioSpec(
        scenario_id="toy_commute_day",
        version="2026.06",
    )
    baseline = PreparedScenario(spec=baseline_spec)
    loader = InMemoryScenarioLoader(baseline)
    variant = ScenarioVariantSpec(
        variant_id="road_closure",
        scheduled_events=(
            ScheduledScenarioEvent(
                time=8 * 3600,
                topic="environment.closure.started",
                payload={"target": "link:home-work"},
            ),
        ),
    )

    prepared = loader.load(
        ScenarioConfig(loader_options={"scenario_id": "toy_commute_day"}),
        variant=variant,
    )

    assert prepared.scenario_id == "toy_commute_day"
    assert prepared.variant_id == "road_closure"
    assert prepared.variant.scheduled_events[0].topic == "environment.closure.started"


def test_scenario_specs_validate_duplicates_and_network_endpoints() -> None:
    with pytest.raises(ScenarioValidationError, match="agents contains duplicate"):
        PopulationSpec(
            agents=(
                AgentSpec(agent_id="worker-1"),
                AgentSpec(agent_id="worker-1"),
            ),
        )

    with pytest.raises(ScenarioValidationError, match="unknown node ids"):
        NetworkSpec(
            nodes=(NetworkNodeSpec(node_id="a"),),
            links=(
                NetworkLinkSpec(
                    link_id="bad-link",
                    from_node_id="a",
                    to_node_id="missing",
                ),
            ),
        )
