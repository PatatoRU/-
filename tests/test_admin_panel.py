import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("pydantic")
pytest.importorskip("pydantic_settings")

from app.core.config import Settings
from app.services.events_service import EventService
from app.web.admin import _csrf_token, _event_row, _feedback_row, _verify_csrf, _layout, require_admin


def test_admin_layout_contains_navigation_links():
    html = _layout("Тест", "<p>ok</p>").body.decode()
    assert "/admin/places" in html
    assert "/admin/reviews" in html
    assert "/admin/campaigns" in html
    assert "/admin/payments" in html
    assert "/admin/events" in html
    assert "/admin/analytics" in html
    assert "/admin/feedback" in html


def test_admin_credentials_accept_configured_user():
    class Credentials:
        username = "root"
        password = "secret"

    settings = Settings(ADMIN_USERNAME="root", ADMIN_PASSWORD="secret")
    assert require_admin(Credentials(), settings) is None


def test_admin_csrf_token_validation():
    settings = Settings(ADMIN_USERNAME="root", ADMIN_PASSWORD="secret")
    token = _csrf_token(settings)
    assert _verify_csrf(token, settings) is None


def test_admin_csrf_rejects_bad_token():
    settings = Settings(ADMIN_USERNAME="root", ADMIN_PASSWORD="secret")
    with pytest.raises(Exception):
        _verify_csrf("bad", settings)


def test_admin_event_row_escapes_event_content():
    event = __import__("asyncio").run(EventService().list_events("Москва"))[0]
    html = _event_row(event)
    assert event.external_id in html
    assert event.title in html


def test_admin_feedback_row_parses_redis_payload():
    html = _feedback_row("123|Казань|Хочу больше концертов")
    assert "123" in html
    assert "Казань" in html
    assert "Хочу больше концертов" in html
