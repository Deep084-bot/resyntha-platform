"""FastAPI application lifespan handler.

Moved from ``main.py`` to keep the entry point focused on wiring.
The lifespan configures structured logging, eagerly initialises the
Redis client, and performs a clean shutdown.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.redis import close_redis, initialize_redis
from app.observability.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager.

    Startup (before yield):
      - Configure structlog.
      - Eagerly initialise the Redis client.
      - Log the startup event.

    Shutdown (after yield):
      - Close the Redis connection pool.
      - Log the shutdown event.
    """
    configure_logging()
    settings = get_settings()

    logger.info("application_startup", env=settings.ENVIRONMENT)

    if settings.REDIS_URL:
        await initialize_redis()
        logger.info("redis_initialized")

    yield

    if settings.REDIS_URL:
        await close_redis()
        logger.info("redis_disconnected")

    logger.info("application_shutdown")
