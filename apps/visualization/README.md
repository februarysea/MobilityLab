# CampusSociety Visualization Viewer

Thin React/Vite/deck.gl viewer for CampusSociety visualization artifacts.

## Development

Install dependencies:

```bash
npm --prefix apps/visualization install
```

Start with the bundled sample dataset:

```bash
npm --prefix apps/visualization run dev
```

Start against a completed run directory that already contains
`visualization_manifest.json`:

```bash
CAMPUSSOCIETY_RUN_DIR=/path/to/run npm --prefix apps/visualization run dev
```

The viewer reads `/run-artifacts/visualization_manifest.json` when
`CAMPUSSOCIETY_RUN_DIR` is set. Otherwise it falls back to the bundled sample.

## Build

```bash
npm --prefix apps/visualization run build
```
