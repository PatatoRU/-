from __future__ import annotations

from app.data_cities import get_city_by_name
from app.providers.provider_base import PlacesProvider
from app.schemas.place import PlaceDTO

CURATED_CITY_PLACES: dict[str, dict[str, list[tuple[str, str, str, float, float, float]]]] = {
    "Москва": {
        "food": [
            ("Кафе Пушкин", "Тверской б-р, 26А", "Исторический ресторан русской кухни", 55.7660, 37.6040, 4.8),
            ("Сыроварня", "Берсеневский пер., 2", "Семейный ресторан с пиццей и сырами", 55.7420, 37.6090, 4.6),
        ],
        "fun": [
            ("ГЭС-2", "Болотная наб., 15", "Выставки, концерты и лекции", 55.7440, 37.6110, 4.7),
            ("Кинотеатр Художественный", "Арбатская пл., 14", "Премьеры и фестивальное кино", 55.7520, 37.6000, 4.7),
        ],
        "relax": [
            ("Парк Зарядье", "ул. Варварка, 6", "Прогулки, смотровая и природа", 55.7520, 37.6280, 4.8),
            ("Аптекарский огород", "пр-т Мира, 26с1", "Ботанический сад", 55.7810, 37.6350, 4.7),
        ],
    },
    "Санкт-Петербург": {
        "food": [
            ("Кококо", "Вознесенский пр., 6", "Современная русская кухня", 59.9317, 30.3086, 4.6),
            ("Бекицер", "ул. Рубинштейна, 40", "Израильская уличная еда", 59.9278, 30.3445, 4.5),
        ],
        "fun": [
            ("Новая Голландия", "наб. Адмиралтейского канала, 2", "События, двор и концерты", 59.9291, 30.2894, 4.8),
            ("Эрарта", "29-я линия В.О., 2", "Музей современного искусства", 59.9326, 30.2517, 4.7),
        ],
        "relax": [
            ("Летний сад", "наб. Кутузова", "Классический парк для прогулок", 59.9461, 30.3351, 4.8),
            ("Парк 300-летия", "Приморский пр.", "Отдых у Финского залива", 59.9839, 30.1996, 4.7),
        ],
    },
    "Новосибирск": {
        "food": [
            ("Аджикинежаль", "Красный пр-т, 37", "Грузинская кухня", 55.0302, 82.9204, 4.6),
            ("Чашка кофе", "Красный пр-т, 22", "Кофе и завтраки", 55.0233, 82.9232, 4.5),
        ],
        "fun": [
            ("НОВАТ", "Красный пр-т, 36", "Опера и балет", 55.0302, 82.9229, 4.9),
            ("Мира Термы", "ул. Одоевского, 1/1", "Термальный комплекс", 54.9438, 82.9982, 4.6),
        ],
        "relax": [
            ("Михайловская набережная", "наб. Оби", "Прогулка у реки", 55.0066, 82.9216, 4.7),
            ("Заельцовский парк", "Заельцовский бор", "Лесной парк", 55.0755, 82.8844, 4.7),
        ],
    },
    "Екатеринбург": {
        "food": [
            ("Гастроли", "ул. 8 Марта, 4", "Гастробар в центре", 56.8391, 60.6045, 4.6),
            ("Паштет", "Толмачёва, 23", "Домашняя кухня", 56.8398, 60.6150, 4.5),
        ],
        "fun": [
            ("Ельцин Центр", "ул. Бориса Ельцина, 3", "Музей и события", 56.8449, 60.5916, 4.6),
            ("Свердловская филармония", "ул. Карла Либкнехта, 38А", "Концерты", 56.8434, 60.6146, 4.8),
        ],
        "relax": [
            ("Плотинка", "Исторический сквер", "Главная прогулочная зона", 56.8397, 60.6057, 4.8),
            ("Харитоновский парк", "ул. Шевченко", "Тихий парк у усадьбы", 56.8469, 60.6139, 4.7),
        ],
    },
    "Казань": {
        "food": [
            ("Татарская усадьба", "ул. Шигабутдина Марджани, 8", "Татарская кухня", 55.7796, 49.1191, 4.6),
            ("Дом чая", "ул. Баумана, 64", "Классика татарской кухни", 55.7899, 49.1176, 4.5),
        ],
        "fun": [
            ("Казанский кремль", "Кремль", "Музеи и прогулки", 55.7995, 49.1052, 4.9),
            ("Театр Камала", "ул. Татарстан, 1", "Спектакли", 55.7834, 49.1148, 4.8),
        ],
        "relax": [
            ("Кремлёвская набережная", "Федосеевская ул.", "Прогулка у Казанки", 55.8033, 49.1157, 4.8),
            ("Парк Горького", "ул. Николая Ершова", "Зелёный парк", 55.7990, 49.1486, 4.7),
        ],
    },
}

CURATED_PLACE_CONTACTS: dict[str, tuple[str | None, str | None, str | None, str | None]] = {
    "Кафе Пушкин": ("+7 495 739-00-33", "https://cafe-pushkin.ru", "ежедневно 09:00–00:00", "https://www.openstreetmap.org/search?query=Кафе%20Пушкин%20Москва"),
    "Сыроварня": ("+7 495 803-24-01", "https://syrovarnya.com", "ежедневно 10:00–00:00", "https://www.openstreetmap.org/search?query=Сыроварня%20Москва"),
    "Парк Зарядье": ("+7 495 531-05-32", "https://www.zaryadyepark.ru", "ежедневно 10:00–22:00", "https://www.openstreetmap.org/search?query=Парк%20Зарядье"),
    "Новая Голландия": ("+7 812 245-20-35", "https://www.newhollandsp.ru", "ежедневно 09:00–23:00", "https://www.openstreetmap.org/search?query=Новая%20Голландия"),
    "Эрарта": ("+7 812 324-08-09", "https://www.erarta.com", "ср–пн 10:00–22:00", "https://www.openstreetmap.org/search?query=Эрарта"),
    "НОВАТ": ("+7 383 222-00-77", "https://novat.nsk.ru", "по расписанию мероприятий", "https://www.openstreetmap.org/search?query=НОВАТ"),
    "Ельцин Центр": ("+7 343 312-43-43", "https://yeltsin.ru", "вт–вс 10:00–21:00", "https://www.openstreetmap.org/search?query=Ельцин%20Центр"),
    "Казанский кремль": ("+7 843 567-80-01", "https://kazan-kremlin.ru", "ежедневно 09:00–18:00", "https://www.openstreetmap.org/search?query=Казанский%20кремль"),
}


class LocalCuratedProvider(PlacesProvider):
    """Production fallback provider based on a curated offline city database."""

    name = "local_curated"

    async def search(
        self,
        category: str,
        city: str | None = None,
        lat: float | None = None,
        lon: float | None = None,
    ) -> list[PlaceDTO]:
        selected_city = get_city_by_name(city)
        normalized_category = "relax" if category == "nearby" else category
        places = CURATED_CITY_PLACES[selected_city.name].get(
            normalized_category,
            CURATED_CITY_PLACES[selected_city.name]["relax"],
        )
        result: list[PlaceDTO] = []
        for index, (name, address, description, place_lat, place_lon, rating) in enumerate(places):
            phone, website, working_hours, source_url = CURATED_PLACE_CONTACTS.get(name, (None, None, None, None))
            result.append(
                PlaceDTO(
                    provider=self.name,
                    external_id=f"{category}-{selected_city.slug}-{index}",
                    name=name,
                    category=category,
                    city=selected_city.name,
                    address=address,
                    description=description,
                    lat=(lat + (index + 1) * 0.003) if category == "nearby" and lat is not None else place_lat,
                    lon=(lon + (index + 1) * 0.003) if category == "nearby" and lon is not None else place_lon,
                    rating=rating,
                    phone=phone,
                    website=website,
                    working_hours=working_hours,
                    source_url=source_url,
                )
            )
        return result
