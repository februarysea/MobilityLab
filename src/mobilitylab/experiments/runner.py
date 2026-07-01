from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from mobilitylab.agents import BehaviorModel
from mobilitylab.experiments.artifacts import RunArtifactWriter, RunDirectory
from mobilitylab.experiments.assembly import SimulationAssembler
from mobilitylab.experiments.config import RunConfig, TraceConfig
from mobilitylab.experiments.listeners import RunListener
from mobilitylab.experiments.metrics import (
    DefaultMetricCollector,
    MetricCollector,
    MetricContext,
)
from mobilitylab.experiments.replay import ReplayBuilder
from mobilitylab.experiments.results import RunResult, RunStatus
from mobilitylab.experiments.traces import EventTraceCollector


@dataclass(slots=True)
class SingleRunRunner:
    """Runs one fully configured deterministic simulation and writes artifacts."""

    assembler: SimulationAssembler
    metric_collector: MetricCollector = field(default_factory=DefaultMetricCollector)
    artifact_writer: RunArtifactWriter = field(default_factory=RunArtifactWriter)
    replay_builder: ReplayBuilder = field(default_factory=ReplayBuilder)
    listeners: tuple[RunListener, ...] = ()

    def __post_init__(self) -> None:
        self.listeners = tuple(self.listeners)

    def run(
        self,
        config: RunConfig,
        *,
        behavior_models: Mapping[str, BehaviorModel] | None = None,
    ) -> RunResult:
        try:
            for listener in self.listeners:
                listener.on_run_started(config)

            paths = RunDirectory.from_config(config).prepare()
            assembled = self.assembler.assemble(
                config,
                behavior_models=behavior_models,
            )
            for listener in self.listeners:
                listener.on_simulation_built(assembled)
            for listener in self.listeners:
                listener.on_before_simulation(assembled)

            snapshot = assembled.simulation.run(
                until=config.until,
                max_steps=config.max_steps,
            )
            for listener in self.listeners:
                listener.on_after_simulation(assembled, snapshot)

            trace_records = EventTraceCollector(config.trace).collect(snapshot)
            metric_trace_records = EventTraceCollector(TraceConfig()).collect(snapshot)
            metric_context = MetricContext(
                config=config,
                scenario=assembled.scenario,
                snapshot=snapshot,
                trace_records=metric_trace_records,
            )
            metrics = self.metric_collector.collect(metric_context)
            event_records = tuple(record.to_record() for record in trace_records)
            metric_records = tuple(metric.to_record() for metric in metrics)
            replay_frames = self.replay_builder.build_frames(
                config,
                metric_trace_records,
            )
            replay_manifest = self.replay_builder.build_manifest(
                config=config,
                scenario=assembled.scenario,
                snapshot=snapshot,
                paths=paths,
                trace_records=metric_trace_records,
                frames=replay_frames,
            )
            self.artifact_writer.write(
                config=config,
                scenario=assembled.scenario,
                snapshot=snapshot,
                event_records=event_records,
                metric_records=metric_records,
                paths=paths,
                replay_manifest=(
                    None if replay_manifest is None else replay_manifest.to_record()
                ),
                replay_frames=tuple(frame.to_record() for frame in replay_frames),
            )

            result = RunResult(
                config=config,
                status=RunStatus.COMPLETED,
                snapshot=snapshot,
                metrics=metrics,
                artifacts=paths,
            )
            for listener in self.listeners:
                listener.on_run_completed(result)
            return result
        except BaseException as exc:
            for listener in self.listeners:
                listener.on_run_failed(config, exc)
            raise


class ExperimentRunner(SingleRunRunner):
    """Alias-style runner name for the experiment layer's public API."""
