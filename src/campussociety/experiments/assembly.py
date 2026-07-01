from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.agents import AgentSystem, AgentSystemBuilder, BehaviorModel
from campussociety.core import Simulation
from campussociety.core.entities import JsonValue
from campussociety.environment import Environment, EnvironmentBuilder
from campussociety.experiments.config import RunConfig
from campussociety.scenario import PreparedScenario, ScenarioLoader


@dataclass(frozen=True, slots=True)
class AssembledRun:
    """Concrete runtime components for one simulation run."""

    config: RunConfig
    scenario: PreparedScenario
    environment: Environment
    agent_system: AgentSystem
    simulation: Simulation
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SimulationAssembler:
    """Builds a runnable Simulation from experiment, scenario, and runtime builders."""

    scenario_loader: ScenarioLoader
    environment_builder: EnvironmentBuilder = field(default_factory=EnvironmentBuilder)
    agent_system_builder: AgentSystemBuilder = field(default_factory=AgentSystemBuilder)

    def assemble(
        self,
        config: RunConfig,
        *,
        behavior_models: Mapping[str, BehaviorModel] | None = None,
    ) -> AssembledRun:
        scenario = self.scenario_loader.load(config.scenario, variant=config.variant)
        environment = self.environment_builder.build(scenario)
        agent_system = self.agent_system_builder.build(
            scenario,
            environment,
            behavior_models=behavior_models,
        )
        simulation = Simulation(
            seed=config.seed,
            simulation_id=config.run_id,
            start_time=config.start_time,
        )
        simulation.add_initializer(scenario.create_initializer())
        simulation.add_initializer(environment.create_initializer())
        simulation.add_initializer(agent_system.create_initializer())
        return AssembledRun(
            config=config,
            scenario=scenario,
            environment=environment,
            agent_system=agent_system,
            simulation=simulation,
            metadata={
                "scenario_id": scenario.scenario_id,
                "scenario_version": scenario.version,
                "variant_id": scenario.variant_id,
            },
        )
