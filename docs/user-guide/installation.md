# Installation

Injinja can be installed in several ways depending on your use case.

## Quick Start with uvx (Recommended)

The fastest way to use Injinja is with `uvx`, which runs it instantly without installation:

```bash
# Instant standalone tool use
uvx injinja --help
```

This approach downloads and runs Injinja in an isolated environment without affecting your system Python.

## Install with uv

If you're using `uv` for Python project management:

```bash
# Add to your project
uv add injinja

# Or install globally
uv install injinja
```

## Install with pip

Traditional installation using pip:

```bash
pip install injinja
```

## Standalone Script

For maximum portability, you can use the standalone script directly:

```bash
# Download the standalone script
curl -O https://raw.githubusercontent.com/neozenith/injinja/main/src/injinja/injinja.py

# Run directly (requires dependencies)
python injinja.py --help
```

The core `injinja.py` file is approximately 500 lines of code and can be embedded directly into your systems.

## Verify Installation

Confirm Injinja is working correctly:

```bash
injinja --help
```

You should see the help message with all available options.

## Requirements

- Python 3.12 or higher
- Dependencies (automatically installed):
  - `jinja2` - Template engine
  - `PyYAML` - YAML parsing
  - `deepmerge` - Configuration merging
  - `jsonschema` and `pydantic` - merged config schema validation checks.

## Next Steps

Once installed, head over to the [Quick Start Guide](quick-start.md) to learn how to use Injinja.
