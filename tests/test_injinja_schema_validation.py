"""Tests for schema validation functionality."""

# Standard Library
import json
import textwrap

# Third Party
import pytest

# Our Libraries
from injinja.injinja import (
    ConfigSchemaValidationError,
    JSONSchemaLoadingError,
    PydanticConfigSchemaLoadingError,
    _load_json_schema,
    _load_pydantic_model,
    merge,
    validate_config_with_jsonschema,
    validate_config_with_pydantic,
    validate_config_with_schema,
)


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_pydantic_model_loading_success(self, tmp_path):
        """Test successful Pydantic model loading."""
        # Create a simple Pydantic model file
        model_file = tmp_path / "test_models.py"
        model_file.write_text(
            textwrap.dedent("""
            from pydantic import BaseModel

            class TestModel(BaseModel):
                name: str
                age: int
        """)
        )

        # Test loading the model
        model_cls = _load_pydantic_model(f"{model_file}::TestModel")
        assert model_cls.__name__ == "TestModel"

        # Test creating instance
        instance = model_cls(name="test", age=30)
        assert instance.name == "test"
        assert instance.age == 30

    def test_pydantic_model_loading_missing_file(self):
        """Test Pydantic model loading with missing file."""
        with pytest.raises(PydanticConfigSchemaLoadingError) as exc_info:
            _load_pydantic_model("/nonexistent/file.py::TestModel")
        assert "Module file '/nonexistent/file.py' not found" in str(exc_info.value)

    def test_pydantic_model_loading_missing_class(self, tmp_path):
        """Test Pydantic model loading with missing class."""
        model_file = tmp_path / "test_models.py"
        model_file.write_text("from pydantic import BaseModel\n\nclass OtherModel(BaseModel): pass")

        with pytest.raises(PydanticConfigSchemaLoadingError) as exc_info:
            _load_pydantic_model(f"{model_file}::MissingModel")
        assert "Class 'MissingModel' not found in" in str(exc_info.value)

    def test_pydantic_model_loading_invalid_syntax(self, tmp_path):
        """Test Pydantic model loading with invalid Python syntax."""
        model_file = tmp_path / "test_models.py"
        model_file.write_text("invalid python syntax !!!")

        with pytest.raises(SyntaxError):
            _load_pydantic_model(f"{model_file}::TestModel")

    def test_json_schema_loading_success(self, tmp_path):
        """Test successful JSON schema loading."""
        schema_file = tmp_path / "test_schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
            "required": ["name", "age"],
        }
        schema_file.write_text(json.dumps(schema_data))

        result = _load_json_schema(str(schema_file))
        assert result == schema_data

    def test_json_schema_loading_missing_file(self):
        """Test JSON schema loading with missing file."""
        with pytest.raises(JSONSchemaLoadingError) as exc_info:
            _load_json_schema("/nonexistent/file.json")
        assert "Schema file '/nonexistent/file.json' not found" in str(exc_info.value)

    def test_json_schema_loading_invalid_json(self, tmp_path):
        """Test JSON schema loading with invalid JSON."""
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text("invalid json content {{{")

        with pytest.raises(JSONSchemaLoadingError) as exc_info:
            _load_json_schema(str(schema_file))
        assert "Invalid JSON in schema file" in str(exc_info.value)

    def test_json_schema_loading_non_json_file(self, tmp_path):
        """Test JSON schema loading with non-.json file."""
        schema_file = tmp_path / "test_schema.yaml"
        schema_file.write_text("name: test")

        with pytest.raises(JSONSchemaLoadingError) as exc_info:
            _load_json_schema(str(schema_file))
        assert "JSON Schema must be a .json file" in str(exc_info.value)

    def test_pydantic_validation_success(self, tmp_path):
        """Test successful Pydantic validation."""
        # Create a Pydantic model
        model_file = tmp_path / "test_models.py"
        model_file.write_text(
            textwrap.dedent("""
            from pydantic import BaseModel

            class ConfigModel(BaseModel):
                database_url: str
                port: int
                debug: bool = False
        """)
        )

        # Valid configuration
        config = {"database_url": "postgresql://localhost:5432/test", "port": 8080, "debug": True}

        # Should not raise an exception
        validate_config_with_pydantic(config, f"{model_file}::ConfigModel")

    def test_pydantic_validation_failure(self, tmp_path):
        """Test Pydantic validation failure."""
        # Create a Pydantic model
        model_file = tmp_path / "test_models.py"
        model_file.write_text(
            textwrap.dedent("""
            from pydantic import BaseModel

            class ConfigModel(BaseModel):
                database_url: str
                port: int
                debug: bool = False
        """)
        )

        # Invalid configuration (missing required field, wrong type)
        config = {
            "port": "not_an_integer",
            "debug": True,
            # missing database_url
        }

        with pytest.raises(ConfigSchemaValidationError) as exc_info:
            validate_config_with_pydantic(config, f"{model_file}::ConfigModel")

        error_msg = str(exc_info.value)
        assert "Pydantic validation failed" in error_msg
        assert "database_url" in error_msg or "port" in error_msg

    def test_pydantic_validation_invalid_format(self):
        """Test Pydantic validation with invalid schema specification format."""
        config = {"test": "value"}

        with pytest.raises(PydanticConfigSchemaLoadingError) as exc_info:
            validate_config_with_pydantic(config, "invalid_format")
        assert "Invalid format" in str(exc_info.value)
        assert "Expected format: 'module.py::ModelClass'" in str(exc_info.value)

    def test_json_schema_validation_success(self, tmp_path):
        """Test successful JSON Schema validation."""
        # Create a JSON schema
        schema_file = tmp_path / "test_schema.json"
        schema_data = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string", "format": "email"},
            },
            "required": ["name", "age"],
        }
        schema_file.write_text(json.dumps(schema_data))

        # Valid configuration
        config = {"name": "John Doe", "age": 30, "email": "john@example.com"}

        # Should not raise an exception
        validate_config_with_jsonschema(config, str(schema_file))

    def test_json_schema_validation_failure(self, tmp_path):
        """Test JSON Schema validation failure."""
        # Create a JSON schema
        schema_file = tmp_path / "test_schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "integer", "minimum": 0}},
            "required": ["name", "age"],
        }
        schema_file.write_text(json.dumps(schema_data))

        # Invalid configuration
        config = {
            "name": 123,  # Should be string
            "age": -5,  # Should be >= 0
            # Missing required fields handled by schema
        }

        with pytest.raises(ConfigSchemaValidationError) as exc_info:
            validate_config_with_jsonschema(config, str(schema_file))

        error_msg = str(exc_info.value)
        assert "Schema validation failed" in error_msg

    def test_unified_schema_validation_pydantic(self, tmp_path):
        """Test unified schema validation interface with Pydantic."""
        # Create a Pydantic model
        model_file = tmp_path / "test_models.py"
        model_file.write_text(
            textwrap.dedent("""
            from pydantic import BaseModel

            class UnifiedModel(BaseModel):
                service_name: str
                replicas: int = 1
        """)
        )

        config = {"service_name": "api", "replicas": 3}

        # Should not raise an exception (contains ::)
        validate_config_with_schema(config, f"{model_file}::UnifiedModel")

    def test_unified_schema_validation_jsonschema(self, tmp_path):
        """Test unified schema validation interface with JSON Schema."""
        # Create a JSON schema
        schema_file = tmp_path / "unified_schema.json"
        schema_data = {
            "type": "object",
            "properties": {"service_name": {"type": "string"}, "replicas": {"type": "integer", "minimum": 1}},
            "required": ["service_name"],
        }
        schema_file.write_text(json.dumps(schema_data))

        config = {"service_name": "api", "replicas": 2}

        # Should not raise an exception (no ::)
        validate_config_with_schema(config, str(schema_file))

    def test_merge_with_schema_validation_success(self, tmp_path):
        """Test merge function with successful schema validation."""
        # Create config and template files
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name: test-app\nport: 8080")

        template_file = tmp_path / "template.txt"
        template_file.write_text("App: {{ name }} on port {{ port }}")

        # Create JSON schema
        schema_file = tmp_path / "schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "port": {"type": "integer"}},
            "required": ["name", "port"],
        }
        schema_file.write_text(json.dumps(schema_data))

        output_file = tmp_path / "output.txt"

        # Should not raise an exception
        merge(config=[str(config_file)], template=str(template_file), output=str(output_file), schema=str(schema_file))

        assert output_file.exists()
        assert "App: test-app on port 8080" in output_file.read_text()

    def test_merge_with_schema_validation_failure(self, tmp_path):
        """Test merge function with schema validation failure."""
        # Create invalid config file
        config_file = tmp_path / "config.yaml"
        config_file.write_text("name: test-app\nport: 'not-a-number'")

        template_file = tmp_path / "template.txt"
        template_file.write_text("App: {{ name }} on port {{ port }}")

        # Create JSON schema that requires port to be integer
        schema_file = tmp_path / "schema.json"
        schema_data = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "port": {"type": "integer"}},
            "required": ["name", "port"],
        }
        schema_file.write_text(json.dumps(schema_data))

        output_file = tmp_path / "output.txt"

        # Should raise ConfigSchemaValidationError due to validation failure
        with pytest.raises(ConfigSchemaValidationError) as exc_info:
            merge(
                config=[str(config_file)], template=str(template_file), output=str(output_file), schema=str(schema_file)
            )
        assert "Schema validation failed" in str(exc_info.value)
        assert "port" in str(exc_info.value)
        assert not output_file.exists()  # Should not create output on validation failure

    def test_configuration_validation_error_custom_exception(self):
        """Test ConfigSchemaValidationError can be raised and caught."""
        error_msg = "Test validation error"

        with pytest.raises(ConfigSchemaValidationError) as exc_info:
            raise ConfigSchemaValidationError(error_msg)

        assert str(exc_info.value) == error_msg

    def test_schema_validation_with_none_schema(self, tmp_path):
        """Test that no validation occurs when schema is None."""
        # Create a config file with test data
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test: value")

        # Call merge without schema - should not raise any validation error
        template_file = tmp_path / "template.txt"
        template_file.write_text("Value: {{ test }}")

        output_file = tmp_path / "output.txt"

        # Should work without schema validation
        merge(
            config=[str(config_file)],
            template=str(template_file),
            output=str(output_file),
            schema=None,  # No schema validation
        )

        assert output_file.exists()
        assert "Value: value" in output_file.read_text()

    def test_validate_config_with_schema_pydantic_vs_json(self, tmp_path):
        """Test that the unified interface correctly routes to Pydantic vs JSON Schema."""
        # Test JSON Schema path (no :: in schema)
        schema_file = tmp_path / "test.json"
        schema_data = {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}
        schema_file.write_text(json.dumps(schema_data))

        config = {"name": "test"}

        # This should route to JSON Schema validation
        validate_config_with_schema(config, str(schema_file))

        # Test Pydantic path (with :: in schema)
        model_file = tmp_path / "models.py"
        model_file.write_text(
            textwrap.dedent("""
            from pydantic import BaseModel
            
            class TestModel(BaseModel):
                name: str
        """)
        )

        # This should route to Pydantic validation
        validate_config_with_schema(config, f"{model_file}::TestModel")
