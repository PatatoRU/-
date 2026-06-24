from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery
from redis.asyncio import Redis

from app.agents.database_agent import DatabasePopulationAgent
from app.agents.query_agent import QueryUnderstandingAgent
from app.bot.keyboards import ad_tariffs_keyboard, city_keyboard, location_confirm_keyboard, main_keyboard, place_detail_keyboard, place_list_keyboard, rating_keyboard
from app.core.config import get_settings
from app.data_cities import CITY_BY_SLUG, MAJOR_RUSSIAN_CITIES
from app.db.session import SessionLocal
from app.repositories.repositories import AdRepository, FavoriteRepository, HistoryRepository, PlaceRepository, ReviewRepository, UserRepository
from app.services.llm_service import LLMService
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
        "/recommend — AI-рекомендация OpenAI по базе мест",
        "/ads — рекламные тарифы и покупка показов",
        "",
        "Можно написать обычным текстом: «найди кафе в Казани» или «куда сходить вечером». ",
        "Города в базе: " + ", ".join(city.name for city in MAJOR_RUSSIAN_CITIES),
    ]
)


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
    payload = f"ad:{tariff.code}:{external_id}"
    await callback.message.answer_invoice(
        title=f"Реклама {tariff.title}",
        description=tariff.description,
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=tariff.title, amount=tariff.stars)],
    )
    await callback.answer("Счёт отправлен")


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    if not pre_checkout_query.invoice_payload.startswith("ad:") or pre_checkout_query.currency != "XTR":
        await pre_checkout_query.answer(ok=False, error_message="Некорректный платёж")
        return
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_ad_payment(message: Message) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    payload = message.successful_payment.invoice_payload
    _, tariff_code, external_id = payload.split(":", 2)
    tariff = AD_TARIFFS[tariff_code]
    async with SessionLocal() as session:
        user = await UserRepository(session).get_or_create(
            message.from_user.id, message.from_user.username, message.from_user.first_name
        )
        await AdRepository(session).create_payment(
            user.id,
            external_id,
            tariff.code,
            message.successful_payment.total_amount,
            message.successful_payment.telegram_payment_charge_id,
            message.successful_payment.provider_payment_charge_id,
        )
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
    if parsed.category in {"food", "fun", "relax"}:
        await _send_places(message, parsed.category, city=parsed.city or user.city)
        return

    city = parsed.city or user.city
    places = await _collect_city_places(city)
    answer = await LLMService(get_settings()).recommend(
        user_text=message.text or "куда сходить сегодня",
        city=city,
        places=places,
    )
    await message.answer(answer, reply_markup=main_keyboard())
