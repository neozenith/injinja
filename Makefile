

format:
	uv run ruff format
	uv run isort .

check:
	uv run ruff check .
	uv run isort . --check-only
	uv run mypy .
	uv run pytest