from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mobilitylab.core.snapshots import Snapshot
    from mobilitylab.experiments.assembly import AssembledRun
    from mobilitylab.experiments.config import RunConfig
    from mobilitylab.experiments.results import RunResult


class RunListener:
    """No-op hook object for experiment-level run orchestration."""

    def on_run_started(self, config: RunConfig) -> None:
        return

    def on_simulation_built(self, assembled: AssembledRun) -> None:
        return

    def on_before_simulation(self, assembled: AssembledRun) -> None:
        return

    def on_after_simulation(self, assembled: AssembledRun, snapshot: Snapshot) -> None:
        return

    def on_run_completed(self, result: RunResult) -> None:
        return

    def on_run_failed(self, config: RunConfig, error: BaseException) -> None:
        return
