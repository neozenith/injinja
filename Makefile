######################################################################
# SETUP
######################################################################
.venv: pyproject.toml
	uv sync

.venv/deps: .venv pyproject.toml
	uv sync
	touch $@

######################################################################
# QUALITY ASSURANCE
######################################################################

format: .venv/deps docs
	uvx ruff format src/ tests/ --respect-gitignore --line-length 120
	uvx isort src/ tests/ --profile 'black'

check: .venv/deps
	uvx ruff check src/ tests/
	uvx isort src/ tests/ --check-only
	uv run mypy src/
test: .venv/deps
	uv run pytest
	uv run .github/scripts/update_coverage.py

######################################################################
# DOCUMENTATION
######################################################################

diagrams/%.png: diagrams/%.mmd
	npx -p @mermaid-js/mermaid-cli mmdc --input $< --output $@ -t default -b transparent -s 4

diag: $(patsubst %.mmd,%.png,$(wildcard diagrams/*.mmd))

docs: diag
	uvx --from md-toc md_toc --in-place github --header-levels 2 *.md
	uvx rumdl check . --fix --respect-gitignore -d MD013

######################################################################
# BUILD AND PUBLISHING
# https://docs.astral.sh/uv/guides/package/
######################################################################

build: .venv/deps check docs
	rm -rf dist
	uv build --wheel

publish-test: build docs
	# export UV_PUBLISH_TOKEN=YOUR_TEST_PYPI_API_TOKEN_HERE
	uv publish --repository testpypi

install-from-test:
	uv run -m pip install --index-url https://test.pypi.org/simple/ --no-deps injinja-neozenith


publish: build docs
	uv publish

clean:
	rm -rf dist
	rm -rf .venv
	rm -rf diagrams/*.png

.PHONY: format check docs build diag clean publish publish-test
