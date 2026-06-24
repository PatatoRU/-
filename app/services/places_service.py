from __future__ import annotations

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.osm_provider import OSMProvider
from app.providers.provider_base import PlacesProvider
from app.repositories.repositories import PlaceRepository
from app.schemas.place import PlaceDTO
from app.services.redis_service import RedisService


class PlacesService:
    """Search use-cases for food, entertainment, leisure, and nearby places."""

    def __init__(
        self,
        session: AsyncSession | None = None,
        redis: Redis | None = None,
        providers: list[PlacesProvider] | None = None,
    ) -> None:
        self.session = session
        self.cache = RedisService(redis)
        self.providers = providers or [OSMProvider()]

    async def search_food(self, city: str) -> list[PlaceDTO]:
        return await self._search("food", city=city)

    async def search_fun(self, city: str) -> list[PlaceDTO]:
        return await self._search("fun", city=city)

    async def search_relax(self, city: str) -> list[PlaceDTO]:
        return await self._search("relax", city=city)

    async def search_nearby(self, lat: float, lon: float) -> list[PlaceDTO]:
        return await self._search("nearby", lat=lat, lon=lon)

    async def _search(
        self,
        category: str,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> list[PlaceDTO]:
        cache_key = f"places:{category}:{city or '-'}:{lat or '-'}:{lon or '-'}"
        cached = await self.cache.get_json(cache_key)
        if cached:
            return [PlaceDTO(**place) for place in cached]

        places: list[PlaceDTO] = []
        for provider in self.providers:
            provider_places = await provider.search(category=category, city=city, lat=lat, lon=lon)
            places.extend(provider_places)

        if self.session is not None and places:
            await PlaceRepository(self.session).upsert_many(places)

        await self.cache.set_json(cache_key, [place.model_dump() for place in places])
        await self.cache.incr_popular(category if city is None else f"{category}:{city}")
        return places
