# Multi-Version Testing

Injinja supports multiple versions of Python and Jinja2. This document describes how to test against all supported combinations.

## Supported Versions

- **Python**: 3.12, 3.13
- **Jinja2**: 3.0.0, 3.1.0, 3.1.6

This creates a testing matrix of **6 combinations** (2 Python × 3 Jinja2 versions).

## Local Testing

### Quick Test (Current Environment)

```bash
make test
```

### Full Matrix Testing

```bash
# Test all combinations
make test-matrix

# Clean up previous test environments and run fresh
make test-matrix-clean
```

### Custom Matrix Testing

```bash
# Test specific Python versions
uv run scripts/test_matrix.py --python-versions 3.12 3.13

# Test specific Jinja2 versions  
uv run scripts/test_matrix.py --jinja2-versions 3.1.6

# Dry run to see what would be tested
uv run scripts/test_matrix.py --dry-run
```

## GitHub Actions

The project includes local testing scripts that can be integrated into CI/CD workflows. The current `cicd.yml` workflow provides basic checks with the default Python/Jinja2 versions.

For comprehensive matrix testing in GitHub Actions, you can add a workflow like this:

```yaml
name: Matrix Tests
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  matrix-tests:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
        jinja2-version: ["3.0.0", "3.1.0", "3.1.6"]

    steps:
      - uses: actions/checkout@v4
      - name: Init submodules
        run: git submodule update --init --recursive --remote
      - uses: astral-sh/setup-uv@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Create test environment
        run: uv venv test-env --python ${{ matrix.python-version }}
          
      - name: Install specific Jinja2 version and dependencies
        run: uv pip install --venv test-env jinja2==${{ matrix.jinja2-version }} PyYAML deepmerge jsonschema pydantic
          
      - name: Install project and test dependencies
        run: |
          uv pip install --venv test-env -e .
          uv pip install --venv test-env pytest pytest-cov

      - name: Run tests
        run: |
          source test-env/bin/activate
          python -m pytest tests/ -v --tb=short
```

## How It Works

### Local Testing Script

The `scripts/test_matrix.py` script:

1. Creates isolated virtual environments for each Python/Jinja2 combination using `uv venv`
2. Installs the specific Jinja2 version and project dependencies
3. Installs the current project in development mode
4. Runs the full test suite
5. Reports results for each combination

### GitHub Actions Integration

To add matrix testing to GitHub Actions:

1. Create a new workflow file (e.g., `.github/workflows/matrix-tests.yml`)
2. Use the example workflow above as a starting point
3. Customize the matrix versions as needed
4. The workflow uses `uv` for fast dependency resolution and environment management

## Adding New Versions

### Python Versions

1. Update `PYTHON_VERSIONS` in `scripts/test_matrix.py`
2. Update the matrix in any GitHub Actions matrix workflow files
3. Add the Python version classifier to `pyproject.toml`
4. Run `uv run scripts/update_python_versions.py` (if using the helper script)

### Jinja2 Versions

1. Update `JINJA2_VERSIONS` in `scripts/test_matrix.py`
2. Update the matrix in any GitHub Actions matrix workflow files
3. Test the new version locally before committing

## Troubleshooting

### Test Environment Issues

If you encounter issues with test environments:

```bash
# Clean up all test environments
make test-matrix-clean

# Or manually remove the test directory
rm -rf tmp/test_matrix/
```

### Python Version Availability

Ensure the Python versions are available to `uv`:

```bash
# List available Python versions
uv python list

# Install a specific Python version
uv python install 3.13
```

### Dependency Conflicts

If there are dependency conflicts between Python/Jinja2 versions:

1. Check the specific error in the matrix test output
2. Consider adding version constraints to handle compatibility issues
3. Update the minimum supported versions if necessary

## Performance

- **Local Testing**: Matrix testing takes longer than single-version tests but provides comprehensive coverage
- **CI/CD**: Matrix jobs run in parallel, so total time is roughly the same as the slowest combination
- **Caching**: Each test environment is created fresh to ensure isolation and accurate results
