from pydantic import BaseModel


class PlaceDTO(BaseModel):
    provider: str = "local_curated"
    external_id: str
    name: str
    category: str
    city: str
    address: str | None = None
    description: str | None = None
    lat: float | None = None
    lon: float | None = None
    rating: float | None = None
    phone: str | None = None
    website: str | None = None
    working_hours: str | None = None
    source_url: str | None = None
