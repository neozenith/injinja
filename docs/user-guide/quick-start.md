# Quick Start

This guide will get you up and running with Injinja in minutes.

## Basic Usage

Injinja follows a simple pattern: **Environment → Config → Template → Output**

```sh
injinja -e KEY=VALUE -c config.yml -t template.j2
```

## **Step 1**: Config files with the power of `Jinja`

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

### **Step 2**: Templating foundational files with your conventions

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

#### **3a** _Generate PROD SQL statements_

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

#### **3b** _Generate DEV Databases per branch_

```sh
# Inject normalised git branch prefix
uvx injinja \
-e env_name=dev \
-e prefix="$(git symbolic-ref --short HEAD | sed 's/\//_/g')__" \ 
-c 'config/*' \
-t sql/databases.sql.j2
```

Assuming our git branch was `JIRA-123/incremental-model`:

```sql
-- Create Databases
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_BRONZE
    WITH COMMENT = 'Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_SILVER
    WITH COMMENT = 'Primary data modelling area manmaged by dbt.';
CREATE OR ALTER DATABASE JIRA-123_INCREMENTAL-MODEL__DEV_GOLD
    WITH COMMENT = 'Curated and well modelled data. Read only access to BI tools.';
```

## Key Concepts

### Two-Step Templating

- **Step 1**: Environment variables template the configuration file
- **Step 2**: The templated configuration is applied to your final template

This allows your configuration files to be dynamic and environment-aware.

### Configuration Merging

Multiple configuration files are deep-merged:

```sh
# Later files override/extend earlier ones
injinja -c databases.yml -c extends.yml -t template.j2
```

For example if `extends.yml` was:

```yaml
databases:
  {{ prefix | default('') | upper }}{{env_name | upper}}_META_ANALYTICS:
    description: Data models for the platform team to analyse the data platform health.
```

Our earlier example would results in a final config like:

```yaml
databases:
  {{ prefix | default('') | upper }}{{env_name | upper}}_BRONZE:
    description: Raw ingestion layer of our medallion architecture. Read only access for dbt. Write only for ingestion tools.

  {{ prefix | default('') | upper }}{{env_name | upper}}_SILVER:
    description: Primary data modelling area manmaged by dbt.

  {{ prefix | default('') | upper }}{{env_name | upper}}_GOLD:
    description: Curated and well modelled data. Read only access to BI tools.

  {{ prefix | default('') | upper }}{{env_name | upper}}_META_ANALYTICS:
    description: Data models for the platform team to analyse the data platform health.
```

The `databases` key already exists in both so we recurse down.
The `_META_ANALYTICS` key does not exist yet so we extend the config.

### Glob Patterns

Use glob patterns to include multiple config files:

```sh
injinja -c 'config/**/*.yml' -t template.j2
```

> **NOTE**: enclose glob patterns in single quotes to prevent early expansion of the glob patterns from your shell.

## Environment Variables

- The `--env` flag will check if the string value is a file first and treat it like a `.env` file.
- If it is not a file, it will then assume the value is in the form `KEY=VALUE`.
- The `--prefix` option allows you to grab ALL environment variables you have namespaced with a prefix.

### Environment File

Create `.env`:

```bash
DATABASE_URL=postgres://localhost/myapp
DEBUG=true
API_KEY=secret123
```

```bash
injinja -e .env -c config.yml -t template.j2
```

### Direct Key-Value Pairs

```bash
injinja -e DATABASE_URL=postgres://... -e DEBUG=true
```

### Prefix Filtering

Import all environment variables with a prefix:

```bash
export MYAPP_DATABASE_URL=postgres://...
export MYAPP_DEBUG=true

injinja --prefix MYAPP_ -c config.yml -t template.j2
```

## Output Options

### Write to File

```bash
injinja -c config.yml -t template.j2 -o output.conf
```

### Debug Configuration

See the merged configuration without templating:

```bash
# Output as JSON
injinja -c config.yml -o config-json

# Output as YAML
injinja -c config.yml -o config-yaml
```

## Next Steps

- Learn about [Configuration](configuration.md) in detail
- Explore [Advanced Usage](advanced.md) patterns
- Check out the [API Reference](../api/injinja.md)
