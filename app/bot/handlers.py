from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from redis.asyncio import Redis
from sqlalchemy import func, select

from app.agents.database_agent import DatabasePopulationAgent
from app.agents.query_agent import QueryUnderstandingAgent
from app.bot.keyboards import ad_tariffs_keyboard, city_keyboard, event_list_keyboard, interests_keyboard, location_confirm_keyboard, main_keyboard, place_detail_keyboard, place_list_keyboard, rating_keyboard
from app.core.config import get_settings
from app.data_cities import CITY_BY_SLUG, MAJOR_RUSSIAN_CITIES
from app.db.session import SessionLocal
from app.models import AdCampaign, AdPayment, Place, SearchHistory, User
from app.repositories.repositories import AdRepository, FavoriteRepository, HistoryRepository, PlaceRepository, ReviewRepository, UserRepository
from app.services.analytics_service import AnalyticsService
from app.services.events_service import EventService
from app.services.llm_service import LLMService
from app.services.payment_service import parse_ad_payment_payload
from app.services.places_service import PlacesService
from app.services.redis_service import RedisService
from app.services.rate_limit_service import RateLimitService
from app.services.tariffs import AD_TARIFFS

router = Router()
query_agent = QueryUnderstandingAgent()
HELP_TEXT = "\n".join(
    [
        "Я помогу найти куда сходить сегодня.",
        "",
        "Команды:",
        "/start — регистрация и запуск",
        "/help — помощь",
        "/profile — профиль и выбранный город",
        "/find_food — еда",
        "/find_fun — развлечения",
        "/find_relax — отдых",
        "/favorites — избранное",
        "/history — история",
        "/settings — выбрать город",
        "/recommend — AI-рекомендация с fallback OpenAI/OpenRouter/Ollama",
        "/events — события города",
        "/interests — выбрать интересы",
        "/feedback — обратная связь",
        "/add_place — заявка на добавление места",
        "/ads — рекламные тарифы и покупка показов",
        "/admin — статистика для ADMIN_IDS",
        "",
        "Можно написать обычным текстом: «найди кафе в Казани» или «куда сходить вечером». ",
        "Города в базе: " + ", ".join(city.name for city in MAJOR_RUSSIAN_CITIES),
    ]
)


def _is_admin(telegram_id: int | None) -> bool:
    return telegram_id is not None and telegram_id in get_settings().admin_ids




async def _ensure_user(message: Message):
    telegram_user = message.from_user
    if telegram_user is None:
        raise ValueError("Telegram user is missing")
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )
        await DatabasePopulationAgent(session).populate_city(user.city)
        return user


async def _collect_city_places(city: str):
    service = PlacesService()
    food = await service.search_food(city)
    fun = await service.search_fun(city)
    relax = await service.search_relax(city)
    return [*food, *fun, *relax]


async def _check_search_limit(message: Message, redis: Redis, user) -> bool:
    allowed, remaining, limit = await RateLimitService(redis).check_and_increment(user.telegram_id)
    if allowed:
        return True
    await message.answer(
        f"Лимит бесплатных поисковых запросов исчерпан: {limit}/день. "
        "Купите рекламный тариф Boost или Premium в карточке места, чтобы расширить лимиты."
    )
    return False


async def _inject_ads(session, category: str, city: str, places):
    ad_places = await AdRepository(session).active_for(category=category, city=city)
    if not ad_places:
        return places
    existing_ids = {place.external_id for place in places}
    sponsored = [place for place in ad_places if place.external_id not in existing_ids]
    for place in sponsored:
        setattr(place, "is_ad", True)
    return [*sponsored, *places]


async def _send_places(message: Message, kind: str, city: str | None = None) -> None:
    user = await _ensure_user(message)
    search_city = city or user.city
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        async with SessionLocal() as session:
            service = PlacesService(session=session, redis=redis)
            search_by_kind = {
                "food": service.search_food,
                "fun": service.search_fun,
                "relax": service.search_relax,
            }
            if not await _check_search_limit(message, redis, user):
                return
            places = await search_by_kind[kind](search_city)
            places = await _inject_ads(session, kind, search_city, places)
            await HistoryRepository(session).add(user.id, kind, city=search_city)
            await AnalyticsService(redis).track("search", user_id=user.telegram_id, city=search_city, category=kind)
    finally:
        await redis.aclose()

    await _answer_places(message=message, places=places)


async def _answer_places(message: Message, places) -> None:
    if not places:
        await message.answer("Пока ничего не нашёл. Попробуйте позже.", reply_markup=main_keyboard())
        return

    for place in places[:5]:
        await message.answer(
            _format_place_summary(place),
            reply_markup=place_list_keyboard(place.external_id, place.lat, place.lon),
        )


def _safe(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _format_place_summary(place) -> str:
    return "\n".join(
        line
        for line in [
            f"<b>{_safe(place.name)}</b>",
            f"📍 {_safe(place.address)}" if place.address else None,
            f"⭐ Рейтинг: {_safe(place.rating)}" if place.rating else None,
            "Реклама" if getattr(place, "is_ad", False) else None,
            "Нажмите «Подробнее», чтобы открыть карточку, отзывы, контакты, карту и маршрут.",
        ]
        if line
    )


def _format_place_details(place) -> str:
    category_label = {"food": "Заведение", "fun": "Мероприятие/развлечение", "relax": "Парк/отдых", "nearby": "Рядом"}.get(
        place.category, "Место"
    )
    return "\n".join(
        line
        for line in [
            f"<b>{_safe(place.name)}</b>",
            f"Тип: {_safe(category_label)}",
            f"Город: {_safe(place.city)}",
            f"Адрес: {_safe(place.address)}" if place.address else None,
            f"Описание: {_safe(place.description)}" if place.description else None,
            f"Телефон: {_safe(place.phone)}" if getattr(place, "phone", None) else None,
            f"Сайт: {_safe(place.website)}" if getattr(place, "website", None) else None,
            f"Время работы: {_safe(place.working_hours)}" if getattr(place, "working_hours", None) else None,
            f"Рейтинг: {_safe(place.rating)}" if place.rating else None,
            f"Источник: {_safe(place.source_url)}" if getattr(place, "source_url", None) else None,
            "Кнопки ниже: отзывы, оценка, реклама, карта и маршрут.",
        ]
        if line
    )




def _format_event_summary(event) -> str:
    return "\n".join(
        line
        for line in [
            f"<b>{_safe(event.title)}</b>",
            f"📍 {_safe(event.venue)}",
            f"🕒 {_safe(event.starts_at)}",
            f"💳 {_safe(event.price_label)}",
            "Нажмите «Подробнее о событии», чтобы увидеть описание, карту и маршрут.",
        ]
        if line
    )


def _format_event_details(event) -> str:
    return "\n".join(
        line
        for line in [
            f"<b>{_safe(event.title)}</b>",
            f"Категория: {_safe(event.category)}",
            f"Город: {_safe(event.city)}",
            f"Площадка: {_safe(event.venue)}",
            f"Адрес: {_safe(event.address)}" if event.address else None,
            f"Когда: {_safe(event.starts_at)}",
            f"Стоимость: {_safe(event.price_label)}",
            f"Описание: {_safe(event.description)}",
            f"Источник: {_safe(event.source_url)}" if event.source_url else None,
        ]
        if line
    )


async def _send_events(message: Message, category: str | None = None, city: str | None = None) -> None:
    user = await _ensure_user(message)
    search_city = city or user.city
    events = await EventService().list_events(search_city, category=category)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        await AnalyticsService(redis).track("events", user_id=user.telegram_id, city=search_city, category=category or "all")
    finally:
        await redis.aclose()
    if not events:
        await message.answer("Пока не нашёл событий под этот сценарий. Попробуйте 🎟 События или /find_fun.", reply_markup=main_keyboard())
        return
    for event in events[:5]:
        await message.answer(_format_event_summary(event), reply_markup=event_list_keyboard(event.external_id, event.lat, event.lon))


async def _get_selected_interests(redis: Redis, telegram_id: int) -> set[str]:
    raw = await RedisService(redis).get_session_value(telegram_id, "interests")
    return {item for item in (raw or "").split(",") if item}

@router.message(CommandStart())
async def start(message: Message) -> None:
    await _ensure_user(message)
    await message.answer(
        "Привет! Я зарегистрировал профиль. Выберите категорию или настройте город.",
        reply_markup=main_keyboard(),
    )
    await message.answer("Если город не Москва, выберите его в настройках:", reply_markup=city_keyboard())


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(HELP_TEXT, reply_markup=main_keyboard())


@router.message(Command("profile"))
async def profile(message: Message) -> None:
    user = await _ensure_user(message)
    await message.answer(f"Профиль: {user.first_name or 'гость'}\nГород: {user.city}")


@router.message(Command("find_food") | (F.text == "🍔 Еда"))
async def food(message: Message) -> None:
    await _send_places(message, "food")


@router.message(Command("find_fun") | (F.text == "🎉 Развлечения"))
async def fun(message: Message) -> None:
    await _send_places(message, "fun")


@router.message(Command("find_relax") | (F.text == "🌳 Отдых"))
async def relax(message: Message) -> None:
    await _send_places(message, "relax")


@router.message(Command("events") | (F.text == "🎟 События"))
async def events(message: Message) -> None:
    await _send_events(message)


@router.message(F.text == "💑 Свидание")
async def date_idea(message: Message) -> None:
    await _send_events(message, category="date")


@router.message(F.text == "👨‍👩‍👧 Семья")
async def family_idea(message: Message) -> None:
    await _send_events(message, category="family")


@router.message(F.text == "🧒 Дети")
async def kids_idea(message: Message) -> None:
    await _send_events(message, category="kids")


@router.message(F.text == "🆓 Бесплатно")
async def free_idea(message: Message) -> None:
    await _send_events(message, category="free")


@router.message(F.text == "🌆 Сегодня вечером")
async def tonight_idea(message: Message) -> None:
    await _send_events(message, category="tonight")


@router.message(Command("interests") | (F.text == "🎯 Интересы"))
async def interests(message: Message) -> None:
    user = await _ensure_user(message)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        selected = await _get_selected_interests(redis, user.telegram_id)
    finally:
        await redis.aclose()
    await message.answer("Выберите интересы — я буду учитывать их в рекомендациях:", reply_markup=interests_keyboard(selected))


@router.message(Command("feedback") | (F.text == "💬 Обратная связь"))
async def feedback_start(message: Message) -> None:
    user = await _ensure_user(message)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        await RedisService(redis).set_session_value(user.telegram_id, "awaiting_feedback", "1", ttl=900)
    finally:
        await redis.aclose()
    await message.answer("Напишите одним сообщением, что улучшить или какая проблема возникла.")


@router.message(F.text == "📍 Рядом со мной")
async def nearby_hint(message: Message) -> None:
    await message.answer("Отправьте геолокацию. Я попрошу подтверждение и найду места рядом на OpenStreetMap.")


@router.message(F.location)
async def nearby_location(message: Message) -> None:
    user = await _ensure_user(message)
    if message.location is None:
        await message.answer("Не вижу геолокацию. Попробуйте отправить её ещё раз.")
        return

    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        session = RedisService(redis)
        await session.set_session_value(user.telegram_id, "last_lat", str(message.location.latitude))
        await session.set_session_value(user.telegram_id, "last_lon", str(message.location.longitude))
    finally:
        await redis.aclose()

    await message.answer(
        "Геолокация получена. Подтвердите поиск рядом с этой точкой.",
        reply_markup=location_confirm_keyboard(),
    )


@router.callback_query(F.data == "geo:confirm")
async def confirm_location_search(callback: CallbackQuery) -> None:
    if callback.from_user is None:
        await callback.answer("Не удалось подтвердить геолокацию", show_alert=True)
        return

    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        session = RedisService(redis)
        lat = await session.get_session_value(callback.from_user.id, "last_lat")
        lon = await session.get_session_value(callback.from_user.id, "last_lon")
        if lat is None or lon is None:
            await callback.answer("Геолокация устарела. Отправьте её ещё раз.", show_alert=True)
            return
        async with SessionLocal() as db_session:
            user = await UserRepository(db_session).get_or_create(
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name,
            )
            places = await PlacesService(session=db_session, redis=redis).search_nearby(float(lat), float(lon))
            await HistoryRepository(db_session).add(user.id, "nearby", lat=float(lat), lon=float(lon))
        await session.clear_session_value(callback.from_user.id, "last_lat")
        await session.clear_session_value(callback.from_user.id, "last_lon")
    finally:
        await redis.aclose()

    await callback.answer("Ищу рядом")
    if callback.message:
        await _answer_places(callback.message, places)


@router.callback_query(F.data == "geo:cancel")
async def cancel_location_search(callback: CallbackQuery) -> None:
    if callback.from_user is not None:
        redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            session = RedisService(redis)
            await session.clear_session_value(callback.from_user.id, "last_lat")
            await session.clear_session_value(callback.from_user.id, "last_lon")
        finally:
            await redis.aclose()
    await callback.answer("Поиск рядом отменён")


@router.message(Command("recommend"))
async def recommend(message: Message) -> None:
    user = await _ensure_user(message)
    text = message.text or "посоветуй куда сходить сегодня"
    places = await _collect_city_places(user.city)
    answer = await LLMService(get_settings()).recommend(user_text=text, city=user.city, places=places)
    await message.answer(answer, reply_markup=main_keyboard())


@router.message(Command("ads"))
async def ads_command(message: Message) -> None:
    await message.answer("Откройте карточку места и нажмите 🚀 Рекламировать. Доступны тарифы: Free, Boost и Premium с оплатой Telegram Stars.")


@router.message(Command("admin"))
async def telegram_admin(message: Message) -> None:
    if not _is_admin(message.from_user.id if message.from_user else None):
        await message.answer("Админ-команды доступны только владельцам, указанным в ADMIN_IDS.")
        return
    async with SessionLocal() as session:
        users_count = await session.scalar(select(func.count(User.id))) or 0
        places_count = await session.scalar(select(func.count(Place.id))) or 0
        searches_count = await session.scalar(select(func.count(SearchHistory.id))) or 0
        active_ads = await session.scalar(select(func.count(AdCampaign.id)).where(AdCampaign.status == "active")) or 0
        paid = await session.scalar(select(func.count(AdPayment.id)).where(AdPayment.status == "paid")) or 0
    await message.answer(
        "\n".join(
            [
                "<b>Админ-панель MVP</b>",
                f"Пользователи: {users_count}",
                f"Места: {places_count}",
                f"Поиски: {searches_count}",
                f"Активная реклама: {active_ads}",
                f"Оплаченные платежи: {paid}",
            ]
        )
    )


@router.message(Command("add_place"))
async def add_place_start(message: Message) -> None:
    user = await _ensure_user(message)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        await RedisService(redis).set_session_value(user.telegram_id, "awaiting_place_submission", "1", ttl=900)
    finally:
        await redis.aclose()
    await message.answer(
        "Пришлите заявку одним сообщением: название, город, категория, адрес, телефон/сайт. "
        "Заявка попадёт на модерацию."
    )


@router.message(Command("favorites") | (F.text == "⭐ Избранное"))
async def favorites(message: Message) -> None:
    user = await _ensure_user(message)
    async with SessionLocal() as session:
        favorites_list = await FavoriteRepository(session).list(user.id)
    if not favorites_list:
        await message.answer("Избранное пусто.")
        return
    await message.answer("\n".join(_safe(favorite.place.name) for favorite in favorites_list))


@router.message(Command("history"))
async def history(message: Message) -> None:
    user = await _ensure_user(message)
    async with SessionLocal() as session:
        rows = await HistoryRepository(session).list(user.id)
    if not rows:
        await message.answer("История пуста.")
        return
    await message.answer("\n".join(f"{row.query_type} {row.city or ''}" for row in rows))


@router.message(Command("settings") | (F.text == "⚙ Настройки"))
async def settings(message: Message) -> None:
    await message.answer("Выберите город:", reply_markup=city_keyboard())


@router.callback_query(F.data.startswith("city:"))
async def set_city(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Не удалось выбрать город", show_alert=True)
        return
    city_slug = callback.data.split(":", 1)[1]
    city = CITY_BY_SLUG.get(city_slug)
    if city is None:
        await callback.answer("Город не найден", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
        )
        await UserRepository(session).update_city(user.id, city.name)
        await DatabasePopulationAgent(session).populate_city(city.name)
    await callback.answer(f"Город выбран: {city.name}")
    if callback.message:
        await callback.message.answer(f"Теперь ищу места в городе {city.name}.", reply_markup=main_keyboard())


@router.callback_query(F.data.startswith("interest:"))
async def toggle_interest(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Не удалось сохранить интерес", show_alert=True)
        return
    code = callback.data.split(":", 1)[1]
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        selected = await _get_selected_interests(redis, callback.from_user.id)
        if code == "done":
            await callback.answer("Интересы сохранены")
            if callback.message:
                await callback.message.answer("Готово. Теперь рекомендации будут учитывать выбранные интересы.", reply_markup=main_keyboard())
            return
        if code in selected:
            selected.remove(code)
        else:
            selected.add(code)
        await RedisService(redis).set_session_value(callback.from_user.id, "interests", ",".join(sorted(selected)))
    finally:
        await redis.aclose()
    await callback.answer("Интересы обновлены")
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=interests_keyboard(selected))


@router.callback_query(F.data.startswith("event:"))
async def show_event_details(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("Событие не найдено", show_alert=True)
        return
    external_id = callback.data.split(":", 1)[1]
    user_city = "Москва"
    if callback.from_user is not None:
        async with SessionLocal() as session:
            user = await UserRepository(session).get_or_create(
                callback.from_user.id,
                callback.from_user.username,
                callback.from_user.first_name,
            )
            user_city = user.city
    events = await EventService().list_events(user_city)
    event = next((item for item in events if item.external_id == external_id), None)
    if event is None:
        for city in MAJOR_RUSSIAN_CITIES:
            city_events = await EventService().list_events(city.name)
            event = next((item for item in city_events if item.external_id == external_id), None)
            if event is not None:
                break
    if event is None:
        await callback.answer("Карточка события устарела. Повторите поиск.", show_alert=True)
        return
    if callback.from_user is not None:
        redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            await AnalyticsService(redis).track("event_ctr", user_id=callback.from_user.id, event_id=external_id)
        finally:
            await redis.aclose()
    await callback.answer("Открываю событие")
    if callback.message:
        await callback.message.answer(_format_event_details(event), reply_markup=event_list_keyboard(event.external_id, event.lat, event.lon))


@router.callback_query(F.data.startswith("place:"))
async def show_place_details(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("Место не найдено", show_alert=True)
        return

    external_id = callback.data.split(":", 1)[1]
    async with SessionLocal() as session:
        place = await PlaceRepository(session).get_by_external_id(external_id)
    if place is None:
        await callback.answer("Карточка устарела. Повторите поиск.", show_alert=True)
        return
    if callback.from_user is not None:
        redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            await AnalyticsService(redis).track("place_ctr", user_id=callback.from_user.id, place_id=external_id)
        finally:
            await redis.aclose()

    await callback.answer("Открываю карточку")
    if callback.message:
        await callback.message.answer(
            _format_place_details(place),
            reply_markup=place_detail_keyboard(place.external_id, place.lat, place.lon),
        )


@router.callback_query(F.data.startswith("reviews:"))
async def show_reviews(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("Отзывы не найдены", show_alert=True)
        return
    external_id = callback.data.split(":", 1)[1]
    async with SessionLocal() as session:
        reviews = await ReviewRepository(session).list_for_place(external_id)
    await callback.answer("Отзывы")
    if callback.message:
        if not reviews:
            await callback.message.answer("Пока отзывов нет. Станьте первым — нажмите «Оценить» в карточке.")
            return
        lines = ["<b>Отзывы</b>"]
        for review in reviews:
            text = f" — {_safe(review.text)}" if review.text else ""
            lines.append(f"{review.rating}⭐{text}")
        await callback.message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("review:"))
async def ask_rating(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("Место не найдено", show_alert=True)
        return
    external_id = callback.data.split(":", 1)[1]
    await callback.answer("Выберите оценку")
    if callback.message:
        await callback.message.answer("Поставьте оценку месту:", reply_markup=rating_keyboard(external_id))


@router.callback_query(F.data.startswith("rate:"))
async def save_rating(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Не удалось сохранить оценку", show_alert=True)
        return
    _, external_id, rating_raw = callback.data.split(":", 2)
    rating = max(1, min(5, int(rating_raw)))
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            callback.from_user.id, callback.from_user.username, callback.from_user.first_name
        )
        ok = await ReviewRepository(session).add_or_update(user.id, external_id, rating)
    await callback.answer("Оценка сохранена" if ok else "Место не найдено", show_alert=not ok)
    if ok and callback.message:
        await callback.message.answer("Спасибо! Если хотите оставить текстовый отзыв, просто отправьте его следующим сообщением.")
        redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
        try:
            await RedisService(redis).set_session_value(callback.from_user.id, "review_place", external_id, ttl=900)
            await RedisService(redis).set_session_value(callback.from_user.id, "review_rating", str(rating), ttl=900)
        finally:
            await redis.aclose()


@router.callback_query(F.data.startswith("ads:"))
async def show_ad_tariffs(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer("Место не найдено", show_alert=True)
        return
    external_id = callback.data.split(":", 1)[1]
    lines = ["<b>Реклама в выдаче</b>"]
    for tariff in AD_TARIFFS.values():
        price = "бесплатно" if tariff.stars == 0 else f"{tariff.stars}⭐"
        lines.append(f"• {tariff.title}: {price}, {tariff.days} дней, приоритет {tariff.priority}. {tariff.description}")
    await callback.answer("Тарифы")
    if callback.message:
        await callback.message.answer("\n".join(lines), reply_markup=ad_tariffs_keyboard(external_id))


@router.callback_query(F.data.startswith("adbuy:"))
async def buy_ad(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer("Не удалось оформить рекламу", show_alert=True)
        return
    _, tariff_code, external_id = callback.data.split(":", 2)
    tariff = AD_TARIFFS.get(tariff_code)
    if tariff is None:
        await callback.answer("Тариф не найден", show_alert=True)
        return
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            callback.from_user.id, callback.from_user.username, callback.from_user.first_name
        )
        if tariff.stars == 0:
            ok = await AdRepository(session).create_campaign(
                user.id, external_id, tariff.code, tariff.priority, tariff.stars, tariff.days
            )
            await callback.answer("Бесплатная реклама активирована" if ok else "Место не найдено", show_alert=not ok)
            return
        payment = await AdRepository(session).create_pending_payment(
            user.id,
            external_id,
            tariff.code,
            tariff.stars,
        )
        if payment is None or payment.invoice_payload is None:
            await callback.answer("Место не найдено", show_alert=True)
            return
    await callback.message.answer_invoice(
        title=f"Реклама {tariff.title}",
        description=tariff.description,
        payload=payment.invoice_payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=tariff.title, amount=tariff.stars)],
    )
    await callback.answer("Счёт отправлен")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    parsed_payload = parse_ad_payment_payload(pre_checkout_query.invoice_payload)
    if parsed_payload is None or pre_checkout_query.currency != "XTR":
        await pre_checkout_query.answer(ok=False, error_message="Некорректный платёж")
        return
    payment_id, tariff_code, _external_id = parsed_payload
    tariff = AD_TARIFFS.get(tariff_code)
    if tariff is None or pre_checkout_query.total_amount != tariff.stars:
        await pre_checkout_query.answer(ok=False, error_message="Некорректная сумма платежа")
        return
    async with SessionLocal() as session:
        payment = await session.get(AdPayment, payment_id)
        if payment is None or payment.status != "pending" or payment.stars_amount != tariff.stars:
            await pre_checkout_query.answer(ok=False, error_message="Счёт не найден или уже обработан")
            return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_ad_payment(message: Message) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    payload = message.successful_payment.invoice_payload
    parsed_payload = parse_ad_payment_payload(payload)
    if parsed_payload is None:
        await message.answer("Платёж получен, но payload некорректен. Напишите поддержке.")
        return
    payment_id, tariff_code, external_id = parsed_payload
    tariff = AD_TARIFFS.get(tariff_code)
    if tariff is None:
        await message.answer("Платёж получен, но тариф не найден. Напишите поддержке.")
        return
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username, message.from_user.first_name
        )
        payment, first_processing = await AdRepository(session).mark_payment_paid(
            payment_id,
            message.successful_payment.telegram_payment_charge_id,
            message.successful_payment.provider_payment_charge_id,
        )
        if payment is None:
            await message.answer("Платёж получен, но счёт не найден. Напишите поддержке.")
            return
        if not first_processing:
            await message.answer("Этот платёж уже был обработан ранее.")
            return
        ok = await AdRepository(session).create_campaign(
            user.id, external_id, tariff.code, tariff.priority, tariff.stars, tariff.days
        )
    await message.answer("Реклама активирована ✅" if ok else "Платёж прошёл, но место не найдено. Напишите поддержке.")


@router.callback_query(F.data.startswith("fav:"))
async def add_favorite(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        await callback.answer("Не удалось сохранить", show_alert=True)
        return

    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            callback.from_user.id,
            callback.from_user.username,
            callback.from_user.first_name,
        )
        ok = await FavoriteRepository(session).add_by_external_id(
            user.id,
            callback.data.split(":", 1)[1],
        )
    await callback.answer("Добавлено в избранное" if ok else "Место не найдено", show_alert=not ok)


@router.message(F.text)
async def ai_text_assistant(message: Message) -> None:
    user = await _ensure_user(message)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        session_cache = RedisService(redis)
        awaiting_feedback = await session_cache.get_session_value(user.telegram_id, "awaiting_feedback")
        if awaiting_feedback == "1":
            feedback_text = (message.text or "").strip()
            if feedback_text:
                await redis.lpush(
                    "feedback:items",
                    f"{user.telegram_id}|{user.city}|{feedback_text[:1000]}",
                )
                await AnalyticsService(redis).track("feedback", user_id=user.telegram_id, city=user.city)
            await session_cache.clear_session_value(user.telegram_id, "awaiting_feedback")
            await message.answer("Спасибо! Обратная связь сохранена и попадёт в админский разбор.")
            return
        awaiting_place_submission = await session_cache.get_session_value(user.telegram_id, "awaiting_place_submission")
        if awaiting_place_submission == "1":
            submission_text = (message.text or "").strip()
            if len(submission_text) < 10:
                await message.answer("Заявка слишком короткая. Укажите название, город, категорию и контакты.")
                return
            await redis.lpush(
                "place_submissions",
                f"{user.telegram_id}|{user.city}|{submission_text[:1500]}",
            )
            await AnalyticsService(redis).track("place_submission", user_id=user.telegram_id, city=user.city)
            await session_cache.clear_session_value(user.telegram_id, "awaiting_place_submission")
            await message.answer("Заявка принята на модерацию. Спасибо!")
            return
        review_place = await session_cache.get_session_value(user.telegram_id, "review_place")
        review_rating = await session_cache.get_session_value(user.telegram_id, "review_rating")
        if review_place and review_rating:
            async with SessionLocal() as session:
                await ReviewRepository(session).add_or_update(user.id, review_place, int(review_rating), message.text or "")
            await session_cache.clear_session_value(user.telegram_id, "review_place")
            await session_cache.clear_session_value(user.telegram_id, "review_rating")
            await message.answer("Отзыв сохранён. Спасибо!")
            return
    finally:
        await redis.aclose()
    parsed = query_agent.parse(message.text or "")
    if parsed.needs_location:
        await nearby_hint(message)
        return
    lowered_text = (message.text or "").lower()
    scenario_by_word = {
        "свидан": "date",
        "сем": "family",
        "дет": "kids",
        "бесплат": "free",
        "вечер": "tonight",
        "концерт": "concerts",
        "выстав": "exhibitions",
        "кино": "cinema",
        "событ": "all",
        "мероприят": "all",
    }
    for word, event_category in scenario_by_word.items():
        if word in lowered_text:
            await _send_events(message, category=event_category, city=parsed.city or user.city)
            return
    if parsed.category in {"food", "fun", "relax"}:
        await _send_places(message, parsed.category, city=parsed.city or user.city)
        return

    city = parsed.city or user.city
    places = await _collect_city_places(city)
    redis = Redis.from_url(get_settings().redis_url, decode_responses=True)
    try:
        selected_interests = await _get_selected_interests(redis, user.telegram_id)
    finally:
        await redis.aclose()
    interest_hint = f"\nИнтересы пользователя: {', '.join(sorted(selected_interests))}" if selected_interests else ""
    answer = await LLMService(get_settings()).recommend(
        user_text=(message.text or "куда сходить сегодня") + interest_hint,
        city=city,
        places=places,
    )
    await message.answer(answer, reply_markup=main_keyboard())
