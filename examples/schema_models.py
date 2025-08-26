"""
Pydantic models for validating injinja configuration.

This demonstrates how to use Pydantic models for schema validation
with the --schema flag in the format: --schema schema_models.py::ConfigModel
"""

from enum import Enum
from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator


class Environment(str, Enum):
    """Allowed environment values."""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"


class AppConfig(BaseModel):
    """Application configuration."""
    name: str = Field(..., min_length=1, description="Application name")
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version")
    environment: Environment = Field(..., description="Deployment environment")


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = Field(..., min_length=1, description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    name: str = Field(..., min_length=1, description="Database name")


class ConfigModel(BaseModel):
    """Main configuration model that validates the entire merged config."""
    app: AppConfig
    database: DatabaseConfig
    features: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    
    @field_validator('features')
    @classmethod
    def validate_features(cls, v: Dict[str, Any]) -> Dict[str, bool]:
        """Ensure all feature values are boolean."""
        for key, value in v.items():
            if not isinstance(value, bool):
                raise ValueError(f"Feature '{key}' must be boolean, got {type(value).__name__}")
        return v

    class Config:
        """Pydantic model configuration."""
        # Allow additional fields not defined in the model
        extra = "allow"


class StrictConfigModel(BaseModel):
    """Strict configuration model that doesn't allow extra fields."""
    app: AppConfig
    database: DatabaseConfig
    
    class Config:
        """Pydantic model configuration."""
        # Forbid additional fields not defined in the model
        extra = "forbid"


# Example model with additional validation
class ProductionConfigModel(ConfigModel):
    """Production-specific configuration with stricter validation."""
    
    @field_validator('app')
    @classmethod
    def validate_production_app(cls, v: AppConfig) -> AppConfig:
        """Additional validation for production environments."""
        if v.environment == Environment.PRODUCTION:
            # In production, version should not contain pre-release identifiers
            if "-" in v.version or "+" in v.version:
                raise ValueError("Production versions cannot contain pre-release or build metadata")
        return v
    
    @field_validator('database')
    @classmethod  
    def validate_production_database(cls, v: DatabaseConfig) -> DatabaseConfig:
        """Additional validation for production databases."""
        if v.host in ["localhost", "127.0.0.1"]:
            raise ValueError("Production database cannot use localhost")
        return v