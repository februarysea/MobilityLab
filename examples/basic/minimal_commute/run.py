from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mobilitylab.experiments import (
    ExperimentRunner,
    OutputConfig,
    RunConfig,
    RunResult,
    SimulationAssembler,
)
from mobilitylab.scenario import InMemoryScenarioLoader, PreparedScenario
from mobilitylab.visualization import VisualizationExporter, VisualizationExportResult

from .scenario import build_minimal_commute_scenario

EXAMPLE_DIR = Path(__file__).resolve().parent
DEFAULT_RUN_ID = "minimal-commute"


@dataclass(frozen=True, slots=True)
class MinimalCommuteResult:
    """Outputs produced by the minimal commute example."""

    run: RunResult
    visualization: VisualizationExportResult


def run_minimal_commute(
    *,
    output_root: Path | None = None,
    run_id: str = DEFAULT_RUN_ID,
    seed: int = 7,
) -> MinimalCommuteResult:
    """Run the example and export visualization-ready datasets."""

    scenario = build_minimal_commute_scenario()
    config = RunConfig(
        run_id=run_id,
        scenario=scenario.spec,
        seed=seed,
        output=OutputConfig(
            output_root=output_root or EXAMPLE_DIR / "runs",
            overwrite=True,
        ),
        metadata={
            "example": "basic/minimal_commute",
            "purpose": "minimal complete mobility simulation",
        },
    )

    return execute_minimal_commute(scenario, config)


def execute_minimal_commute(
    scenario: PreparedScenario,
    run_config: RunConfig,
) -> MinimalCommuteResult:
    runner = ExperimentRunner(
        assembler=SimulationAssembler(InMemoryScenarioLoader(scenario)),
    )
    run = runner.run(run_config)
    visualization = VisualizationExporter().export_run(run.artifacts.run_dir)
    return MinimalCommuteResult(run=run, visualization=visualization)


def print_minimal_commute_result(result: MinimalCommuteResult) -> None:
    metrics = {metric.name: metric.value for metric in result.run.metrics}

    print(f"Run id: {result.run.run_id}")
    print(f"Status: {result.run.status.value}")
    print(f"Final time: {result.run.snapshot.time} seconds")
    print(f"Agents completed: {metrics.get('agents.lifecycle_status.completed.count')}")
    print(f"Movements arrived: {metrics.get('movement.arrived.count')}")
    print(f"Run artifacts: {result.run.artifacts.run_dir}")
    print(f"Visualization manifest: {result.visualization.manifest_path}")


def main() -> None:
    print_minimal_commute_result(run_minimal_commute())


if __name__ == "__main__":
    main()
