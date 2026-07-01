# CampusSociety

CampusSociety is a simulation framework for LLM-driven, traditional, and hybrid
agent-based mobility simulation.

The initial testbeds use openly available U.S. public datasets for classic ABM
and mobility experiments, while the package structure keeps the core simulation
architecture compatible with regional and city-scale scenarios.

## Development

This project uses a `src/` Python package layout and `uv` for local development.

```bash
uv sync --extra dev
make check
```

Useful commands:

```bash
make format
make lint
make typecheck
make test
```

Install pre-commit hooks after installing dependencies:

```bash
uv run pre-commit install
```

## Architecture

The architecture guide lives in `AGENTS.md`. Long-lived architecture decisions
are recorded in `docs/decisions/`.
