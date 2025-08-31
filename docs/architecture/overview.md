# Architecture Overview

Injinja implements a two-step templating system that separates dynamic runtime configuration from static configuration files, enabling powerful configuration-driven workflows.

## Core Concepts

### Two-Step Templating Process

1. **Step 1: Configuration Templating**
   - Static configuration files are treated as Jinja2 templates
   - Dynamic environment variables populate template variables in configs
   - Results in rendered configuration data structures

2. **Step 2: Template Application**
   - The merged configuration is applied to target templates
   - Produces final output files (SQL, YAML, JSON, etc.)

This separation allows configuration files themselves to be dynamic and environment-aware while maintaining clear boundaries between configuration and output generation.

### Configuration Flow

```text
Environment Variables → Template Config Files → Merge Configs → Apply to Template → Output
      (DYNAMIC)              (STATIC)           (MERGED)         (FINAL)        (RESULT)
```

## Architecture Diagram

![Architecture Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/architecture.png?raw=true)

## Component Breakdown

### 1. Environment Variable Collection

**Sources (in precedence order):**

1. **Environment Files** (`.env` files via `-e file.env`)
2. **Prefix Filtering** (via `--prefix MYAPP_`)
3. **Direct Variables** (via `-e KEY=VALUE`)

**Functions:**

- `get_environment_variables()` - Orchestrates collection from all sources
- `read_env_file()` - Parses `.env` files with quoted value support
- `dict_from_prefixes()` - Filters `os.environ` by prefixes
- `dict_from_keyvalue_list()` - Parses `KEY=VALUE` strings

### 2. Configuration File Processing

**File Discovery:**

- `expand_files_list()` - Resolves file paths and glob patterns
- Supports YAML (`.yml`, `.yaml`), JSON (`.json`), and TOML (`.toml`)

**Configuration Loading:**

- `load_config()` - Detects format and parses files
- Each config file is templated with environment variables
- `map_env_to_confs()` - Applies environment variables to each config file independently

### 3. Configuration Merging

**Deep Merge Process:**

- `reduce_confs()` - Uses `deepmerge.always_merger` for recursive merging
- Later configurations override earlier ones
- Maintains nested structure while allowing targeted overrides

### 4. Template Processing

**Template Application:**

- `merge_template()` - Applies final merged config to target templates
- Uses Jinja2's `StrictUndefined` for error detection (Jinja2 3.x+)
- Supports custom filters and tests via function loading

### 5. Custom Function System

**Function Loading:**

- `get_functions()` - Dynamically imports Python modules
- Discovers functions with `filter_` and `test_` prefixes
- Registers with global Jinja2 environment

## Data Flow Details

### Configuration Collection

```python
# Simplified flow
env_vars = get_environment_variables(env_flags, prefixes)
configs = map_env_to_confs(config_files, env_vars)  # Each config templated independently
merged_config = reduce_confs(configs)  # Deep merge all configs
```

### Template Rendering

```python
# Template application
final_output = merge_template(template_file, merged_config)
```

### Collections of Configs Pattern

![Collections of Configs](https://github.com/neozenith/injinja/blob/main/diagrams/collections_of_configs.png?raw=true)

The "Collections of Configs" pattern enables:

1. **Hierarchical Organization** - Split monolithic configs into focused files
2. **Environment Overrides** - Layer environment-specific configs over base configs  
3. **Component Separation** - Organize configs by functional domain
4. **Override Flexibility** - Precise control over configuration precedence

Example structure:

```text
config/
├── base/
│   ├── database.yml      # Base database config
│   ├── logging.yml       # Base logging config
│   └── features.yml      # Base feature flags
├── environments/
│   ├── development.yml   # Dev-specific overrides
│   ├── staging.yml       # Staging-specific overrides
│   └── production.yml    # Prod-specific overrides
└── overrides/
    └── local.yml         # Local development overrides
```

## Key Design Decisions

### 1. Separate Configuration and Template Steps

**Why:** Enables configuration files to be dynamic while keeping clear separation of concerns.

**Benefits:**

- Configuration logic doesn't mix with output formatting
- Environment-specific configs can be validated independently
- Debugging is easier with clear intermediate states

### 2. Deep Merge Strategy

**Why:** Allows partial overrides without losing entire configuration sections.

**Example:**

```yaml
# base.yml
database:
  host: localhost
  port: 5432
  options:
    ssl: false
    timeout: 30

# production.yml  
database:
  host: prod.example.com
  options:
    ssl: true
    # timeout: 30 preserved from base
```

### 3. File-Order Precedence

**Why:** Provides predictable override behavior.

**Usage:**

```bash
# Base → Environment → Local overrides
injinja -c base.yml -c environments/prod.yml -c local-overrides.yml
```

### 4. Multiple Environment Variable Sources

**Why:** Supports different deployment and development patterns.

**Flexibility:**

- Development: `.env` files for local configuration
- CI/CD: Direct environment variables
- Platform: Prefix filtering for namespace isolation

### 5. Format Agnostic

**Why:** Teams can use their preferred configuration formats.

**Support:** YAML, JSON, and TOML can be mixed within the same project.

## Error Handling

### Strict Undefined Variables

Injinja uses Jinja2's `StrictUndefined` (when available) to catch template errors early:

```yaml
# This will raise an error if DATABASE_URL is not defined
database_url: {{ DATABASE_URL }}

# This provides a fallback
database_url: {{ DATABASE_URL | default('sqlite:///app.db') }}
```

### Configuration Validation

Environment variable validation can be built into configuration files:

```yaml
{% if not DATABASE_URL %}
  {{ raise_error('DATABASE_URL environment variable is required') }}
{% endif %}
```

### File Discovery Errors

- Invalid glob patterns are handled gracefully
- Missing files in explicit paths raise clear errors
- Empty glob results are logged in debug mode

## Performance Characteristics

### Scalability

- **Configuration Files:** Linear with number of files (each parsed once)
- **Template Rendering:** Depends on template complexity and config size
- **Memory Usage:** All configs held in memory during merge

### Optimization Strategies

1. **Minimal Globbing:** Use specific patterns vs. overly broad globs
2. **Configuration Preprocessing:** Handle complex logic in config phase
3. **Template Simplification:** Minimize complex logic in templates

## Extension Points

### Custom Functions

Add domain-specific filters and tests:

```python
# functions.py
def filter_k8s_name(value):
    """Convert to valid Kubernetes name."""
    return re.sub(r'[^a-z0-9-]', '-', str(value).lower())

def test_is_valid_port(value):
    """Test if value is valid port number."""
    try:
        port = int(value)
        return 1 <= port <= 65535
    except:
        return False
```

### Configuration Sources

The environment variable collection system can be extended to support additional sources (cloud metadata, configuration management systems, etc.).

### Output Formats

Templates can generate any text-based format. Common patterns:

- **Infrastructure:** Terraform, CloudFormation, Kubernetes YAML
- **Application Config:** INI, TOML, JSON, environment files
- **Database:** SQL DDL, migration scripts
- **Documentation:** Markdown, restructuredText

## Testing Strategy

![Testing Diagram](https://github.com/neozenith/injinja/blob/main/diagrams/testing.png?raw=true)

### Configuration Testing

1. **Unit Tests:** Test individual configuration files with known environment variables
2. **Integration Tests:** Test complete configuration merging across environments
3. **Output Validation:** Use `-v` flag to compare against known-good output

### Validation Workflow

```bash
# Generate output and validate
injinja -c config.yml -t template.j2 -v expected-output.txt

# Debug configuration without templating
injinja -c config.yml -o config-json | jq '.'
```

This architecture enables Injinja to handle complex configuration scenarios while maintaining simplicity and predictability in its core operations.
