"""Base configuration for the application."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Hello-FastApi"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_VERSION: str = "v1"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Rate Limiting
    RATE_LIMIT_TIMES: int = 100
    RATE_LIMIT_SECONDS: int = 60

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class DevelopmentSettings(Settings):
    """Development environment settings."""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionSettings(Settings):
    """Production environment settings."""

    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class TestingSettings(Settings):
    """Testing environment settings."""

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    LOG_LEVEL: str = "DEBUG"


def get_settings() -> Settings:
    """Get settings based on APP_ENV environment variable."""
    import os

    env = os.getenv("APP_ENV", "development")
    settings_map = {
        "development": DevelopmentSettings,
        "production": ProductionSettings,
        "testing": TestingSettings,
    }
    settings_class = settings_map.get(env, DevelopmentSettings)
    return settings_class()


settings = get_settings()
