# Test Scenarios for Schema Validation

## Test Cases to Verify Both Implementations

### JSON Schema Test Cases

#### Valid Configuration
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_example.json
```
**Expected**: ✅ Success with templated output

#### Invalid Configuration  
```bash
injinja -c examples/config_invalid.yaml -t examples/template.yml --schema examples/schema_example.json
```
**Expected**: ❌ Validation errors for:
- Invalid version pattern (1.2 vs 1.2.3)
- Invalid environment enum (testing vs development/staging/production)  
- Port out of range (70000 vs 1-65535)
- Missing required database.name field

#### Dynamic Environment Variables
```bash
injinja -e env_name=production -e db_host=prod.example.com -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_example.json
```
**Expected**: ✅ Success with production values templated

### Pydantic Test Cases

#### Basic Model Validation
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::ConfigModel
```
**Expected**: ✅ Success with templated output

#### Strict Model Validation
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::StrictConfigModel
```
**Expected**: ❌ Failure due to extra 'features' field not allowed in strict mode

#### Production Model Validation
```bash
injinja -c examples/config_pydantic_invalid.yaml -t examples/template.yml --schema examples/schema_models.py::ProductionConfigModel
```
**Expected**: ❌ Multiple validation errors:
- Production versions cannot contain pre-release metadata (1.2.3-beta)
- Production database cannot use localhost
- Feature flag must be boolean, not string

#### Missing Model Class
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py::NonExistentModel
```
**Expected**: ❌ Error about missing class with list of available classes

#### Invalid Module Path
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/missing_file.py::ConfigModel
```
**Expected**: ❌ Error about module file not found

#### Invalid Format
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml --schema examples/schema_models.py
```
**Expected**: ❌ Error about invalid format, expected module.py::ClassName

### Edge Cases

#### Empty Configuration
```bash
echo '{}' | injinja --stdin-format json -t examples/template.yml --schema examples/schema_example.json
```
**Expected**: ❌ Missing required fields

#### Config-Only Mode with Schema
```bash
injinja -c examples/config_valid.yaml -o config-json --schema examples/schema_example.json
```
**Expected**: ✅ Success with JSON config output (validation occurs before output)

#### No Schema Provided
```bash
injinja -c examples/config_valid.yaml -t examples/template.yml
```
**Expected**: ✅ Success (no validation performed)

### Performance Considerations

For large configurations, both validation approaches should:
- Validate quickly (sub-second for typical configs)
- Provide specific error locations
- Not significantly impact memory usage
- Fail fast on first critical error

### Error Message Quality

Test that error messages include:
- Exact field path where error occurred
- Clear description of what was wrong
- Expected vs actual values
- Relevant schema context
- Actionable guidance for fixing the issue