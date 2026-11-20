from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


@dataclass(slots=True)
class GeocodingPoint:
    lat: float
    lng: float
    formatted_address: str = ""


class GeocodingIssue(Enum):
    AMBIGUOUS = "ambiguous"
    PROVIDER_ERROR = "provider_error"
    LOCATION_UNRESOLVED = "location_unresolved"


class IGeocodingRepository(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | GeocodingIssue | None:
        raise NotImplementedError
