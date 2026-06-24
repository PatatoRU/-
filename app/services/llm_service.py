from __future__ import annotations

from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.place import PlaceDTO

logger = get_logger("app")

SYSTEM_PROMPT = """
Ты — ассистент Telegram-бота «Куда Сегодня». Отвечай по-русски, кратко и полезно.
Помогай выбрать места для еды, развлечений, отдыха и прогулок в крупных городах России.
Не выдумывай точные цены, расписания и наличие билетов. Если не уверен — предложи проверить перед визитом.
""".strip()


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    async def recommend(self, user_text: str, city: str, places: list[PlaceDTO]) -> str:
        fallback = self._fallback_response(city=city, places=places)
        if self.client is None:
            return fallback

        places_context = "\n".join(
            f"- {place.name}: {place.category}, {place.address or 'адрес не указан'}, "
            f"рейтинг {place.rating or '—'}"
            for place in places[:8]
        )
        try:
            response = await self.client.responses.create(
                model=self.settings.openai_model,
                instructions=SYSTEM_PROMPT,
                input=(
                    f"Город: {city}\n"
                    f"Запрос пользователя: {user_text}\n"
                    f"Доступные места из базы бота:\n{places_context}\n\n"
                    "Составь 3 рекомендации и объясни, кому они подойдут."
                ),
            )
            return response.output_text or fallback
        except OpenAIError as exc:
            logger.warning("openai_recommendation_failed", error=str(exc))
            return fallback

    @staticmethod
    def _fallback_response(city: str, places: list[PlaceDTO]) -> str:
        if not places:
            return f"Пока нет рекомендаций для города {city}. Попробуйте /find_food или /find_fun."
        lines = [f"Вот что могу посоветовать в городе {city}:"]
        for place in places[:3]:
            lines.append(f"• {place.name} — {place.description or place.category}")
        return "\n".join(lines)
