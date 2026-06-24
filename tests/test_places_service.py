import pytest

pytest.importorskip("redis")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from app.providers.local_provider import LocalCuratedProvider
from app.services.places_service import PlacesService


@pytest.mark.asyncio
async def test_search_food_returns_places_without_network():
    service = PlacesService(providers=[LocalCuratedProvider()])
    places = await service.search_food("Москва")
    assert places and places[0].category == "food"


@pytest.mark.asyncio
async def test_search_fun_for_each_launch_city_without_network():
    service = PlacesService(providers=[LocalCuratedProvider()])
    for city in ["Москва", "Екатеринбург", "Казань", "Санкт-Петербург", "Новосибирск"]:
        places = await service.search_fun(city)
        assert places, city
        assert all(place.city == city for place in places)
