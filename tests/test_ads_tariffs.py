from app.services.tariffs import AD_TARIFFS


def test_ad_tariffs_include_free_and_two_paid_plans():
    assert set(AD_TARIFFS) == {"free", "boost", "premium"}
    assert AD_TARIFFS["free"].stars == 0
    assert AD_TARIFFS["boost"].stars > 0
    assert AD_TARIFFS["premium"].stars > AD_TARIFFS["boost"].stars
    assert AD_TARIFFS["premium"].priority > AD_TARIFFS["boost"].priority > AD_TARIFFS["free"].priority

import asyncio

from app.services.rate_limit_service import RateLimitService


class FakeRedis:
    def __init__(self) -> None:
        self.values = {}
        self.expirations = {}

    async def incr(self, key: str) -> int:
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    async def expire(self, key: str, ttl: int) -> None:
        self.expirations[key] = ttl


def test_rate_limit_service_blocks_after_daily_limit():
    async def scenario():
        redis = FakeRedis()
        limiter = RateLimitService(redis, daily_limit=2)
        assert await limiter.check_and_increment(123) == (True, 1, 2)
        assert await limiter.check_and_increment(123) == (True, 0, 2)
        assert await limiter.check_and_increment(123) == (False, 0, 2)

    asyncio.run(scenario())
