from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdTariff:
    code: str
    title: str
    stars: int
    days: int
    priority: int
    daily_request_limit: int
    description: str


AD_TARIFFS: dict[str, AdTariff] = {
    "free": AdTariff(
        code="free",
        title="Free Start",
        stars=0,
        days=7,
        priority=1,
        daily_request_limit=20,
        description="1 бесплатное рекламное место на 7 дней, базовый показ в выдаче.",
    ),
    "boost": AdTariff(
        code="boost",
        title="Boost",
        stars=150,
        days=14,
        priority=5,
        daily_request_limit=200,
        description="Приоритетный показ в выдаче на 14 дней и расширенный лимит запросов.",
    ),
    "premium": AdTariff(
        code="premium",
        title="Premium",
        stars=450,
        days=30,
        priority=10,
        daily_request_limit=1000,
        description="Максимальный приоритет в рекламных слотах на 30 дней.",
    ),
}

DEFAULT_DAILY_REQUEST_LIMIT = AD_TARIFFS["free"].daily_request_limit
