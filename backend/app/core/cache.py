"""Redis cache layer using redis-py async client (compatible with Python 3.11+)."""
import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logging import logger

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> None:
    try:
        redis = await get_redis()
        await redis.setex(key, ttl, json.dumps(value))
    except Exception as exc:
        logger.warning("cache_set_failed", key=key, error=str(exc))


async def cache_get(key: str) -> Any | None:
    try:
        redis = await get_redis()
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning("cache_get_failed", key=key, error=str(exc))
        return None


async def cache_delete(key: str) -> None:
    try:
        redis = await get_redis()
        await redis.delete(key)
    except Exception as exc:
        logger.warning("cache_delete_failed", key=key, error=str(exc))


async def cache_invalidate_prefix(prefix: str) -> None:
    try:
        redis = await get_redis()
        keys = await redis.keys(f"{prefix}*")
        if keys:
            await redis.delete(*keys)
    except Exception as exc:
        logger.warning("cache_invalidate_failed", prefix=prefix, error=str(exc))
