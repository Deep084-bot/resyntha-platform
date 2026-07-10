from __future__ import annotations

import re
from urllib.parse import urlparse

from app.config.environments import Environment
from app.config.settings import Settings


class ConfigurationError(RuntimeError):
    """Raised when application configuration is invalid."""


def validate_url_field(
    value: str,
    field_name: str,
    *,
    allowed_schemes: set[str] | None = None,
    require_non_empty: bool = True,
) -> list[str]:
    errors: list[str] = []
    if not value.strip():
        if require_non_empty:
            errors.append(f"{field_name} must not be empty")
        return errors

    parsed = urlparse(value)
    if not parsed.scheme:
        errors.append(f"{field_name} must have a scheme (e.g. postgresql:// or redis://)")
    if allowed_schemes and parsed.scheme not in allowed_schemes:
        errors.append(
            f"{field_name} scheme '{parsed.scheme}' is not allowed; "
            f"allowed: {', '.join(sorted(allowed_schemes))}"
        )
    if not parsed.netloc and parsed.scheme not in ("sqlite", "sqlite+aiosqlite"):
        errors.append(f"{field_name} must have a host part")
    return errors


def validate_settings(settings: Settings) -> None:
    errors: list[str] = []

    # --- Database URL ---
    errors.extend(
        validate_url_field(
            settings.DATABASE_URL,
            "DATABASE_URL",
            allowed_schemes={"postgresql", "postgresql+psycopg", "postgresql+asyncpg", "sqlite", "sqlite+aiosqlite"},
        )
    )

    # --- Redis URL ---
    # Allow empty Redis URL in non-production (caching/queue gracefully degrade)
    if settings.REDIS_URL.strip():
        errors.extend(
            validate_url_field(
                settings.REDIS_URL,
                "REDIS_URL",
                allowed_schemes={"redis", "rediss"},
            )
        )
    elif settings.ENVIRONMENT.is_production:
        errors.append("REDIS_URL must not be empty in production")

    # --- Secret key ---
    if settings.ENVIRONMENT.is_production:
        if not settings.SECRET_KEY.strip():
            errors.append("SECRET_KEY must not be empty in production")
        elif settings.SECRET_KEY in ("change-me", "CHANGE-ME", "change-me-to-a-random-secret-key"):
            errors.append("SECRET_KEY must be changed from the default value in production")
        elif len(settings.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters in production")

    # --- LLM provider ---
    if settings.ENVIRONMENT.is_production:
        if settings.LLM_PROVIDER == "groq" and not settings.GROQ_API_KEY.strip():
            errors.append("GROQ_API_KEY must be set when LLM_PROVIDER is 'groq' in production")
        if settings.LLM_PROVIDER == "openai" and not settings.OPENAI_API_KEY.strip():
            errors.append("OPENAI_API_KEY must be set when LLM_PROVIDER is 'openai' in production")

    # --- Embedding provider ---
    if settings.EMBEDDING_PROVIDER not in ("local",):
        errors.append(
            f"EMBEDDING_PROVIDER '{settings.EMBEDDING_PROVIDER}' is not supported; "
            "supported: 'local'"
        )

    # --- Trusted hosts ---
    if settings.ENVIRONMENT.is_production:
        if not settings.TRUSTED_HOSTS.strip():
            errors.append("TRUSTED_HOSTS must not be empty in production")
        if settings.TRUSTED_HOSTS == "*":
            errors.append("TRUSTED_HOSTS must not be '*' in production")

    # --- CORS ---
    if settings.ENVIRONMENT.is_production:
        for origin in settings.cors_origin_list:
            if origin == "*":
                errors.append("CORS_ORIGINS must not contain '*' in production")
                break

    # --- Request timeouts ---
    if settings.REQUEST_TIMEOUT_SECONDS <= 0:
        errors.append("REQUEST_TIMEOUT_SECONDS must be greater than 0")

    # --- Request size limits ---
    if settings.MAX_REQUEST_SIZE <= 0:
        errors.append("MAX_REQUEST_SIZE must be greater than 0")
    if settings.MAX_JSON_SIZE <= 0:
        errors.append("MAX_JSON_SIZE must be greater than 0")
    if settings.MAX_UPLOAD_SIZE <= 0:
        errors.append("MAX_UPLOAD_SIZE must be greater than 0")

    if errors:
        raise ConfigurationError("\n".join(errors))
