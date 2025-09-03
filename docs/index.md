# injinja 🥷

<p align="center">
    <!-- TODO: Catchy Logo, 450px wide -->
    <a href="https://github.com/neozenith/injinja/releases"><img src="https://img.shields.io/github/release/neozenith/injinja" alt="Latest Release"></a>
    <a href="https://github.com/neozenith/injinja/actions/workflows/publish.yml"><img src="https://github.com/neozenith/injinja/actions/workflows/publish.yml/badge.svg" alt="Build Status"></a>
</p>

<p align="center">Injinja: <b>Inj</b>ectable <b>Jinja</b> Configuration tool.</p>
<p align="center"><i>Insanely configurable... config system.</i></p>
  

<!-- TODO: Animated GIF demoing features. 800px wide -->

## Features

- **Ultra-simple:** The implementation is a single stand-alone python file. Take a copy of the file or `pip install`. Choice is yours.
- **Flexible:** You design your configuration schema yourself in any of JSON, YAML or TOML.
- **Deep Merge:** Finally split those big mega config files into smaller more manageable ones in a folder hierarchy. We recursively merge them like they are the one mega file.
- **Powerful:** Any of your config files are now empowered with the full programming capabilities of [`Jinja`](https://jinja.palletsprojects.com/en/stable/) templating engine.
- **Platform Engineering:** Separate your projects into _Extensible Code_ driven by _Flexible Config_ to allow _"Drive By Contributors"_. Edit one YAML in Github Browser to start a PR to spin up new Snowflake Databases or Terraform modules.


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