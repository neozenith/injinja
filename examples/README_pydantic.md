# Pydantic Model Validation Example

This example demonstrates using injinja with Pydantic models for schema validation. Pydantic provides type safety, data validation, and serialization in a Pythonic way.

## Files in this example:

- `schema_models.py` - Pydantic model definitions with various validation rules
- `config_valid.yaml` - A configuration file that passes validation  
- `config_pydantic_invalid.yaml` - A configuration file that fails validation
- `template.yml` - A Jinja2 template to render the final output

## Available Pydantic Models:

### ConfigModel (Recommended)
- Basic validation with required fields
- Allows extra fields (flexible)
- Validates feature flags as booleans

### StrictConfigModel  
- Same as ConfigModel but forbids extra fields
- Use when you want strict schema enforcement

### ProductionConfigModel
- Extends ConfigModel with production-specific rules
- Forbids localhost database hosts in production
- Forbids pre-release versions in production

## Usage Examples:

### Basic Pydantic Validation
```bash
# This will succeed - configuration passes validation
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::ConfigModel

# With environment variables
injinja -e env_name=production -e db_host=prod-db.example.com -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::ConfigModel
```

### Strict Validation (No Extra Fields)
```bash
# This will fail if config contains fields not in the model
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::StrictConfigModel
```

### Production-Specific Validation
```bash
# This will fail with production-specific validation errors
injinja -c examples/config_pydantic_invalid.yaml -t examples/template.yml --schema examples/schema_models.py::ProductionConfigModel
```

## Expected Error Output for Invalid Config:

```
❌ Pydantic validation failed:
   Error at path: features -> feature_b
   Message: Feature 'feature_b' must be boolean, got str
   Input value: not_boolean

   Error at path: database
   Message: Production database cannot use localhost

   Error at path: app  
   Message: Production versions cannot contain pre-release or build metadata

   Model: examples/schema_models.py::ProductionConfigModel
```

## Advantages of Pydantic vs JSON Schema:

### Type Safety
- Python native types with IDE support
- Automatic type coercion where appropriate
- Rich validation with custom validators

### Flexibility
- Custom validation logic using `@field_validator`
- Model inheritance and composition  
- Dynamic validation based on other fields

### Developer Experience
- Clear error messages with field paths
- Auto-completion in Python IDEs
- Can reuse models in application code

### Advanced Features
- Enum support for constrained values
- Nested models for complex data structures
- Field aliases and custom serialization
- Data conversion and normalization

## Best Practices:

1. **Start with basic models** and add validation as needed
2. **Use Enums** for constrained string values (like environments)
3. **Add custom validators** for business logic
4. **Use field descriptions** for self-documenting schemas
5. **Consider inheritance** for environment-specific validation
6. **Set extra="allow"** for flexibility or extra="forbid" for strictness