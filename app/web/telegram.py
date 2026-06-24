from __future__ import annotations

import secrets
from typing import Annotated

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.bot.handlers import router as bot_router
from app.bot.middlewares import ErrorMiddleware
from app.core.config import get_settings

router = APIRouter(tags=["telegram"])


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> dict[str, bool]:
    settings = get_settings()
    if settings.telegram_webhook_secret:
        if not x_telegram_bot_api_secret_token or not secrets.compare_digest(
            x_telegram_bot_api_secret_token,
            settings.telegram_webhook_secret,
        ):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram secret token")

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(ErrorMiddleware())
    dispatcher.include_router(bot_router)
    try:
        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
        await dispatcher.feed_update(bot, update)
    finally:
        await bot.session.close()
    return {"ok": True}
