"""Health-check service layer.

Each dependency exposes a check function that returns a
``ComponentHealth`` model.  The readiness endpoint composes these
into an overall status.
"""

from __future__ import annotations

import asyncio
import time

from app.config import get_settings
from app.database.health import check_database as _check_db
from app.infrastructure.redis.health import check_redis as _check_redis
from app.observability.logger import get_logger

from .models import ComponentHealth

logger = get_logger(__name__)

# Start time is set explicitly via ``record_startup_time()`` during the
# application lifespan.  Falls back to import time if not called.
_START_TIME: float | None = None


def record_startup_time() -> None:
    """Record the current monotonic clock as the application start time."""
    global _START_TIME  # noqa: PLW0603
    _START_TIME = time.monotonic()


def get_startup_timestamp() -> float:
    """Return the monotonic clock value recorded at process start."""
    if _START_TIME is None:
        record_startup_time()
    return _START_TIME  # type: ignore[return-value]


def get_uptime() -> str:
    """Return a human-readable uptime string."""
    start = _START_TIME if _START_TIME is not None else time.monotonic()
    elapsed = time.monotonic() - start
    hours, remainder = divmod(int(elapsed), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


async def check_database() -> ComponentHealth:
    """Check PostgreSQL / SQLite connectivity."""
    try:
        ok = await asyncio.to_thread(_check_db)
        if ok:
            return ComponentHealth(status="healthy")
        return ComponentHealth(status="unhealthy", reason="database ping failed")
    except Exception as exc:
        logger.warning("health_database_failure", error=str(exc))
        return ComponentHealth(status="unhealthy", reason=str(exc))


async def check_redis() -> ComponentHealth:
    """Check Redis connectivity."""
    try:
        ok = await _check_redis()
        if ok:
            return ComponentHealth(status="healthy")
        return ComponentHealth(status="unhealthy", reason="redis ping failed")
    except Exception as exc:
        logger.warning("health_redis_failure", error=str(exc))
        return ComponentHealth(status="unhealthy", reason=str(exc))


async def check_llm() -> ComponentHealth:
    """Check LLM provider configuration (no live call)."""
    settings = get_settings()
    provider = settings.LLM_PROVIDER

    if provider == "groq" and not settings.GROQ_API_KEY:
        return ComponentHealth(
            status="unhealthy",
            reason="GROQ_API_KEY is not configured",
        )
    if provider == "openai" and not settings.OPENAI_API_KEY:
        return ComponentHealth(
            status="unhealthy",
            reason="OPENAI_API_KEY is not configured",
        )
    return ComponentHealth(status="configured")


async def check_embedding_provider() -> ComponentHealth:
    """Check embedding provider configuration (no live call)."""
    settings = get_settings()
    provider = settings.EMBEDDING_PROVIDER

    if provider != "local":
        return ComponentHealth(
            status="unhealthy",
            reason=f"embedding provider '{provider}' is not supported",
        )
    return ComponentHealth(status="healthy")


async def check_worker() -> ComponentHealth:
    """Check worker availability by verifying Redis is reachable."""
    settings = get_settings()
    if not settings.REDIS_URL:
        return ComponentHealth(status="disabled", reason="no Redis URL configured")

    redis_ok = await check_redis()
    if redis_ok.status == "healthy":
        return ComponentHealth(status="healthy")
    return ComponentHealth(status="unhealthy", reason="worker depends on Redis")
