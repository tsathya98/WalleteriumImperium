"""
Configuration management for Project Raseed
Handles environment-specific settings and validation
"""

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment-specific overrides"""
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="forbid"
    )
    
    # Basic Configuration
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    PORT: int = Field(default=8080)
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None)
    VERTEX_AI_LOCATION: str = Field(default="asia-south1")
    FIRESTORE_DATABASE: str = Field(default="(default)")
    
    # API Configuration
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5000,http://localhost:8080,https://*.run.app,https://*.googleapis.com"
    )
    
    # Processing Configuration
    MAX_RETRIES: int = Field(default=3)
    PROCESSING_TIMEOUT: int = Field(default=300)  # 5 minutes
    TOKEN_EXPIRY_MINUTES: int = Field(default=10)
    MAX_IMAGE_SIZE_MB: int = Field(default=10)
    
    # Performance Configuration
    ENABLE_CACHE: bool = Field(default=True)
    CACHE_TTL: int = Field(default=3600)  # 1 hour
    
    # Vertex AI Configuration
    VERTEX_AI_MODEL: str = Field(default="gemini-2.0-flash-exp")
    VERTEX_AI_TEMPERATURE: float = Field(default=0.1)
    VERTEX_AI_MAX_TOKENS: int = Field(default=2048)
    
    # Development/Testing Configuration
    USE_EMULATORS: bool = Field(default=False)
    FIRESTORE_EMULATOR_HOST: Optional[str] = Field(default=None)
    VERTEX_AI_MOCK_HOST: Optional[str] = Field(default=None)
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @field_validator("GOOGLE_CLOUD_PROJECT")
    @classmethod
    def validate_project_in_production(cls, v: Optional[str], info) -> Optional[str]:
        # Note: In Pydantic v2, we need to access other field values differently
        # For now, we'll validate this in the application startup
        return v
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS if isinstance(self.ALLOWED_ORIGINS, list) else []
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def use_firestore_emulator(self) -> bool:
        return self.USE_EMULATORS and self.FIRESTORE_EMULATOR_HOST is not None
    
    @property
    def use_vertex_ai_mock(self) -> bool:
        return self.USE_EMULATORS and self.VERTEX_AI_MOCK_HOST is not None


class DevelopmentSettings(Settings):
    """Development-specific settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    USE_EMULATORS: bool = True
    FIRESTORE_EMULATOR_HOST: str = "localhost:8080"
    VERTEX_AI_MOCK_HOST: str = "localhost:8090"


class ProductionSettings(Settings):
    """Production-specific settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    USE_EMULATORS: bool = False
    
    # Performance optimizations
    MAX_RETRIES: int = 3
    PROCESSING_TIMEOUT: int = 300
    TOKEN_EXPIRY_MINUTES: int = 10
    
    # Security
    ALLOWED_ORIGINS: str = Field(
        default="https://*.run.app,https://api.raseed-app.com"
    )


def get_settings() -> Settings:
    """Get settings based on environment"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "development":
        return DevelopmentSettings()
    else:
        return Settings()


# Global settings instance
settings = get_settings()