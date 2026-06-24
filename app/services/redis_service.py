from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger

logger = get_logger("app")


class RedisService:
    """Small Redis adapter used for cache, sessions, and popular-search counters."""

    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    async def get_json(self, key: str) -> Any | None:
        if self.redis is None:
            return None
        try:
            value = await self.redis.get(key)
            return json.loads(value) if value else None
        except (RedisError, json.JSONDecodeError) as exc:
            logger.warning("redis_cache_read_failed", key=key, error=str(exc))
            return None

    async def set_json(self, key: str, value: Any, ttl: int = 600) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        except RedisError as exc:
            logger.warning("redis_cache_write_failed", key=key, error=str(exc))

    async def incr_popular(self, query: str) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.zincrby("popular_searches", 1, query)
        except RedisError as exc:
            logger.warning("redis_popular_increment_failed", query=query, error=str(exc))

    async def set_session_value(self, telegram_id: int, key: str, value: str, ttl: int = 86_400) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.hset(f"session:{telegram_id}", key, value)
            await self.redis.expire(f"session:{telegram_id}", ttl)
        except RedisError as exc:
            logger.warning("redis_session_write_failed", telegram_id=telegram_id, error=str(exc))

    async def get_session_value(self, telegram_id: int, key: str) -> str | None:
        if self.redis is None:
            return None
        try:
            value = await self.redis.hget(f"session:{telegram_id}", key)
            return str(value) if value is not None else None
        except RedisError as exc:
            logger.warning("redis_session_read_failed", telegram_id=telegram_id, error=str(exc))
            return None

    async def clear_session_value(self, telegram_id: int, key: str) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.hdel(f"session:{telegram_id}", key)
        except RedisError as exc:
            logger.warning("redis_session_clear_failed", telegram_id=telegram_id, error=str(exc))
