from __future__ import annotations

from dataclasses import dataclass

from app.data_cities import CITY_BY_NAME

CITY_ALIASES = {
    "москв": "Москва",
    "санкт-петербург": "Санкт-Петербург",
    "петербург": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "новосибирск": "Новосибирск",
    "екатеринбург": "Екатеринбург",
    "казан": "Казань",
}

CATEGORY_KEYWORDS = {
    "food": {"еда", "поесть", "ресторан", "кафе", "ужин", "завтрак", "обед", "бар"},
    "fun": {"развлеч", "музей", "театр", "кино", "концерт", "событи", "вечерин", "афиша"},
    "relax": {"отдых", "парк", "погуля", "прогул", "природ", "спокой", "релакс"},
    "nearby": {"рядом", "поблизости", "около меня", "недалеко", "геолокац"},
}


@dataclass(frozen=True)
class ParsedUserQuery:
    category: str | None
    city: str | None
    needs_location: bool
    original_text: str


class QueryUnderstandingAgent:
    """Deterministic query agent that extracts category/city before optional LLM response."""

    def parse(self, text: str) -> ParsedUserQuery:
        normalized = text.lower().replace("ё", "е")
        category = self._extract_category(normalized)
        city = self._extract_city(normalized)
        return ParsedUserQuery(
            category=category,
            city=city,
            needs_location=category == "nearby",
            original_text=text,
        )

    def _extract_category(self, normalized: str) -> str | None:
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return category
        return None

    def _extract_city(self, normalized: str) -> str | None:
        for alias, city_name in CITY_ALIASES.items():
            if alias in normalized:
                return city_name
        for city in CITY_BY_NAME.values():
            if city.name.lower().replace("ё", "е") in normalized:
                return city.name
        return None
