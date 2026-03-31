from __future__ import annotations

from dataclasses import dataclass

from catalog.interfaces.geocoding import GeocodingPoint, IGeocodingRepository
from catalog.repositories.geocoding_repositories import GoogleMapsGeocodingRepository

GEOCODING_LOCATION_FIELDS = ("address", "district", "metro")


@dataclass(slots=True)
class PlaceGeocodingLookupResult:
    resolved: bool
    reason: str
    query: str
    point: GeocodingPoint | None = None


@dataclass(slots=True)
class PlaceGeocodingResult:
    updated: bool
    reason: str
    point: GeocodingPoint | None = None


@dataclass(slots=True)
class PlaceGeocodingService:
    geocoding_repository: IGeocodingRepository

    @classmethod
    def build_default(cls) -> "PlaceGeocodingService":
        return cls(geocoding_repository=GoogleMapsGeocodingRepository())

    @staticmethod
    def build_query_from_location(*, address: str = "", district: str = "", metro: str = "") -> str:
        address = (address or "").strip()
        if not address:
            return ""

        parts: list[str] = [address]
        district = (district or "").strip()
        metro = (metro or "").strip()

        if district:
            parts.append(district)
        if metro:
            parts.append(f"метро {metro}")

        parts.extend(["Баку", "Азербайджан"])

        normalized_parts: list[str] = []
        seen: set[str] = set()
        for raw_value in parts:
            value = (raw_value or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized_parts.append(value)
        return ", ".join(normalized_parts)

    @classmethod
    def build_query(cls, place) -> str:
        return cls.build_query_from_location(
            address=getattr(place, "address", ""),
            district=getattr(place, "district", ""),
            metro=getattr(place, "metro", ""),
        )

    def geocode_location(
        self,
        *,
        address: str = "",
        district: str = "",
        metro: str = "",
    ) -> PlaceGeocodingLookupResult:
        query = self.build_query_from_location(address=address, district=district, metro=metro)
        if not query:
            return PlaceGeocodingLookupResult(resolved=False, reason="missing_query", query="")

        if not self.geocoding_repository.is_configured():
            return PlaceGeocodingLookupResult(resolved=False, reason="provider_not_configured", query=query)

        point = self.geocoding_repository.geocode(query=query, language="ru", region="az")
        if point is None:
            return PlaceGeocodingLookupResult(resolved=False, reason="not_found", query=query)

        return PlaceGeocodingLookupResult(resolved=True, reason="resolved", query=query, point=point)

    def geocode_place(self, *, place, overwrite: bool = False) -> PlaceGeocodingResult:
        has_coordinates = place.lat is not None and place.lng is not None
        if has_coordinates and not overwrite:
            return PlaceGeocodingResult(updated=False, reason="coordinates_present")

        lookup_result = self.geocode_location(
            address=getattr(place, "address", ""),
            district=getattr(place, "district", ""),
            metro=getattr(place, "metro", ""),
        )
        if not lookup_result.resolved or lookup_result.point is None:
            return PlaceGeocodingResult(updated=False, reason=lookup_result.reason)

        point = lookup_result.point
        if place.lat == point.lat and place.lng == point.lng:
            return PlaceGeocodingResult(updated=False, reason="unchanged", point=point)

        place.lat = point.lat
        place.lng = point.lng
        place.save(update_fields=["lat", "lng", "updated_at"])
        return PlaceGeocodingResult(updated=True, reason="updated", point=point)


def place_location_fields_changed(*, previous_values: dict[str, object], place) -> bool:
    return any(previous_values.get(field_name) != getattr(place, field_name) for field_name in GEOCODING_LOCATION_FIELDS)
