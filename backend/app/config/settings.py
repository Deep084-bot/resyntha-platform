"""Application settings loaded from environment variables and .env file.

Uses pydantic-settings v2 with SettingsConfigDict to become the single
source of truth for all configuration.  No other module should call
os.getenv() or load_dotenv() directly.

A cached singleton is exposed via get_settings() so that the Settings
object is constructed only once per process and can be injected through
FastAPI dependency injection.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.constants import BUILD_TIME, GIT_COMMIT
from app.config.environments import Environment
from app.observability.logger import get_logger

logger = get_logger(__name__)


class Settings(BaseSettings):
    """Type-safe, validated configuration for the Resyntha platform."""

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "resyntha"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    BUILD_TIME: str = BUILD_TIME
    GIT_COMMIT: str = GIT_COMMIT

    # ------------------------------------------------------------------
    # Security
    # ------------------------------------------------------------------
    SECRET_KEY: str = ""
    SECURITY_HEADERS_ENABLED: bool = True
    REQUEST_TIMEOUT_SECONDS: float = 30.0
    MAX_REQUEST_SIZE: int = 1_048_576  # 1 MB – general request body
    MAX_JSON_SIZE: int = 1_048_576  # 1 MB – JSON bodies
    MAX_UPLOAD_SIZE: int = 10_485_760  # 10 MB – file uploads

    # ------------------------------------------------------------------
    # Content Security Policy
    # ------------------------------------------------------------------
    CSP_ENABLED: bool = True
    CSP_DIRECTIVES: str = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/resyntha"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: float = 30.0
    DB_POOL_RECYCLE: int = 1800

    # ------------------------------------------------------------------
    # Redis
    # ------------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    API_V1_PREFIX: str = "/api/v1"
    TRUSTED_HOSTS: str = "localhost,127.0.0.1"

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    CORS_ORIGINS: str = (
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://localhost:8000"
    )
    CORS_ALLOWED_METHODS: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD"
    CORS_ALLOWED_HEADERS: str = (
        "Authorization,Content-Type,X-Request-ID,Accept,Origin,"
        "User-Agent,DNT,Cache-Control,X-Mx-ReqToken,Keep-Alive,"
        "X-Frame-Options,X-Content-Type-Options"
    )
    CORS_ALLOW_CREDENTIALS: bool = True

    # ------------------------------------------------------------------
    # OpenAPI / Docs
    # ------------------------------------------------------------------
    OPENAPI_ENABLED: bool = True
    DOCS_ENABLED: bool = True
    REDOC_ENABLED: bool = True

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_FORMAT: str = "console"
    LOG_LEVEL: str = "INFO"

    # ------------------------------------------------------------------
    # AI / LLM providers
    # ------------------------------------------------------------------
    LLM_PROVIDER: str = "groq"

    # Groq (default provider)
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.3

    # OpenAI (optional)
    OPENAI_API_KEY: str = ""

    # ------------------------------------------------------------------
    # Retrieval providers
    # ------------------------------------------------------------------
    RETRIEVAL_PROVIDERS: str = "semantic_scholar,arxiv,openalex"

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300
    CACHE_GRAPH_TTL: int = 1800
    CACHE_LANDSCAPE_TTL: int = 1800
    CACHE_GAP_REPORT_TTL: int = 1800
    CACHE_KNOWLEDGE_PACKAGE_TTL: int = 1800
    CACHE_RETRIEVAL_TTL: int = 600
    CACHE_INVESTIGATION_TTL: int = 300

    # ------------------------------------------------------------------
    # Rate Limiting
    # ------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_BACKEND: str = "redis"
    DEFAULT_RATE_LIMIT: int = 120
    COPILOT_RATE_LIMIT: int = 20
    INVESTIGATION_RATE_LIMIT: int = 10
    RUN_RATE_LIMIT: int = 5
    RATE_LIMIT_WINDOW: int = 60

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/api/v1/metrics"
    METRICS_NAMESPACE: str = "resyntha"
    METRICS_SUBSYSTEM: str = "backend"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def coerce_environment(cls, v: object) -> object:
        if isinstance(v, str):
            return Environment.from_string(v)
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def coerce_debug(cls, v: object) -> bool:
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes")
        return bool(v)

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def validate_log_level(cls, v: object) -> str:
        if isinstance(v, str):
            upper = v.upper()
            allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
            if upper in allowed:
                return upper
        return "INFO"

    @field_validator("LOG_FORMAT", mode="before")
    @classmethod
    def validate_log_format(cls, v: object) -> str:
        if isinstance(v, str) and v.lower() in ("console", "json"):
            return v.lower()
        return "console"

    @field_validator("RATE_LIMIT_BACKEND", mode="before")
    @classmethod
    def validate_rate_limit_backend(cls, v: object) -> str:
        if isinstance(v, str) and v.lower() in ("redis", "memory"):
            return v.lower()
        return "redis"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cors_method_list(self) -> list[str]:
        return [m.strip() for m in self.CORS_ALLOWED_METHODS.split(",") if m.strip()]

    @property
    def cors_header_list(self) -> list[str]:
        return [h.strip() for h in self.CORS_ALLOWED_HEADERS.split(",") if h.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [h.strip() for h in self.TRUSTED_HOSTS.split(",") if h.strip()]

    @property
    def csp_directive_list(self) -> list[str]:
        return [d.strip() for d in self.CSP_DIRECTIVES.split(";") if d.strip()]


def parse_retrieval_providers(raw: str | None = None) -> list[str]:
    """Parse a comma-separated provider string into a validated list."""
    if raw is None:
        raw = get_settings().RETRIEVAL_PROVIDERS
    providers = [n.strip() for n in raw.split(",") if n.strip()]

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
    """Return a cached singleton instance of Settings."""
    return Settings()
