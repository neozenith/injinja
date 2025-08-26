# Injinja 🥷

**Injinja**: Injectable Jinja Configuration tool. *Insanely configurable... config system.*

## Overview

Injinja is a powerful configuration templating tool that enables two-step templating for complex configuration scenarios. It combines:

- **Runtime DYNAMIC** configuration (environment variables, CLI flags)
- **STATIC** configuration (files that can be templated)
- **Template output** (your final rendered files)

This approach allows you to maintain configuration-driven systems similar to Kubernetes, dbt, and other modern platform tools, but with the flexibility to template configurations themselves before applying them to your final output.

## Key Features

- 🔧 **Two-step templating**: Template your configs, then template your output
- 📁 **Recursive folder configs**: Break up "One Big Fat YAML" into hierarchical folders
- 🔄 **Deep merging**: All configs are recursively merged at runtime
- 📝 **Multi-format support**: Works with YAML, JSON, and TOML files
- 🎯 **Flexible output**: Generate any text-based format (SQL, Terraform, etc.)
- ⚡ **Standalone**: Core functionality in ~500 lines of code

## Quick Example

```bash
# Template SQL DDL with dynamic environment and static config
uvx injinja -e home_dir="$HOME" -c 'config/*' -t sql/warehouse.sql.j2
```

## Architecture

![Overview Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/overview.png?raw=true)

1. **Dynamic Configuration**: Environment variables and CLI flags provide runtime values
2. **Static Configuration**: YAML/JSON/TOML files that can themselves be Jinja templates
3. **Template Rendering**: Apply the merged configuration to your target template

## Getting Started

Ready to dive in? Check out our [Installation Guide](user-guide/installation.md) and [Quick Start](user-guide/quick-start.md) to get up and running in minutes.

For a deeper understanding of the architecture and advanced usage patterns, explore our [User Guide](user-guide/configuration.md) and [Architecture documentation](architecture/overview.md).