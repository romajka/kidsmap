"""Offline administrative lookup, independent of Place/Branch and map providers.

GeoJSON uses longitude, latitude. Public functions take latitude, longitude.
Boundary tolerance is 1e-6 degrees (about 0.1 m), matching the map pickers'
coordinate precision; it is NOT a claim about survey accuracy of the dataset.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

from catalog.services.locations import BAKU_DISTRICTS_MAP, normalize_to_key

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "baku_districts.geojson"
BOUNDARY_EPSILON = 1e-6


@dataclass(frozen=True)
class LocationResolution:
    status: str
    city_key: str = ""
    district_key: str = ""
    candidates: tuple[str, ...] = ()
    dataset_version: str = ""


@lru_cache(maxsize=1)
def _dataset():
    raw = DATA_FILE.read_bytes()
    data = json.loads(raw)
    features = data['features']
    if not features or data.get('type') != 'FeatureCollection':
        raise ValueError('Invalid administrative dataset')
    return features, 'baku-' + hashlib.sha256(raw).hexdigest()[:16]


def _features():
    return _dataset()[0]


def _point_in_ring(lng, lat, ring):
    inside = False
    for a, b in zip(ring, ring[1:]):
        x, y = a[:2]
        previous_x, previous_y = b[:2]
        if (y > lat) != (previous_y > lat):
            crossing_x = (previous_x - x) * (lat - y) / (previous_y - y) + x
            if lng < crossing_x:
                inside = not inside
    return inside


def _on_ring(lng, lat, ring):
    for a, b in zip(ring, ring[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length_squared = dx * dx + dy * dy
        t = max(0, min(1, ((lng - a[0]) * dx + (lat - a[1]) * dy) / length_squared)) if length_squared else 0
        if math.hypot(lng - (a[0] + t * dx), lat - (a[1] + t * dy)) <= BOUNDARY_EPSILON:
            return True
    return False


def _polygon_contains(lng, lat, rings):
    return bool(rings and _point_in_ring(lng, lat, rings[0]) and not any(_point_in_ring(lng, lat, hole) for hole in rings[1:]))


def resolve_location(lat, lng) -> LocationResolution:
    try:
        if isinstance(lat, bool) or isinstance(lng, bool):
            raise ValueError('Boolean coordinate')
        lat, lng = float(lat), float(lng)
        if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError('Invalid coordinate')
    except (TypeError, ValueError, OverflowError):
        return LocationResolution('invalid_coordinates')

    matches, boundary = set(), False
    try:
        features = _features()
        version = _dataset()[1]
        for feature in features:
            key = normalize_to_key(feature['properties']['district'])
            if key not in BAKU_DISTRICTS_MAP:
                raise ValueError('Unknown administrative key')
            geometry = feature['geometry']
            if geometry['type'] not in ('Polygon', 'MultiPolygon'):
                raise ValueError('Invalid administrative geometry')
            polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
            for rings in polygons:
                if not rings or any(len(ring) < 4 or ring[0] != ring[-1] for ring in rings):
                    raise ValueError('Unclosed administrative ring')
                if any(_on_ring(lng, lat, ring) for ring in rings):
                    boundary = True
                    matches.add(key)
                elif _polygon_contains(lng, lat, rings):
                    matches.add(key)
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return LocationResolution('unavailable')

    candidates = tuple(sorted(matches))
    if boundary or len(matches) > 1:
        return LocationResolution('ambiguous', 'baku', candidates=candidates, dataset_version=version)
    if matches:
        return LocationResolution('resolved', 'baku', candidates[0], candidates, version)
    return LocationResolution('outside_coverage', dataset_version=version)


def district_for_coordinates(lat, lng) -> str | None:
    """Compatibility API. Ambiguous points never silently choose a district."""
    result = resolve_location(lat, lng)
    return result.district_key if result.status == 'resolved' else None
