from __future__ import annotations

import html

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.data_cities import get_city_by_name
from app.providers.local_provider import LocalCuratedProvider
from app.providers.provider_base import PlacesProvider
from app.schemas.place import PlaceDTO

logger = get_logger("app")

CATEGORY_QUERIES = {
    "food": "restaurants cafes",
    "fun": "events museums theatres entertainment",
    "relax": "parks gardens viewpoints",
    "nearby": "restaurants cafes parks museums",
}


class OSMProvider(PlacesProvider):
    """OpenStreetMap provider backed by Nominatim with an offline curated fallback."""

    name = "osm_nominatim"

    def __init__(self, fallback_provider: PlacesProvider | None = None) -> None:
        self.settings = get_settings()
        self.fallback_provider = fallback_provider or LocalCuratedProvider()

    async def search(
        self,
        category: str,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> list[PlaceDTO]:
        try:
            places = await self._search_nominatim(category=category, city=city, lat=lat, lon=lon)
        except httpx.HTTPError as exc:
            logger.warning("osm_nominatim_failed", category=category, city=city, error=str(exc))
            places = []

        if places:
            return places
        return await self.fallback_provider.search(category=category, city=city, lat=lat, lon=lon)

    async def _search_nominatim(
        self,
        category: str,
        city: str | None,
        lat: float | None,
        lon: float | None,
    ) -> list[PlaceDTO]:
        selected_city = get_city_by_name(city)
        query_category = CATEGORY_QUERIES.get(category, CATEGORY_QUERIES["relax"])
        query = f"{query_category} {selected_city.name} Russia"
        params: dict[str, str | int | float] = {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "extratags": 1,
            "limit": self.settings.osm_result_limit,
            "accept-language": "ru",
        }
        if lat is not None and lon is not None:
            delta = 0.08
            params["viewbox"] = f"{lon - delta},{lat + delta},{lon + delta},{lat - delta}"
            params["bounded"] = 1

        headers = {"User-Agent": self.settings.osm_user_agent}
        async with httpx.AsyncClient(timeout=self.settings.osm_timeout_seconds, headers=headers) as client:
            response = await client.get(str(self.settings.osm_nominatim_url), params=params)
            response.raise_for_status()
            payload = response.json()

        places: list[PlaceDTO] = []
        for item in payload:
            place = self._parse_place(item=item, category=category, city=selected_city.name)
            if place is not None:
                places.append(place)
        return places

    def _parse_place(self, item: dict, category: str, city: str) -> PlaceDTO | None:
        try:
            lat = float(item["lat"])
            lon = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            return None

        raw_name = item.get("name") or item.get("display_name", "").split(",", 1)[0]
        name = html.unescape(str(raw_name)).strip()
        if not name:
            return None

        external_id = str(item.get("osm_id") or item.get("place_id") or f"{lat}:{lon}")
        address = html.unescape(str(item.get("display_name", ""))).strip() or None
        extratags = item.get("extratags") or {}
        phone = extratags.get("phone") or extratags.get("contact:phone")
        website = extratags.get("website") or extratags.get("contact:website")
        working_hours = extratags.get("opening_hours")
        source_url = f"https://www.openstreetmap.org/{item.get('osm_type', 'node')}/{external_id}"
        return PlaceDTO(
            provider=self.name,
            external_id=f"{category}-{external_id}",
            name=name,
            category=category,
            city=city,
            address=address,
            description="Источник: OpenStreetMap / Nominatim",
            lat=lat,
            lon=lon,
            rating=None,
            phone=html.unescape(str(phone)).strip() if phone else None,
            website=html.unescape(str(website)).strip() if website else None,
            working_hours=html.unescape(str(working_hours)).strip() if working_hours else None,
            source_url=source_url,
        )
