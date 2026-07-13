"""CacheService — an abstraction over Redis that gracefully degrades.

Every method is safe to call when Redis is unavailable: failures are
logged and the operation is skipped so the application continues to
work without caching.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

import pydantic
import redis.asyncio as aioredis

from app.infrastructure.redis.client import get_redis
from app.observability.logger import get_logger

logger = get_logger(__name__)

CacheFallback = Callable[[], Awaitable[Any]]


class CacheService:
    """Production cache layer with graceful degradation.

    Usage::

        cache = CacheService()
        result = await cache.get("my_key")
        if result is None:
            result = await compute_expensive()
            await cache.set("my_key", result, ttl=300)
    """

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        self._redis = redis

    async def _client(self) -> aioredis.Redis | None:
        if self._redis is not None:
            return self._redis
        try:
            return await get_redis()
        except Exception:
            return None

    # ── Public API ──────────────────────────────────────────────────

    async def get(self, key: str) -> Any | None:
        """Return the deserialized value for *key*, or ``None``."""
        client = await self._client()
        if client is None:
            return None
        try:
            raw = await client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.warning("cache_get_failed", key=key)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Serialize *value* as JSON and store it with the given *ttl*.

        Pydantic ``BaseModel`` instances are automatically converted to
        dicts via ``model_dump()`` before serialization.
        """
        client = await self._client()
        if client is None:
            return False
        try:
            if isinstance(value, pydantic.BaseModel):
                raw = value.model_dump_json()
            else:
                raw = json.dumps(value, default=str)
            await client.setex(key, ttl, raw)
            return True
        except Exception:
            logger.warning("cache_set_failed", key=key)
            return False

    async def delete(self, key: str) -> bool:
        """Remove a single key from the cache."""
        client = await self._client()
        if client is None:
            return False
        try:
            await client.delete(key)
            return True
        except Exception:
            logger.warning("cache_delete_failed", key=key)
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Remove all keys matching the glob *pattern*.

        Returns the number of keys deleted, or 0 on failure.

        Uses ``SCAN`` internally so it is safe for production use.
        """
        client = await self._client()
        if client is None:
            return 0
        try:
            cursor = 0
            keys_to_delete: list[str] = []
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern, count=100)
                keys_to_delete.extend(keys)
                if cursor == 0:
                    break
            if keys_to_delete:
                await client.delete(*keys_to_delete)
            return len(keys_to_delete)
        except Exception:
            logger.warning("cache_delete_pattern_failed", pattern=pattern)
            return 0

    async def exists(self, key: str) -> bool:
        """Check whether *key* exists in the cache."""
        client = await self._client()
        if client is None:
            return False
        try:
            return bool(await client.exists(key))
        except Exception:
            return False

    # ── Convenience: get-or-compute ─────────────────────────────────

    async def get_or_compute(
        self,
        key: str,
        fallback: CacheFallback,
        ttl: int = 300,
    ) -> tuple[Any, bool]:
        """Return ``(value, from_cache)``.

        If *key* exists in the cache the cached value is returned with
        ``from_cache=True``.  Otherwise *fallback* is called, the result
        is stored, and ``(result, False)`` is returned.

        Example::

            result, cached = await cache.get_or_compute(
                key="my_key",
                fallback=compute_expensive,
                ttl=300,
            )
            logger.info("result", cache_hit=cached)
        """
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value, True

        value = await fallback()
        await self.set(key, value, ttl=ttl)
        return value, False

    # ── Health / diagnostics ────────────────────────────────────────

    async def ping(self) -> bool:
        """Return ``True`` when Redis is reachable."""
        client = await self._client()
        if client is None:
            return False
        try:
            return bool(await client.ping())
        except Exception:
            return False
