from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field

from mobilitylab.core.entities import JsonValue, copy_state
from mobilitylab.core.snapshots import Snapshot
from mobilitylab.experiments.artifacts import ArtifactPaths
from mobilitylab.experiments.config import RunConfig
from mobilitylab.experiments.traces import TraceRecord
from mobilitylab.scenario.base import PreparedScenario


@dataclass(frozen=True, slots=True)
class ReplayFrame:
    """Events grouped at one simulation time for replay viewers."""

    run_id: str
    time: int
    events: tuple[Mapping[str, JsonValue], ...] = ()
    schema: str = "mobilitylab.experiment.replay_frame.v1"

    def __post_init__(self) -> None:
        if self.run_id == "":
            msg = "run_id must not be empty"
            raise ValueError(msg)
        if self.time < 0:
            msg = "time must be non-negative"
            raise ValueError(msg)
        object.__setattr__(
            self,
            "events",
            tuple(copy_state(event) for event in self.events),
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "time": self.time,
            "event_count": len(self.events),
            "events": [copy_state(event) for event in self.events],
        }


@dataclass(frozen=True, slots=True)
class ReplayManifest:
    """Visualization-ready replay entrypoint for one completed run."""

    run_id: str
    scenario_id: str
    scenario_version: str
    variant_id: str
    seed: int
    start_time: int
    final_time: int
    simulation_status: str
    event_count: int
    frame_count: int
    artifacts: Mapping[str, JsonValue]
    metadata: Mapping[str, JsonValue] = field(default_factory=dict)
    schema: str = "mobilitylab.experiment.replay_manifest.v1"

    def __post_init__(self) -> None:
        for field_name, value in {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "variant_id": self.variant_id,
            "simulation_status": self.simulation_status,
            "schema": self.schema,
        }.items():
            if value == "":
                msg = f"{field_name} must not be empty"
                raise ValueError(msg)
        object.__setattr__(self, "artifacts", copy_state(self.artifacts))
        object.__setattr__(self, "metadata", copy_state(self.metadata))

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "scenario_version": self.scenario_version,
            "variant_id": self.variant_id,
            "seed": self.seed,
            "start_time": self.start_time,
            "final_time": self.final_time,
            "simulation_status": self.simulation_status,
            "event_count": self.event_count,
            "frame_count": self.frame_count,
            "artifacts": copy_state(self.artifacts),
            "metadata": copy_state(self.metadata),
        }


class ReplayBuilder:
    """Builds replay manifest and timeline records from completed run outputs."""

    def build_frames(
        self,
        config: RunConfig,
        trace_records: tuple[TraceRecord, ...],
    ) -> tuple[ReplayFrame, ...]:
        if not config.replay.enabled or not config.replay.write_timeline:
            return ()

        grouped: dict[int, list[dict[str, JsonValue]]] = defaultdict(list)
        for trace_record in trace_records:
            record = trace_record.to_record()
            raw_time = record.get("time")
            if not isinstance(raw_time, int):
                continue
            grouped[raw_time].append(record)

        return tuple(
            ReplayFrame(
                run_id=config.run_id,
                time=time,
                events=tuple(sorted(grouped[time], key=self._event_sequence_sort_key)),
            )
            for time in sorted(grouped)
        )

    def build_manifest(
        self,
        *,
        config: RunConfig,
        scenario: PreparedScenario,
        snapshot: Snapshot,
        paths: ArtifactPaths,
        trace_records: tuple[TraceRecord, ...],
        frames: tuple[ReplayFrame, ...],
    ) -> ReplayManifest | None:
        if not config.replay.enabled:
            return None

        return ReplayManifest(
            run_id=config.run_id,
            scenario_id=scenario.scenario_id,
            scenario_version=scenario.version,
            variant_id=scenario.variant_id,
            seed=config.seed,
            start_time=config.start_time,
            final_time=snapshot.time,
            simulation_status=snapshot.status,
            event_count=len(trace_records),
            frame_count=len(frames),
            artifacts=paths.to_record(),
            metadata={
                "replay_timeline_written": config.replay.write_timeline,
            },
        )

    def _event_sequence_sort_key(self, record: Mapping[str, JsonValue]) -> int:
        raw_sequence = record.get("sequence")
        return raw_sequence if isinstance(raw_sequence, int) else 0
