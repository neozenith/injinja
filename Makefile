.venv: pyproject.toml
	uv sync

.venv/deps: .venv pyproject.toml
	uv sync
	touch $@

build: .venv/deps check
	rm -rf dist
	uv run -m build --wheel

format: .venv/deps docs
	uv run ruff format
	uv run isort .

check: .venv/deps
	uv run ruff check .
	uv run isort . --check-only
	uv run mypy src/
	uv run pytest

docs:
	uv run md_toc --in-place github --header-levels 2 *.md

publish: build docs
	uv run -m twine upload dist/*

clean:
	rm -rf dist
	rm -rf .venv

.PHONY: format check docs build