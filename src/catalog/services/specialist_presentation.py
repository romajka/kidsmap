"""Public labels and consent/date presentation; no inferred identity or consent."""
import math

from django.core.exceptions import ValidationError
from django.utils import timezone
from catalog.models.specialist_domain import SpecialistEmployment
from catalog.services.age_display import format_age_range
from catalog.services.phone_numbers import normalize_whatsapp, safe_phone
from catalog.services.pricing_plans import format_price_amount, format_price_range
from catalog.services.public_presentation import language_code, visible


_LABELS = {
    'az': {
        'any_age': 'Hər hansı yaş', 'years': 'yaş',
        'from_price': '{value} AZN-dən', 'to_price': '{value} AZN-dək',
        'languages': ('Azərbaycan dili', 'Rus dili', 'İngilis dili'),
        'formats': {'online': 'Yalnız onlayn', 'offline': 'Yalnız əyani', 'both': 'Onlayn və əyani'},
        'private_office': 'Şəxsi kabinet',
    },
    'ru': {
        'any_age': 'Любой возраст', 'years': 'лет',
        'from_price': 'от {value} AZN', 'to_price': 'до {value} AZN',
        'languages': ('Азербайджанский', 'Русский', 'Английский'),
        'formats': {'online': 'Только онлайн', 'offline': 'Только очно', 'both': 'Онлайн и очно'},
        'private_office': 'Собственный кабинет',
    },
    'en': {
        'any_age': 'Any age', 'years': 'years',
        'from_price': 'from {value} AZN', 'to_price': 'up to {value} AZN',
        'languages': ('Azerbaijani', 'Russian', 'English'),
        'formats': {'online': 'Online only', 'offline': 'In person only', 'both': 'Online and in person'},
        'private_office': 'Private office',
    },
}


def _public_labels(specialist, language):
    words = _LABELS[language]
    low, high = specialist.price_from, specialist.price_to
    if low is not None and high is not None:
        price = format_price_range(low, high, language)['full']
    elif low is not None:
        price = words['from_price'].format(value=format_price_amount(low))
    elif high is not None:
        price = words['to_price'].format(value=format_price_amount(high))
    else:
        price = '—'
    age = format_age_range(specialist.age_from, specialist.age_to, language)
    phone = safe_phone(specialist.phone)
    try:
        whatsapp = normalize_whatsapp(specialist.whatsapp)
    except ValidationError:
        whatsapp = ''
    rating = specialist.rating_avg or 0
    rating_percent = max(0, min(100, round(rating * 20))) if math.isfinite(rating) else 0
    return {
        'price_label': price,
        'age_label': f"{age} {words['years']}" if age else words['any_age'],
        'phone_href': f'tel:{phone}' if phone else '',
        'whatsapp_url': f'https://wa.me/{whatsapp.lstrip("+")}' if whatsapp else '',
        'languages': [label for code, label in zip(('az', 'ru', 'en'), words['languages'])
                      if getattr(specialist, f'language_{code}')],
        'rating_percent': rating_percent,
        'format_label': words['formats'].get(specialist.consultation_format, '—'),
    }


def _map_locations(locations, language):
    """Plain data only: consumers must use JSON serialization and text DOM nodes."""
    result = []
    for location in locations:
        try:
            lat, lng = float(location.lat), float(location.lng)
        except (TypeError, ValueError, OverflowError):
            continue
        if not (math.isfinite(lat) and math.isfinite(lng) and -90 <= lat <= 90 and -180 <= lng <= 180):
            continue
        result.append({
            'lat': lat, 'lng': lng, 'address': location.address or '',
            # Preserve the existing unlink-only behavior for hidden place names.
            'place_name': location.place.name_i18n(language) if location.place else _LABELS[language]['private_office'],
        })
    return result


def public_profile_context(specialist):
    current, past, future = [], [], []
    today = timezone.localdate()
    links = specialist.employment_links.select_related(
        'organization', 'organization__owner', 'specialist__verified_person_user'
    ).order_by('-start_date', '-pk')
    for item in links:
        # An unconfirmed invitation is never public employment history.
        if not (item.person_confirmed_at and item.organization_confirmed_at):
            continue
        org = item.organization
        if not visible(org):
            continue
        person = item.specialist
        live_consent = bool(
            person.verified_person_user_id and person.person_verified_at
            and person.verified_person_user.is_active
            and org.owner_id and org.owner.is_active
            and item.person_user_id == person.verified_person_user_id
            and item.person_confirmed_by_id == person.verified_person_user_id
            and item.organization_owner_id == org.owner_id
            and item.organization_confirmed_by_id == org.owner_id
            and item.organization_ownership_version == org.ownership_version
        )
        if item.status == SpecialistEmployment.CANCELLED or (item.end_date and item.end_date < today):
            item.temporal_state = 'history'
            past.append(item)
        elif item.status == SpecialistEmployment.ACTIVE and live_consent:
            if item.start_date > today:
                item.temporal_state = 'future'
                future.append(item)
            else:
                item.temporal_state = 'current'
                current.append(item)

    from catalog.services.features import is_organizations_section_enabled
    orgs_enabled = is_organizations_section_enabled()
    for item in current + past + future:
        item.organization_linkable = orgs_enabled and visible(item.organization)

    active_locs = list(specialist.practice_locations.filter(is_active=True)
        .select_related('place', 'region', 'district', 'metro'))
    for loc in active_locs:
        loc.is_place_visible = bool(loc.place and visible(loc.place))

    language = language_code()
    map_locations = _map_locations(active_locs, language)

    from catalog.services.specialist_subjects import SUBJECTS, profile_subjects
    return {
        'specialist_subjects': profile_subjects(specialist, language),
        'specialist_categories': [s for s in specialist.specializations.all() if s.code not in SUBJECTS],
        'specialist_public': _public_labels(specialist, language),
        'specialist_map_locations': map_locations,
        'has_coords': bool(map_locations),
        'specialist_current_employment': current,
        'specialist_past_employment': past,
        'specialist_future_employment': future,
        'specialist_active_practice_locations': active_locs,
        'organizations_section_enabled': orgs_enabled,
        # Retired private addresses stay visible only in the person's workspace.
        'practice_history': [],
    }
