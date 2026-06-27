"""Redis connectivity check.

Provides ``check_redis`` used by the ``/ready`` health endpoint.
"""

from app.infrastructure.redis.client import get_redis


async def check_redis() -> bool:
    """Return ``True`` if Redis is reachable, ``False`` otherwise.

    Sends a ``PING`` command to verify the connection.  If Redis is
    not configured or unreachable the exception is swallowed and
    ``False`` is returned.
    """
    try:
        redis = await get_redis()
        if redis is None:
            return False
        await redis.ping()
        return True
    except Exception:  # noqa: BLE001
        return False
