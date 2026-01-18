"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    APP_NAME: str = Field(default="CV Parser API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="production")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8005)

    # Database
    DATABASE_URL: str = Field(
        default="", description="PostgreSQL connection string with asyncpg driver"
    )
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_ECHO: bool = Field(default=False)

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = Field(default="")
    AZURE_OPENAI_ENDPOINT: str = Field(default="")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-12-01-preview")
    AZURE_OPENAI_DEPLOYMENT: str = Field(
        default="gpt-5-mini-cv-parse",
        description="Azure OpenAI deployment name for both text and vision",
    )
    OPENAI_MAX_TOKENS: int = Field(default=16384)

    # File Processing
    MAX_FILE_SIZE_MB: int = Field(default=10)
    MAX_WORKERS: int = Field(default=4)
    CACHE_TTL_SECONDS: int = Field(default=3600)
    CACHE_MAX_SIZE: int = Field(default=1000)

    # File Storage
    FILE_STORAGE_PATH: str = Field(
        default="/tmp/cv_parser",
        description="Path to store uploaded CV files with timestamp",
    )
    FILE_STORAGE_ENABLED: bool = Field(
        default=True, description="Enable/disable file storage to disk"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="text")
    LOG_FILE_PATH: Optional[str] = Field(default="logs/app.log")

    # Security
    SECRET_KEY: str = Field(default="")
    ALGORITHM: str = Field(default="HS256")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @field_validator("DATABASE_URL", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "SECRET_KEY")
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        """Ensure required fields are not empty."""
        if not v:
            raise ValueError("This field is required and cannot be empty")
        return v

    @property
    def database_url_async(self) -> str:
        """Get async database URL."""
        return self.DATABASE_URL


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (Singleton pattern)."""
    return Settings()


# Global settings instance
settings = get_settings()
