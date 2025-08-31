# injinja 🥷

<p align="center">
    <!-- TODO: Catchy Logo, 450px wide -->
    <a href="https://github.com/neozenith/injinja/releases"><img src="https://img.shields.io/github/release/neozenith/injinja" alt="Latest Release"></a>
    <a href="https://github.com/neozenith/injinja/actions/workflows/publish.yml"><img src="https://github.com/neozenith/injinja/actions/workflows/publish.yml/badge.svg" alt="Build Status"></a>
    <!-- coverage-badge -->
    <img src="https://img.shields.io/badge/coverage-90%25-brightgreen.svg" alt="Coverage">
    <!-- coverage-badge -->
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

----

<!--TOC-->

- [injinja 🥷](#injinja-)
  - [Features](#features)
  - [Quickstart](#quickstart)
  - [Overview](#overview)
  - [User Guide](#user-guide)
  - [Intermediate Guide](#intermediate-guide)
  - [Roadmap and TODO list](#roadmap-and-todo-list)

<!--TOC-->

## Quickstart

`injinja.py` is ~500 LOC and runs stand-alone. You can literally take that one file and embed it into your system right now.  

This project aims to add some SLDC rigour, testing and publication around this one core file.

**USAGE:**

```sh
uvx injinja -e home_dir="$HOME" -c 'samples/config/*' -t sql/ddl/warehouse__roles.sql.j2
# OR
uv run injinja.py -e home_dir="$HOME" -c 'samples/config/*' -t sql/ddl/warehouse__roles.sql.j2
```

Two step templating configuration system:

- Runtime `DYNAMIC` configuration (`-e` or `--env`)
- Can template the `STATIC` configuration (`-c` or `--config`)
- To allow deep and rich config to populate your `TEMPLATE` file (`-t` or `--template`).

**WHY?**

Imagine a folder full of database DDL SQL files that you want to template based on complex configurations your base templates use `Jinja2` syntax to iterate over all the possible variations.

Now imagine maintaining entire copies of those config for `dev`, `test`, `prod`? No thank you.

----

## Overview

Inspired by some prior work I have been icubating since 2021 and also a style of platform engineering I am seeing which is _configuration driven platform components_.

This setup allows for configuration driven code based akin to Kubernetes, dbt etc with what I like to called `Recursive Folders of Config`.

- Split up `One Big Fat YAML` into many smaller sensible `.yml` files
- Organise your `yml` config into hierarchical folders.
- Just like `dbt` assume every config file is `jinja` templated first
- Magically they are all `RecursivelyDeepMerge`d at runtime so it is like they were always `One Big Fat YAML`.

*_All of the above also works with `json` and `toml` and mixing them_. You're welcome! 🦾

Oh yeah, and then apply this ultra flexible config to your target jinja template output file.

![Overview Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/overview.png?raw=true)

1. Literally **ANY** config schema in a file format YML, JSON or TOML can be treated as a _Jinja2 Template itself_.
   - This makes for **VERY** dynamic config.
2. Then that config **IS** the config provided for a target Jinja template.
3. This final template could be terraform, SQL, js, python or even more JSON or YAML.

Output defaults to `stdout` or an output file can be specified.

This allows some "ahead-of-time config" (`STATIC`) and some "just-in-time config" (`DYNAMIC`) to all be injected into a final output.

Absence of the "just-in-time" config results in merely merging the config file into the template.

Templating variables and not providing a value will throw an error to ensure templating is correct at runtime.

## User Guide

### Installation

```sh
# Instant standalone tool use
uvx injinja --help

# OR install
uv add injinja
# OR
pip install injinja
```

```sh
injinja --help

USAGE: Injinja [-h] [-d] [-e ENV] [-p PREFIX] [-c CONFIG] [-t TEMPLATE] [-f FUNCTIONS] [-o OUTPUT] [-v VALIDATE] [-s {json,yml,yaml,toml}]

Injinja: Injectable Jinja Configuration tool. Insanely configurable... config system.

        - Collate DYNAMIC configuration from environment variables using --env, --prefix flags
        - Collate the STATIC configuration (files) using the --config flags.
        - DYNAMIC config templates the STATIC config.
        - The _Templated STATIC Config_ is then applied to your target Jinja2 template file using the --template flag.
        - The output is then rendered to either stdout or a target file.

        OPTIONALLY:
        - Can take custom Jinja2 Functions to inject into the Jinja2 Templating Engine Environment
        - Can take a validation file to assist with checking expected templated output against a known file.

options:
  -h, --help            show this help message and exit
  -d, --debug
  -e ENV, --env ENV     Environment variables to pass to the template. Can be KEY=VALUE or path to an .env file.
  -p PREFIX, --prefix PREFIX
                        Import all environment variables with given prefix. eg 'MYAPP_' could find MYAPP_NAME and will import as `myapp.name`. This argument can be repeated.
  -c CONFIG, --config CONFIG
                        The configuration file(s) to use. Either specify a single file, repeated config flags for multiple files or a glob pattern.
  -t TEMPLATE, --template TEMPLATE
                        The Jinja2 template file to use.
  -f FUNCTIONS, --functions FUNCTIONS
                        Path or glob pattern to a python file containing custom functions to use in the template.
  -o OUTPUT, --output OUTPUT
  -v VALIDATE, --validate VALIDATE
                        Filename of an outputfile to validate the output against.
  -s {json,yml,yaml,toml}, --stdin-format {json,yml,yaml,toml}
                        Format of the configuration data piped via stdin (json, yaml, toml). If set, injinja will attempt to read from stdin. eg cat config.json | python3 injinja.py --stdin-format json
```

## Intermediate Guide

### Architecture

![Architecture Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/architecture.png?raw=true)

#### Advanced - Collections of config files

![Collections of Configs](https://github.com/neozenith/injinja/blob/main/diagrams/collections_of_configs.png?raw=true)

- Firstly the `--env` flags are collected and turned into a `dict`
- Next the `--config/-c` flags are collected
  - If the value passes the `pathlib.Path(c).is_file()` check then it is used as-is.
  - If it fails the above check then it is attempted to be expanded using `glob.glob(c)`
  - The order of the `-c` flags allow re-specifying the same file again as the last file to ensure it is an override file.
- This list of configs are each independently templated with the `dict` from `--env`
- They then use `deepmerge.always_merger` to iteratively layer the config to make a final config. (Hence the importance of the ordering of flags.)

#### Testing

![Testing Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/testing.png?raw=true)

For the sake of some testing, adding the flag for a fixed text output allows the use of `difflib` to generate a text diff for sanity checking output from an expectation.

### Debugging

#### Export Merged Config

Addded the `--output` options of either `config-json` or `config-yaml` / `config-yml`, which will actually output the merged config to `stdout`. This can then be filtered and triaged using tools like `jq` or `yq`.

#### Stream Config from `stdin`

Added the `--stdin-format json` and `--stdin-format yml` so that we can stream input that is potentially the output of `jq` and continue templating.

This was the easiest way to add `jq` functionality without vendoring the tool into `injinja`.

Here is a broken out example:

```sh
# The '-o config-json' skips the templating file and outputs the merged config  
python3 injinja.py -c config/**/*.yml -o config-json | \  

# Leverage tools like jq to filter subsets of the config eg a single COPY INTO statement for testing and debugging  
jq '.tables[] | keys' | \  

# Take the output of jq as input back into injinja.py to finish templating.  
python3 injinja.py --stdin-format json -t template.sql -o finalfile.sql
```

## Roadmap and TODO list

[Open Issues that are raised by `neozenith`](https://github.com/neozenith/injinja/issues?q=is%3Aissue%20state%3Aopen%20author%3Aneozenith)
