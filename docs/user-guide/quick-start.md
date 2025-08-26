# Quick Start

This guide will get you up and running with Injinja in minutes.

## Basic Usage

Injinja follows a simple pattern: **Environment → Config → Template → Output**

```bash
injinja -e KEY=VALUE -c config.yml -t template.j2
```

## Your First Template

Let's create a simple example to demonstrate Injinja's capabilities.

### 1. Create a Configuration File

Create `config.yml`:

```yaml
# config.yml
app:
  name: "{{ app_name | default('MyApp') }}"
  version: "{{ app_version | default('1.0.0') }}"
  environment: "{{ env | default('development') }}"

database:
  host: "{{ db_host | default('localhost') }}"
  port: 5432
  name: "{{ app.name | lower }}_{{ app.environment }}"
```

### 2. Create a Template

Create `app.conf.j2`:

```jinja2
# app.conf.j2
[app]
name = {{ app.name }}
version = {{ app.version }}
environment = {{ app.environment }}

[database]
host = {{ database.host }}
port = {{ database.port }}
database = {{ database.name }}

# Generated on {{ ansible_date_time.iso8601 | default('now') }}
```

### 3. Run Injinja

```bash
# Basic usage with environment variables
injinja -e app_name=MyAwesomeApp -e app_version=2.1.0 -e env=production -e db_host=prod.example.com -c config.yml -t app.conf.j2
```

### 4. Output

```ini
[app]
name = MyAwesomeApp
version = 2.1.0
environment = production

[database]
host = prod.example.com
port = 5432
database = myawesomeapp_production
```

## Key Concepts

### Two-Step Templating

1. **Step 1**: Environment variables template the configuration file
2. **Step 2**: The templated configuration is applied to your final template

This allows your configuration files to be dynamic and environment-aware.

### Configuration Merging

Multiple configuration files are deep-merged:

```bash
# Later files override earlier ones
injinja -c base.yml -c environment.yml -c overrides.yml -t template.j2
```

### Glob Patterns

Use glob patterns to include multiple config files:

```bash
injinja -c 'config/**/*.yml' -t template.j2
```

## Environment Variables

### Direct Key-Value Pairs

```bash
injinja -e DATABASE_URL=postgres://... -e DEBUG=true
```

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

## Real-World Example

Here's a practical example for generating database migration scripts:

**Environment:**
```bash
export ENV=production
export DB_HOST=prod-db.example.com
export SCHEMA_VERSION=v2.1
```

**Config (`db-config.yml`):**
```yaml
database:
  host: "{{ ENV == 'production' and DB_HOST or 'localhost' }}"
  schema_version: "{{ SCHEMA_VERSION }}"
  tables:
    users:
      columns:
        - name: id
          type: bigserial
        - name: email
          type: varchar(255)
    products:
      columns:
        - name: id
          type: bigserial
        - name: name
          type: varchar(100)
```

**Template (`migration.sql.j2`):**
```sql
-- Migration for {{ database.schema_version }}
-- Target: {{ database.host }}

{% for table_name, table_config in database.tables.items() %}
CREATE TABLE IF NOT EXISTS {{ table_name }} (
  {% for column in table_config.columns -%}
  {{ column.name }} {{ column.type }}{{ "," if not loop.last }}
  {% endfor %}
);
{% endfor %}
```

**Command:**
```bash
injinja --prefix ENV,DB_HOST,SCHEMA_VERSION -c db-config.yml -t migration.sql.j2 -o migration_v2.1.sql
```

## Next Steps

- Learn about [Configuration](configuration.md) in detail
- Explore [Advanced Usage](advanced.md) patterns
- Check out the [API Reference](../api/injinja.md)