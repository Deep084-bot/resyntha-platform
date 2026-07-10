"""Caching layer — CacheService, decorators, and key management.

Usage::

    from app.cache import CacheService, cached, invalidate, invalidate_investigation
    from app.cache.keys import investigation_key, graph_key
"""

from app.cache.decorators import cached, invalidate, invalidate_investigation
from app.cache.service import CacheService

__all__ = [
    "CacheService",
    "cached",
    "invalidate",
    "invalidate_investigation",
]
