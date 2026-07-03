.PHONY: install format lint typecheck test check viz-install viz-dev viz-build viz-typecheck

install:
	uv sync --extra dev

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src tests examples

test:
	uv run pytest

check: lint typecheck test

viz-install:
	npm --prefix apps/visualization install

viz-dev:
	npm --prefix apps/visualization run dev

viz-build:
	npm --prefix apps/visualization run build

viz-typecheck:
	npm --prefix apps/visualization run typecheck
