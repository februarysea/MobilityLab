from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from campussociety.core.entities import JsonValue
from campussociety.core.snapshots import Snapshot
from campussociety.experiments.artifacts import ArtifactPaths
from campussociety.experiments.config import RunConfig
from campussociety.experiments.metrics import MetricResult


class RunStatus(StrEnum):
    """Experiment-level status for one run."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RunResult:
    """Structured result returned by a completed experiment run."""

    config: RunConfig
    status: RunStatus
    snapshot: Snapshot
    metrics: tuple[MetricResult, ...]
    artifacts: ArtifactPaths

    @property
    def run_id(self) -> str:
        return self.config.run_id

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": "campussociety.experiment.run_result.v1",
            "run_id": self.run_id,
            "status": self.status.value,
            "final_time": self.snapshot.time,
            "simulation_status": self.snapshot.status,
            "metric_count": len(self.metrics),
            "artifacts": self.artifacts.to_record(),
        }
