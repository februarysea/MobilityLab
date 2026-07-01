from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from campussociety.core.entities import JsonValue

JsonRecord = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class RunArtifactReader:
    """Reads canonical experiment artifacts from one completed run directory."""

    run_dir: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "run_dir", Path(self.run_dir))

    @property
    def run_manifest_path(self) -> Path:
        return self.run_dir / "run_manifest.json"

    @property
    def replay_manifest_path(self) -> Path:
        return self.run_dir / "replay_manifest.json"

    @property
    def replay_timeline_path(self) -> Path:
        return self.run_dir / "replay_timeline.jsonl"

    @property
    def metrics_path(self) -> Path:
        return self.run_dir / "metrics.json"

    @property
    def events_path(self) -> Path:
        return self.run_dir / "events.jsonl"

    @property
    def final_snapshot_path(self) -> Path:
        return self.run_dir / "final_snapshot.json"

    @property
    def scenario_summary_path(self) -> Path:
        return self.run_dir / "scenario_summary.json"

    def read_run_manifest(self) -> JsonRecord:
        return self.read_json(self.run_manifest_path)

    def read_replay_manifest(self) -> JsonRecord:
        return self.read_json(self.replay_manifest_path)

    def read_replay_frames(self) -> tuple[JsonRecord, ...]:
        return tuple(self.read_jsonl(self.replay_timeline_path))

    def read_metrics(self) -> JsonRecord:
        return self.read_json(self.metrics_path)

    def read_trace_events(self) -> tuple[JsonRecord, ...]:
        return tuple(self.read_jsonl(self.events_path))

    def read_final_snapshot(self) -> JsonRecord:
        return self.read_json(self.final_snapshot_path)

    def read_scenario_summary(self) -> JsonRecord:
        return self.read_json(self.scenario_summary_path)

    def read_json(self, path: Path) -> JsonRecord:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            msg = f"expected JSON object in {path}"
            raise ValueError(msg)
        return cast(JsonRecord, payload)

    def read_jsonl(self, path: Path) -> Iterable[JsonRecord]:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if stripped == "":
                    continue
                payload = json.loads(stripped)
                if not isinstance(payload, dict):
                    msg = f"expected JSON object at {path}:{line_number}"
                    raise ValueError(msg)
                yield cast(JsonRecord, payload)


def json_record(mapping: Mapping[str, JsonValue]) -> JsonRecord:
    return dict(mapping)
