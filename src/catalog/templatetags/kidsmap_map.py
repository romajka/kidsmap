"""Template helpers for map data and address lookup."""
import json

from catalog.services.map_payload import compact_map_point
from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Same escaping as Django's json_script: the payload can never close the tag.
_SCRIPT_ESCAPES = (('>', '\\u003E'), ('<', '\\u003C'), ('&', '\\u0026'))


@register.filter
def map_points_json(points, element_id):
    """Like ``json_script`` but without duplicate members and \\u-escaped letters
    (Azerbaijani and Russian text stays as UTF-8): about half the bytes."""
    data = json.dumps([compact_map_point(point) for point in (points or [])], cls=DjangoJSONEncoder,
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


@register.filter(is_safe=True)
def compact_catalog_layout(html):
    """Keep a separating space between elements; leave preformatted content intact."""
    import re

    protected = r"<!--.*?-->|<(script|style|pre|textarea)\b[^>]*>.*?</\1\s*>"
    pattern = protected + r"|(?<=>)[ \t\r\n]+(?=<)"
    return re.sub(pattern, lambda match: match[0] if match[0].startswith("<") else " ",
                  str(html), flags=re.DOTALL | re.IGNORECASE)
