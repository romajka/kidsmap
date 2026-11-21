"""Public specialist price ceilings and matching known service prices."""
from math import ceil

from django.db.models import Case, DecimalField, Exists, F, Max, Min, OuterRef, Q, Value, When
from django.db.models.functions import Coalesce, Greatest, Least

from catalog.models import Specialist, SpecialistPracticeLocation


def get_specialist_max_price(queryset=None) -> int:
    if queryset is None:
        queryset = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True)
    maxima = queryset.aggregate(
        lesson=Max('lesson_price'),
        profile_from=Max('price_from', filter=Q(lesson_price__isnull=True)),
        profile_to=Max('price_to', filter=Q(lesson_price__isnull=True)),
        location=Max('practice_locations__price_per_session',
                     filter=Q(practice_locations__is_active=True)),
    )
    return ceil(max((value for value in maxima.values() if value is not None), default=0))


def _with_profile_prices(queryset):
    # A single legacy endpoint is still a known price, not an invented interval.
    return queryset.alias(
        _service_price_low=Coalesce('lesson_price', 'price_from', 'price_to', output_field=DecimalField()),
        _service_price_high=Coalesce('lesson_price', 'price_to', 'price_from', output_field=DecimalField()),
    )


def _price_lookups(lower, upper, low_field, high_field):
    lookups = {}
    if lower is not None:
        lookups[high_field + '__gte'] = lower
    if upper is not None:
        lookups[low_field + '__lte'] = upper
    return lookups


def order_by_specialist_price(queryset, *, descending, lower=None, upper=None):
    """Compare single-session offers within the selected budget, missing prices last."""
    queryset = _with_profile_prices(queryset)
    if descending:
        aggregate, endpoint = Max, Greatest
        profile = F('_service_price_high')
        if upper is not None:
            profile = Least(profile, Value(upper), output_field=DecimalField())
    else:
        aggregate, endpoint = Min, Least
        profile = F('_service_price_low')
        if lower is not None:
            profile = Greatest(profile, Value(lower), output_field=DecimalField())
    bounds = _price_lookups(lower, upper, '_service_price_low', '_service_price_high')
    if bounds:
        profile = Case(When(**bounds, then=profile), output_field=DecimalField())
    field = 'practice_locations__price_per_session'
    location = aggregate(field, filter=Q(practice_locations__is_active=True,
                                        **_price_lookups(lower, upper, field, field)))
    # SQLite's least/greatest return NULL when one price is missing.
    comparable = Coalesce(endpoint(profile, location, output_field=DecimalField()),
                          profile, location, output_field=DecimalField())
    ordering = F('_single_price').desc(nulls_last=True) if descending else F('_single_price').asc(nulls_last=True)
    return queryset.annotate(_single_price=comparable).order_by(ordering, '-created_at', '-pk')


def _price_bound(value):
    try:
        clean = '' if value is None else str(value).strip()
        return int(clean) if clean.isascii() and clean.isdecimal() else None
    except (TypeError, ValueError):
        return None


def normalize_specialist_price_bounds(raw_from, raw_to, *, ceiling):
    lower, upper = _price_bound(raw_from), _price_bound(raw_to)
    if lower is not None and upper is not None and lower > upper:
        lower, upper = upper, lower
    if upper is not None and upper > 0 and upper >= ceiling:
        upper = None
    if lower == 0:
        lower = None
    return lower, upper


def apply_specialist_price_filter(queryset, lower, upper):
    if lower is None and upper is None:
        return queryset

    queryset = _with_profile_prices(queryset)
    profile_match = Q(**_price_lookups(lower, upper, '_service_price_low', '_service_price_high'))
    locations = SpecialistPracticeLocation.objects.filter(
        specialist_id=OuterRef('pk'), is_active=True,
        **_price_lookups(lower, upper, 'price_per_session', 'price_per_session'),
    )
    # Correlate both bounds to one location; different addresses cannot combine.
    return queryset.filter(profile_match | Exists(locations))


def specialist_format_match(formats, *, region="", district="", district_region=None, metro=""):
    """Match a format together with its own geography. An online match is worldwide."""
    from catalog.services.specialist_formats import format_q

    if not any((region, district, metro)):
        if not formats:
            return Q()
        matches = Q(pk__in=[])
        for code in formats:
            matches |= format_q(code)
        return matches

    matches = format_q("online") if "online" in formats else Q(pk__in=[])
    if not formats or "office" in formats or "offline" in formats:
        office = Q(practice_locations__is_active=True)
        if region:
            office &= Q(practice_locations__region_id=region)
        if district:
            office &= Q(practice_locations__district_id=district)
        if metro:
            office &= Q(practice_locations__metro_id=metro)
        matches |= format_q("office") & office
    if not metro and (not formats or "visit" in formats or "offline" in formats):
        visits = format_q("visit") & Q(visit_region__isnull=False)
        if region:
            visits &= Q(visit_region_id=region)
        if district:
            visits &= Q(visit_region_id=district_region)
            visits &= Q(visit_districts__pk=district) | Q(visit_citywide=True)
        matches |= visits
    return matches
