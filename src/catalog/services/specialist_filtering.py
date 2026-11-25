"""Public specialist price ceilings and matching known service prices."""
from django.core.cache import cache
from django.db.models import Exists, Max, OuterRef, Q
from django.db.models.functions import Coalesce

from catalog.models import Specialist, SpecialistPracticeLocation


SPECIALIST_PRICE_MAX_CACHE_KEY = 'specialists:price_max:v1'


def get_specialist_max_price() -> int:
    """Global public ceiling; unrelated search filters must not move the slider."""
    cached = cache.get(SPECIALIST_PRICE_MAX_CACHE_KEY)
    if cached is not None:
        return cached
    maxima = Specialist.objects.filter(
        status=Specialist.STATUS_PUBLISHED, is_active=True,
    ).aggregate(
        profile_from=Max('price_from'),
        profile_to=Max('price_to'),
        location=Max('practice_locations__price_per_session',
                     filter=Q(practice_locations__is_active=True)),
    )
    maximum = max((value for value in maxima.values() if value is not None), default=0)
    step = 50 if maximum <= 2000 else 100
    ceiling = max(500, ((maximum + step - 1) // step) * step)
    cache.set(SPECIALIST_PRICE_MAX_CACHE_KEY, ceiling, timeout=300)
    return ceiling


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
    if upper is not None and upper >= ceiling:
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
