"""Application shutdown cleanup.

Gracefully releases infrastructure resources in reverse order of
initialization.
"""

from __future__ import annotations

from app.config import get_settings
from app.infrastructure.redis import close_redis
from app.observability.logger import get_logger

logger = get_logger(__name__)


async def shutdown_services() -> None:
    """Release all infrastructure resources."""
    settings = get_settings()

    if settings.REDIS_URL:
        await close_redis()
        logger.info("redis_disconnected")

    logger.info(
        "application_shutdown",
        environment=settings.ENVIRONMENT.value,
        app_name=settings.APP_NAME,
    )
