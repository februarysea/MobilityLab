from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from campussociety.core.entities import JsonValue, copy_state


@dataclass(frozen=True, slots=True)
class MetricTable:
    """Chart-ready flat table derived from one run's metric artifact."""

    run_id: str
    rows: tuple[Mapping[str, JsonValue], ...] = field(default_factory=tuple)
    schema: str = "campussociety.visualization.metric_table.v1"

    def __post_init__(self) -> None:
        if self.run_id == "":
            msg = "run_id must not be empty"
            raise ValueError(msg)
        object.__setattr__(self, "rows", tuple(copy_state(row) for row in self.rows))

    @classmethod
    def from_metrics_payload(cls, payload: Mapping[str, JsonValue]) -> MetricTable:
        raw_run_id = payload.get("run_id")
        if not isinstance(raw_run_id, str) or raw_run_id == "":
            msg = "metrics payload must include non-empty run_id"
            raise ValueError(msg)
        raw_metrics = payload.get("metrics")
        rows: list[dict[str, JsonValue]] = []
        if isinstance(raw_metrics, list):
            for metric in raw_metrics:
                if isinstance(metric, dict):
                    rows.append(copy_state(metric))
        return cls(run_id=raw_run_id, rows=tuple(rows))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "rows": [copy_state(row) for row in self.rows],
        }
