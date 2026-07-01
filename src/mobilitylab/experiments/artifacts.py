from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from mobilitylab.core.entities import JsonValue
from mobilitylab.core.snapshots import Snapshot
from mobilitylab.experiments.config import RunConfig
from mobilitylab.scenario.base import PreparedScenario


@dataclass(frozen=True, slots=True)
class ArtifactPaths:
    """Canonical artifact paths for a single run."""

    run_dir: Path
    run_manifest: Path
    events: Path
    metrics: Path
    final_snapshot: Path
    scenario_summary: Path
    replay_manifest: Path
    replay_timeline: Path

    @classmethod
    def for_run_dir(cls, run_dir: Path) -> ArtifactPaths:
        return cls(
            run_dir=run_dir,
            run_manifest=run_dir / "run_manifest.json",
            events=run_dir / "events.jsonl",
            metrics=run_dir / "metrics.json",
            final_snapshot=run_dir / "final_snapshot.json",
            scenario_summary=run_dir / "scenario_summary.json",
            replay_manifest=run_dir / "replay_manifest.json",
            replay_timeline=run_dir / "replay_timeline.jsonl",
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "run_dir": str(self.run_dir),
            "run_manifest": str(self.run_manifest),
            "events": str(self.events),
            "metrics": str(self.metrics),
            "final_snapshot": str(self.final_snapshot),
            "scenario_summary": str(self.scenario_summary),
            "replay_manifest": str(self.replay_manifest),
            "replay_timeline": str(self.replay_timeline),
        }


@dataclass(frozen=True, slots=True)
class RunDirectory:
    """Prepared output directory for one run."""

    path: Path
    overwrite: bool = False

    @classmethod
    def from_config(cls, config: RunConfig) -> RunDirectory:
        return cls(path=config.run_dir, overwrite=config.output.overwrite)

    def prepare(self) -> ArtifactPaths:
        if self.path.exists() and any(self.path.iterdir()) and not self.overwrite:
            msg = f"run directory already exists and is not empty: {self.path}"
            raise FileExistsError(msg)
        self.path.mkdir(parents=True, exist_ok=True)
        return ArtifactPaths.for_run_dir(self.path)


class RunArtifactWriter:
    """Writes MVP run artifacts as JSON and JSONL files."""

    def write(
        self,
        *,
        config: RunConfig,
        scenario: PreparedScenario,
        snapshot: Snapshot,
        event_records: Iterable[Mapping[str, JsonValue]],
        metric_records: Iterable[Mapping[str, JsonValue]],
        paths: ArtifactPaths,
        replay_manifest: Mapping[str, JsonValue] | None = None,
        replay_frames: Iterable[Mapping[str, JsonValue]] = (),
    ) -> None:
        if config.output.write_manifest:
            self._write_json(
                paths.run_manifest,
                {
                    "schema": "mobilitylab.experiment.run_manifest.v1",
                    "run_config": config.to_record(),
                    "scenario": scenario.summary_state(),
                    "artifacts": paths.to_record(),
                },
            )
        if config.output.write_scenario_summary:
            self._write_json(paths.scenario_summary, scenario.summary_state())
        if config.output.write_final_snapshot:
            self._write_json(paths.final_snapshot, snapshot.to_record())
        if config.output.write_events:
            self._write_jsonl(paths.events, event_records)
        if config.output.write_metrics:
            metrics_payload: list[JsonValue] = [
                dict(record) for record in metric_records
            ]
            self._write_json(
                paths.metrics,
                {
                    "schema": "mobilitylab.experiment.metrics.v1",
                    "run_id": config.run_id,
                    "metrics": metrics_payload,
                },
            )
        if replay_manifest is not None:
            self._write_json(paths.replay_manifest, replay_manifest)
            if config.replay.write_timeline:
                self._write_jsonl(paths.replay_timeline, replay_frames)

    def _write_json(self, path: Path, record: Mapping[str, JsonValue]) -> None:
        path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _write_jsonl(
        self,
        path: Path,
        records: Iterable[Mapping[str, JsonValue]],
    ) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True))
                handle.write("\n")
