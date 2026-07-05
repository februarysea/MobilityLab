# Example Issue Report: EX-BASIC-MINCOMM-001

## Report Metadata

- Report path:
  `docs/example-reports/basic-minimal-commute/EX-BASIC-MINCOMM-001.md`
- Example path: `examples/basic/minimal_commute`
- Issue id: `EX-BASIC-MINCOMM-001`
- Last updated: 2026-07-06

## Issue Summary

- Status: verified
- Severity: major
- Suspected layer: visualization
- Issue type: framework bug

## Run Context

- Commit under test: `ebb35fe`
- Branch: `main`
- Date: 2026-07-03T14:15:22+08:00
- Command: `uv run python -m examples.basic.minimal_commute.run_from_config`
- Working directory: `/nvme01/home/jichunhou/CampusSociety`
- Python version: Python 3.12.3 through `uv run python`
- Package install mode: local workspace through `uv`
- Operating system: Linux `umep` 6.8.0-53-generic x86_64

## Example Contract

### Expected Behavior

The `basic/minimal_commute` example should run a complete minimal mobility
simulation from YAML, export visualization-ready artifacts, and allow the
React/Vite replay viewer to inspect the completed run.

### Expected Outputs

- `examples/basic/minimal_commute/runs/minimal-commute/visualization_manifest.json`
- `examples/basic/minimal_commute/runs/minimal-commute/datasets/network.geojson`
- `examples/basic/minimal_commute/runs/minimal-commute/datasets/facilities.geojson`
- `examples/basic/minimal_commute/runs/minimal-commute/datasets/replay_frames.jsonl`
- `examples/basic/minimal_commute/runs/minimal-commute/datasets/metrics.json`
- `examples/basic/minimal_commute/runs/minimal-commute/datasets/trace_events.jsonl`
- The viewer should render the exported minimal commute network, including all
  3 network links and all 3 facilities.

## Actual Behavior

The simulation run and visualization export complete successfully. The exported
run artifacts contain the expected network and facility data:

- Network dataset: 7 map features total, including 4 `Point` features and
  3 `LineString` features.
- Network link ids: `main-to-work`, `north-home-to-main`,
  `south-home-to-main`.
- Facilities dataset: 3 features with ids `home-north`, `home-south`,
  `workplace-a`.

However, the documented viewer command does not serve those run artifacts from
`/run-artifacts`. A request to
`/run-artifacts/visualization_manifest.json` returns the Vite HTML app shell
with `Content-Type: text/html`. The frontend manifest loader then falls back to
the bundled sample manifest. The bundled sample network has only one
`LineString`, which explains the observed map with only one line.

## Reproduction

- Reproduction command:
  `MOBILITYLAB_RUN_DIR=examples/basic/minimal_commute/runs/minimal-commute npm --prefix apps/visualization run dev -- --host 127.0.0.1 --port 5176`
- Expected:
  `http://127.0.0.1:5176/run-artifacts/visualization_manifest.json` returns the
  example run manifest as JSON, and the viewer renders the 3 exported network
  links.
- Actual:
  `http://127.0.0.1:5176/run-artifacts/visualization_manifest.json` returns the
  Vite HTML app shell. The viewer falls back to
  `/sample/visualization_manifest.json`, whose sample network has one link.
- Error output:

```text
HTTP/1.1 200 OK
Content-Type: text/html
```

## Notes

Relevant files:

- `apps/visualization/vite.config.ts`
- `apps/visualization/src/data/loaders.ts`
- `examples/basic/minimal_commute/README.md`
- `examples/README.md`

Likely cause: `runArtifactsPlugin()` resolves `MOBILITYLAB_RUN_DIR` with
`path.resolve(configuredRunDir)`. With
`npm --prefix apps/visualization`, the Vite process can resolve that relative
path from `apps/visualization` instead of the repository root where the
documented command is issued. The middleware does not find the run files, calls
`next()`, and Vite serves the app shell.

This is not currently supported by evidence as a core, scenario, environment,
agent, experiment, or example data bug. The exported minimal commute artifacts
contain the expected links and facilities.

## Framework Gap

The visualization dev server needs a stable path-resolution contract for
locally served run artifacts. Either `MOBILITYLAB_RUN_DIR` should resolve
relative to the repository-root command invocation, or the example docs should
use a path that is correct from the visualization app process directory.

## Resolution Log

- 2026-07-03: Fixed `apps/visualization/vite.config.ts` so
  `MOBILITYLAB_RUN_DIR` is resolved relative to the directory where the `npm`
  command is invoked, using `INIT_CWD` when available. This makes the documented
  repository-root relative path work with `npm --prefix apps/visualization`.
- 2026-07-03: Changed `/run-artifacts/*` misses to return text 404 responses
  instead of falling through to the Vite HTML app shell.
- 2026-07-03: Added a run-artifact status response header and updated the
  frontend manifest loader so sample data fallback is used only when
  `MOBILITYLAB_RUN_DIR` is not configured. If a configured run directory is
  missing the requested artifact, the viewer now reports the configured-run
  failure instead of silently showing bundled sample data.

## Verification

- `uv run python -m examples.basic.minimal_commute.run_from_config`
- `npm --prefix apps/visualization run typecheck`
- `MOBILITYLAB_RUN_DIR=examples/basic/minimal_commute/runs/minimal-commute npm --prefix apps/visualization run dev -- --host 127.0.0.1 --port 5176`
- `curl -i http://127.0.0.1:5176/run-artifacts/visualization_manifest.json`
  returned `HTTP/1.1 200 OK` with
  `Content-Type: application/json; charset=utf-8`.
- `curl -s http://127.0.0.1:5176/run-artifacts/datasets/network.geojson`
  returned the expected minimal commute network with 7 features, including all
  3 `LineString` links.
- `curl -i http://127.0.0.1:5176/run-artifacts/not-found.json` returned
  `HTTP/1.1 404 Not Found` with a text response, not the Vite HTML app shell.
- With `MOBILITYLAB_RUN_DIR=examples/basic/minimal_commute/runs/does-not-exist`,
  `/run-artifacts/visualization_manifest.json` returned `HTTP/1.1 404 Not
  Found` with `X-MobilityLab-Run-Artifacts: configured`, allowing the frontend
  loader to report the configured-run error instead of falling back to the
  bundled sample.
- `make check`
- `npm --prefix apps/visualization run build`

## Follow-ups

- Add an automated frontend smoke check that requests
  `/run-artifacts/visualization_manifest.json` and verifies JSON content before
  relying on the map.
- Complete screenshot-level viewer QA on a local machine that can run the
  browser directly, confirming `DeckMapPanel` renders all 3 minimal commute
  links and all 3 facilities.
