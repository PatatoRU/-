from __future__ import annotations

import html
import hmac
import secrets
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings as AppSettings
from app.core.config import get_settings
from app.db.session import get_session
from app.models import AdCampaign, AdPayment, Place, Review, SearchHistory, User

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


def _escape(value: object) -> str:
    return html.escape("" if value is None else str(value))


def _csrf_token(settings: AppSettings) -> str:
    return hmac.new(settings.admin_password.encode("utf-8"), b"admin-csrf", "sha256").hexdigest()


def _verify_csrf(token: str, settings: AppSettings) -> None:
    if not secrets.compare_digest(token, _csrf_token(settings)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token")


def _layout(title: str, body: str) -> HTMLResponse:
    nav = """
    <nav>
      <a href="/admin">Дашборд</a>
      <a href="/admin/places">Места</a>
      <a href="/admin/reviews">Отзывы</a>
      <a href="/admin/campaigns">Реклама</a>
      <a href="/admin/payments">Платежи</a>
    </nav>
    """
    html_doc = f"""
    <!doctype html>
    <html lang="ru">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>{_escape(title)} — Куда Сегодня Admin</title>
        <style>
          body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; margin: 0; background: #f6f7fb; color: #17202a; }}
          header {{ background: #101828; color: white; padding: 18px 28px; }}
          main {{ padding: 24px 28px; }}
          nav {{ display: flex; gap: 12px; padding: 12px 28px; background: white; border-bottom: 1px solid #e4e7ec; }}
          nav a {{ color: #175cd3; text-decoration: none; font-weight: 600; }}
          table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }}
          th, td {{ padding: 10px 12px; border-bottom: 1px solid #eaecf0; text-align: left; vertical-align: top; }}
          th {{ background: #f2f4f7; font-size: 13px; text-transform: uppercase; color: #475467; }}
          .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
          .card {{ background: white; border: 1px solid #e4e7ec; border-radius: 12px; padding: 18px; }}
          .metric {{ font-size: 32px; font-weight: 800; }}
          .muted {{ color: #667085; }}
          .badge {{ padding: 3px 8px; border-radius: 999px; background: #eef4ff; color: #175cd3; font-weight: 700; }}
          button {{ border: 0; border-radius: 8px; padding: 8px 10px; cursor: pointer; font-weight: 700; }}
          .danger {{ background: #fee4e2; color: #b42318; }}
          .ok {{ background: #dcfae6; color: #067647; }}
        </style>
      </head>
      <body>
        <header><h1>{_escape(title)}</h1><div class="muted">Админ-панель «Куда Сегодня»</div></header>
        {nav}
        <main>{body}</main>
      </body>
    </html>
    """
    return HTMLResponse(html_doc)


def require_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    settings: Annotated[AppSettings, Depends(get_settings)],
) -> None:
    username_ok = secrets.compare_digest(credentials.username, settings.admin_username)
    password_ok = secrets.compare_digest(credentials.password, settings.admin_password)
    if not username_ok or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


AdminSession = Annotated[AsyncSession, Depends(get_session)]
AdminAuth = Annotated[None, Depends(require_admin)]


@router.get("", response_class=HTMLResponse)
async def dashboard(_: AdminAuth, session: AdminSession) -> Response:
    users = await session.scalar(select(func.count(User.id))) or 0
    places = await session.scalar(select(func.count(Place.id))) or 0
    reviews = await session.scalar(select(func.count(Review.id))) or 0
    active_ads = await session.scalar(select(func.count(AdCampaign.id)).where(AdCampaign.status == "active")) or 0
    stars = await session.scalar(select(func.coalesce(func.sum(AdPayment.stars_amount), 0))) or 0
    searches = await session.scalar(select(func.count(SearchHistory.id))) or 0
    body = f"""
    <section class="cards">
      <div class="card"><div class="metric">{users}</div><div>Пользователи</div></div>
      <div class="card"><div class="metric">{places}</div><div>Места</div></div>
      <div class="card"><div class="metric">{reviews}</div><div>Отзывы</div></div>
      <div class="card"><div class="metric">{active_ads}</div><div>Активная реклама</div></div>
      <div class="card"><div class="metric">{stars}⭐</div><div>Stars выручка</div></div>
      <div class="card"><div class="metric">{searches}</div><div>Поиски</div></div>
    </section>
    """
    return _layout("Дашборд", body)


@router.get("/places", response_class=HTMLResponse)
async def places(_: AdminAuth, session: AdminSession) -> Response:
    result = await session.scalars(select(Place).order_by(Place.id.desc()).limit(100))
    rows = "".join(_place_row(place) for place in result.all())
    return _layout("Места", f"<table><tr><th>ID</th><th>Название</th><th>Категория</th><th>Город</th><th>Рейтинг</th><th>Контакты</th></tr>{rows}</table>")


def _place_row(place: Place) -> str:
    contacts = "<br>".join(filter(None, [_escape(place.phone), _escape(place.website)]))
    return f"""
    <tr>
      <td>{place.id}</td><td>{_escape(place.name)}<br><span class="muted">{_escape(place.address)}</span></td>
      <td>{_escape(place.category)}</td><td>{_escape(place.city)}</td><td>{_escape(place.rating)}</td><td>{contacts}</td>
    </tr>
    """


@router.get("/reviews", response_class=HTMLResponse)
async def reviews(_: AdminAuth, session: AdminSession) -> Response:
    result = await session.scalars(select(Review).options(selectinload(Review.place)).order_by(Review.created_at.desc()).limit(100))
    rows = "".join(_review_row(review) for review in result.all())
    return _layout("Отзывы", f"<table><tr><th>ID</th><th>Место</th><th>Оценка</th><th>Текст</th><th>Дата</th></tr>{rows}</table>")


def _review_row(review: Review) -> str:
    return f"""
    <tr>
      <td>{review.id}</td><td>{_escape(review.place.name if review.place else review.place_id)}</td>
      <td>{review.rating}⭐</td><td>{_escape(review.text)}</td><td>{_escape(review.created_at)}</td>
    </tr>
    """


@router.get("/campaigns", response_class=HTMLResponse)
async def campaigns(_: AdminAuth, session: AdminSession, settings: Annotated[AppSettings, Depends(get_settings)]) -> Response:
    result = await session.scalars(select(AdCampaign).options(selectinload(AdCampaign.place)).order_by(AdCampaign.created_at.desc()).limit(100))
    csrf_token = _csrf_token(settings)
    rows = "".join(_campaign_row(campaign, csrf_token) for campaign in result.all())
    return _layout("Реклама", f"<table><tr><th>ID</th><th>Место</th><th>Тариф</th><th>Статус</th><th>Приоритет</th><th>До</th><th>Действия</th></tr>{rows}</table>")


def _campaign_row(campaign: AdCampaign, csrf_token: str) -> str:
    next_status = "paused" if campaign.status == "active" else "active"
    action_label = "Пауза" if campaign.status == "active" else "Активировать"
    action_class = "danger" if campaign.status == "active" else "ok"
    return f"""
    <tr>
      <td>{campaign.id}</td><td>{_escape(campaign.place.name if campaign.place else campaign.place_id)}</td>
      <td>{_escape(campaign.tariff_code)} / {campaign.stars_paid}⭐</td><td><span class="badge">{_escape(campaign.status)}</span></td>
      <td>{campaign.priority}</td><td>{_escape(campaign.ends_at)}</td>
      <td><form method="post" action="/admin/campaigns/{campaign.id}/status?status={next_status}&csrf_token={csrf_token}"><button class="{action_class}">{action_label}</button></form></td>
    </tr>
    """


@router.post("/campaigns/{campaign_id}/status")
async def set_campaign_status(campaign_id: int, status: str, csrf_token: str, _: AdminAuth, session: AdminSession, settings: Annotated[AppSettings, Depends(get_settings)]) -> RedirectResponse:
    _verify_csrf(csrf_token, settings)
    if status not in {"active", "paused", "rejected"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    campaign = await session.get(AdCampaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.status = status
    await session.commit()
    return RedirectResponse(url="/admin/campaigns", status_code=303)


@router.get("/payments", response_class=HTMLResponse)
async def payments(_: AdminAuth, session: AdminSession) -> Response:
    result = await session.scalars(select(AdPayment).order_by(AdPayment.created_at.desc()).limit(100))
    rows = "".join(_payment_row(payment) for payment in result.all())
    return _layout("Платежи", f"<table><tr><th>ID</th><th>User</th><th>Place</th><th>Тариф</th><th>Stars</th><th>Charge</th><th>Дата</th></tr>{rows}</table>")


def _payment_row(payment: AdPayment) -> str:
    return f"""
    <tr>
      <td>{payment.id}</td><td>{payment.user_id}</td><td>{payment.place_id}</td><td>{_escape(payment.tariff_code)}</td>
      <td>{payment.stars_amount}⭐</td><td>{_escape(payment.telegram_payment_charge_id)}</td><td>{_escape(payment.created_at)}</td>
    </tr>
    """
