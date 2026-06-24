from app.data_cities import MAJOR_RUSSIAN_CITIES, get_city_by_name


def test_city_base_contains_five_major_russian_cities():
    names = {city.name for city in MAJOR_RUSSIAN_CITIES}
    assert names == {"Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"}


def test_unknown_city_falls_back_to_moscow():
    assert get_city_by_name("Неизвестно").name == "Москва"
