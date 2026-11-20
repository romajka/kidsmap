"""Public specialist price ceilings and matching known service prices."""
from django.db.models import Exists, Max, OuterRef, Q
from django.db.models.functions import Coalesce

from catalog.models import Specialist, SpecialistPracticeLocation


def get_specialist_max_price(queryset=None) -> int:
    if queryset is None:
        queryset = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True)
    maxima = queryset.aggregate(
        profile_from=Max('price_from'),
        profile_to=Max('price_to'),
        location=Max('practice_locations__price_per_session',
                     filter=Q(practice_locations__is_active=True)),
    )
    return max((value for value in maxima.values() if value is not None), default=0)


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

    # A single known endpoint is still a known price, not an invented interval.
    queryset = queryset.alias(
        _service_price_low=Coalesce('price_from', 'price_to'),
        _service_price_high=Coalesce('price_to', 'price_from'),
    )
    profile_match = Q()
    locations = SpecialistPracticeLocation.objects.filter(
        specialist_id=OuterRef('pk'), is_active=True,
    )
    if lower is not None:
        profile_match &= Q(_service_price_high__gte=lower)
        locations = locations.filter(price_per_session__gte=lower)
    if upper is not None:
        profile_match &= Q(_service_price_low__lte=upper)
        locations = locations.filter(price_per_session__lte=upper)
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
