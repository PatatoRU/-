from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.core.logging import get_logger

logger = get_logger("telegram")


class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            logger.exception("telegram_handler_error", error=str(exc))
            message = getattr(event, "message", None) or event
            if hasattr(message, "answer"):
                await message.answer("Что-то пошло не так, но я уже восстановился. Попробуйте ещё раз.")
            return None
