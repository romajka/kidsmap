"""Public map points: verified physical identity, never inferred business identity."""
import math
from catalog.services.public_presentation import prepare_cards


def valid_coordinates(lat, lng):
    try:
        if lat is None or lng is None or isinstance(lat, bool) or isinstance(lng, bool):
            return None
        lat, lng = float(lat), float(lng)
    except (ValueError, TypeError, OverflowError):
        return None
    if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
        return None
    # Existing map transport excludes the conventional missing-coordinate sentinel.
    if abs(lat) < .001 and abs(lng) < .001:
        return None
    return lat, lng


def map_identity(place):
    location = place.confirmed_location if place.confirmed_location_id else None
    if location and place.venue_confirmed_at and location.confirmed_at and location.archived_at is None:
        coords = valid_coordinates(location.lat, location.lng)
        if coords:
            return f'venue:{location.pk}', coords
        # A verified address-only location has no authoritative pin. Keep the list,
        # rather than choosing one business's coordinates for every member.
        return None
    coords = valid_coordinates(place.lat, place.lng)
    return (f'place:{place.pk}', coords) if coords else None


def serialize_map_places(qs, language_code, filters=None):
    from django.utils.translation import override
    with override(language_code):
        return _serialize_map_places(qs, language_code, filters)


def _serialize_map_places(qs, language_code, filters=None):
    if filters is not None:
        qs = filters.apply(qs)
    points = {}
    seen = set()
    for place in prepare_cards(qs, language_code, filters=filters):
        if place.pk in seen:
            continue
        seen.add(place.pk)
        identity = map_identity(place)
        if not identity:
            continue
        key, (lat, lng) = identity
        data = place._card_presentation
        category = place.category
        member = {
            'id': place.pk, 'name': data['name'], 'url': data['url'],
            'lat': lat, 'lng': lng, 'price': data['prices']['label'],
            'image_url': data['image_url'], 'has_phone': data['contacts']['has_phone'],
            'category': data['category_label'], 'category_code': place.category_code,
            'category_color_bg': category.resolved_color_bg if category else '#F3F4F6',
            'category_color_text': category.resolved_color_text if category else '#6B7280',
            'category_icon_svg': category.icon_svg_source if category else '',
            'category_icon_url': category.icon_file_url if category else '',
            'category_icon_is_svg': category.icon_is_svg if category else False,
            'category_icon_is_font': category.icon_is_font_class if category else False,
            'category_icon_name': category.icon if category else '',
            'address': place.address_i18n(language_code),
            'district': place.district, 'district_label': place.district_i18n(language_code),
            'metro': place.metro, 'metro_label': place.metro_i18n(language_code),
            'location': ' / '.join(filter(None, (place.district_i18n(language_code), place.metro_i18n(language_code)))),
            'rating': float(place.rating_avg) if place.rating_avg is not None else None,
            'reviews_count': int(place.rating_count or 0),
            'schedule': place.schedule_summary or '',
            'matched_offers': data['matched_offers'],
            'translation_fallback': data['translation_fallback'], 'content_language': data['content_language'],
            'translation_label': {'az':'Mətn azərbaycancadır', 'ru':'Текст на азербайджанском', 'en':'Text in Azerbaijani'}.get(language_code, 'Mətn azərbaycancadır') if data['translation_fallback'] else '',
        }
        if key not in points:
            points[key] = {**member, 'key': key, 'members': []}
        points[key]['members'].append(member)
    return list(points.values())


def venue_identity_patch_changed(previous, values):
    return any(name in values and values[name] != getattr(previous, name) for name in ('address', 'lat', 'lng'))


def venue_identity_changed(previous, current, fields=None):
    return venue_identity_patch_changed(previous, {
        name: getattr(current, name) for name in ('address', 'lat', 'lng')
        if fields is None or name in fields
    })
