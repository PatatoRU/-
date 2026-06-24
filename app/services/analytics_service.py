from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

logger = logging.getLogger("app")

if TYPE_CHECKING:
    from redis.asyncio import Redis
else:
    Redis = Any


class AnalyticsService:
    """Redis-backed lightweight analytics for MVP metrics and CTR counters."""

    def __init__(self, redis: Redis | None) -> None:
        self.redis = redis

    async def track(self, event: str, **dimensions: str | int | float | None) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.incr(f"analytics:event:{event}")
            for key, value in dimensions.items():
                if value is not None:
                    await self.redis.zincrby(f"analytics:{event}:{key}", 1, str(value))
        except Exception as exc:
            logger.warning("analytics_write_failed event=%s error=%s", event, exc)

    async def snapshot(self) -> dict[str, int]:
        if self.redis is None:
            return {}
        try:
            keys = await self.redis.keys("analytics:event:*")
            result: dict[str, int] = {}
            for key in keys:
                name = str(key).split(":")[-1]
                result[name] = int(await self.redis.get(key) or 0)
            return result
        except Exception as exc:
            logger.warning("analytics_snapshot_failed error=%s", exc)
            return {}
