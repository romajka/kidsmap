"""Public labels and consent/date presentation; no inferred identity or consent."""
import math
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.utils import timezone
from catalog.models.specialist_domain import SpecialistEmployment
from catalog.services.age_display import format_age_range
from catalog.services.specialist_formats import profile_format_codes, public_format_label
from catalog.services.phone_numbers import normalize_whatsapp, safe_phone
from catalog.services.pricing_plans import format_price_amount, format_price_range
from catalog.services.public_presentation import language_code, visible


_LABELS = {
    'az': {
        'any_age': 'Hər hansı yaş', 'years': 'yaş',
        'from_price': '{value} AZN-dən', 'to_price': '{value} AZN-dək',
        'languages': ('Azərbaycan dili', 'Rus dili', 'İngilis dili'),
        'private_office': 'Şəxsi kabinet',
        'per_lesson': '{amount} ₼ / dərs', 'at_location': 'qəbul yerində',
        'free': 'Pulsuz', 'month': 'Aylıq abunəlik', 'package': 'Dərs paketi',
        'single': 'Birdəfəlik dərs', 'per_month': 'ayda', 'saving': '{value}% qənaət',
    },
    'ru': {
        'any_age': 'Любой возраст', 'years': 'лет',
        'from_price': 'от {value} AZN', 'to_price': 'до {value} AZN',
        'languages': ('Азербайджанский', 'Русский', 'Английский'),
        'private_office': 'Собственный кабинет',
        'per_lesson': '{amount} ₼ за занятие', 'at_location': 'по адресу приёма',
        'free': 'Бесплатно', 'month': 'Месячный абонемент', 'package': 'Пакет занятий',
        'single': 'Разовое занятие', 'per_month': 'в месяц', 'saving': 'выгода {value}%',
    },
    'en': {
        'any_age': 'Any age', 'years': 'years',
        'from_price': 'from {value} AZN', 'to_price': 'up to {value} AZN',
        'languages': ('Azerbaijani', 'Russian', 'English'),
        'private_office': 'Private office',
        'per_lesson': '{amount} ₼ per lesson', 'at_location': 'at a practice location',
        'free': 'Free', 'month': 'Monthly subscription', 'package': 'Lesson package',
        'single': 'Single lesson', 'per_month': 'per month', 'saving': 'save {value}%',
    },
}


def _legacy_price(low, high, language):
    words = _LABELS[language]
    if low is not None and high is not None:
        return format_price_range(low, high, language)['full']
    if low is not None:
        return words['from_price'].format(value=format_price_amount(low))
    if high is not None:
        return words['to_price'].format(value=format_price_amount(high))
    return ''


def _tariff_amount(amount, language):
    """Whole manats stay short (30); fractional sums always show gapiks (32,50)."""
    value = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    text = str(int(value)) if value == value.to_integral_value() else format(value, 'f')
    return text if language == 'en' else text.replace('.', ',')


def _lesson_price_label(amount, language):
    if Decimal(str(amount)) == 0:
        return _LABELS[language]['free']
    return _LABELS[language]['per_lesson'].format(amount=_tariff_amount(amount, language))


def _sessions_label(count, language):
    if language == 'az':
        return f'{count} dərs'
    if language == 'en':
        return f'{count} lesson' + ('' if count == 1 else 's')
    tail = count % 100
    if 11 <= tail <= 14:
        word = 'занятий'
    else:
        word = {1: 'занятие', 2: 'занятия', 3: 'занятия', 4: 'занятия'}.get(count % 10, 'занятий')
    return f'{count} {word}'


def specialist_card_price(specialist, language, locations=(), *, lower=None, upper=None):
    amount = specialist.lesson_price
    if amount is not None:
        sorted_price = getattr(specialist, '_single_price', None)
        if sorted_price is not None and sorted_price != amount:
            return f"{_lesson_price_label(sorted_price, language)} · {_LABELS[language]['at_location']}"
        if (lower is None or lower <= amount) and (upper is None or amount <= upper):
            return _lesson_price_label(amount, language)
        # This profile matched an active location at a different price.
        fees = [loc.price_per_session for loc in locations if loc.price_per_session is not None
                and (lower is None or lower <= loc.price_per_session)
                and (upper is None or loc.price_per_session <= upper)]
        if fees:
            return f"{_lesson_price_label(min(fees), language)} · {_LABELS[language]['at_location']}"
        return ''

    low, high = specialist.price_from, specialist.price_to
    if low is None and high is None:
        fees = [loc.price_per_session for loc in locations if loc.price_per_session is not None]
        if fees:
            low, high = min(fees), max(fees)
    price = _legacy_price(low, high, language)
    if not price:
        return ''
    unit = {'az': 'dəq', 'ru': 'мин', 'en': 'min'}[language]
    session = {'az': 'seans', 'ru': 'занятие', 'en': 'session'}[language]
    if specialist.duration_minutes:
        session = f'{specialist.duration_minutes} {unit}'
    return f'{price} / {session}'


def public_lesson_packages(specialist, language):
    from catalog.forms_specialist_pricing import normalize_pricing_packages

    packages = []
    if not isinstance(specialist.pricing_packages, list):
        return packages
    for raw in specialist.pricing_packages:
        try:
            row, = normalize_pricing_packages([raw])
        except ValidationError:
            continue
        total = Decimal(row['amount'])
        unit = (total / row['sessions']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        words = _LABELS[language]
        sessions = _sessions_label(row['sessions'], language)
        if row['period'] == 'month':
            sessions = f"{sessions} {words['per_month']}"
        base = specialist.lesson_price
        saving = 0
        if base and unit < base:
            saving = int(((base - unit) * 100 / base).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        packages.append({
            'period': row['period'], 'sessions': row['sessions'],
            'title': words[row['period']], 'sessions_label': sessions,
            'total': _tariff_amount(total, language),
            'unit_price': _lesson_price_label(unit, language) if row['sessions'] > 1 else '',
            'saving_label': words['saving'].format(value=saving) if saving >= 1 else '',
        })
    return packages


def public_single_lesson(specialist, language):
    """The always-bookable single lesson shown first in the pricing card."""
    if specialist.lesson_price is None:
        return None
    words = _LABELS[language]
    details = []
    if specialist.lesson_type:
        details.append(str(specialist.get_lesson_type_display()))
    if specialist.duration_minutes:
        unit = {'az': 'dəq', 'ru': 'мин', 'en': 'min'}[language]
        details.append(f'{specialist.duration_minutes} {unit}')
    free = specialist.lesson_price == 0
    return {
        'title': words['single'], 'details': ' · '.join(details), 'is_free': free,
        'total': words['free'] if free else f"{_tariff_amount(specialist.lesson_price, language)} ₼",
    }


def _public_labels(specialist, language):
    words = _LABELS[language]
    price = (_lesson_price_label(specialist.lesson_price, language) if specialist.lesson_price is not None
             else _legacy_price(specialist.price_from, specialist.price_to, language) or '—')
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
        'packages': public_lesson_packages(specialist, language),
        'single_lesson': public_single_lesson(specialist, language),
        'age_label': f"{age} {words['years']}" if age else words['any_age'],
        'phone_href': f'tel:{phone}' if phone else '',
        'whatsapp_url': f'https://wa.me/{whatsapp.lstrip("+")}' if whatsapp else '',
        'languages': [label for code, label in zip(('az', 'ru', 'en'), words['languages'])
                      if getattr(specialist, f'language_{code}')],
        'rating_percent': rating_percent,
        'format_label': public_format_label(specialist, language) or '—',
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

    formats = profile_format_codes(specialist)
    active_locs = (list(specialist.practice_locations.filter(is_active=True)
                       .select_related('place', 'region', 'district', 'metro')) if 'office' in formats else [])
    for loc in active_locs:
        loc.is_place_visible = bool(loc.place and visible(loc.place))

    language = language_code()
    map_locations = _map_locations(active_locs, language)
    visit_area = ""
    if "visit" in formats and specialist.visit_region_id:
        if specialist.visit_citywide:
            coverage = {"az": "Bütün şəhər", "ru": "Весь город", "en": "Entire city"}[language]
        else:
            coverage = ", ".join(d.name_i18n(language) for d in specialist.visit_districts.filter(region_id=specialist.visit_region_id))
        if coverage:
            visit_area = f"{specialist.visit_region.name_i18n(language)} · {coverage}"

    from catalog.services.specialist_subjects import SUBJECTS, profile_subjects
    return {
        'specialist_subjects': profile_subjects(specialist, language),
        'specialist_categories': [s for s in specialist.specializations.all() if s.code not in SUBJECTS],
        'specialist_public': _public_labels(specialist, language),
        'specialist_map_locations': map_locations,
        'specialist_visit_area': visit_area,
        'has_coords': bool(map_locations),
        'specialist_current_employment': current,
        'specialist_past_employment': past,
        'specialist_future_employment': future,
        'specialist_active_practice_locations': active_locs,
        'organizations_section_enabled': orgs_enabled,
        # Retired private addresses stay visible only in the person's workspace.
        'practice_history': [],
    }
