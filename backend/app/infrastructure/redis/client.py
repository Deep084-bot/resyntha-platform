"""Redis async client singleton.

Manages a single ``redis.asyncio.Redis`` connection pool for the
application.  The client is created lazily or can be initialised
eagerly via ``initialize_redis()`` during the lifespan startup hook.
"""

import redis.asyncio as aioredis

from app.config import get_settings

_redis: aioredis.Redis | None = None


async def initialize_redis() -> aioredis.Redis | None:
    """Create and store the global Redis client.

    Returns the client, or ``None`` when ``REDIS_URL`` is not
    configured.  Safe to call multiple times — only the first call
    creates a client.
    """
    global _redis  # noqa: PLW0603

    if _redis is not None:
        return _redis

    settings = get_settings()
    if not settings.REDIS_URL:
        return None

    _redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )
    return _redis


async def get_redis() -> aioredis.Redis | None:
    """Return the global Redis client, if initialised."""
    return _redis


async def close_redis() -> None:
    """Close the global Redis client and release its connection pool."""
    global _redis  # noqa: PLW0603

    if _redis is not None:
        await _redis.aclose()
        _redis = None
