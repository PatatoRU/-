from __future__ import annotations

import asyncio

import httpx
from openai import AsyncOpenAI, OpenAIError

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.place import PlaceDTO

logger = get_logger("app")

SYSTEM_PROMPT = """
Ты — ассистент Telegram-бота «Куда Сегодня». Отвечай по-русски, кратко и полезно.
Помогай выбрать места для еды, развлечений, отдыха, событий и прогулок в крупных городах России.
Не выдумывай точные цены, расписания и наличие билетов. Если не уверен — предложи проверить перед визитом.
""".strip()


class LLMService:
    """LLM recommendation service with OpenAI → OpenRouter → Ollama → deterministic fallback."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.openrouter_client = (
            AsyncOpenAI(api_key=settings.openrouter_api_key, base_url=settings.openrouter_base_url)
            if settings.openrouter_api_key
            else None
        )

    async def recommend(self, user_text: str, city: str, places: list[PlaceDTO]) -> str:
        fallback = self._fallback_response(city=city, places=places)
        prompt = self._build_prompt(user_text=user_text, city=city, places=places)
        for provider_name, call in (
            ("openai", self._recommend_openai),
            ("openrouter", self._recommend_openrouter),
            ("ollama", self._recommend_ollama),
        ):
            try:
                answer = await asyncio.wait_for(call(prompt), timeout=self.settings.llm_timeout_seconds)
            except (OpenAIError, httpx.HTTPError, TimeoutError, asyncio.TimeoutError) as exc:
                logger.warning("llm_provider_failed", provider=provider_name, error=str(exc))
                continue
            except Exception as exc:  # defensive boundary: LLM outage must not break bot flow
                logger.warning("llm_provider_unexpected_error", provider=provider_name, error=str(exc))
                continue
            if answer:
                return answer
        return fallback

    async def _recommend_openai(self, prompt: str) -> str | None:
        if self.openai_client is None:
            return None
        response = await self.openai_client.responses.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=prompt,
            max_output_tokens=600,
        )
        return response.output_text or None

    async def _recommend_openrouter(self, prompt: str) -> str | None:
        if self.openrouter_client is None:
            return None
        response = await self.openrouter_client.chat.completions.create(
            model=self.settings.openrouter_model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            max_tokens=600,
        )
        if not response.choices:
            return None
        return response.choices[0].message.content or None

    async def _recommend_ollama(self, prompt: str) -> str | None:
        async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.ollama_base_url.rstrip('/')}/api/generate",
                json={"model": self.settings.ollama_model, "prompt": f"{SYSTEM_PROMPT}\n\n{prompt}", "stream": False},
            )
            if response.status_code >= 400:
                return None
            data = response.json()
            return data.get("response") or None

    @staticmethod
    def _build_prompt(user_text: str, city: str, places: list[PlaceDTO]) -> str:
        places_context = "\n".join(
            f"- {place.name}: {place.category}, {place.address or 'адрес не указан'}, "
            f"рейтинг {place.rating or '—'}"
            for place in places[:8]
        )
        return (
            f"Город: {city}\n"
            f"Запрос пользователя: {user_text}\n"
            f"Доступные места из базы бота:\n{places_context}\n\n"
            "Составь 3 рекомендации и объясни, кому они подойдут. "
            "Если запрос про детей, семью, свидание, бесплатно или вечер — учти это явно."
        )

    @staticmethod
    def _fallback_response(city: str, places: list[PlaceDTO]) -> str:
        if not places:
            return f"Пока нет рекомендаций для города {city}. Попробуйте /find_food, /find_fun или /events."
        lines = [f"Вот что могу посоветовать в городе {city}:"]
        for place in places[:3]:
            lines.append(f"• {place.name} — {place.description or place.category}")
        return "\n".join(lines)
