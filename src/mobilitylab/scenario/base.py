from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeAlias

from mobilitylab.core.entities import (
    Entity,
    EntityId,
    JsonValue,
    State,
    copy_state,
)
from mobilitylab.core.simulation import RunContext
from mobilitylab.scenario._utils import (
    copy_json_mapping,
    require_non_empty,
    require_unique,
)
from mobilitylab.scenario.errors import ScenarioValidationError
from mobilitylab.scenario.population import PopulationSpec
from mobilitylab.scenario.spatial import SpatialLayersSpec
from mobilitylab.scenario.variants import ScenarioVariantSpec, baseline_variant
from mobilitylab.scenario.world import (
    FacilitiesSpec,
    MobilitySupplySpec,
    NetworkSpec,
)

ScenarioInitializer: TypeAlias = Callable[[RunContext], None]


@dataclass(frozen=True, slots=True)
class DataSource:
    """Normalized reference to one scenario input source."""

    source_id: str
    source_type: str
    path: Path | None = None
    schema_version: str | None = None
    options: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.source_id, "source_id")
        require_non_empty(self.source_type, "source_type")
        if self.path is not None:
            object.__setattr__(self, "path", Path(self.path))
        object.__setattr__(self, "options", copy_json_mapping(self.options))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "path": str(self.path) if self.path is not None else None,
            "schema_version": self.schema_version,
            "options": copy_json_mapping(self.options),
        }


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    """Canonical scenario declaration after user config has been normalized."""

    scenario_id: str
    version: str
    variant_id: str = "baseline"
    data_sources: tuple[DataSource, ...] = ()
    policy_defaults: Mapping[str, JsonValue] = field(default_factory=dict)
    initial_assumptions: Mapping[str, JsonValue] = field(default_factory=dict)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(self.scenario_id, "scenario_id")
        require_non_empty(self.version, "version")
        require_non_empty(self.variant_id, "variant_id")
        object.__setattr__(self, "data_sources", tuple(self.data_sources))
        require_unique(
            (data_source.source_id for data_source in self.data_sources),
            "data_sources",
        )
        object.__setattr__(
            self,
            "policy_defaults",
            copy_json_mapping(self.policy_defaults),
        )
        object.__setattr__(
            self,
            "initial_assumptions",
            copy_json_mapping(self.initial_assumptions),
        )
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))

    def with_variant(self, variant: ScenarioVariantSpec) -> ScenarioSpec:
        return ScenarioSpec(
            scenario_id=self.scenario_id,
            version=self.version,
            variant_id=variant.variant_id,
            data_sources=self.data_sources,
            policy_defaults=self.policy_defaults,
            initial_assumptions=self.initial_assumptions,
            metadata=self.metadata,
        )

    def data_source(self, source_id: str) -> DataSource:
        for data_source in self.data_sources:
            if data_source.source_id == source_id:
                return data_source
        msg = f"unknown data source: {source_id}"
        raise KeyError(msg)

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "scenario_id": self.scenario_id,
            "version": self.version,
            "variant_id": self.variant_id,
            "data_sources": [
                data_source.to_record() for data_source in self.data_sources
            ],
            "policy_defaults": copy_json_mapping(self.policy_defaults),
            "initial_assumptions": copy_json_mapping(self.initial_assumptions),
            "metadata": copy_json_mapping(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ScenarioEntity:
    """Small core entity used for scenario metadata and loader-created state."""

    id: EntityId
    entity_type: str
    state: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        require_non_empty(str(self.id), "id")
        require_non_empty(self.entity_type, "entity_type")
        object.__setattr__(self, "state", copy_json_mapping(self.state))

    def snapshot_state(self) -> State:
        state = copy_state(self.state)
        state["entity_type"] = self.entity_type
        return state


@dataclass(frozen=True, slots=True)
class PreparedScenario:
    """Loaded, validated scenario ready to install into a Simulation."""

    spec: ScenarioSpec
    population: PopulationSpec = field(default_factory=PopulationSpec)
    network: NetworkSpec = field(default_factory=NetworkSpec)
    facilities: FacilitiesSpec = field(default_factory=FacilitiesSpec)
    mobility_supply: MobilitySupplySpec = field(default_factory=MobilitySupplySpec)
    spatial_layers: SpatialLayersSpec = field(default_factory=SpatialLayersSpec)
    variant: ScenarioVariantSpec = field(default_factory=baseline_variant)
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    initial_entities: tuple[Entity, ...] = ()

    def __post_init__(self) -> None:
        if self.spec.variant_id != self.variant.variant_id:
            msg = (
                "prepared scenario variant does not match spec: "
                f"{self.variant.variant_id} != {self.spec.variant_id}"
            )
            raise ScenarioValidationError(msg)
        object.__setattr__(self, "metadata", copy_json_mapping(self.metadata))
        object.__setattr__(self, "initial_entities", tuple(self.initial_entities))

    @property
    def scenario_id(self) -> str:
        return self.spec.scenario_id

    @property
    def version(self) -> str:
        return self.spec.version

    @property
    def variant_id(self) -> str:
        return self.spec.variant_id

    @property
    def metadata_entity_id(self) -> EntityId:
        return EntityId(f"scenario:{self.scenario_id}")

    def summary_state(self) -> State:
        return {
            "scenario_id": self.scenario_id,
            "version": self.version,
            "variant_id": self.variant_id,
            "schema": "mobilitylab.prepared_scenario.summary.v1",
            "population_size": self.population.size,
            "network_nodes": self.network.node_count,
            "network_links": self.network.link_count,
            "facility_count": self.facilities.size,
            "mobility_modes": self.mobility_supply.mode_count,
            "spatial_areas": self.spatial_layers.area_count,
            "grid_layers": self.spatial_layers.grid_layer_count,
            "spatial_indexes": self.spatial_layers.spatial_index_count,
            "spatial_layers": self.spatial_layers.to_record(),
            "spec": self.spec.to_record(),
            "variant": self.variant.to_record(),
            "metadata": copy_json_mapping(self.metadata),
        }

    def metadata_entity(self) -> ScenarioEntity:
        return ScenarioEntity(
            id=self.metadata_entity_id,
            entity_type="scenario",
            state=self.summary_state(),
        )

    def create_initializer(
        self,
        *,
        register_metadata_entity: bool = True,
    ) -> ScenarioInitializer:
        def initialize(context: RunContext) -> None:
            self.install(
                context,
                register_metadata_entity=register_metadata_entity,
            )

        return initialize

    def install(
        self,
        context: RunContext,
        *,
        register_metadata_entity: bool = True,
    ) -> None:
        source: EntityId | None = None
        if register_metadata_entity:
            metadata_entity = self.metadata_entity()
            context.entities.register(metadata_entity)
            source = metadata_entity.id

        for entity in self.initial_entities:
            context.entities.register(entity)

        for event in self.variant.scheduled_events:
            source_id = EntityId(event.source) if event.source is not None else None

            def emit_scenario_event(
                inner_context: RunContext,
                *,
                event_topic: str = event.topic,
                event_payload: Mapping[str, JsonValue] = event.payload,
                event_source: EntityId | None = source_id,
            ) -> None:
                inner_context.emit(
                    event_topic,
                    copy_json_mapping(event_payload),
                    source=event_source,
                )

            context.schedule_at(
                event.time,
                emit_scenario_event,
                priority=event.priority,
                label=event.label or f"scenario:{self.variant_id}:{event.topic}",
            )

        context.emit(
            "scenario.initialized",
            self.summary_state(),
            source=source,
        )
