"""Offline district lookup. Geometry is deliberately kept out of models."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from catalog.services.locations import normalize_to_key


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "baku_districts.geojson"


@lru_cache(maxsize=1)
def _features():
    with DATA_FILE.open(encoding="utf-8") as source:
        return json.load(source).get("features", [])


def _point_in_ring(lng: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    previous = len(ring) - 1
    for current, point in enumerate(ring):
        x, y = point[0], point[1]
        previous_x, previous_y = ring[previous][0], ring[previous][1]
        if (y > lat) != (previous_y > lat):
            crossing_x = (previous_x - x) * (lat - y) / (previous_y - y) + x
            if lng < crossing_x:
                inside = not inside
        previous = current
    return inside


def _polygon_contains(lng: float, lat: float, rings) -> bool:
    return bool(rings and _point_in_ring(lng, lat, rings[0]) and not any(_point_in_ring(lng, lat, hole) for hole in rings[1:]))


def district_for_coordinates(lat: float, lng: float) -> str | None:
    """Return a KidsMap Baku district key for a point, otherwise None."""
    for feature in _features():
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        geometry_type = geometry.get("type")
        polygons = [coordinates] if geometry_type == "Polygon" else coordinates if geometry_type == "MultiPolygon" else []
        if any(_polygon_contains(lng, lat, polygon) for polygon in polygons):
            return normalize_to_key(feature["properties"]["district"])
    return None
