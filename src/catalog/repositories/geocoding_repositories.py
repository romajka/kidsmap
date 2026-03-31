from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

from catalog.interfaces.geocoding import GeocodingPoint, IGeocodingRepository


class GoogleMapsGeocodingRepository(IGeocodingRepository):
    API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def is_configured(self) -> bool:
        return bool((getattr(settings, "GOOGLE_MAPS_API_KEY", "") or "").strip())

    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | None:
        normalized_query = (query or "").strip()
        api_key = (getattr(settings, "GOOGLE_MAPS_API_KEY", "") or "").strip()
        if not normalized_query or not api_key:
            return None

        params = {
            "address": normalized_query,
            "components": "country:AZ",
            "key": api_key,
            "language": language or "ru",
        }
        if region:
            params["region"] = region

        url = f"{self.API_URL}?{urlencode(params)}"

        try:
            with urlopen(url, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, ValueError, json.JSONDecodeError):
            return None

        if payload.get("status") != "OK":
            return None

        results = payload.get("results") or []
        if not results:
            return None

        location = ((results[0].get("geometry") or {}).get("location") or {})
        lat = location.get("lat")
        lng = location.get("lng")
        if lat is None or lng is None:
            return None

        return GeocodingPoint(
            lat=float(lat),
            lng=float(lng),
            formatted_address=(results[0].get("formatted_address") or "").strip(),
        )
