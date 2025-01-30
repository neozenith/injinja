.venv: pyproject.toml
	uv sync

.venv/deps: .venv pyproject.toml
	uv sync
	touch .venv/deps

build: .venv/deps
	rm -rf ./dist/
	.venv/bin/python -m build

format: .venv/deps
	uv run ruff format
	uv run isort .

check:
	uv run ruff check .
	uv run isort . --check-only
	uv run mypy .
	uv run pytest

docs:
	uv run md_toc --in-place github --header-levels 2 *.md

build:
	rm -rf dist
	uv run -m build --wheel

publish:
	uv run -m twine upload dist/*

clean:
	rm -rf dist
	rm -rf .venv

.PHONY: format check docs