# Configuration

This guide covers Injinja's configuration system in detail, including advanced patterns and best practices.

## Configuration Sources

Injinja pulls configuration from multiple sources, merged in the following precedence order:

1. **Environment files** (`.env` files via `-e`)
2. **Environment prefixes** (via `--prefix`)
3. **Direct environment variables** (via `-e KEY=VALUE`)

## Configuration Files

### Supported Formats

Injinja supports three configuration file formats:

- **YAML** (`.yml`, `.yaml`)
- **JSON** (`.json`)
- **TOML** (`.toml`)

All formats can be mixed within the same project.

### File Detection

```bash
# Single file
injinja -c config.yml -t template.j2

# Multiple files (explicit)
injinja -c base.yml -c prod.yml -c overrides.yml -t template.j2

# Glob patterns
injinja -c 'config/**/*.yml' -t template.j2
injinja -c 'config/{base,prod}/*.{yml,json}' -t template.j2
```

### Configuration Templating

Configuration files are themselves Jinja2 templates, templated with environment variables:

**Environment:**

```bash
export ENVIRONMENT=production
export DB_PORT=5432
```

**Configuration (`config.yml`):**

```yaml
app:
  name: myapp
  environment: "{{ ENVIRONMENT }}"

database:
  host: "{{ 'prod-db.example.com' if ENVIRONMENT == 'production' else 'localhost' }}"
  port: {{ DB_PORT }}
  ssl: {{ ENVIRONMENT == 'production' }}
```

**Result after templating:**

```yaml
app:
  name: myapp
  environment: production

database:
  host: prod-db.example.com
  port: 5432
  ssl: true
```

## Deep Merging

Configuration files are recursively merged using deep merge semantics:

**base.yml:**

```yaml
app:
  name: myapp
  features:
    auth: true
    logging: true
database:
  port: 5432
```

**production.yml:**

```yaml
app:
  features:
    debug: false  # Added
    logging: false  # Overridden
database:
  host: prod.example.com  # Added
  port: 5433  # Overridden
```

**Merged result:**

```yaml
app:
  name: myapp
  features:
    auth: true
    debug: false
    logging: false  # Overridden from production.yml
database:
  host: prod.example.com
  port: 5433  # Overridden from production.yml
```

## Environment Variables

### Direct Key-Value Pairs

```bash
injinja -e DATABASE_URL=postgres://localhost/myapp -e DEBUG=true
```

### Environment Files

**`.env` file:**

```bash
# Database configuration
DATABASE_URL=postgres://localhost/myapp
DB_POOL_SIZE=10

# Application settings
DEBUG=true
LOG_LEVEL=info

# API keys (quoted values supported)
API_KEY="abc-123-def"
SECRET_KEY='very-secret-key'
```

```bash
injinja -e .env -c config.yml -t template.j2
```

### Prefix Filtering

Import environment variables by prefix:

```bash
# Set environment variables
export MYAPP_DATABASE_URL=postgres://localhost/myapp
export MYAPP_LOG_LEVEL=debug
export MYAPP_FEATURE_X=enabled
export OTHER_VAR=ignored

# Import only MYAPP_ variables
injinja --prefix MYAPP_ -c config.yml -t template.j2
```

The prefix is removed and variables are lowercased:
- `MYAPP_DATABASE_URL` → `myapp_database_url`
- `MYAPP_LOG_LEVEL` → `myapp_log_level`

### Multiple Prefixes

```bash
injinja --prefix MYAPP_ --prefix DB_ -c config.yml -t template.j2
```

## Advanced Configuration Patterns

### Hierarchical Configuration Structure

Organize configs by environment and component:

```text
config/
├── base/
│   ├── app.yml
│   ├── database.yml
│   └── logging.yml
├── environments/
│   ├── development.yml
│   ├── staging.yml
│   └── production.yml
└── overrides/
    └── local.yml
```

Usage:

```bash
injinja \
  -c 'config/base/*.yml' \
  -c 'config/environments/production.yml' \
  -c 'config/overrides/*.yml' \
  -t template.j2
```

### Conditional Configuration

Use Jinja2 logic in configuration files:

```yaml
# config.yml
app:
  name: myapp
  debug: {{ ENVIRONMENT != 'production' }}

database:
  host: |
    {%- if ENVIRONMENT == 'production' -%}
    prod-db.example.com
    {%- elif ENVIRONMENT == 'staging' -%}
    staging-db.example.com
    {%- else -%}
    localhost
    {%- endif %}

  connection_pool:
    min_connections: {{ 5 if ENVIRONMENT == 'production' else 1 }}
    max_connections: {{ 50 if ENVIRONMENT == 'production' else 5 }}

{% if FEATURE_REDIS is defined %}
redis:
  host: {{ REDIS_HOST | default('localhost') }}
  port: {{ REDIS_PORT | default(6379) }}
{% endif %}
```

### Configuration Validation

Use defaults and validation in templates:

```yaml
# config.yml
app:
  name: "{{ APP_NAME | default('unnamed-app') }}"
  port: {{ APP_PORT | default(8080) | int }}

{% if not DATABASE_URL %}
{{ raise_error('DATABASE_URL environment variable is required') }}
{% endif %}

database:
  url: "{{ DATABASE_URL }}"
  pool_size: {{ DB_POOL_SIZE | default(10) | int }}
```

### Dynamic Lists and Iterations

Generate dynamic configuration structures:

```yaml
# config.yml
microservices:
{% for i in range(REPLICA_COUNT | default(3) | int) %}
  - name: "api-{{ i }}"
    port: {{ 8000 + i }}
    host: "api-{{ i }}.example.com"
{% endfor %}

databases:
{% for env in ['development', 'staging', 'production'] %}
  {{ env }}:
    url: "postgres://{{ env }}-db.example.com/myapp"
    readonly: {{ env != 'production' }}
{% endfor %}
```

## Debugging Configuration

### Output Merged Configuration

See the final merged configuration without applying templates:

```bash
# As JSON
injinja -c 'config/*.yml' -o config-json | jq '.'

# As YAML  
injinja -c 'config/*.yml' -o config-yaml
```

### Chain with External Tools

Combine Injinja with `jq` or `yq` for advanced processing:

```bash
# Extract specific sections
injinja -c 'config/*.yml' -o config-json | \
  jq '.database' | \
  injinja --stdin-format json -t db-template.j2

# Filter and transform
injinja -c 'config/*.yml' -o config-json | \
  jq '.microservices[] | select(.environment == "production")' | \
  injinja --stdin-format json -t service-config.j2
```

### Debug Mode

Enable debug output for troubleshooting:

```bash
injinja --debug -c config.yml -t template.j2
```

Debug mode shows:
- Environment variable collection
- Configuration file discovery and parsing  
- Template rendering steps
- Final merged configuration

## Best Practices

### 1. Use Hierarchical Configuration

Organize configs by concern and environment:

```bash
injinja -c 'config/base/*.yml' -c 'config/env/prod.yml' -c 'config/overrides/*.yml'
```

### 2. Validate Required Variables

Use Jinja2 to validate required environment variables:

```yaml
{% if not DATABASE_URL %}
  {% set _ = raise_error('DATABASE_URL is required') %}
{% endif %}
```

### 3. Provide Sensible Defaults

Always provide defaults for optional configuration:

```yaml
app:
  port: {{ APP_PORT | default(8080) | int }}
  workers: {{ WORKERS | default(4) | int }}
```

### 4. Use Environment-Specific Configs

Separate configuration by environment while sharing common base configuration:

```bash
injinja -c base.yml -c environments/production.yml
```

### 5. Document Environment Variables

Create a `.env.example` file documenting all environment variables:

```bash
# .env.example
DATABASE_URL=postgres://localhost/myapp
APP_PORT=8080
LOG_LEVEL=info
```

## Next Steps

- Explore [Advanced Usage](advanced.md) patterns
- Learn about custom functions and filters
- Check the [API Reference](../api/injinja.md) for programmatic usage
