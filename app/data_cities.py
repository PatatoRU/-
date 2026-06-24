from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    slug: str
    name: str
    lat: float
    lon: float


MAJOR_RUSSIAN_CITIES: tuple[City, ...] = (
    City(slug="moscow", name="Москва", lat=55.7558, lon=37.6173),
    City(slug="spb", name="Санкт-Петербург", lat=59.9343, lon=30.3351),
    City(slug="novosibirsk", name="Новосибирск", lat=55.0084, lon=82.9357),
    City(slug="ekaterinburg", name="Екатеринбург", lat=56.8389, lon=60.6057),
    City(slug="kazan", name="Казань", lat=55.7961, lon=49.1064),
)

CITY_BY_SLUG = {city.slug: city for city in MAJOR_RUSSIAN_CITIES}
CITY_BY_NAME = {city.name.lower(): city for city in MAJOR_RUSSIAN_CITIES}
DEFAULT_CITY = MAJOR_RUSSIAN_CITIES[0]


def get_city_by_name(name: str | None) -> City:
    if not name:
        return DEFAULT_CITY
    return CITY_BY_NAME.get(name.lower(), DEFAULT_CITY)
