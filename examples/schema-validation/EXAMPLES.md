# Config Schema Validation Examples

The below examples are illustrative of this feature. The official tests for `injinja` can be run using:

```sh
uv run pytest tests/test_injinja.py::TestSchemaValidation
```

> **NOTE**: The output for validations may change overtime and is not gauranteed just yet incase you're planning on leveraging it as an input into another system.

<!-- TOC -->
<!-- TOC -->

## JSON Schema Test Cases

### Valid Configuration

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json 
```

**Expected**: ✅ Success with templated output

### Invalid Configurations

#### Example 1

```sh
# Invalid version pattern (1.2 vs 1.2.3)
injinja \
-c examples/schema-validation/config_invalid_1.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json

ERROR:root:Schema validation failed:
  Error at path: app -> version
  Message: '1.2' does not match '^\\d+\\.\\d+\\.\\d+$'
  Expected: ^\d+\.\d+\.\d+$
  Actual value: 1.2
  Full validation context:
  Schema rule: pattern = ^\d+\.\d+\.\d+$
```

#### Example 2

```sh
# Invalid environment enum (testing vs development/staging/production)  
injinja \
-c examples/schema-validation/config_invalid_2.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json

ERROR:root:Schema validation failed:
  Error at path: app -> environment
  Message: 'testing' is not one of ['development', 'staging', 'production']
  Expected: ['development', 'staging', 'production']
  Actual value: testing
  Full validation context:
  Schema rule: enum = ['development', 'staging', 'production']
```

#### Example 3

```sh
# Port out of range (70000 vs 1-65535)
injinja \
-c examples/schema-validation/config_invalid_3.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json

ERROR:root:Schema validation failed:
  Error at path: database -> port
  Message: 70000 is greater than the maximum of 65535
  Expected: 65535
  Actual value: 70000
  Full validation context:
  Schema rule: maximum = 65535
```

#### Example 4

```sh
# Missing required database.name field
injinja \
-c examples/schema-validation/config_invalid_4.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json

ERROR:root:Schema validation failed:
  Error at path: database
  Message: 'name' is a required property
  Expected: ['host', 'port', 'name']
  Actual value: {'host': 'localhost', 'port': 5432}
  Full validation context:
  Schema rule: required = ['host', 'port', 'name']
```

### Dynamic Environment Variables

```sh
injinja \
-e env_name=production \
-e db_host=prod.example.com \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_example.json
```

**Expected**: ✅ Success with production values templated

## Pydantic Test Cases

### Basic Model Validation

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_models.py::ConfigModel
```

**Expected**: ✅ Success with templated output

### Strict Model Validation

Using a `strict` Pydantic model with the `extra = 'forbid'` option. Being strict can help discover typos in config.

The the default is to `ignore` extra data.

[_See Pydantic documentation_](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra) for more information.

```python
class StrictConfigModel(BaseModel):
    """Strict configuration model that doesn't allow extra fields."""
    app: AppConfig
    database: DatabaseConfig

    class Config:
        """Pydantic model configuration."""
        # Forbid additional fields not defined in the model
        extra = "forbid"
```

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_models.py::StrictConfigModel

ERROR:root:Pydantic validation failed:
  Error at path: features
  Message: Extra inputs are not permitted
  Input value: {'feature_a': True, 'feature_b': False}
  Model: examples/schema-validation/schema_models.py::StrictConfigModel
```

**Expected**: ❌ Failure due to extra 'features' field not allowed in strict mode

### Production Model Validation

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_pydantic_invalid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_models.py::ProductionConfigModel

ERROR:root:Pydantic validation failed:
  Model: examples/schema-validation/schema_models.py::ProductionConfigModel
    Error at path: app -> version
    Message: String should match pattern '^\d+\.\d+\.\d+$'
    Input value: 1.2.3-beta

    Error at path: database
    Message: Value error, Production database cannot use localhost
    Input value: {'host': 'localhost', 'port': 5432, 'name': 'my_app_db'}

    Error at path: features -> feature_b
    Message: Input should be a valid boolean, unable to interpret input
    Input value: not_boolean
```

**Expected**: ❌ Multiple validation errors:
- Production versions cannot contain pre-release metadata (1.2.3-beta)
- Production database cannot use localhost
- Feature flag must be boolean, not string

### Missing Model Class

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_models.py::NonExistentModel

ERROR:root:Pydantic validation failed:
Class 'NonExistentModel' not found in 'examples/schema-validation/schema_models.py'.
Available classes:
- AppConfig
- ConfigModel
- DatabaseConfig
- ProductionConfigModel
- StrictConfigModel
```

**Expected**: ❌ Error about missing class with list of available classes

### Invalid Module Path

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/missing_file.py::ConfigModel

ERROR:root:Pydantic validation failed: Module file 'examples/schema-validation/missing_file.py' not found.
```

**Expected**: ❌ Error about module file not being found

### Invalid Format

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml \
-s examples/schema-validation/schema_models.py

ERROR:root:Pydantic validation failed: 
Invalid format 'examples/schema-validation/schema_models.py'. 
Expected format: 'module.py::ModelClass'
```

**Expected**: ❌ Error about invalid format, expected module.py::ClassName

## Edge Cases

### Empty Configuration

```sh
echo '{}' | injinja --stdin-format json -t examples/schema-validation/template.yml --schema examples/schema-validation/schema_example.json

ERROR:root:Schema validation failed:
  Error at path: root
  Message: 'app' is a required property
  Expected: ['app', 'database']
  Actual value: {}
  Full validation context:
  Schema rule: required = ['app', 'database']
```

**Expected**: ❌ Missing required fields

### No Schema Provided

```sh
injinja \
-e env_name=production \
-c examples/schema-validation/config_valid.yaml \
-t examples/schema-validation/template.yml
```

**Expected**: ✅ Success (no validation performed)
