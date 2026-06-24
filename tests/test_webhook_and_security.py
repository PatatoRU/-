import pytest

pytest.importorskip("pydantic")
pytest.importorskip("pydantic_settings")

from app.core.config import Settings


def test_production_webhook_requires_secret():
    settings = Settings(APP_ENV="production", BOT_TOKEN="1234567890:abcdefghijklmnopqrstuvwxyzABCDE", DATABASE_URL="postgresql+asyncpg://u:p@db/k", ADMIN_PASSWORD="safe-password", BOT_MODE="webhook")
    with pytest.raises(ValueError, match="TELEGRAM_WEBHOOK_SECRET"):
        settings.validate_production_safety()


def test_production_admin_password_must_be_changed():
    settings = Settings(APP_ENV="production", BOT_TOKEN="1234567890:abcdefghijklmnopqrstuvwxyzABCDE", DATABASE_URL="postgresql+asyncpg://u:p@db/k", ADMIN_PASSWORD="change_me")
    with pytest.raises(ValueError, match="ADMIN_PASSWORD"):
        settings.validate_production_safety()
