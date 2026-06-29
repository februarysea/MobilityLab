.PHONY: install format lint typecheck test check

install:
	uv sync --extra dev

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest

check: lint typecheck test

