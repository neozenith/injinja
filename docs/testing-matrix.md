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

The CI/CD workflows automatically test the full matrix on every push and pull request:

1. **Basic Checks** (`cicd.yml`) - Fast feedback with linting, type checking, and tests on the default Python/Jinja2 versions
2. **Matrix Tests** (`matrix-tests.yml`) - Comprehensive testing across all supported Python/Jinja2 combinations

The matrix tests run in parallel and are configured to not fail fast, so you can see results for all combinations even if some fail.

## How It Works

### Local Testing Script

The `scripts/test_matrix.py` script:

1. Creates isolated virtual environments for each Python/Jinja2 combination using `uv venv`
2. Installs the specific Jinja2 version and project dependencies
3. Installs the current project in development mode
4. Runs the full test suite
5. Reports results for each combination

### GitHub Actions Workflows

The `.github/workflows/matrix-tests.yml` workflow:

1. Uses GitHub's matrix strategy to run jobs in parallel
2. Each job tests one Python/Jinja2 combination
3. Uses `uv` for fast dependency resolution and environment management
4. Provides detailed test output for debugging

## Adding New Versions

### Python Versions

1. Update `PYTHON_VERSIONS` in `scripts/test_matrix.py`
2. Update the matrix in `.github/workflows/matrix-tests.yml`
3. Add the Python version classifier to `pyproject.toml`
4. Run `uv run scripts/update_python_versions.py` (if using the helper script)

### Jinja2 Versions

1. Update `JINJA2_VERSIONS` in `scripts/test_matrix.py`
2. Update the matrix in `.github/workflows/matrix-tests.yml`
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
