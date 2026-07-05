from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from mobilitylab.config import load_experiment_config

from .run import (
    MinimalCommuteResult,
    execute_minimal_commute,
    print_minimal_commute_result,
)

EXAMPLE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = EXAMPLE_DIR / "config.yaml"


def run_minimal_commute_from_config(
    *,
    config_path: Path = CONFIG_PATH,
    output_root: Path | None = None,
) -> MinimalCommuteResult:
    """Run the minimal commute example from a MobilityLab YAML config."""

    bundle = load_experiment_config(config_path)
    run_config = bundle.run_config
    if output_root is not None:
        run_config = replace(
            run_config,
            output=replace(run_config.output, output_root=output_root),
        )
    return execute_minimal_commute(bundle.scenario, run_config)


def main() -> None:
    print_minimal_commute_result(run_minimal_commute_from_config())


if __name__ == "__main__":
    main()
