# JSON Schema Validation Example

This example demonstrates using injinja with JSON Schema validation to ensure your final merged configuration meets specific requirements.

## Files in this example:

- `schema_example.json` - A JSON Schema defining the structure and validation rules
- `config_valid.yaml` - A configuration file that passes schema validation  
- `config_invalid.yaml` - A configuration file that fails schema validation
- `template.yml` - A Jinja2 template to render the final output

## Usage Examples:

### Valid Configuration
```bash
# This will succeed - configuration passes schema validation
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_example.json

# With environment variables for dynamic config
injinja -e env_name=production -e db_host=prod-db.example.com -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_example.json
```

### Invalid Configuration  
```bash
# This will fail with detailed validation errors
injinja -c examples/config_invalid.yaml -t examples/template.yml --schema examples/schema_example.json
```

## Expected Output for Valid Config:

```yaml
# Generated configuration for my-awesome-app
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-awesome-app-config
  namespace: development
data:
  APP_NAME: "my-awesome-app"
  APP_VERSION: "1.2.3"
  ENVIRONMENT: "development"
  DATABASE_URL: "postgres://user:pass@localhost:5432/my_app_db"
  # Feature flags
  FEATURE_A_ENABLED: "true"
  FEATURE_B_ENABLED: "false"
```

## Expected Error Output for Invalid Config:

```
❌ Schema validation failed:
   Error at path: app -> version
   Message: '1.2' does not match '^\\d+\\.\\d+\\.\\d+$'
   Expected: ^\\d+\\.\\d+\\.\\d+$
   Actual value: 1.2

   Full validation context:
   Schema rule: pattern = ^\\d+\\.\\d+\\.\\d+$
```

## Schema Features:

The example schema validates:
- **Required fields**: `app.name`, `app.version`, `app.environment`, `database.host`, `database.port`, `database.name`
- **Data types**: strings, integers, objects
- **String patterns**: version must follow semantic versioning (e.g., "1.2.3")  
- **Enums**: environment must be one of "development", "staging", "production"
- **Numeric ranges**: database port must be 1-65535
- **String lengths**: names must be non-empty
- **Additional properties**: allowed at root level, forbidden in specific objects

This approach ensures your configuration is valid before templating begins, catching errors early and providing clear feedback about what needs to be fixed.