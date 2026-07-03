# Example Issue Report: EX-BASIC-MINCOMM-002

## Report Metadata

- Report path:
  `docs/example-reports/basic-minimal-commute/EX-BASIC-MINCOMM-002.md`
- Example path: `examples/basic/minimal_commute`
- Issue id: `EX-BASIC-MINCOMM-002`
- Last updated: 2026-07-03

## Issue Summary

- Status: resolved
- Severity: major
- Suspected layer: visualization
- Issue type: framework bug

## Run Context

- Commit under test: `a0cceb3`
- Branch: `main`
- Date: 2026-07-03T14:51:04+08:00
- Command: `uv run python -m examples.basic.minimal_commute.run_from_config`
- Working directory: `/nvme01/home/jichunhou/CampusSociety`
- Python version: Python 3.12.3 through `uv run python`
- Package install mode: local workspace through `uv`
- Operating system: Linux `umep` 6.8.0-53-generic x86_64

## Example Contract

### Expected Behavior

The `basic/minimal_commute` example should open in the React/Vite replay
viewer and display the exported network and facilities in a usable first-screen
layout.

### Expected Outputs

- Header shows the loaded run:
  `minimal_commute · baseline · run minimal-commute`.
- Summary chips show `7 map features`, `7 frames`, and `31 metrics`.
- The `Network Replay` map renders all 3 network links and all 3 facilities in
  the visible map viewport.
- Metrics, event panels, and timeline controls are visible or reachable without
  an oversized page layout.

## Actual Behavior

The viewer loads the correct run artifacts and displays the expected run
metadata and counts. The HTTP artifact endpoints return JSON and GeoJSON from
the `minimal-commute` run, not the bundled sample.

However, the initial 1280x720 viewport shows a mostly blank `Network Replay`
map area except for the background grid and legend. A full-page screenshot shows
that the network links and facility markers are rendered much farther down the
page, and the events panel and timeline are pushed below the first viewport.

This means the current failure is not simply "deck.gl did not draw anything";
it is a visualization layout and map framing problem. The loaded geometry is
not positioned inside the useful first-screen map area, and the overall
dashboard is too tall for the default desktop viewport.

## Reproduction

- Reproduction command:
  `MOBILITYLAB_RUN_DIR=examples/basic/minimal_commute/runs/minimal-commute npm --prefix apps/visualization run dev -- --host 0.0.0.0 --port 5174`
- Browser URL: `http://127.0.0.1:5174/`
- Expected:
  The map panel renders the exported minimal commute network links and
  facilities in the visible map viewport, with metrics, events, and timeline
  arranged in a usable dashboard layout.
- Actual:
  The page header and metrics confirm the run is loaded. In a normal viewport,
  the map appears blank because the rendered geometry is far below the visible
  part of the map panel. The right-side event panel and bottom timeline are also
  pushed below the first viewport.
- Error output:
  No HTTP artifact-serving error was observed. The layout/framing issue appears
  after successful data loading.

## Notes

Artifact serving checks passed:

```text
/run-artifacts/visualization_manifest.json
Content-Type: application/json; charset=utf-8
X-MobilityLab-Run-Artifacts: configured
run_id: minimal-commute
scenario_id: minimal_commute
dataset_count: 5
```

Network dataset check:

```text
feature_count: 7
line_count: 3
point_count: 4
link_ids:
- main-to-work
- north-home-to-main
- south-home-to-main
```

Facilities dataset check:

```text
feature_count: 3
facility_ids:
- home-north
- home-south
- workplace-a
```

Viewport screenshot reproduction:

```text
npx playwright screenshot --browser=chromium --wait-for-timeout=2000 \
  http://127.0.0.1:5174/ \
  /tmp/mobilitylab-minimal-commute-rendering-bug.png
```

The viewport screenshot shows the correct header counts, metrics panel, map
toolbar, and legend, but no visible links or facility markers in the first
screen.

Full-page screenshot reproduction:

```text
npx playwright screenshot --browser=chromium --wait-for-timeout=1000 \
  --full-page \
  http://127.0.0.1:5174/ \
  /tmp/mobilitylab-minimal-commute-layout-fullpage.png
```

The full-page screenshot shows that links and facility markers are rendered far
below the top of the map panel. It also shows the events panel and timeline far
below the first viewport, indicating a dashboard layout and viewport sizing
problem.

Relevant files:

- `apps/visualization/src/components/DeckMapPanel.tsx`
- `apps/visualization/src/styles.css`
- `apps/visualization/src/views/ReplayDashboard.tsx`
- `apps/visualization/src/data/loaders.ts`

Likely investigation areas:

- `.app-shell`, `.workspace`, `.map-panel`, `.deck-frame`, `.side-region`, and
  `.timeline` height constraints.
- Whether the dashboard should be one viewport tall with internal scrolling
  panels instead of a very tall document.
- `DeckMapPanel` view state for local Cartesian coordinates and whether it
  frames local coordinates inside the visible panel after layout sizing.
- `OrthographicView` target and zoom calculation.
- deck.gl canvas sizing inside `.deck-frame`.
- Whether the deck.gl canvas is sized from an oversized parent and therefore
  centers geometry outside the initially visible portion.

This issue is separate from `EX-BASIC-MINCOMM-001`. Artifact serving no longer
falls back to the bundled sample; the remaining failure is dashboard layout and
map viewport framing after successful data load.

## Framework Gap

The visualization viewer lacks a dashboard layout contract and automated visual
smoke check that confirm loaded GeoJSON features, events, metrics, and timeline
controls are visible in a normal desktop viewport. Current checks can prove data
loading but not usable visual layout.

## Resolution Log

- 2026-07-03: Fixed the replay dashboard CSS so the desktop app shell is
  constrained to one viewport, with the workspace, map panel, metrics panel,
  events panel, and timeline sized inside that viewport instead of allowing
  event content to stretch the whole document.
- 2026-07-03: Kept the mobile layout as a normal vertical document by restoring
  body scrolling and auto-height shell behavior below the mobile breakpoint.
- 2026-07-03: Reduced the default Cartesian map fit from 520 pixels to 320
  pixels so the minimal commute network and all facility markers are visible
  with padding in both desktop and mobile viewports.

## Verification

- Reproduced before fix with:
  `npx playwright screenshot --browser=chromium --viewport-size=1280,720 --wait-for-timeout=2000 http://127.0.0.1:5175/ /tmp/mobilitylab-002-before.png`.
  The first viewport showed the loaded run header and metrics but no visible
  network or facility geometry.
- Verified after fix with:
  `npx playwright screenshot --browser=chromium --viewport-size=1280,720 --wait-for-timeout=1200 http://127.0.0.1:5175/ /tmp/mobilitylab-002-after-fit.png`.
  The first desktop viewport showed all 3 network links, all 3 facility
  markers, metrics, events, and the timeline.
- Verified mobile with:
  `npx playwright screenshot --browser=chromium --viewport-size=390,844 --wait-for-timeout=1200 http://127.0.0.1:5175/ /tmp/mobilitylab-002-after-fit-mobile.png`.
  The mobile viewport showed the map with all 3 links and all 3 facility
  markers before the metrics section.
- Verified interaction with Playwright: page title was `MobilityLab Replay`,
  body scroll height matched the 720px viewport on desktop, one deck.gl canvas
  was present, timeline was inside the viewport, and clicking `Play` advanced
  the timeline from frame 1 to frame 2.
- `npm --prefix apps/visualization run typecheck`
- `npm --prefix apps/visualization run build`
- `make check`

## Follow-ups

- Add a frontend rendering smoke test for `DeckMapPanel` using the minimal
  commute network.
- Add a screenshot-level layout check for the full replay dashboard at a
  default desktop viewport, including map, metrics, events, and timeline.
- Keep artifact-serving verification separate from map-rendering verification
  so future regressions can be diagnosed quickly.
