import redis.asyncio as redis
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

_redis_client = None

async def get_redis_client() -> redis.Redis | None:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await _redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Redis features will be disabled.")
            _redis_client = None
    return _redis_client

async def close_redis_client():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None