from __future__ import annotations

import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.conf import settings

from catalog.interfaces.geocoding import GeocodingIssue, GeocodingPoint, IGeocodingRepository
from catalog.services.place_card_validation import AZERBAIJAN_BOUNDS


GEOCODING_POINT_TYPES = ("street_address", "premise", "subpremise", "establishment", "point_of_interest", "intersection")
GEOCODING_TRANSIT_TYPES = ("transit_station", "subway_station", "train_station", "bus_station", "light_rail_station")
GEOCODING_POINT_PRECISIONS = ("ROOFTOP", "GEOMETRIC_CENTER")


def _read_candidate(candidate) -> GeocodingPoint | GeocodingIssue:
    if not isinstance(candidate, dict):
        return GeocodingIssue.PROVIDER_ERROR
    geometry = candidate.get("geometry")
    if not isinstance(geometry, dict) or not isinstance(geometry.get("location"), dict):
        return GeocodingIssue.PROVIDER_ERROR
    location = geometry["location"]
    lat, lng = location.get("lat"), location.get("lng")
    if type(lat) not in (int, float) or type(lng) not in (int, float):
        return GeocodingIssue.PROVIDER_ERROR
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return GeocodingIssue.PROVIDER_ERROR

    min_lat, max_lat, min_lng, max_lng = AZERBAIJAN_BOUNDS
    if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
        return GeocodingIssue.LOCATION_UNRESOLVED
    components = candidate.get("address_components", [])
    if not isinstance(components, list):
        return GeocodingIssue.PROVIDER_ERROR
    for component in components:
        if not isinstance(component, dict) or not isinstance(component.get("types"), list):
            return GeocodingIssue.PROVIDER_ERROR
        if "country" in component["types"] and component.get("short_name") != "AZ":
            return GeocodingIssue.LOCATION_UNRESOLVED

    types = candidate.get("types")
    if not isinstance(types, list) or not all(isinstance(kind, str) for kind in types):
        return GeocodingIssue.PROVIDER_ERROR
    if (candidate.get("partial_match") or geometry.get("location_type") not in GEOCODING_POINT_PRECISIONS
            or not any(kind in GEOCODING_POINT_TYPES for kind in types)
            or any(kind in GEOCODING_TRANSIT_TYPES for kind in types)):
        return GeocodingIssue.AMBIGUOUS
    address = candidate.get("formatted_address")
    return GeocodingPoint(lat=lat, lng=lng, formatted_address=address.strip() if isinstance(address, str) else "")


def _select_point(results) -> GeocodingPoint | GeocodingIssue | None:
    if not isinstance(results, list):
        return GeocodingIssue.PROVIDER_ERROR
    if not results:
        return None
    points = {}
    issues = set()
    for candidate in results:
        result = _read_candidate(candidate)
        if isinstance(result, GeocodingIssue):
            issues.add(result)
        else:
            # Editor inputs and map submissions use six decimal places.
            points[(round(result.lat, 6), round(result.lng, 6))] = result
    if len(points) == 1:
        return next(iter(points.values()))
    if points or GeocodingIssue.AMBIGUOUS in issues:
        return GeocodingIssue.AMBIGUOUS
    if GeocodingIssue.LOCATION_UNRESOLVED in issues:
        return GeocodingIssue.LOCATION_UNRESOLVED
    return GeocodingIssue.PROVIDER_ERROR


class GoogleMapsGeocodingRepository(IGeocodingRepository):
    API_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def is_configured(self) -> bool:
        return bool((getattr(settings, "GOOGLE_MAPS_API_KEY", "") or "").strip())

    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | GeocodingIssue | None:
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
        except (OSError, URLError, ValueError):
            return GeocodingIssue.PROVIDER_ERROR

        if not isinstance(payload, dict):
            return GeocodingIssue.PROVIDER_ERROR
        if payload.get("status") == "ZERO_RESULTS":
            return None
        if payload.get("status") != "OK":
            return GeocodingIssue.PROVIDER_ERROR
        return _select_point(payload.get("results"))
