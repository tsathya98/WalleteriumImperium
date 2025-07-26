"""
Configuration management for Project Raseed
Handles environment-specific settings and validation
"""

from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment-specific overrides"""
    
    # Basic Configuration
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    PORT: int = Field(default=8080, env="PORT")
    
    # Google Cloud Configuration
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    VERTEX_AI_LOCATION: str = Field(default="asia-south1", env="VERTEX_AI_LOCATION")
    FIRESTORE_DATABASE: str = Field(default="(default)", env="FIRESTORE_DATABASE")
    
    # API Configuration
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5000,http://localhost:8080,https://*.run.app,https://*.googleapis.com",
        env="ALLOWED_ORIGINS"
    )
    
    # Processing Configuration
    MAX_RETRIES: int = Field(default=3, env="MAX_RETRIES")
    PROCESSING_TIMEOUT: int = Field(default=300, env="PROCESSING_TIMEOUT")  # 5 minutes
    TOKEN_EXPIRY_MINUTES: int = Field(default=10, env="TOKEN_EXPIRY_MINUTES")
    MAX_IMAGE_SIZE_MB: int = Field(default=10, env="MAX_IMAGE_SIZE_MB")
    
    # Performance Configuration
    ENABLE_CACHE: bool = Field(default=True, env="ENABLE_CACHE")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Vertex AI Configuration
    VERTEX_AI_MODEL: str = Field(default="gemini-2.0-flash-exp", env="VERTEX_AI_MODEL")
    VERTEX_AI_TEMPERATURE: float = Field(default=0.1, env="VERTEX_AI_TEMPERATURE")
    VERTEX_AI_MAX_TOKENS: int = Field(default=2048, env="VERTEX_AI_MAX_TOKENS")
    
    # Development/Testing Configuration
    USE_EMULATORS: bool = Field(default=False, env="USE_EMULATORS")
    FIRESTORE_EMULATOR_HOST: Optional[str] = Field(default=None, env="FIRESTORE_EMULATOR_HOST")
    VERTEX_AI_MOCK_HOST: Optional[str] = Field(default=None, env="VERTEX_AI_MOCK_HOST")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("GOOGLE_CLOUD_PROJECT")
    def validate_project_in_production(cls, v, values):
        if values.get("ENVIRONMENT") == "production" and not v:
            raise ValueError("GOOGLE_CLOUD_PROJECT is required in production")
        return v
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string from .env file
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            # Handle list directly
            return v
        return v
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get ALLOWED_ORIGINS as a list"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS
    
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
    ALLOWED_ORIGINS: str = "https://*.run.app,https://api.raseed-app.com"


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