"""Scenario loading, population construction, and variant definitions."""

from campussociety.scenario.base import (
    DataSource,
    PreparedScenario,
    ScenarioEntity,
    ScenarioInitializer,
    ScenarioSpec,
)
from campussociety.scenario.config import (
    SCENARIO_CONFIG_SCHEMA_VERSION,
    ScenarioConfig,
)
from campussociety.scenario.errors import (
    ScenarioError,
    ScenarioLoadError,
    ScenarioValidationError,
)
from campussociety.scenario.loaders import InMemoryScenarioLoader, ScenarioLoader
from campussociety.scenario.population import (
    ActivitySpec,
    AgentSpec,
    PlanSpec,
    PopulationSpec,
)
from campussociety.scenario.variants import (
    BASELINE_VARIANT_ID,
    ScenarioVariantSpec,
    ScheduledScenarioEvent,
    baseline_variant,
)
from campussociety.scenario.world import (
    FacilitiesSpec,
    FacilitySpec,
    MobilityModeSpec,
    MobilitySupplySpec,
    NetworkLinkSpec,
    NetworkNodeSpec,
    NetworkSpec,
)

__all__ = [
    "BASELINE_VARIANT_ID",
    "SCENARIO_CONFIG_SCHEMA_VERSION",
    "ActivitySpec",
    "AgentSpec",
    "DataSource",
    "FacilitiesSpec",
    "FacilitySpec",
    "InMemoryScenarioLoader",
    "MobilityModeSpec",
    "MobilitySupplySpec",
    "NetworkLinkSpec",
    "NetworkNodeSpec",
    "NetworkSpec",
    "PlanSpec",
    "PopulationSpec",
    "PreparedScenario",
    "ScenarioConfig",
    "ScenarioEntity",
    "ScenarioError",
    "ScenarioInitializer",
    "ScenarioLoadError",
    "ScenarioLoader",
    "ScenarioSpec",
    "ScenarioValidationError",
    "ScenarioVariantSpec",
    "ScheduledScenarioEvent",
    "baseline_variant",
]
