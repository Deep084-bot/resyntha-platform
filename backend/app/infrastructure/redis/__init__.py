"""Redis infrastructure package.

Provides a singleton Redis client, a factory function, and a
connectivity check.  No caching or queue logic lives here — those
belong in higher-level modules.
"""

from app.infrastructure.redis.client import close_redis, get_redis, initialize_redis
from app.infrastructure.redis.health import check_redis

__all__ = [
    "close_redis",
    "get_redis",
    "initialize_redis",
    "check_redis",
]
