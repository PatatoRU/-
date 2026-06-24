import asyncio

from app.services.analytics_service import AnalyticsService


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.zsets = {}

    async def incr(self, key):
        self.values[key] = self.values.get(key, 0) + 1

    async def zincrby(self, key, amount, member):
        self.zsets[(key, member)] = self.zsets.get((key, member), 0) + amount

    async def keys(self, pattern):
        assert pattern == "analytics:event:*"
        return list(self.values)

    async def get(self, key):
        return self.values.get(key)


def test_analytics_tracks_event_and_dimensions():
    async def run():
        redis = FakeRedis()
        service = AnalyticsService(redis)
        await service.track("search", city="Москва", category="food")
        assert await service.snapshot() == {"search": 1}
        assert redis.zsets[("analytics:search:city", "Москва")] == 1
        assert redis.zsets[("analytics:search:category", "food")] == 1
    asyncio.run(run())
