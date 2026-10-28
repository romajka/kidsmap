from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING
from functools import cached_property

from django.core.cache import cache
from django.db.models import Exists, Max, OuterRef, Q
from django.utils import timezone



CATALOG_PRICE_MAX_CACHE_KEY = "catalog:price_max:v1"


def get_catalog_max_price() -> int:
    """Ceiling for the public catalog, using the price filter's tariff scope."""
    cached = cache.get(CATALOG_PRICE_MAX_CACHE_KEY)
    if cached is not None:
        return cached

    from catalog.models import Place, PricingPlan
    from catalog.services.content_quality import public_place_queryset
    from catalog.services.pricing_plans import current_pricing_plan_q

    public_places = public_place_queryset(Place.objects.all())
    public_ids = public_places.values("pk")
    eligible = PricingPlan.objects.filter(
        current_pricing_plan_q(), charge_role="primary", is_trial=False, currency="AZN",
    )
    live_group = Q(
        place__isnull=True,
        offering_group__activity__status="published",
        offering_group__activity__archived_at__isnull=True,
        offering_group__archived_at__isnull=True,
    )
    plan_maxima = eligible.filter(
        Q(place_id__in=public_ids, offering_group__isnull=True)
        | (live_group & Q(offering_group__activity__place_id__in=public_ids))
    ).aggregate(**{name: Max(name) for name in ("price", "price_min", "price_max")})
    # Even expired/foreign tariffs supersede potentially stale AZN projections.
    existing_plans = PricingPlan.objects.filter(charge_role="primary", is_trial=False).filter(
        Q(place_id=OuterRef("pk"), offering_group__isnull=True)
        | (live_group & Q(offering_group__activity__place_id=OuterRef("pk")))
    )
    legacy_maxima = public_places.filter(~Exists(existing_plans)).aggregate(
        **{name: Max(name) for name in
           ("price_from", "price_to", "price_per_month", "price_per_lesson")}
    )
    maximum = max((Decimal("0"), *(value for value in
        (*plan_maxima.values(), *legacy_maxima.values()) if value is not None)))
    step = Decimal("50") if maximum <= 2000 else Decimal("100")
    result = max(500, int((maximum / step).to_integral_value(rounding=ROUND_CEILING) * step))
    cache.set(CATALOG_PRICE_MAX_CACHE_KEY, result, timeout=300)
    return result


def _direct_price_audience_q(filters, prefix=""):
    """Direct/legacy prices inherit their Place audience, never another group."""
    query = Q()
    if filters is None:
        return query
    if filters.category:
        query &= Q(**{prefix + "category_id": filters.category})
    if filters.subcategory:
        query &= Q(**{prefix + "subcategory_id": filters.subcategory})
    low, high = filters._normalized_age_bounds()
    if low is not None:
        query &= Q(**{prefix + "age_to__isnull": True}) | Q(**{prefix + "age_to__gte": low})
    if high is not None:
        query &= Q(**{prefix + "age_from__isnull": True}) | Q(**{prefix + "age_from__lte": high})
    return query


def pricing_plan_age_q(filters):
    """Explicit tariff ages; unspecified bounds inherit the matching parent."""
    query = Q()
    if filters is not None:
        age_low, age_high = filters._normalized_age_bounds()
        # Unspecified tariff ages inherit the matching group/place audience.
        # Price and explicit tariff age must be true for this same row.
        if age_low is not None:
            query &= Q(age_to__isnull=True) | Q(age_to__gte=age_low)
        if age_high is not None:
            query &= Q(age_from__isnull=True) | Q(age_from__lte=age_high)
    return query


def matching_pricing_plan_q(price_from_int, price_to_int, filters=None):
    """One current tariff must satisfy the requested age and both price bounds."""
    from catalog.services.pricing_plans import current_pricing_plan_q

    plan_q = current_pricing_plan_q() & Q(charge_role="primary", is_trial=False, currency="AZN")
    plan_q &= pricing_plan_age_q(filters)
    if price_to_int is not None:
        plan_q &= (
            Q(price_kind__in=("exact", "free"), price__lte=price_to_int)
            | Q(price_kind__in=("from", "range"), price_min__lte=price_to_int)
        )
    if price_from_int is not None and price_from_int > 0:
        plan_q &= ~Q(price_kind="free")
        plan_q &= (
            Q(price_kind="exact", price__gte=price_from_int)
            | Q(price_kind="from", price_min__gte=price_from_int)
            | Q(price_kind="range", price_max__gte=price_from_int)
        )
    return plan_q


def apply_price_filter(qs, price_from_int, price_to_int, filters=None):
    from catalog.models import Place, PricingPlan

    plan_q = matching_pricing_plan_q(price_from_int, price_to_int, filters)

    direct_plans = PricingPlan.objects.filter(
        plan_q & _direct_price_audience_q(filters, "place__"),
        place_id=OuterRef("pk"),
        offering_group__isnull=True,
    )

    if filters is not None:
        from catalog.services.catalog_search import has_offer_filters, matching_groups
        if has_offer_filters(filters):
            nested_plans = PricingPlan.objects.filter(
                plan_q,
                place__isnull=True,
                offering_group__in=matching_groups(filters),
                offering_group__activity__place_id=OuterRef("pk"),
            )
        else:
            nested_plans = PricingPlan.objects.filter(
                plan_q,
                place__isnull=True,
                offering_group__activity__place_id=OuterRef("pk"),
                offering_group__activity__status="published",
                offering_group__archived_at__isnull=True,
                offering_group__activity__archived_at__isnull=True,
            )
    else:
        nested_plans = PricingPlan.objects.filter(
            plan_q,
            place__isnull=True,
            offering_group__activity__place_id=OuterRef("pk"),
            offering_group__activity__status="published",
            offering_group__archived_at__isnull=True,
            offering_group__activity__archived_at__isnull=True,
        )

    has_matching_plan = Exists(direct_plans) | Exists(nested_plans)

    free_mode_match = Q(pk__in=[])
    if (price_from_int is None or price_from_int <= 0) and (price_to_int is None or price_to_int >= 0):
        free_mode_match = Q(price_mode__in=(Place.PRICE_MODE_FREE, Place.PRICE_MODE_FREE_ENTRY)) & _direct_price_audience_q(filters)

    all_plans = PricingPlan.objects.filter(
        Q(place_id=OuterRef("pk"), offering_group__isnull=True)
        | Q(
            place__isnull=True,
            offering_group__activity__place_id=OuterRef("pk"),
            offering_group__activity__status="published",
            offering_group__archived_at__isnull=True,
            offering_group__activity__archived_at__isnull=True,
        ),
        charge_role="primary",
        is_trial=False,
    )
    legacy_q = ~Exists(all_plans) & _direct_price_audience_q(filters)
    # Check both budget bounds on one source before OR-ing independent units.
    # The explicit legacy range is a real interval; a lone lower bound is a
    # known starting price, not evidence of an arbitrary higher ticket.
    legacy_range = Q(price_from__isnull=False) | Q(price_to__isnull=False)
    if price_to_int is not None:
        legacy_range &= Q(price_from__lte=price_to_int) | (Q(price_from__isnull=True) & Q(price_to__lte=price_to_int))
    if price_from_int is not None and price_from_int > 0:
        legacy_range &= Q(price_to__gte=price_from_int) | (Q(price_to__isnull=True) & Q(price_from__gte=price_from_int))
    legacy_filters = legacy_range
    for field_name in ("price_per_lesson", "price_per_month"):
        same_source = Q(**{field_name + "__isnull": False})
        if price_to_int is not None:
            same_source &= Q(**{field_name + "__lte": price_to_int})
        if price_from_int is not None and price_from_int > 0:
            same_source &= Q(**{field_name + "__gte": price_from_int})
        legacy_filters |= same_source
    legacy_q &= legacy_filters

    return qs.filter(has_matching_plan | free_mode_match | legacy_q)


@dataclass
class PlaceListFilters:
    category: str = ""
    subcategory: str = ""
    query: str = ""
    district: str = ""
    metro: str = ""
    age: str = ""
    age_from: str = ""
    age_to: str = ""
    price_from: str = ""
    price_to: str = ""
    price_max: str = ""
    min_rating: str = ""
    sort: str = "new"
    days: str = "30"
    with_photo: str = ""
    verified_only: str = ""
    event_type: str = ""
    view_mode: str = "grid"
    force_new_only: bool = False
    rating_sort_available: bool | None = field(default=None, init=False)

    @cached_property
    def catalog_price_max(self) -> int:
        return get_catalog_max_price()

    @classmethod
    def from_request(cls, request, force_new_only=False):
        from catalog.services.locations import normalize_to_key
        data = cls(
            category=(request.GET.get("category") or "").strip(),
            subcategory=(request.GET.get("subcategory") or "").strip(),
            query=(request.GET.get("q") or "").strip(),
            district=normalize_to_key((request.GET.get("district") or "").strip()),
            metro=(request.GET.get("metro") or "").strip(),
            age=(request.GET.get("age") or "").strip(),
            age_from=(request.GET.get("age_from") or "").strip(),
            age_to=(request.GET.get("age_to") or "").strip(),
            price_from=(request.GET.get("price_from") or "").strip(),
            price_to=(request.GET.get("price_to") or "").strip(),
            price_max=(request.GET.get("price_max") or "").strip(),
            min_rating=(request.GET.get("min_rating") or "").strip(),
            sort=(request.GET.get("sort") or "new").strip(),
            days=(request.GET.get("days") or "30").strip(),
            with_photo=(request.GET.get("with_photo") or "").strip(),
            verified_only="",
            event_type=(request.GET.get("event_type") or "").strip(),
            view_mode="grid",
            force_new_only=force_new_only,
        )
        if data.event_type not in {"temporary", "permanent"}:
            data.event_type = ""
        if data.event_type and not cls._events_section_enabled():
            data.event_type = ""
        if data.age_from == "0" and data.age_to == "18":
            data.age_from = data.age_to = ""
        # Only an upper price bound needs the ceiling. SEO and other non-price
        # queries must not aggregate the whole catalog just to parse filters.
        if (data._int_or_none(data.price_to) is not None
                or data._int_or_none(data.price_max) is not None):
            # URL normalization and context construction may parse the same
            # request: keep one ceiling if the shared cache expires in between.
            if not hasattr(request, "_catalog_price_max"):
                request._catalog_price_max = get_catalog_max_price()
            data.catalog_price_max = request._catalog_price_max
        price_from, price_to = data._normalized_price_bounds()
        data.price_from = str(price_from) if price_from is not None else ""
        data.price_to = str(price_to) if price_to is not None else ""
        data.price_max = ""
        if data.sort in {"price_asc", "price_desc"}:
            data.sort = "new"
        data._normalize_subcategory()
        if data.force_new_only:
            data.sort = "new"
            if data.days not in {"7", "14", "30"}:
                data.days = "30"
        return data

    def _normalize_subcategory(self) -> None:
        """Подкатегория хранится как pk и осмысленна только вместе со своей
        категорией. Мусор отбрасываем, а ссылку вида ?subcategory=12 без
        категории достраиваем — иначе фильтр применился бы, но в сайдбаре
        его было бы не видно и не снять."""
        if not self.subcategory:
            return
        if not self.subcategory.isdigit():
            self.subcategory = ""
            return

        from catalog.models import Subcategory

        subcategory = (
            Subcategory.active.select_related("category")
            .filter(pk=self.subcategory)
            .first()
        )
        if subcategory is None:
            self.subcategory = ""
            return

        parent_code = subcategory.category.code
        if self.category and self.category != parent_code:
            self.subcategory = ""
        elif not self.category:
            self.category = parent_code

    @staticmethod
    def _events_section_enabled() -> bool:
        from catalog.services.features import is_events_section_enabled

        return is_events_section_enabled()

    def _int_or_none(self, value):
        return int(value) if str(value).isdigit() else None

    def _normalized_age_bounds(self):
        age_from = self.age_from
        age_to = self.age_to

        if not age_from and not age_to and self.age.isdigit():
            age_from = self.age
            age_to = self.age

        age_from_int = self._int_or_none(age_from)
        age_to_int = self._int_or_none(age_to)

        if age_from_int is not None and age_to_int is not None and age_from_int > age_to_int:
            age_from_int, age_to_int = age_to_int, age_from_int

        return age_from_int, age_to_int

    def _normalized_price_bounds(self):
        price_from_int = self._int_or_none(self.price_from)
        price_to_int = self._int_or_none(self.price_to)

        if price_to_int is None:
            price_to_int = self._int_or_none(self.price_max)

        if price_from_int is not None and price_to_int is not None and price_from_int > price_to_int:
            price_from_int, price_to_int = price_to_int, price_from_int

        if price_to_int is not None and price_to_int >= self.catalog_price_max:
            price_to_int = None
        if price_from_int == 0:
            price_from_int = None

        return price_from_int, price_to_int

    def apply(self, qs, created_after=None):
        if self.force_new_only:
            recent_cutoff = timezone.now() - timedelta(days=int(self.days))
            qs = qs.filter(created_at__gte=recent_cutoff)
        elif created_after is not None:
            qs = qs.filter(created_at__gte=created_after)

        from catalog.services.catalog_search import apply_offer_matching
        qs = apply_offer_matching(qs, self)

        price_from_int, price_to_int = self._normalized_price_bounds()
        if price_from_int is not None or price_to_int is not None:
            qs = apply_price_filter(qs, price_from_int, price_to_int, filters=self)

        if self.sort in {"price_asc", "price_desc"}:
            self.sort = "new"

        if self.district:
            if self.district.lower() == "baku":
                qs = qs.filter(Q(district__iexact="baku") | Q(district__startswith="baku_"))
            else:
                qs = qs.filter(district__iexact=self.district)

        if self.min_rating:
            try:
                min_rating_value = float(self.min_rating.replace(",", "."))
            except ValueError:
                min_rating_value = None
            if min_rating_value is not None:
                min_rating_value = max(0, min(5, min_rating_value))
                qs = qs.filter(rating_avg__gte=min_rating_value)

        if not self.force_new_only:
            if self.event_type == "temporary":
                now = timezone.now()
                qs = qs.filter(is_temporary=True).filter(Q(temporary_end__isnull=True) | Q(temporary_end__gte=now))
            elif self.event_type == "permanent":
                qs = qs.filter(is_temporary=False)

        if self.force_new_only:
            if self.with_photo == "1":
                qs = qs.exclude(
                    (Q(cover_photo="") | Q(cover_photo__isnull=True))
                    & (Q(photo="") | Q(photo__isnull=True))
                )

        if self.metro:
            qs = qs.filter(metro__iexact=self.metro)

        if self.sort == "reviews_desc" and not self.force_new_only:
            return qs.order_by("-rating_count", "-rating_avg", "-created_at")
        if self.sort == "rating" and not self.force_new_only:
            from catalog.services.rating_ranking import (
                apply_weighted_rating_ordering,
                get_active_rating_calibration,
            )

            calibration = get_active_rating_calibration()
            self.rating_sort_available = calibration is not None
            if calibration is not None:
                return apply_weighted_rating_ordering(qs, calibration)
        self.sort = "new"
        return qs.order_by("-created_at")

    def selected(self):
        age_from_int, age_to_int = self._normalized_age_bounds()
        price_from_int, price_to_int = self._normalized_price_bounds()
        sel_price_from = str(price_from_int) if price_from_int is not None else ""
        sel_price_to = str(price_to_int) if price_to_int is not None else ""

        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "q": self.query,
            "district": self.district,
            "metro": self.metro,
            "age": self.age,
            "age_from": str(age_from_int if age_from_int is not None else self.age_from),
            "age_to": str(age_to_int if age_to_int is not None else self.age_to),
            "price_from": sel_price_from,
            "price_to": sel_price_to,
            "min_rating": self.min_rating,
            "sort": self.sort,
            "days": self.days,
            "with_photo": self.with_photo,
            "event_type": self.event_type,
            "view": self.view_mode,
        }


def build_new_page_stats(qs):
    return {
        "places": qs.count(),
        "districts": qs.exclude(district="").exclude(district__isnull=True).values("district").distinct().count(),
        "categories": qs.values("category").distinct().count(),
    }
