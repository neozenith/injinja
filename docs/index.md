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

### **Step 1**: Config files with the power of `Jinja`

`config/databases.yml`
```yml
databases:
  {{ prefix | default('') | upper }}{{env_name | upper}}_BRONZE:
    description: Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.
      
  {{ prefix | default('') | upper }}{{env_name | upper}}_SILVER:
    description: Primary data modelling area manmaged by dbt.

  {{ prefix | default('') | upper }}{{env_name | upper}}_GOLD:
    description: Curated and well modelled data. Read only access to BI tools.
```

### **Step 2**: Templating foundational files with your convention

`sql/databases.sql.j2`
```sql
-- Create Databases
{% for database_name, database_properties in databases.items() -%}
CREATE OR ALTER DATABASE {{ database_name }}
    {%- if database_properties.description is defined %}
    WITH COMMENT = '{{ database_properties.description }}'
    {%- endif -%}
    ;
{% endfor %}
```

### **Step 3**: One config for every environment (and branch)

**3a** _Generate PROD SQL statements_

```sh
# Template SQL DDL with dynamic environment variables and static config
uvx injinja \
-e env_name=prod \
-c 'config/*' \
-t sql/databases.sql.j2
```

```sql
-- Create Databases
CREATE OR ALTER DATABASE PROD_BRONZE
    WITH COMMENT = 'Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.';
CREATE OR ALTER DATABASE PROD_SILVER
    WITH COMMENT = 'Primary data modelling area manmaged by dbt.';
CREATE OR ALTER DATABASE PROD_GOLD
    WITH COMMENT = 'Curated and well modelled data. Read only access to BI tools.';
```

**3b** _Generate DEV Databases per branch_

```sh
# Inject normalised git branch prefix
uvx injinja \
-e env_name=dev \
-e prefix="_$(git symbolic-ref --short HEAD | sed 's/\//_/g')" \ 
-c 'config/*' \
-t sql/databases.sql.j2
```

```sql
-- Create Databases
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_BRONZE
    WITH COMMENT = 'Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_SILVER
    WITH COMMENT = 'Primary data modelling area manmaged by dbt.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_GOLD
    WITH COMMENT = 'Curated and well modelled data. Read only access to BI tools.';
```

### **(Optional) Step 4**: Run the templated output

This command pipes the output directly from `stdout` to `stdin` of the `snow sql` cli tool.

```sh
uvx injinja ... | snow sql -i
```

### **Summary**

Now you can see how you can have enhanced configuration which stays as the central source of truth for the structure of your environments and then parametrise as need be.


## Simplified Architecture

![Overview Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/overview.png?raw=true)

1. **Dynamic Configuration**: Environment variables and CLI flags provide runtime values
2. **Static Configuration**: YAML/JSON/TOML files that can themselves be Jinja templates
3. **Template Rendering**: Apply the merged configuration to your target template

## Next Steps

Ready to dive in? Check out our [Installation Guide](user-guide/installation.md) and [Quick Start](user-guide/quick-start.md) to get up and running in minutes.

For a deeper understanding of the architecture and advanced usage patterns, explore our [User Guide](user-guide/configuration.md) and [Architecture documentation](architecture/overview.md).
