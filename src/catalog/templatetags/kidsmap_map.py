"""Template helpers for map data and address lookup."""
import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Same escaping as Django's json_script: the payload can never close the tag.
_SCRIPT_ESCAPES = (('>', '\\u003E'), ('<', '\\u003C'), ('&', '\\u0026'))


def _compact_point(point):
    """Drop ``members`` when it only repeats the point itself.

    A venue with one place is serialised as the place plus a one-item
    ``members`` copy; every map script already treats a point without
    ``members`` as ``[point]``.
    """
    members = point.get('members')
    if isinstance(members, list) and len(members) == 1 and isinstance(members[0], dict):
        if all(point.get(key) == value for key, value in members[0].items()):
            return {key: value for key, value in point.items() if key != 'members'}
    return point


@register.filter
def map_points_json(points, element_id):
    """Like ``json_script`` but without duplicate members and \\u-escaped letters
    (Azerbaijani and Russian text stays as UTF-8): about half the bytes."""
    data = json.dumps([_compact_point(point) for point in (points or [])], cls=DjangoJSONEncoder,
                      ensure_ascii=False, separators=(',', ':'))
    for char, escaped in _SCRIPT_ESCAPES:
        data = data.replace(char, escaped)
    return format_html('<script id="{}" type="application/json">{}</script>', element_id, mark_safe(data))


@register.simple_tag
def geocoding_policy_json():
    from catalog.repositories.geocoding_repositories import (
        AZERBAIJAN_BOUNDS, GEOCODING_POINT_PRECISIONS, GEOCODING_POINT_TYPES, GEOCODING_TRANSIT_TYPES,
    )
    return json.dumps({
        "bounds": AZERBAIJAN_BOUNDS,
        "types": GEOCODING_POINT_TYPES,
        "transit": GEOCODING_TRANSIT_TYPES,
        "precision": GEOCODING_POINT_PRECISIONS,
    }, separators=(",", ":"))
