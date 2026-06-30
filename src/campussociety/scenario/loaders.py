from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from campussociety.scenario.base import PreparedScenario, ScenarioSpec
from campussociety.scenario.config import ScenarioConfig
from campussociety.scenario.errors import ScenarioLoadError
from campussociety.scenario.variants import ScenarioVariantSpec


@runtime_checkable
class ScenarioLoader(Protocol):
    """Build a PreparedScenario from normalized config or spec input."""

    def load(
        self,
        config: ScenarioConfig | ScenarioSpec,
        *,
        variant: ScenarioVariantSpec | None = None,
    ) -> PreparedScenario: ...


@dataclass(frozen=True, slots=True)
class InMemoryScenarioLoader:
    """Small loader useful for tests, examples, and adapter bootstrapping."""

    scenarios: dict[str, PreparedScenario]

    def __init__(self, *scenarios: PreparedScenario) -> None:
        object.__setattr__(
            self,
            "scenarios",
            {scenario.scenario_id: scenario for scenario in scenarios},
        )

    def load(
        self,
        config: ScenarioConfig | ScenarioSpec,
        *,
        variant: ScenarioVariantSpec | None = None,
    ) -> PreparedScenario:
        scenario_id = self._scenario_id(config)
        try:
            scenario = self.scenarios[scenario_id]
        except KeyError as exc:
            msg = f"unknown in-memory scenario: {scenario_id}"
            raise ScenarioLoadError(msg) from exc

        if variant is None or variant.variant_id == scenario.variant_id:
            return scenario

        if scenario.variant.is_baseline:
            return PreparedScenario(
                spec=scenario.spec.with_variant(variant),
                population=scenario.population,
                network=scenario.network,
                facilities=scenario.facilities,
                mobility_supply=scenario.mobility_supply,
                variant=variant,
                metadata=scenario.metadata,
                initial_entities=scenario.initial_entities,
            )

        msg = (
            "cannot override a non-baseline prepared scenario variant: "
            f"{scenario.variant_id}"
        )
        raise ScenarioLoadError(msg)

    def _scenario_id(self, config: ScenarioConfig | ScenarioSpec) -> str:
        if isinstance(config, ScenarioSpec):
            return config.scenario_id

        value = config.loader_options.get("scenario_id")
        if isinstance(value, str):
            return value

        if len(self.scenarios) == 1:
            return next(iter(self.scenarios))

        msg = "ScenarioConfig loader_options must include a string scenario_id"
        raise ScenarioLoadError(msg)
