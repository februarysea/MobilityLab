from __future__ import annotations

from pathlib import Path

import pytest

from campussociety.core import EntityId, Simulation
from campussociety.scenario import (
    ActivitySpec,
    AgentSpec,
    AreaSpec,
    BoundingBox,
    CoordinateReference,
    DataSource,
    FacilitiesSpec,
    FacilitySpec,
    GridCellSpec,
    GridLayerSpec,
    GridLayerType,
    InMemoryScenarioLoader,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
    PlanSpec,
    PointSpec,
    PopulationSpec,
    PreparedScenario,
    ScenarioConfig,
    ScenarioEntity,
    ScenarioSpec,
    ScenarioValidationError,
    ScenarioVariantSpec,
    ScheduledScenarioEvent,
    SpatialIndexKind,
    SpatialIndexSpec,
    SpatialLayersSpec,
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
    spatial_layers = SpatialLayersSpec(
        coordinate_reference=CoordinateReference(
            crs_id="local-planar",
            units="meters",
        ),
        extent=BoundingBox(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0),
        areas=(
            AreaSpec(
                area_id="area:residential",
                area_type="residential",
                name="Residential area",
                centroid=PointSpec(100.0, 100.0),
            ),
            AreaSpec(
                area_id="area:employment",
                area_type="employment",
                name="Employment area",
                centroid=PointSpec(800.0, 800.0),
            ),
        ),
        grid_layers=(
            GridLayerSpec(
                layer_id="grid:heatmap",
                grid_type=GridLayerType.REGULAR_SQUARE,
                extent=BoundingBox(min_x=0.0, min_y=0.0, max_x=1000.0, max_y=1000.0),
                cell_size_meters=250.0,
                topology="moore",
                cells=(
                    GridCellSpec(
                        cell_id="grid:heatmap:0:0",
                        row=0,
                        column=0,
                        area_id="area:residential",
                        centroid=PointSpec(125.0, 125.0),
                    ),
                ),
                initial_property_layers={"walkability": {"default": 1.0}},
            ),
        ),
        spatial_indexes=(
            SpatialIndexSpec(
                index_id="idx:areas",
                index_kind=SpatialIndexKind.STRTREE,
                target_id="areas",
                target_kinds=("area", "cell"),
            ),
        ),
    )

    return PreparedScenario(
        spec=spec,
        population=population,
        network=network,
        facilities=facilities,
        mobility_supply=mobility_supply,
        spatial_layers=spatial_layers,
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
    assert initialized.entities["scenario:toy_commute_day"]["spatial_areas"] == 2
    assert initialized.entities["scenario:toy_commute_day"]["grid_layers"] == 1
    assert initialized.entities["scenario:toy_commute_day"]["spatial_indexes"] == 1
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


def test_spatial_layers_validate_static_spatial_declarations() -> None:
    with pytest.raises(ScenarioValidationError, match="max_x"):
        BoundingBox(min_x=10.0, min_y=0.0, max_x=1.0, max_y=1.0)

    with pytest.raises(ScenarioValidationError, match="areas contains duplicate"):
        SpatialLayersSpec(
            areas=(
                AreaSpec(area_id="area:1", area_type="district"),
                AreaSpec(area_id="area:1", area_type="district"),
            ),
        )

    with pytest.raises(ScenarioValidationError, match="unknown parent ids"):
        SpatialLayersSpec(
            areas=(
                AreaSpec(
                    area_id="area:child",
                    area_type="district",
                    parent_area_id="area:missing",
                ),
            ),
        )

    with pytest.raises(ScenarioValidationError, match="cells contains duplicate"):
        GridLayerSpec(
            layer_id="grid:duplicate-cells",
            grid_type=GridLayerType.CUSTOM,
            cells=(
                GridCellSpec(cell_id="cell:1"),
                GridCellSpec(cell_id="cell:1"),
            ),
        )

    with pytest.raises(ScenarioValidationError, match="unknown targets"):
        SpatialLayersSpec(
            spatial_indexes=(
                SpatialIndexSpec(
                    index_id="idx:missing",
                    index_kind=SpatialIndexKind.QUADTREE,
                    target_id="grid:missing",
                ),
            ),
        )
