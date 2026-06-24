import asyncio

from app.data_cities import MAJOR_RUSSIAN_CITIES
from app.services.events_service import EventService


def test_events_exist_for_all_start_cities():
    async def run():
        service = EventService()
        for city in MAJOR_RUSSIAN_CITIES:
            events = await service.list_events(city.name)
            assert events, city.name
            assert all(event.city == city.name for event in events)
            assert all(event.lat is not None and event.lon is not None for event in events)
    asyncio.run(run())


def test_free_and_tonight_event_filters():
    async def run():
        service = EventService()
        free_events = await service.list_events("Казань", category="free")
        tonight_events = await service.list_events("Казань", category="tonight")
        assert free_events
        assert tonight_events
    asyncio.run(run())
