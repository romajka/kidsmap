from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class GeocodingPoint:
    lat: float
    lng: float
    formatted_address: str = ""


class IGeocodingRepository(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | None:
        raise NotImplementedError
