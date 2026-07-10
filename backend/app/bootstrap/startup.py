"""Application startup initialization.

Initializes infrastructure services in the correct order and logs
startup diagnostics.  Each service is initialized only if the
corresponding configuration is present.
"""

from __future__ import annotations

import sys

from app.config import Environment, Settings, get_settings, validate_settings
from app.config.constants import BUILD_TIME, GIT_COMMIT, PYTHON_VERSION
from app.infrastructure.redis import initialize_redis
from app.observability.logger import get_logger

logger = get_logger(__name__)


def _extract_db_provider(url: str) -> str:
    if not url:
        return "none"
    if "postgresql" in url or "psycopg" in url:
        return "postgresql"
    if "sqlite" in url:
        return "sqlite"
    return url.split("://")[0] if "://" in url else "unknown"


def _extract_redis_provider(url: str) -> str:
    if not url:
        return "none"
    if "rediss://" in url:
        return "redis+tls"
    if "redis://" in url:
        return "redis"
    return "unknown"


async def initialize_services(settings: Settings | None = None) -> None:
    """Initialize all infrastructure services.

    Runs configuration validation, then initializes Redis and any
    other services that need eager startup.
    """
    if settings is None:
        settings = get_settings()

    validate_settings(settings)

    logger.info(
        "application_startup",
        environment=settings.ENVIRONMENT.value,
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        python_version=PYTHON_VERSION,
        database_provider=_extract_db_provider(settings.DATABASE_URL),
        redis_provider=_extract_redis_provider(settings.REDIS_URL),
        llm_provider=settings.LLM_PROVIDER,
        embedding_provider=settings.EMBEDDING_PROVIDER,
        debug=settings.DEBUG,
        build_time=BUILD_TIME,
        git_commit=GIT_COMMIT,
    )

    if settings.REDIS_URL:
        redis_client = await initialize_redis()
        if redis_client is not None:
            logger.info("redis_initialized")
        else:
            logger.warning("redis_initialization_failed")
    else:
        logger.info("redis_disabled_no_url")

    worker_status = "enabled" if settings.REDIS_URL else "disabled"
    logger.info("worker_status", status=worker_status)

    if settings.ENVIRONMENT.is_production:
        logger.info("production_mode_active")
    elif settings.ENVIRONMENT.is_testing:
        logger.info("testing_mode_active")
    else:
        logger.info("development_mode_active")

    logger.info("startup_complete")
