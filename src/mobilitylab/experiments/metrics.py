from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from mobilitylab.core.entities import JsonValue, copy_state
from mobilitylab.core.snapshots import Snapshot
from mobilitylab.experiments.config import MetricConfig, RunConfig
from mobilitylab.experiments.traces import TraceRecord
from mobilitylab.scenario.base import PreparedScenario


@dataclass(frozen=True, slots=True)
class MetricResult:
    """One structured metric produced by a run."""

    name: str
    value: JsonValue
    unit: str | None = None
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.name == "":
            msg = "metric name must not be empty"
            raise ValueError(msg)
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "metadata": copy_state(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class MetricContext:
    """Readonly context passed to metric collectors."""

    config: RunConfig
    scenario: PreparedScenario
    snapshot: Snapshot
    trace_records: tuple[TraceRecord, ...] = ()


class MetricCollector(Protocol):
    """Contract for experiment-level metric collectors."""

    def collect(self, context: MetricContext) -> tuple[MetricResult, ...]: ...


@dataclass(frozen=True, slots=True)
class DefaultMetricCollector:
    """Small built-in collector for run, event, agent, and movement summaries."""

    config: MetricConfig = MetricConfig()

    def collect(self, context: MetricContext) -> tuple[MetricResult, ...]:
        if not self.config.enabled:
            return ()

        metrics: list[MetricResult] = []
        if self.config.include_run_summary:
            metrics.extend(self._run_summary(context))
        if self.config.include_event_counts:
            metrics.extend(self._event_counts(context.trace_records))
        if self.config.include_agent_summary:
            metrics.extend(self._agent_summary(context.snapshot))
        if self.config.include_movement_summary:
            metrics.extend(self._movement_summary(context.trace_records))
        return tuple(metrics)

    def _run_summary(self, context: MetricContext) -> tuple[MetricResult, ...]:
        return (
            MetricResult("run.start_time", context.config.start_time, unit="seconds"),
            MetricResult("run.final_time", context.snapshot.time, unit="seconds"),
            MetricResult(
                "run.duration",
                context.snapshot.time - context.config.start_time,
                unit="seconds",
            ),
            MetricResult("run.pending_tasks", context.snapshot.pending_tasks),
            MetricResult("run.entity_count", len(context.snapshot.entities)),
            MetricResult("run.event_count", len(context.trace_records)),
            MetricResult("scenario.population_size", context.scenario.population.size),
            MetricResult("scenario.network_nodes", context.scenario.network.node_count),
            MetricResult("scenario.network_links", context.scenario.network.link_count),
            MetricResult("scenario.facility_count", context.scenario.facilities.size),
        )

    def _event_counts(
        self,
        trace_records: tuple[TraceRecord, ...],
    ) -> tuple[MetricResult, ...]:
        counts = Counter(self._topic(record) for record in trace_records)
        return tuple(
            MetricResult(
                name=f"events.{topic}.count",
                value=count,
                metadata={"topic": topic},
            )
            for topic, count in sorted(counts.items())
            if topic is not None
        )

    def _agent_summary(self, snapshot: Snapshot) -> tuple[MetricResult, ...]:
        agent_system = snapshot.entities.get("agents")
        if agent_system is None:
            return ()
        raw_agents = agent_system.get("agents")
        if not isinstance(raw_agents, dict):
            return ()

        status_counts: Counter[str] = Counter()
        for agent_state in raw_agents.values():
            if not isinstance(agent_state, dict):
                continue
            raw_state = agent_state.get("state")
            if not isinstance(raw_state, dict):
                continue
            raw_status = raw_state.get("lifecycle_status")
            if isinstance(raw_status, str):
                status_counts[raw_status] += 1

        metrics = [MetricResult("agents.count", len(raw_agents))]
        metrics.extend(
            MetricResult(
                name=f"agents.lifecycle_status.{status}.count",
                value=count,
                metadata={"lifecycle_status": status},
            )
            for status, count in sorted(status_counts.items())
        )
        return tuple(metrics)

    def _movement_summary(
        self,
        trace_records: tuple[TraceRecord, ...],
    ) -> tuple[MetricResult, ...]:
        started = 0
        arrived = 0
        failed = 0
        mode_counts: Counter[str] = Counter()
        for record in trace_records:
            event = record.to_record()
            topic = event.get("topic")
            if topic == "movement.started":
                started += 1
                payload = event.get("payload")
                if isinstance(payload, dict):
                    raw_mode = payload.get("mode")
                    if isinstance(raw_mode, str):
                        mode_counts[raw_mode] += 1
            elif topic == "movement.arrived":
                arrived += 1
            elif topic == "movement.failed":
                failed += 1

        metrics = [
            MetricResult("movement.started.count", started),
            MetricResult("movement.arrived.count", arrived),
            MetricResult("movement.failed.count", failed),
        ]
        metrics.extend(
            MetricResult(
                name=f"movement.mode.{mode}.count",
                value=count,
                metadata={"mode": mode},
            )
            for mode, count in sorted(mode_counts.items())
        )
        return tuple(metrics)

    def _topic(self, record: TraceRecord) -> str | None:
        topic = record.to_record().get("topic")
        return topic if isinstance(topic, str) else None
