"""Tests for the configuration layer.

Covers settings loading, environment enum, configuration validation,
and startup lifecycle.  Tests construct Settings objects directly
with explicit kwargs to avoid depending on .env files or the cached
singleton.
"""

from __future__ import annotations

import pytest

from app.config import (
    BUILD_TIME,
    PYTHON_VERSION,
    ConfigurationError,
    Environment,
    Settings,
    validate_settings,
)


def _settings(**kwargs: object) -> Settings:
    """Construct a Settings with safe defaults that bypass .env loading."""
    defaults: dict[str, object] = {
        "_env_file": None,
        "SECRET_KEY": "test-key-not-empty-1234567890123456",
        "DATABASE_URL": "sqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/0",
    }
    defaults.update(kwargs)
    return Settings(**defaults)  # type: ignore[arg-type]


class TestEnvironment:
    def test_development_value(self) -> None:
        assert Environment.DEVELOPMENT.value == "development"

    def test_testing_value(self) -> None:
        assert Environment.TESTING.value == "testing"

    def test_production_value(self) -> None:
        assert Environment.PRODUCTION.value == "production"

    def test_from_string_valid(self) -> None:
        assert Environment.from_string("development") is Environment.DEVELOPMENT
        assert Environment.from_string("production") is Environment.PRODUCTION
        assert Environment.from_string("testing") is Environment.TESTING

    def test_from_string_case_insensitive(self) -> None:
        assert Environment.from_string("DEVELOPMENT") is Environment.DEVELOPMENT
        assert Environment.from_string("Production") is Environment.PRODUCTION

    def test_from_string_invalid_defaults_to_development(self) -> None:
        assert Environment.from_string("staging") is Environment.DEVELOPMENT

    def test_is_development(self) -> None:
        assert Environment.DEVELOPMENT.is_development
        assert not Environment.PRODUCTION.is_development

    def test_is_testing(self) -> None:
        assert Environment.TESTING.is_testing
        assert not Environment.DEVELOPMENT.is_testing

    def test_is_production(self) -> None:
        assert Environment.PRODUCTION.is_production
        assert not Environment.TESTING.is_production


class TestSettings:
    def test_defaults(self) -> None:
        settings = _settings()
        assert settings.APP_NAME == "resyntha"
        assert settings.APP_VERSION == "0.1.0"
        assert settings.ENVIRONMENT is Environment.DEVELOPMENT
        assert settings.DEBUG is False
        assert settings.LOG_FORMAT == "console"
        assert settings.LOG_LEVEL == "INFO"

    def test_environment_coercion_from_string(self) -> None:
        settings = _settings(ENVIRONMENT="production")
        assert settings.ENVIRONMENT is Environment.PRODUCTION

    def test_debug_coercion(self) -> None:
        settings = _settings(DEBUG="true")
        assert settings.DEBUG is True

    def test_cors_origin_list(self) -> None:
        settings = _settings(CORS_ORIGINS="http://a.com,http://b.com")
        assert settings.cors_origin_list == ["http://a.com", "http://b.com"]

    def test_cors_origin_list_handles_empty(self) -> None:
        settings = _settings(CORS_ORIGINS="")
        assert settings.cors_origin_list == []

    def test_trusted_host_list(self) -> None:
        settings = _settings(TRUSTED_HOSTS="api.example.com,localhost")
        assert settings.trusted_host_list == ["api.example.com", "localhost"]

    def test_trusted_host_list_empty(self) -> None:
        settings = _settings(TRUSTED_HOSTS="")
        assert settings.trusted_host_list == []

    def test_log_format_coercion(self) -> None:
        settings = _settings(LOG_FORMAT="JSON")
        assert settings.LOG_FORMAT == "json"

    def test_log_format_invalid_defaults_to_console(self) -> None:
        settings = _settings(LOG_FORMAT="xml")
        assert settings.LOG_FORMAT == "console"

    def test_log_level_coercion(self) -> None:
        settings = _settings(LOG_LEVEL="debug")
        assert settings.LOG_LEVEL == "DEBUG"

    def test_log_level_invalid_defaults_to_info(self) -> None:
        settings = _settings(LOG_LEVEL="trace")
        assert settings.LOG_LEVEL == "INFO"

    def test_build_time_is_set(self) -> None:
        assert BUILD_TIME != ""

    def test_python_version_is_set(self) -> None:
        assert PYTHON_VERSION != ""


class TestSettingsValidation:
    def test_valid_development_config_passes(self) -> None:
        settings = _settings()
        validate_settings(settings)

    def test_missing_database_url_raises(self) -> None:
        settings = _settings(DATABASE_URL="")
        with pytest.raises(ConfigurationError, match="DATABASE_URL"):
            validate_settings(settings)

    def test_invalid_database_scheme_raises(self) -> None:
        settings = _settings(DATABASE_URL="mysql://localhost:3306/db")
        with pytest.raises(ConfigurationError, match="DATABASE_URL"):
            validate_settings(settings)

    def test_missing_redis_url_allowed_non_production(self) -> None:
        settings = _settings(REDIS_URL="")
        # Empty Redis URL is allowed outside production — services gracefully degrade
        validate_settings(settings)

    def test_missing_redis_url_raises_in_production(self) -> None:
        settings = _settings(ENVIRONMENT="production", REDIS_URL="")
        with pytest.raises(ConfigurationError, match="REDIS_URL"):
            validate_settings(settings)

    def test_invalid_redis_scheme_raises(self) -> None:
        settings = _settings(REDIS_URL="mongodb://localhost:27017")
        with pytest.raises(ConfigurationError, match="REDIS_URL"):
            validate_settings(settings)

    def test_empty_secret_key_in_production_raises(self) -> None:
        settings = _settings(ENVIRONMENT="production", SECRET_KEY="")
        with pytest.raises(ConfigurationError, match="SECRET_KEY"):
            validate_settings(settings)

    def test_default_secret_key_in_production_raises(self) -> None:
        settings = _settings(
            ENVIRONMENT="production",
            SECRET_KEY="change-me-to-a-random-secret-key",
        )
        with pytest.raises(ConfigurationError, match="SECRET_KEY"):
            validate_settings(settings)

    def test_short_secret_key_in_production_raises(self) -> None:
        settings = _settings(ENVIRONMENT="production", SECRET_KEY="short")
        with pytest.raises(ConfigurationError, match="SECRET_KEY"):
            validate_settings(settings)

    def test_missing_groq_key_in_production_raises(self) -> None:
        settings = _settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-32-char-secret-key-for-production!",
            DATABASE_URL="postgresql+psycopg://localhost:5432/db",
            LLM_PROVIDER="groq",
            GROQ_API_KEY="",
        )
        with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
            validate_settings(settings)

    def test_empty_trusted_hosts_in_production_raises(self) -> None:
        settings = _settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-32-char-secret-key-for-production!",
            DATABASE_URL="postgresql+psycopg://localhost:5432/db",
            TRUSTED_HOSTS="",
        )
        with pytest.raises(ConfigurationError, match="TRUSTED_HOSTS"):
            validate_settings(settings)

    def test_wildcard_trusted_hosts_in_production_raises(self) -> None:
        settings = _settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-32-char-secret-key-for-production!",
            DATABASE_URL="postgresql+psycopg://localhost:5432/db",
            TRUSTED_HOSTS="*",
        )
        with pytest.raises(ConfigurationError, match="TRUSTED_HOSTS"):
            validate_settings(settings)

    def test_unsupported_embedding_provider_raises(self) -> None:
        settings = _settings(EMBEDDING_PROVIDER="openai")
        with pytest.raises(ConfigurationError, match="EMBEDDING_PROVIDER"):
            validate_settings(settings)

    def test_valid_production_config_passes(self) -> None:
        settings = _settings(
            ENVIRONMENT="production",
            SECRET_KEY="a-32-char-secret-key-for-production!",
            DATABASE_URL="postgresql+psycopg://user:pass@host:5432/db",
            REDIS_URL="rediss://default:pass@host:6379",
            TRUSTED_HOSTS="api.example.com",
            GROQ_API_KEY="gsk_valid_key_for_production",
            CORS_ORIGINS="https://app.example.com",
        )
        validate_settings(settings)

    def test_sqlite_allowed_in_development(self) -> None:
        settings = _settings()
        validate_settings(settings)

    def test_database_url_without_scheme_raises(self) -> None:
        settings = _settings(DATABASE_URL="localhost:5432/db")
        with pytest.raises(ConfigurationError, match="DATABASE_URL"):
            validate_settings(settings)

    def test_database_url_without_host_raises(self) -> None:
        settings = _settings(DATABASE_URL="postgresql://")
        with pytest.raises(ConfigurationError, match="DATABASE_URL"):
            validate_settings(settings)


class TestParseRetrievalProviders:
    def test_parse_comma_separated(self) -> None:
        from app.config.settings import parse_retrieval_providers

        result = parse_retrieval_providers("semantic_scholar,arxiv")
        assert result == ["semantic_scholar", "arxiv"]

    def test_parse_strips_whitespace(self) -> None:
        from app.config.settings import parse_retrieval_providers

        result = parse_retrieval_providers("  semantic_scholar , arxiv  ")
        assert result == ["semantic_scholar", "arxiv"]

    def test_parse_empty_returns_empty_list(self) -> None:
        from app.config.settings import parse_retrieval_providers

        result = parse_retrieval_providers("")
        assert result == []

    def test_parse_unknown_provider_logs_warning(self, capsys: pytest.CaptureFixture[str]) -> None:
        from app.config.settings import parse_retrieval_providers

        result = parse_retrieval_providers("unknown_provider")
        assert result == ["unknown_provider"]
        captured = capsys.readouterr()
        assert "unknown_retrieval_provider" in captured.out
