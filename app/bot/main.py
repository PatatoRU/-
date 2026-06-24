from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.bot.handlers import router
from app.bot.middlewares import ErrorMiddleware
from app.core.config import get_settings
from app.core.logging import setup_logging

BOT_COMMANDS = [
    BotCommand(command="start", description="Запуск"),
    BotCommand(command="help", description="Помощь"),
    BotCommand(command="profile", description="Профиль"),
    BotCommand(command="find_food", description="Найти еду"),
    BotCommand(command="find_fun", description="Найти развлечения"),
    BotCommand(command="find_relax", description="Найти отдых"),
    BotCommand(command="favorites", description="Избранное"),
    BotCommand(command="history", description="История"),
    BotCommand(command="settings", description="Настройки"),
    BotCommand(command="recommend", description="AI-рекомендация"),
    BotCommand(command="ads", description="Реклама и тарифы"),
]


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    settings.validate_production_safety()
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.update.outer_middleware(ErrorMiddleware())
    dispatcher.include_router(router)
    await bot.set_my_commands(BOT_COMMANDS)
    if settings.bot_mode == "webhook":
        if settings.telegram_webhook_url:
            await bot.set_webhook(
                settings.telegram_webhook_url,
                secret_token=settings.telegram_webhook_secret,
                drop_pending_updates=True,
            )
        await bot.session.close()
        return
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
