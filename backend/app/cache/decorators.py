"""Caching decorators.

``@cached`` wraps a callable to transparently store and return cached
results.  ``@invalidate`` removes specific cache keys after the wrapped
function completes.

Both decorators work with async and sync functions.  For sync functions
the cache operation is still dispatched via the async ``CacheService``;
the caller is responsible for running in an appropriate event loop.
"""

from __future__ import annotations

import functools
import inspect
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.cache.keys import all_investigation_pattern
from app.cache.service import CacheService
from app.config import get_settings
from app.observability.logger import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Module-level cache service (lazily created).
_cache_service: CacheService | None = None


def _cache() -> CacheService:
    global _cache_service  # noqa: PLW0603
    if _cache_service is None:
        settings = get_settings()
        _cache_service = CacheService() if settings.CACHE_ENABLED else CacheService(redis=None)  # type: ignore[arg-type]
    return _cache_service


def cached(
    key: str,
    ttl: int = 300,
) -> Callable[[F], F]:
    """Decorate an async function so its return value is cached.

    Parameters
    ----------
    key:
        Cache key (static, or you may pass a format-string that gets
        ``.format()``-ed with the decorated function's keyword args).
    ttl:
        Time-to-live in seconds.

    Usage::

        @cached("investigation:{investigation_id}", ttl=300)
        async def get_investigation(investigation_id: str) -> ...:
            ...

    The cache is transparently checked on every call.  When the cache
    is unavailable (e.g. Redis down) the underlying function runs
    without caching — no exception is raised.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            resolved_key = key.format(**kwargs) if "{" in key else key
            cache = _cache()
            cached_value = await cache.get(resolved_key)
            if cached_value is not None:
                logger.info(
                    "cache_hit",
                    cache_key=resolved_key,
                )
                return cached_value
            logger.info(
                "cache_miss",
                cache_key=resolved_key,
            )
            start = time.monotonic()
            result = await func(*args, **kwargs)
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            await cache.set(resolved_key, result, ttl=ttl)
            logger.info(
                "cache_set",
                cache_key=resolved_key,
                cache_duration_ms=duration_ms,
            )
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return async_wrapper  # type: ignore[return-value]

    return decorator


def invalidate(
    *keys: str,
) -> Callable[[F], F]:
    """Decorate a function so that the given cache keys are removed on
    successful completion (i.e. when no exception is raised).

    Each *key* may contain ``{keyword}`` placeholders that are resolved
    from the decorated function's keyword arguments.

    Usage::

        @invalidate("graph:{investigation_id}", "landscape:{investigation_id}")
        async def rerun_investigation(investigation_id: str) -> ...:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            cache = _cache()
            for raw_key in keys:
                resolved = raw_key.format(**kwargs) if "{" in raw_key else raw_key
                await cache.delete(resolved)
                logger.info(
                    "cache_invalidated",
                    cache_key=resolved,
                )
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return async_wrapper  # type: ignore[return-value]

    return decorator


def invalidate_investigation(
    investigation_id_key: str = "investigation_id",
) -> Callable[[F], F]:
    """Convenience decorator that invalidates all investigation-related
    cache keys on successful completion of the wrapped function.

    This is equivalent to passing every single key pattern to
    ``@invalidate`` but is more resilient to new key types being added
    later since it uses ``delete_pattern`` with a wildcard.

    Usage::

        @invalidate_investigation()
        async def rerun_investigation(investigation_id: str) -> ...:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            inv_id = kwargs.get(investigation_id_key)
            result = await func(*args, **kwargs)
            if inv_id is not None:
                cache = _cache()
                pattern = all_investigation_pattern(str(inv_id))
                count = await cache.delete_pattern(pattern)
                logger.info(
                    "cache_bulk_invalidated",
                    pattern=pattern,
                    deleted_count=count,
                )
            return result

        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return async_wrapper  # type: ignore[return-value]

    return decorator
