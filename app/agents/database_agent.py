from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.data_cities import MAJOR_RUSSIAN_CITIES
from app.providers.local_provider import LocalCuratedProvider
from app.repositories.repositories import PlaceRepository


class DatabasePopulationAgent:
    """Keeps the searchable local place base warm in PostgreSQL."""

    def __init__(self, session: AsyncSession, provider: LocalCuratedProvider | None = None) -> None:
        self.session = session
        self.provider = provider or LocalCuratedProvider()

    async def populate_initial_cities(self) -> int:
        places = []
        for city in MAJOR_RUSSIAN_CITIES:
            for category in ("food", "fun", "relax"):
                places.extend(await self.provider.search(category=category, city=city.name))
        persisted = await PlaceRepository(self.session).upsert_many(places)
        return len(persisted)

    async def populate_city(self, city: str) -> int:
        places = []
        for category in ("food", "fun", "relax"):
            places.extend(await self.provider.search(category=category, city=city))
        persisted = await PlaceRepository(self.session).upsert_many(places)
        return len(persisted)
