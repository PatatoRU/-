from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EventDTO:
    provider: str
    external_id: str
    title: str
    category: str
    city: str
    venue: str
    address: str | None
    description: str
    starts_at: str
    price_label: str
    lat: float | None = None
    lon: float | None = None
    source_url: str | None = None
