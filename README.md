# MobilityLab

MobilityLab is an experimental platform for traditional, agent-based,
LLM-enabled, and hybrid mobility and transportation simulation.

The initial implementation target is a mobility-first simulation foundation,
with public U.S. datasets planned as later scenario inputs. The package
structure keeps the core simulation architecture compatible with regional and
city-scale scenarios.

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

## Examples

Runnable reference examples live in `examples/`.

```bash
uv run python -m examples.basic.minimal_commute.run_from_config
uv run python -m examples.basic.minimal_commute.run
```

## Architecture

The architecture guide lives in `AGENTS.md`. Long-lived architecture decisions
are recorded in `docs/decisions/`.
