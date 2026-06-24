import pytest

pytest.importorskip("aiogram")
pytest.importorskip("pydantic")

from app.bot.handlers import _format_place_details, _format_place_summary
from app.bot.keyboards import place_detail_keyboard, place_list_keyboard
from app.schemas.place import PlaceDTO


def _place() -> PlaceDTO:
    return PlaceDTO(
        provider="local_curated",
        external_id="relax-moscow-0",
        name="Парк <Зарядье>",
        category="relax",
        city="Москва",
        address="ул. Варварка, 6",
        description="Парк & смотровая",
        lat=55.752,
        lon=37.628,
        rating=4.8,
        phone="+7 495 531-05-32",
        website="https://www.zaryadyepark.ru",
        working_hours="ежедневно 10:00–22:00",
    )


def test_place_summary_has_details_hint_and_escapes_html():
    rendered = _format_place_summary(_place())
    assert "Подробнее" in rendered
    assert "&lt;Зарядье&gt;" in rendered
    assert "Парк &amp; смотровая" not in rendered


def test_place_details_contains_contacts_and_escapes_html():
    rendered = _format_place_details(_place())
    assert "Телефон: +7 495 531-05-32" in rendered
    assert "Сайт: https://www.zaryadyepark.ru" in rendered
    assert "Время работы: ежедневно 10:00–22:00" in rendered
    assert "Парк &amp; смотровая" in rendered


def test_place_keyboards_have_details_map_route_and_favorite_buttons():
    list_text = str(place_list_keyboard("relax-moscow-0", 55.752, 37.628).model_dump())
    detail_text = str(place_detail_keyboard("relax-moscow-0", 55.752, 37.628).model_dump())
    assert "Подробнее" in list_text
    assert "Маршрут" in list_text
    assert "На карте" in list_text
    assert "В избранное" in detail_text
    assert "Построить маршрут" in detail_text
