# Architecture Diagrams

This page contains all the architectural diagrams that illustrate Injinja's design and data flow.

## Overview Diagram

The high-level flow showing the two-step templating process:

![Overview Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/overview.png?raw=true)

This diagram shows:
1. **Environment Variables** (DYNAMIC) provide runtime configuration
2. **Configuration Files** (STATIC) are templated with environment variables
3. **Final Template** is rendered with the merged configuration
4. **Output** is generated (SQL, YAML, JSON, etc.)

## Detailed Architecture

The complete system architecture showing all components and their interactions:

![Architecture Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/architecture.png?raw=true)

Key components illustrated:
- Environment variable collection from multiple sources
- Configuration file discovery and templating
- Deep merge process
- Template rendering with custom functions
- Output generation

## Collections of Configs Pattern

The hierarchical configuration management pattern:

![Collections of Configs](https://github.com/neozenith/injinja/blob/main/diagrams/collections_of_configs.png?raw=true)

This shows:
- How multiple configuration files are collected via `-c` flags
- File vs. glob pattern resolution
- Independent templating of each config with environment variables
- Deep merge process to create final unified configuration

## Testing Architecture

The validation and testing workflow:

![Testing Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/testing.png?raw=true)

Illustrates:
- Configuration validation against expected outputs
- Debug output for troubleshooting
- Integration with external tools like `jq` and `yq`
- Diff generation for output validation

## Diagram Source

All diagrams are created using [Mermaid](https://mermaid.js.org/) and stored as `.mmd` files in the `diagrams/` folder of the repository. They are automatically converted to PNG format using the project's Makefile.

To update diagrams:

1. Edit the `.mmd` files in the `diagrams/` folder
2. Run `make diag` to regenerate PNG files
3. The documentation automatically references the updated images

For local editing, we recommend using the [VSCode Mermaid Preview Extension](https://marketplace.visualstudio.com/items?itemName=vstirbu.vscode-mermaid-preview).

## Diagram Files

The source Mermaid files are:

- `diagrams/overview.mmd` - High-level overview
- `diagrams/architecture.mmd` - Detailed architecture
- `diagrams/collections_of_configs.mmd` - Configuration collection pattern
- `diagrams/testing.mmd` - Testing and validation workflow