import type {
  FeatureCollection,
  LoadedVisualization,
  MetricTable,
  ReplayFrame,
  SimulationEvent,
  VisualizationDataset,
  VisualizationManifest,
} from "../types";

const DEFAULT_MANIFEST_CANDIDATES = [
  "/run-artifacts/visualization_manifest.json",
  "/sample/visualization_manifest.json",
];

export async function loadVisualization(): Promise<LoadedVisualization> {
  const { manifest, manifestUrl } = await loadManifest();
  const datasetUrl = (datasetId: string) =>
    resolveDatasetUrl(manifestUrl, dataset(manifest, datasetId));

  const [network, facilities, replayFrames, metrics, traceEvents] =
    await Promise.all([
      loadJson<FeatureCollection>(datasetUrl("network")),
      loadJson<FeatureCollection>(datasetUrl("facilities")),
      loadJsonl<ReplayFrame>(datasetUrl("replay_frames")),
      loadJson<MetricTable>(datasetUrl("metrics")),
      loadJsonl<SimulationEvent>(datasetUrl("trace_events")),
    ]);

  return {
    manifest,
    manifestUrl,
    network,
    facilities,
    replayFrames,
    metrics,
    traceEvents,
  };
}

async function loadManifest(): Promise<{
  manifest: VisualizationManifest;
  manifestUrl: string;
}> {
  const params = new URLSearchParams(window.location.search);
  const explicitManifest = params.get("manifest");
  const candidates = explicitManifest
    ? [explicitManifest]
    : DEFAULT_MANIFEST_CANDIDATES;
  const failures: string[] = [];

  for (const candidate of candidates) {
    const url = new URL(candidate, window.location.href).toString();
    try {
      return {
        manifest: await loadJson<VisualizationManifest>(url),
        manifestUrl: url,
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      failures.push(`${url} (${message})`);
      if (explicitManifest) {
        break;
      }
    }
  }

  throw new Error(`Could not load visualization manifest: ${failures.join(", ")}`);
}

async function loadJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  try {
    return (await response.json()) as T;
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`Failed to parse JSON from ${url}: ${message}`);
  }
}

async function loadJsonl<T>(url: string): Promise<T[]> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to load ${url}: ${response.status}`);
  }
  const text = await response.text();
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
    .map((line) => JSON.parse(line) as T);
}

function dataset(
  manifest: VisualizationManifest,
  datasetId: string,
): VisualizationDataset {
  const found = manifest.catalog.datasets.find(
    (item) => item.dataset_id === datasetId,
  );
  if (!found) {
    throw new Error(`Manifest does not include dataset: ${datasetId}`);
  }
  return found;
}

function resolveDatasetUrl(
  manifestUrl: string,
  dataset: VisualizationDataset,
): string {
  return new URL(dataset.path, manifestUrl).toString();
}
