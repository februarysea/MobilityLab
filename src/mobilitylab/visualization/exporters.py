from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from mobilitylab.core.entities import JsonValue, copy_state
from mobilitylab.visualization.dashboards import default_replay_dashboard
from mobilitylab.visualization.datasets import (
    ColumnSpec,
    DatasetCapability,
    DatasetCatalog,
    VisualizationDataset,
    VisualizationManifest,
)
from mobilitylab.visualization.geometry import geometry_from_snapshot
from mobilitylab.visualization.metrics import MetricTable
from mobilitylab.visualization.readers import JsonRecord, RunArtifactReader


@dataclass(frozen=True, slots=True)
class VisualizationExportResult:
    """Paths written by a visualization export."""

    run_dir: Path
    manifest_path: Path
    datasets_dir: Path
    manifest: VisualizationManifest


@dataclass(frozen=True, slots=True)
class VisualizationExporter:
    """Exports visualization-ready datasets from completed experiment artifacts."""

    datasets_dir_name: str = "datasets"
    manifest_filename: str = "visualization_manifest.json"

    def export_run(
        self,
        run_dir: Path,
        *,
        output_dir: Path | None = None,
    ) -> VisualizationExportResult:
        run_dir = Path(run_dir)
        target_dir = run_dir if output_dir is None else Path(output_dir)
        datasets_dir = target_dir / self.datasets_dir_name
        datasets_dir.mkdir(parents=True, exist_ok=True)

        reader = RunArtifactReader(run_dir)
        replay_manifest = reader.read_replay_manifest()
        final_snapshot = reader.read_final_snapshot()
        replay_frames = reader.read_replay_frames()
        trace_events = reader.read_trace_events()
        metric_table = MetricTable.from_metrics_payload(reader.read_metrics())
        geometry = geometry_from_snapshot(final_snapshot)

        self._write_json(datasets_dir / "network.geojson", geometry.network_geojson)
        self._write_json(
            datasets_dir / "facilities.geojson",
            geometry.facilities_geojson,
        )
        self._write_jsonl(datasets_dir / "replay_frames.jsonl", replay_frames)
        self._write_json(datasets_dir / "metrics.json", metric_table.to_record())
        self._write_jsonl(datasets_dir / "trace_events.jsonl", trace_events)

        catalog = default_dataset_catalog()
        dashboard = default_replay_dashboard()
        manifest = VisualizationManifest(
            run_id=_string(replay_manifest, "run_id"),
            scenario_id=_string(replay_manifest, "scenario_id"),
            scenario_version=_string(replay_manifest, "scenario_version"),
            variant_id=_string(replay_manifest, "variant_id"),
            final_time=_int(replay_manifest, "final_time"),
            catalog=catalog,
            dashboards=(dashboard.to_record(),),
            source_artifacts=copy_state(_mapping(replay_manifest.get("artifacts"))),
            metadata={
                "event_count": replay_manifest.get("event_count"),
                "frame_count": replay_manifest.get("frame_count"),
                "exporter": "VisualizationExporter",
            },
        )
        manifest_path = target_dir / self.manifest_filename
        self._write_json(manifest_path, manifest.to_record())
        return VisualizationExportResult(
            run_dir=run_dir,
            manifest_path=manifest_path,
            datasets_dir=datasets_dir,
            manifest=manifest,
        )

    def _write_json(
        self,
        path: Path,
        record: Mapping[str, JsonValue],
    ) -> None:
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


def default_dataset_catalog() -> DatasetCatalog:
    """Datasets emitted by the MVP visualization exporter."""

    return DatasetCatalog(
        (
            VisualizationDataset(
                dataset_id="network",
                title="Network Geometry",
                kind="geojson",
                path="datasets/network.geojson",
                format="geojson",
                capabilities=(DatasetCapability.NETWORK_GEOMETRY,),
                geometry_key="geometry",
                metadata={"recommended_layer": "network"},
            ),
            VisualizationDataset(
                dataset_id="facilities",
                title="Facility Points",
                kind="geojson",
                path="datasets/facilities.geojson",
                format="geojson",
                capabilities=(DatasetCapability.FACILITY_POINTS,),
                geometry_key="geometry",
                metadata={"recommended_layer": "facilities"},
            ),
            VisualizationDataset(
                dataset_id="replay_frames",
                title="Replay Frames",
                kind="jsonl",
                path="datasets/replay_frames.jsonl",
                format="jsonl",
                capabilities=(DatasetCapability.REPLAY_FRAMES,),
                columns=(
                    ColumnSpec("time", "integer", role="time", unit="seconds"),
                    ColumnSpec("event_count", "integer", role="measure"),
                    ColumnSpec("events", "array", role="nested_events"),
                ),
                time_key="time",
                metadata={"recommended_panel": "timeline"},
            ),
            VisualizationDataset(
                dataset_id="metrics",
                title="Run Metrics",
                kind="json",
                path="datasets/metrics.json",
                format="json",
                capabilities=(DatasetCapability.METRIC_SUMMARY,),
                columns=(
                    ColumnSpec("name", "string", role="dimension"),
                    ColumnSpec("value", "json", role="measure"),
                    ColumnSpec("unit", "string", role="unit", required=False),
                ),
                metadata={"recommended_panel": "metrics"},
            ),
            VisualizationDataset(
                dataset_id="trace_events",
                title="Trace Events",
                kind="jsonl",
                path="datasets/trace_events.jsonl",
                format="jsonl",
                capabilities=(
                    DatasetCapability.EVENT_TIMELINE,
                    DatasetCapability.TRACE_EVENTS,
                ),
                columns=(
                    ColumnSpec("time", "integer", role="time", unit="seconds"),
                    ColumnSpec("sequence", "integer", role="order"),
                    ColumnSpec("topic", "string", role="category"),
                    ColumnSpec("payload", "object", role="details"),
                ),
                time_key="time",
                metadata={"recommended_panel": "events"},
            ),
        )
    )


def _string(record: Mapping[str, JsonValue], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or value == "":
        msg = f"expected non-empty string field: {key}"
        raise ValueError(msg)
    return value


def _int(record: Mapping[str, JsonValue], key: str) -> int:
    value = record.get(key)
    if not isinstance(value, int):
        msg = f"expected integer field: {key}"
        raise ValueError(msg)
    return value


def _mapping(value: JsonValue | None) -> JsonRecord:
    return dict(value) if isinstance(value, dict) else {}
