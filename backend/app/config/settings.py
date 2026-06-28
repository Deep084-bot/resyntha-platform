"""Application settings loaded from environment variables and .env file.

Uses pydantic-settings v2 with SettingsConfigDict to become the single
source of truth for all configuration.  No other module should call
os.getenv() or load_dotenv() directly.

A cached singleton is exposed via get_settings() so that the Settings
object is constructed only once per process and can be injected through
FastAPI dependency injection.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Type-safe, validated configuration for the Resyntha platform."""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "resyntha"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/resyntha"

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    API_V1_PREFIX: str = "/api/v1"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://localhost:8000"
    )

    # ------------------------------------------------------------------
    # AI / External services  (placeholders for future sprints)
    # ------------------------------------------------------------------
    GROQ_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings.

    The LRU cache guarantees that the .env file and environment variables
    are read exactly once, after which every call receives the same
    immutable object.
    """
    return Settings()
