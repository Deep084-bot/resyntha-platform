from app.infrastructure.redis.client import get_redis


async def check_redis() -> bool:
    try:
        redis = await get_redis()

        if redis is None:
            return False

        await redis.ping()
        return True

    except Exception:
        return False
