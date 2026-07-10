"""Rate-limit service with Redis-backed counters and in-memory fallback.

Supports sliding-window rate limiting using Redis ``INCR`` + ``EXPIRE``
for the distributed backend and a per-client deque of timestamps for
the local in-memory backend.  When Redis is unavailable the service
gracefully degrades to the local backend.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import redis.asyncio as aioredis

from app.config import get_settings
from app.infrastructure.redis.client import get_redis
from app.observability.logger import get_logger
from app.rate_limit.models import RateLimitResult

logger = get_logger(__name__)


@dataclass
class _WindowEntry:
    timestamp: float = 0.0
    count: int = 0


class InMemoryBackend:
    """Thread-safe in-memory sliding-window rate limiter.

    Uses a dict-of-deques keyed by ``client_id``.  Stale entries are
    pruned on every ``check()`` call so the structure does not grow
    unbounded.
    """

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)

    async def check(self, key: str, limit: int, window: int) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - window
        timestamps = self._windows[key]

        # Prune expired entries
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        if len(timestamps) >= limit:
            oldest = timestamps[0]
            reset_at = oldest + window
            retry_after = max(0, int(reset_at - now))
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=retry_after,
            )

        timestamps.append(now)
        remaining = limit - len(timestamps)
        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_at=now + window,
        )


class RedisBackend:
    """Redis-backed sliding-window rate limiter.

    Key format: ``rate_limit:{client_id}:{window_start}``
    Uses ``INCR`` + ``EXPIRE`` for atomic counting.

    When Redis is unavailable it falls back to an internal
    ``InMemoryBackend`` (created once and reused across calls).
    """

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        self._redis = redis
        self._memory_fallback: InMemoryBackend | None = None

    def _get_memory_fallback(self) -> InMemoryBackend:
        if self._memory_fallback is None:
            self._memory_fallback = InMemoryBackend()
        return self._memory_fallback

    async def _client(self) -> aioredis.Redis | None:
        if self._redis is not None:
            return self._redis
        try:
            return await get_redis()
        except Exception:
            return None

    async def check(self, key: str, limit: int, window: int) -> RateLimitResult:
        client = await self._client()
        if client is None:
            logger.warning("rate_limit_redis_unavailable_falling_back_to_memory")
            return await self._get_memory_fallback().check(key, limit, window)

        now = time.time()
        window_key = int(now / window)
        redis_key = f"rate_limit:{key}:{window_key}"

        try:
            count = await client.incr(redis_key)
            if count == 1:
                await client.expire(redis_key, window)

            reset_at = ((window_key + 1) * window) + 0.001
            remaining = max(0, limit - count)
            retry_after = max(0, int(reset_at - now))

            return RateLimitResult(
                allowed=count <= limit,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=0 if count <= limit else retry_after,
            )
        except Exception:
            logger.warning("rate_limit_redis_error_falling_back_to_memory")
            return await self._get_memory_fallback().check(key, limit, window)


class RateLimitService:
    """Top-level rate-limit service with automatic backend selection.

    Uses the backend specified by configuration (or in-memory fallback
    when Redis is unavailable).
    """

    def __init__(
        self,
        backend: str | None = None,
        redis: aioredis.Redis | None = None,
    ) -> None:
        settings = get_settings()
        self._enabled = settings.RATE_LIMIT_ENABLED
        chosen = backend or settings.RATE_LIMIT_BACKEND
        if chosen == "memory":
            self._backend: InMemoryBackend | RedisBackend = InMemoryBackend()
        else:
            self._backend = RedisBackend(redis=redis)

    async def check(self, key: str, limit: int, window: int) -> RateLimitResult:
        if not self._enabled:
            return RateLimitResult(allowed=True, limit=limit)
        start = time.monotonic()
        result = await self._backend.check(key, limit, window)
        decision_ms = int((time.monotonic() - start) * 1000)
        logger.info(
            "rate_limit_check",
            rate_limit_key=key,
            limit=limit,
            remaining=result.remaining,
            reset_at=result.reset_at,
            blocked=not result.allowed,
            decision_time_ms=decision_ms,
        )
        return result
