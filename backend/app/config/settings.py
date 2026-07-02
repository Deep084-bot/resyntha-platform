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

from app.observability.logger import get_logger

logger = get_logger(__name__)


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
    # AI / LLM providers
    # ------------------------------------------------------------------
    # Primary LLM provider (default: groq)
    LLM_PROVIDER: str = "groq"

    # Groq (default provider)
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.3

    # OpenAI (optional — requires separate install)
    OPENAI_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Retrieval providers
    # ------------------------------------------------------------------
    # Comma-separated list of active paper-search providers.
    # Supported: semantic_scholar, arxiv, openalex
    RETRIEVAL_PROVIDERS: str = "semantic_scholar,arxiv,openalex"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def parse_retrieval_providers(raw: str | None = None) -> list[str]:
    """Parse a comma-separated provider string into a validated list.

    Parameters
    ----------
    raw:
        Comma-separated provider names (e.g. ``"semantic_scholar,arxiv"``).
        When ``None``, reads from ``get_settings().RETRIEVAL_PROVIDERS``.

    Returns
    -------
    list[str]
        Provider names with whitespace stripped and empty entries removed.

    Warnings
    --------
    Unknown provider names are logged but not removed — they will be
    rejected at instantiation time by ``RetrievalProviderRegistry``.
    """
    if raw is None:
        raw = get_settings().RETRIEVAL_PROVIDERS
    providers = [n.strip() for n in raw.split(",") if n.strip()]

    # Log a warning for unrecognised provider names.
    known = {"semantic_scholar", "arxiv", "openalex"}
    for name in providers:
        if name not in known:
            logger.warning(
                "unknown_retrieval_provider",
                provider=name,
                known=sorted(known),
            )

    return providers


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of Settings.

    The LRU cache guarantees that the .env file and environment variables
    are read exactly once, after which every call receives the same
    immutable object.
    """
    return Settings()
