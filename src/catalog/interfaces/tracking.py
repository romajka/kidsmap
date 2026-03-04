from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

from catalog.models import Place


class IEventPlaceRepository(ABC):
    @abstractmethod
    def find_active_for_event(self, place_id: int) -> Place | None:
        raise NotImplementedError


class IFunnelEventRepository(ABC):
    @abstractmethod
    def create_event(
        self,
        *,
        event_type: str,
        path: str,
        place: Place | None,
        user,
        session_key: str,
        event_meta: dict[str, Any],
    ) -> None:
        raise NotImplementedError


class ISiteVisitRepository(ABC):
    @abstractmethod
    def increment_or_create_hit(self, *, day: date, session_key: str, path: str) -> None:
        raise NotImplementedError
