import pytest

pytest.importorskip("aiogram")

from app.bot.keyboards import main_keyboard


def test_keyboard_contains_categories():
    text = str(main_keyboard().model_dump())
    assert "🍔 Еда" in text and "⚙ Настройки" in text
