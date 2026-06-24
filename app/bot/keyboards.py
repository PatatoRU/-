from __future__ import annotations

from urllib.parse import quote_plus

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.data_cities import MAJOR_RUSSIAN_CITIES


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🍔 Еда"), KeyboardButton(text="🎉 Развлечения")],
            [KeyboardButton(text="🌳 Отдых"), KeyboardButton(text="🎟 События")],
            [KeyboardButton(text="💑 Свидание"), KeyboardButton(text="👨‍👩‍👧 Семья")],
            [KeyboardButton(text="🧒 Дети"), KeyboardButton(text="🆓 Бесплатно")],
            [KeyboardButton(text="🌆 Сегодня вечером"), KeyboardButton(text="📍 Рядом со мной")],
            [KeyboardButton(text="🎯 Интересы"), KeyboardButton(text="💬 Обратная связь")],
            [KeyboardButton(text="⭐ Избранное"), KeyboardButton(text="⚙ Настройки")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите категорию",
    )


def city_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=city.name, callback_data=f"city:{city.slug}")]
            for city in MAJOR_RUSSIAN_CITIES
        ]
    )


def location_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Найти рядом", callback_data="geo:confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="geo:cancel"),
            ]
        ]
    )


def _map_url(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "https://www.openstreetmap.org"
    return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=16/{lat}/{lon}"


def _route_url(lat: float | None, lon: float | None) -> str:
    if lat is None or lon is None:
        return "https://www.openstreetmap.org/directions"
    destination = quote_plus(f"{lat},{lon}")
    return f"https://www.openstreetmap.org/directions?from=&to={destination}#map=16/{lat}/{lon}"


def place_list_keyboard(external_id: str, lat: float | None = None, lon: float | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Подробнее", callback_data=f"place:{external_id}")],
            [
                InlineKeyboardButton(text="🗺 На карте", url=_map_url(lat, lon)),
                InlineKeyboardButton(text="🧭 Маршрут", url=_route_url(lat, lon)),
            ],
        ]
    )


def place_detail_keyboard(external_id: str, lat: float | None = None, lon: float | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⭐ В избранное", callback_data=f"fav:{external_id}"),
                InlineKeyboardButton(text="💬 Отзывы", callback_data=f"reviews:{external_id}"),
            ],
            [
                InlineKeyboardButton(text="✍️ Оценить", callback_data=f"review:{external_id}"),
                InlineKeyboardButton(text="🚀 Рекламировать", callback_data=f"ads:{external_id}"),
            ],
            [
                InlineKeyboardButton(text="🗺 Посмотреть на карте", url=_map_url(lat, lon)),
                InlineKeyboardButton(text="🧭 Построить маршрут", url=_route_url(lat, lon)),
            ],
        ]
    )


def interests_keyboard(selected: set[str] | None = None) -> InlineKeyboardMarkup:
    selected = selected or set()
    options = [
        ("food", "🍔 Поесть"),
        ("walk", "🚶 Погулять"),
        ("events", "🎟 События"),
        ("date", "💑 Свидание"),
        ("family", "👨‍👩‍👧 Семья"),
        ("kids", "🧒 Дети"),
        ("free", "🆓 Бесплатно"),
        ("tonight", "🌆 Сегодня вечером"),
    ]
    rows = []
    for code, title in options:
        prefix = "✅ " if code in selected else ""
        rows.append([InlineKeyboardButton(text=prefix + title, callback_data=f"interest:{code}")])
    rows.append([InlineKeyboardButton(text="Готово", callback_data="interest:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def event_list_keyboard(external_id: str, lat: float | None = None, lon: float | None = None) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Подробнее о событии", callback_data=f"event:{external_id}")],
            [
                InlineKeyboardButton(text="🗺 На карте", url=_map_url(lat, lon)),
                InlineKeyboardButton(text="🧭 Маршрут", url=_route_url(lat, lon)),
            ],
        ]
    )

# Backward-compatible alias for older code/tests.
def place_keyboard(external_id: str, lat: float | None = None, lon: float | None = None) -> InlineKeyboardMarkup:
    return place_detail_keyboard(external_id, lat, lon)


def rating_keyboard(external_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{stars}⭐", callback_data=f"rate:{external_id}:{stars}") for stars in range(1, 6)],
            [InlineKeyboardButton(text="Отзывы", callback_data=f"reviews:{external_id}")],
        ]
    )


def ad_tariffs_keyboard(external_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Бесплатный — 0⭐ / 7 дней", callback_data=f"adbuy:free:{external_id}")],
            [InlineKeyboardButton(text="Boost — 150⭐ / 14 дней", callback_data=f"adbuy:boost:{external_id}")],
            [InlineKeyboardButton(text="Premium — 450⭐ / 30 дней", callback_data=f"adbuy:premium:{external_id}")],
        ]
    )
