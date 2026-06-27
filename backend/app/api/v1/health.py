"""Health-check endpoints for the Resyntha API.

Provides ``/health`` (always healthy), ``/live`` (always alive), and
``/ready`` (reflects database and Redis reachability).
"""

import asyncio

from fastapi import APIRouter, Response, status

from app.database.health import check_database
from app.infrastructure.redis.health import check_redis
from app.observability.logger import get_logger

router = APIRouter(tags=["health"])
logger = get_logger(__name__)


@router.get("/health")
async def health() -> dict[str, str]:
    """Return a static healthy response."""
    logger.info("health_check")
    return {"status": "healthy"}


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Return a static alive response."""
    logger.info("liveness_check")
    return {"status": "alive"}


@router.get("/ready")
async def readiness(response: Response) -> dict[str, bool | str]:
    """Return readiness status for database and Redis.

    Returns HTTP 200 when all dependencies are reachable, HTTP 503
    otherwise.
    """
    logger.info("readiness_check")
    db_ok = await asyncio.to_thread(check_database)
    redis_ok = await check_redis()

    if db_ok and redis_ok:
        return {
            "status": "ready",
            "database": True,
            "redis": True,
        }

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "not_ready",
        "database": db_ok,
        "redis": redis_ok,
    }
