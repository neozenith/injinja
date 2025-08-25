.venv: pyproject.toml
	uv sync

.venv/deps: .venv pyproject.toml
	uv sync
	touch $@

build: .venv/deps check
	rm -rf dist
	uv run -m build --wheel

format: .venv/deps docs
	uvx ruff format src/ tests/ --respect-gitignore --line-length 120
	uvx isort src/ tests/ --profile 'black'

check: .venv/deps
	uvx ruff check src/ tests/
	uvx isort src/ tests/ --check-only
	uv run mypy src/
	uv run pytest

docs:
# 	uv run md_toc --in-place github --header-levels 2 *.md
	uvx --from md-toc md_toc --in-place github --header-levels 2 *.md
	uvx rumdl check . --fix --respect-gitignore -d MD013

publish: build docs
	uv run -m twine upload dist/*

clean:
	rm -rf dist
	rm -rf .venv

.PHONY: format check docs build
