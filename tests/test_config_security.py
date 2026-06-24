import pytest

pytest.importorskip("pydantic")
pytest.importorskip("pydantic_settings")

from app.core.config import Settings


def test_admin_ids_are_parsed_from_env_string():
    settings = Settings(ADMIN_IDS="123, 456")
    assert settings.admin_ids == {123, 456}


def test_production_requires_admin_ids():
    settings = Settings(
        APP_ENV="production",
        BOT_TOKEN="1234567890:test.token.for.unit.tests.not.real",
        DATABASE_URL="postgresql+asyncpg://u:p@db/k",
        ADMIN_PASSWORD="safe-password",
        ADMIN_IDS="",
    )
    with pytest.raises(ValueError, match="ADMIN_IDS"):
        settings.validate_production_safety()
