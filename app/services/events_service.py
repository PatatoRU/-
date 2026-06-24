from __future__ import annotations

from app.data_cities import get_city_by_name
from app.schemas.event import EventDTO

EVENT_CATEGORIES = {
    "concerts": "концерты",
    "festivals": "фестивали",
    "exhibitions": "выставки",
    "cinema": "кино",
    "city": "городские события",
    "kids": "детям",
    "family": "семья",
    "date": "свидание",
    "free": "бесплатно",
    "tonight": "сегодня вечером",
}

_BASE_EVENTS: dict[str, list[tuple[str, str, str, str, str, str, float, float]]] = {
    "Москва": [
        ("Вечерний маршрут по Зарядью", "tonight", "Парк Зарядье", "ул. Варварка, 6", "Прогулка, смотровая и световые виды центра", "сегодня 19:00", "бесплатно", 55.7520, 37.6280),
        ("Семейная выставка в ГЭС-2", "family", "ГЭС-2", "Болотная наб., 15", "Выставка и творческие мастерские для взрослых и детей", "ежедневно", "по регистрации", 55.7440, 37.6110),
        ("Кино вечер в Художественном", "cinema", "Художественный", "Арбатская пл., 14", "Премьеры и авторское кино", "сегодня вечером", "платно", 55.7520, 37.6000),
    ],
    "Санкт-Петербург": [
        ("Концерт во дворе Новой Голландии", "concerts", "Новая Голландия", "наб. Адмиралтейского канала, 2", "Музыка и городская атмосфера", "сегодня 20:00", "по расписанию", 59.9291, 30.2894),
        ("Выставка современного искусства", "exhibitions", "Эрарта", "29-я линия В.О., 2", "Маршрут для свидания и вдохновения", "ежедневно", "платно", 59.9326, 30.2517),
        ("Прогулка по Летнему саду", "free", "Летний сад", "наб. Кутузова", "Классический бесплатный маршрут", "днём и вечером", "бесплатно", 59.9461, 30.3351),
    ],
    "Новосибирск": [
        ("Балетный вечер в НОВАТ", "concerts", "НОВАТ", "Красный пр-т, 36", "Театр, музыка и сильный вечерний сценарий", "по афише", "платно", 55.0302, 82.9229),
        ("Семейная прогулка по набережной", "family", "Михайловская набережная", "наб. Оби", "Маршрут с детьми и видом на реку", "сегодня", "бесплатно", 55.0066, 82.9216),
        ("Релакс в термах", "date", "Мира Термы", "ул. Одоевского, 1/1", "Спокойный сценарий для пары", "вечером", "платно", 54.9438, 82.9982),
    ],
    "Екатеринбург": [
        ("Лекция и выставка в Ельцин Центре", "exhibitions", "Ельцин Центр", "ул. Бориса Ельцина, 3", "Культура, история и события", "по расписанию", "платно/бесплатно", 56.8449, 60.5916),
        ("Концерт в филармонии", "concerts", "Свердловская филармония", "ул. Карла Либкнехта, 38А", "Классическая музыка вечером", "по афише", "платно", 56.8434, 60.6146),
        ("Бесплатная прогулка по Плотинке", "free", "Плотинка", "Исторический сквер", "Главная прогулочная зона города", "сегодня вечером", "бесплатно", 56.8397, 60.6057),
    ],
    "Казань": [
        ("Вечер на Кремлёвской набережной", "tonight", "Кремлёвская набережная", "Федосеевская ул.", "Прогулка у Казанки и вид на Кремль", "сегодня вечером", "бесплатно", 55.8033, 49.1157),
        ("Спектакль в театре Камала", "city", "Театр Камала", "ул. Татарстан, 1", "Городское культурное событие", "по афише", "платно", 55.7834, 49.1148),
        ("Детский маршрут по Кремлю", "kids", "Казанский кремль", "Кремль", "Познавательная прогулка для семьи", "днём", "по билетам", 55.7995, 49.1052),
    ],
}


class EventService:
    """Curated event service with extension points for external event providers."""

    provider_name = "local_events"

    async def list_events(self, city: str, category: str | None = None, limit: int = 5) -> list[EventDTO]:
        selected_city = get_city_by_name(city)
        events = []
        for index, item in enumerate(_BASE_EVENTS[selected_city.name]):
            title, event_category, venue, address, description, starts_at, price, lat, lon = item
            if category and category not in {event_category, "all"}:
                if category == "tonight" and "вечер" not in starts_at and event_category != "tonight":
                    continue
                if category == "free" and "бесплат" not in price and event_category != "free":
                    continue
                if category not in {"tonight", "free"}:
                    continue
            events.append(
                EventDTO(
                    provider=self.provider_name,
                    external_id=f"event-{selected_city.slug}-{event_category}-{index}",
                    title=title,
                    category=event_category,
                    city=selected_city.name,
                    venue=venue,
                    address=address,
                    description=description,
                    starts_at=starts_at,
                    price_label=price,
                    lat=lat,
                    lon=lon,
                    source_url="https://www.openstreetmap.org/search?query=" + venue.replace(" ", "%20"),
                )
            )
        return events[:limit]
