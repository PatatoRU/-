from abc import ABC, abstractmethod
from app.schemas.place import PlaceDTO
class PlacesProvider(ABC):
    name: str
    @abstractmethod
    async def search(self, category: str, city: str | None = None, lat: float | None = None, lon: float | None = None) -> list[PlaceDTO]: ...
