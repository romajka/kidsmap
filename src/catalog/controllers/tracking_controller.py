from __future__ import annotations

import json
from dataclasses import dataclass

from catalog.services.tracking import track_cta_click_event


@dataclass(slots=True)
class TrackEventResult:
    ok: bool
    status_code: int
    error: str = ""

    def as_payload(self) -> dict:
        if self.ok:
            return {"ok": True}
        return {"ok": False, "error": self.error}


class TrackingController:
    @classmethod
    def build_default(cls) -> "TrackingController":
        return cls()

    def track_cta_event_from_json(self, *, request, raw_body: bytes) -> TrackEventResult:
        try:
            payload = json.loads((raw_body or b"{}").decode("utf-8"))
        except (ValueError, TypeError, UnicodeDecodeError):
            return TrackEventResult(ok=False, status_code=400, error="invalid_payload")

        event_type = str(payload.get("event_type") or "").strip()
        place_id_raw = payload.get("place_id")
        source = str(payload.get("source") or "").strip()
        path = str(payload.get("path") or "").strip()

        place_id = None
        if str(place_id_raw).isdigit():
            place_id = int(place_id_raw)

        saved = track_cta_click_event(
            request=request,
            event_type=event_type,
            place_id=place_id,
            source=source,
            path=path,
        )
        if not saved:
            return TrackEventResult(ok=False, status_code=400, error="unsupported_event")

        return TrackEventResult(ok=True, status_code=200)
