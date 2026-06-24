from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.services.tariffs import DEFAULT_DAILY_REQUEST_LIMIT

if TYPE_CHECKING:
    from redis.asyncio import Redis
else:
    Redis = Any


class RateLimitService:
    def __init__(self, redis: Redis | None, daily_limit: int = DEFAULT_DAILY_REQUEST_LIMIT) -> None:
        self.redis = redis
        self.daily_limit = daily_limit

    async def check_and_increment(self, telegram_id: int, action: str = "search") -> tuple[bool, int, int]:
        if self.redis is None:
            return True, 0, self.daily_limit
        key = f"rate:{action}:{telegram_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 86_400)
        return current <= self.daily_limit, max(self.daily_limit - current, 0), self.daily_limit
