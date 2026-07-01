import type {
  Feature,
  FeatureCollection as GeoJsonFeatureCollection,
  LineString,
  Point,
} from "geojson";

export interface VisualizationManifest {
  schema: string;
  run_id: string;
  scenario_id: string;
  scenario_version: string;
  variant_id: string;
  final_time: number;
  catalog: DatasetCatalog;
  dashboards: DashboardSpec[];
  source_artifacts: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export interface DatasetCatalog {
  schema: string;
  datasets: VisualizationDataset[];
}

export interface VisualizationDataset {
  schema: string;
  dataset_id: string;
  title: string;
  kind: string;
  path: string;
  format: string;
  capabilities: string[];
  columns: ColumnSpec[];
  time_key: string | null;
  entity_key: string | null;
  geometry_key: string | null;
  metadata: Record<string, unknown>;
}

export interface ColumnSpec {
  name: string;
  logical_type: string;
  role: string | null;
  unit: string | null;
  required: boolean;
  metadata: Record<string, unknown>;
}

export interface DashboardSpec {
  schema: string;
  dashboard_id: string;
  title: string;
  panels: PanelSpec[];
  layers: LayerSpec[];
  metadata: Record<string, unknown>;
}

export interface PanelSpec {
  schema: string;
  panel_id: string;
  title: string;
  panel_type: string;
  dataset_ids: string[];
  layer_ids: string[];
  options: Record<string, unknown>;
}

export interface LayerSpec {
  schema: string;
  layer_id: string;
  title: string;
  layer_type: string;
  dataset_id: string;
  visible: boolean;
  encoding: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

export type FeatureCollection = GeoJsonFeatureCollection<
  Point | LineString,
  Record<string, unknown>
> & {
  metadata?: Record<string, unknown>;
};

export type GeoJsonFeature = Feature<Point | LineString, Record<string, unknown>>;

export interface ReplayFrame {
  schema: string;
  run_id: string;
  time: number;
  event_count: number;
  events: SimulationEvent[];
}

export interface SimulationEvent {
  time?: number;
  sequence?: number;
  topic?: string;
  source?: string | null;
  payload?: Record<string, unknown>;
}

export interface MetricTable {
  schema: string;
  run_id: string;
  rows: MetricRow[];
}

export interface MetricRow {
  name: string;
  value: unknown;
  unit?: string | null;
  metadata?: Record<string, unknown>;
}

export interface LoadedVisualization {
  manifest: VisualizationManifest;
  manifestUrl: string;
  network: FeatureCollection;
  facilities: FeatureCollection;
  replayFrames: ReplayFrame[];
  metrics: MetricTable;
  traceEvents: SimulationEvent[];
}
