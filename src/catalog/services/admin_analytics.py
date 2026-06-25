from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import FunnelEvent, Place, PlaceReview, SiteReview, SiteVisit, Category
from catalog.services.google_analytics_reporting import build_google_analytics_context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _date_range(start_day, end_day):
    day = start_day
    while day <= end_day:
        yield day
        day += timedelta(days=1)


def _safe_pct(numerator: int, denominator: int) -> float | None:
    """Return percentage or None if denominator is 0."""
    if not denominator:
        return None
    return round(numerator / denominator * 100, 1)


def _safe_ratio(numerator: int, denominator: int) -> float | None:
    """Return ratio (not percent) or None if denominator is 0."""
    if not denominator:
        return None
    return round(numerator / denominator, 1)


def _delta_pct(current: int, previous: int) -> float | str | None:
    """Return delta % vs previous period, or 'new' string, or None."""
    if previous == 0:
        if current == 0:
            return None
        return "new"
    return round((current - previous) / previous * 100, 1)


def _build_delta_meta(value: float | str | None) -> dict:
    """Prepare UI-friendly delta metadata for KPI cards."""
    if value == "new":
        return {
            "kind": "new",
            "class_name": "km-delta--new",
            "arrow": "↑",
            "text": str(_("Новые данные")),
        }
    if value is None:
        return {
            "kind": "none",
            "class_name": "km-delta--none",
            "arrow": "",
            "text": str(_("Нет базы для сравнения")),
        }
    if value > 0:
        return {
            "kind": "up",
            "class_name": "km-delta--up",
            "arrow": "↑",
            "text": f"{value:.1f}%",
        }
    if value < 0:
        return {
            "kind": "down",
            "class_name": "km-delta--down",
            "arrow": "↓",
            "text": f"{abs(value):.1f}%",
        }
    return {
        "kind": "none",
        "class_name": "km-delta--none",
        "arrow": "•",
        "text": str(_("Без изменений")),
    }


def _build_funnel_steps(funnel_stats: dict) -> list[dict]:
    steps = [
        {"label": str(_("Поиск")), "count": int(funnel_stats.get("search") or 0), "tone": "purple"},
        {"label": str(_("Фильтры")), "count": int(funnel_stats.get("filter") or 0), "tone": "blue"},
        {"label": str(_("Карточки")), "count": int(funnel_stats.get("open") or 0), "tone": "green"},
        {"label": str(_("CTA")), "count": int(funnel_stats.get("cta_total") or 0), "tone": "orange"},
    ]
    max_count = max((step["count"] for step in steps), default=0)
    for step in steps:
        step["bar_pct"] = round(step["count"] / max_count * 100) if max_count else 0
    return steps


# ---------------------------------------------------------------------------
# Period-aware visit stats
# ---------------------------------------------------------------------------

def _build_visits_for_period(visits_qs, start_day) -> dict:
    period_qs = visits_qs.filter(day__gte=start_day)
    row = period_qs.aggregate(
        unique_sessions=Count("session_key", distinct=True),
        page_views=Sum("hits"),
    )
    return {
        "unique_sessions": int(row.get("unique_sessions") or 0),
        "page_views": int(row.get("page_views") or 0),
    }


def _build_funnel_for_period(events_qs, start_day) -> dict:
    period_qs = events_qs.filter(day__gte=start_day)
    row = period_qs.aggregate(
        search=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_SEARCH)),
        catalog_filter=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_FILTER)),
        place_open=Count("id", filter=Q(event_type=FunnelEvent.EVENT_PLACE_OPEN)),
        cta_call=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CTA_CALL)),
        cta_whatsapp=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CTA_WHATSAPP)),
        cta_instagram=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CTA_INSTAGRAM)),
    )
    search = int(row.get("search") or 0)
    place_open = int(row.get("place_open") or 0)
    cta_total = (
        int(row.get("cta_call") or 0)
        + int(row.get("cta_whatsapp") or 0)
        + int(row.get("cta_instagram") or 0)
    )
    return {
        "search": search,
        "filter": int(row.get("catalog_filter") or 0),
        "open": place_open,
        "cta_total": cta_total,
        # open_per_search is a ratio (NOT percent), to avoid showing "1400%"
        "open_per_search": _safe_ratio(place_open, search),
        "cta_from_open_pct": _safe_pct(cta_total, place_open),
    }


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def _build_daily_visits_chart(visits_qs, start_day, end_day) -> dict:
    raw_rows = (
        visits_qs.filter(day__gte=start_day, day__lte=end_day)
        .values("day")
        .annotate(unique_sessions=Count("session_key", distinct=True), page_views=Sum("hits"))
        .order_by("day")
    )
    by_day = {
        row["day"]: {
            "unique_sessions": int(row.get("unique_sessions") or 0),
            "page_views": int(row.get("page_views") or 0),
        }
        for row in raw_rows
    }

    labels, unique_values, page_view_values = [], [], []
    for day in _date_range(start_day, end_day):
        point = by_day.get(day, {})
        labels.append(day.strftime("%d.%m"))
        unique_values.append(int(point.get("unique_sessions") or 0))
        page_view_values.append(int(point.get("page_views") or 0))

    return {
        "labels": labels,
        "unique_sessions": unique_values,
        "page_views": page_view_values,
    }


def _build_weekly_visits(visits_qs, start_day):
    rows = (
        visits_qs.filter(day__gte=start_day)
        .annotate(period=TruncWeek("day"))
        .values("period")
        .annotate(unique_sessions=Count("session_key", distinct=True), page_views=Sum("hits"))
        .order_by("period")
    )
    return [
        {
            "period": row["period"].date() if hasattr(row["period"], "date") else row["period"],
            "unique_sessions": int(row.get("unique_sessions") or 0),
            "page_views": int(row.get("page_views") or 0),
        }
        for row in rows
    ]


def _build_monthly_visits(visits_qs, start_day):
    rows = (
        visits_qs.filter(day__gte=start_day)
        .annotate(period=TruncMonth("day"))
        .values("period")
        .annotate(unique_sessions=Count("session_key", distinct=True), page_views=Sum("hits"))
        .order_by("period")
    )
    return [
        {
            "period": row["period"].date() if hasattr(row["period"], "date") else row["period"],
            "unique_sessions": int(row.get("unique_sessions") or 0),
            "page_views": int(row.get("page_views") or 0),
        }
        for row in rows
    ]


def _build_weekly_funnel_stats(events_qs, start_day):
    rows = (
        events_qs.filter(day__gte=start_day)
        .annotate(period=TruncWeek("day"))
        .values("period")
        .annotate(
            search=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_SEARCH)),
            catalog_filter=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_FILTER)),
            place_open=Count("id", filter=Q(event_type=FunnelEvent.EVENT_PLACE_OPEN)),
            cta_total=Count(
                "id",
                filter=Q(
                    event_type__in=(
                        FunnelEvent.EVENT_CTA_CALL,
                        FunnelEvent.EVENT_CTA_WHATSAPP,
                        FunnelEvent.EVENT_CTA_INSTAGRAM,
                    )
                ),
            ),
        )
        .order_by("period")
    )
    return [
        {
            "period": row["period"].date() if hasattr(row["period"], "date") else row["period"],
            "search": int(row.get("search") or 0),
            "catalog_filter": int(row.get("catalog_filter") or 0),
            "place_open": int(row.get("place_open") or 0),
            "cta_total": int(row.get("cta_total") or 0),
        }
        for row in rows
    ]


def _build_monthly_funnel_stats(events_qs, start_day):
    rows = (
        events_qs.filter(day__gte=start_day)
        .annotate(period=TruncMonth("day"))
        .values("period")
        .annotate(
            search=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_SEARCH)),
            catalog_filter=Count("id", filter=Q(event_type=FunnelEvent.EVENT_CATALOG_FILTER)),
            place_open=Count("id", filter=Q(event_type=FunnelEvent.EVENT_PLACE_OPEN)),
            cta_total=Count(
                "id",
                filter=Q(
                    event_type__in=(
                        FunnelEvent.EVENT_CTA_CALL,
                        FunnelEvent.EVENT_CTA_WHATSAPP,
                        FunnelEvent.EVENT_CTA_INSTAGRAM,
                    )
                ),
            ),
        )
        .order_by("period")
    )
    return [
        {
            "period": row["period"].date() if hasattr(row["period"], "date") else row["period"],
            "search": int(row.get("search") or 0),
            "catalog_filter": int(row.get("catalog_filter") or 0),
            "place_open": int(row.get("place_open") or 0),
            "cta_total": int(row.get("cta_total") or 0),
        }
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Main context builder (new, period-aware)
# ---------------------------------------------------------------------------

VALID_PERIODS = {7, 30, 90, 365}


def build_statistics_context(period_days: int = 30) -> dict:
    """
    Build statistics context for the admin analytics page.

    Accepts period_days = 7 | 30 | 90 | 365.
    Compares current period with the immediately preceding period of the same length.
    """
    if period_days not in VALID_PERIODS:
        period_days = 30

    today = timezone.localdate()
    current_start = today - timedelta(days=period_days - 1)
    prev_start = current_start - timedelta(days=period_days)
    prev_end = current_start - timedelta(days=1)

    visits_qs = SiteVisit.objects.all()
    events_qs = FunnelEvent.objects.all()
    places_qs = Place.objects.all()
    place_reviews_qs = PlaceReview.objects.all()

    # ── 1. Visits: current & previous period ──────────────────────────────
    visits_current = _build_visits_for_period(visits_qs, current_start)
    visits_prev = _build_visits_for_period(visits_qs.filter(day__lte=prev_end), prev_start)

    # ── 2. Funnel: current & previous period ──────────────────────────────
    funnel_current = _build_funnel_for_period(events_qs.filter(day__gte=current_start), current_start)
    funnel_prev = _build_funnel_for_period(
        events_qs.filter(day__gte=prev_start, day__lte=prev_end), prev_start
    )

    # ── 3. KPI deltas ─────────────────────────────────────────────────────
    kpi = {
        "unique_sessions": visits_current["unique_sessions"],
        "page_views": visits_current["page_views"],
        "searches": funnel_current["search"],
        "place_opens": funnel_current["open"],
        "cta_total": funnel_current["cta_total"],
        "cta_from_open_pct": funnel_current["cta_from_open_pct"],
        "open_per_search": funnel_current["open_per_search"],
        # Deltas
        "delta_unique_sessions": _delta_pct(visits_current["unique_sessions"], visits_prev["unique_sessions"]),
        "delta_page_views": _delta_pct(visits_current["page_views"], visits_prev["page_views"]),
        "delta_searches": _delta_pct(funnel_current["search"], funnel_prev["search"]),
        "delta_place_opens": _delta_pct(funnel_current["open"], funnel_prev["open"]),
        "delta_cta_total": _delta_pct(funnel_current["cta_total"], funnel_prev["cta_total"]),
        "delta_cta_from_open_pct": _delta_pct(
            float(funnel_current["cta_from_open_pct"] or 0),
            float(funnel_prev["cta_from_open_pct"] or 0),
        ),
    }
    kpi_cards = [
        {
            "key": "unique_sessions",
            "label": str(_("Уникальные посетители")),
            "value": kpi["unique_sessions"],
            "icon": "👥",
            "icon_class": "km-kpi-icon--blue",
            "delta": _build_delta_meta(kpi["delta_unique_sessions"]),
        },
        {
            "key": "page_views",
            "label": str(_("Просмотры")),
            "value": kpi["page_views"],
            "icon": "👁",
            "icon_class": "km-kpi-icon--green",
            "delta": _build_delta_meta(kpi["delta_page_views"]),
        },
        {
            "key": "searches",
            "label": str(_("Поиски")),
            "value": kpi["searches"],
            "icon": "⌕",
            "icon_class": "km-kpi-icon--purple",
            "delta": _build_delta_meta(kpi["delta_searches"]),
        },
        {
            "key": "place_opens",
            "label": str(_("Открытия карточек")),
            "value": kpi["place_opens"],
            "icon": "▣",
            "icon_class": "km-kpi-icon--orange",
            "delta": _build_delta_meta(kpi["delta_place_opens"]),
        },
        {
            "key": "cta_total",
            "label": str(_("CTA")),
            "value": kpi["cta_total"],
            "icon": "✈",
            "icon_class": "km-kpi-icon--teal",
            "delta": _build_delta_meta(kpi["delta_cta_total"]),
        },
        {
            "key": "cta_from_open_pct",
            "label": str(_("CTA / Open")),
            "value": kpi["cta_from_open_pct"],
            "formatted_value": f'{kpi["cta_from_open_pct"]:.1f}%' if kpi["cta_from_open_pct"] is not None else "—",
            "icon": "%",
            "icon_class": "km-kpi-icon--pink",
            "delta": _build_delta_meta(kpi["delta_cta_from_open_pct"]),
        },
    ]
    open_per_search_display = f'{kpi["open_per_search"]:.1f}' if kpi["open_per_search"] is not None else "—"

    # ── 4. Daily chart ────────────────────────────────────────────────────
    visits_daily_chart = _build_daily_visits_chart(visits_qs, current_start, today)

    # ── 5. Places (catalog state) ─────────────────────────────────────────
    places_agg = places_qs.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        verified=Count("id", filter=Q(is_verified=True)),
        pending=Count("id", filter=Q(status=Place.STATUS_PENDING)),
        no_coords=Count("id", filter=Q(lat__isnull=True) | Q(lng__isnull=True)),
    )
    place_reviews_agg = place_reviews_qs.aggregate(
        total=Count("id"),
        avg_rating=Avg("rating"),
    )
    catalog_state = {
        "total": int(places_agg.get("total") or 0),
        "active": int(places_agg.get("active") or 0),
        "verified": int(places_agg.get("verified") or 0),
        "pending": int(places_agg.get("pending") or 0),
        "no_coords": int(places_agg.get("no_coords") or 0),
        "reviews_total": int(place_reviews_agg.get("total") or 0),
        "avg_rating": round(float(place_reviews_agg.get("avg_rating") or 0), 2),
    }

    # ── 6. Top CTA places (with category and district) ────────────────────
    cta_events_period = events_qs.filter(
        day__gte=current_start,
        event_type__in=(
            FunnelEvent.EVENT_CTA_CALL,
            FunnelEvent.EVENT_CTA_WHATSAPP,
            FunnelEvent.EVENT_CTA_INSTAGRAM,
        ),
        place__isnull=False,
    )
    cta_by_place = (
        cta_events_period
        .values("place_id", "place__name_ru", "place__name", "place__category", "place__district")
        .annotate(cta_count=Count("id"))
        .order_by("-cta_count")[:5]
    )
    # Also get open counts per place for the same period
    opens_by_place = dict(
        events_qs.filter(
            day__gte=current_start,
            event_type=FunnelEvent.EVENT_PLACE_OPEN,
            place__isnull=False,
        )
        .values("place_id")
        .annotate(open_count=Count("id"))
        .values_list("place_id", "open_count")
    )
    category_labels = {c.code: c.name_i18n() for c in Category.objects.all()}
    top_cta_places = [
        {
            "place_id": row["place_id"],
            "name": row["place__name_ru"] or row["place__name"],
            "category": category_labels.get(row["place__category"], row["place__category"]),
            "district": row["place__district"] or "—",
            "cta_count": int(row["cta_count"]),
            "open_count": int(opens_by_place.get(row["place_id"]) or 0),
            "cta_from_open_pct": _safe_pct(
                int(row["cta_count"]),
                int(opens_by_place.get(row["place_id"]) or 0),
            ),
        }
        for row in cta_by_place
    ]

    # ── 7. Top categories (by place count) ───────────────────────────────
    top_categories_qs = (
        places_qs
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    top_categories = [
        {"name": category_labels.get(item["category"], item["category"]), "total": item["total"]}
        for item in top_categories_qs
    ]
    max_cat = max((c["total"] for c in top_categories), default=1)
    for c in top_categories:
        c["bar_pct"] = round(c["total"] / max_cat * 100) if max_cat else 0

    # ── 8. Top districts (by place count) ────────────────────────────────
    top_districts_qs = (
        places_qs
        .exclude(district__isnull=True)
        .exclude(district="")
        .values("district")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    top_districts = list(top_districts_qs)
    max_dist = max((d["total"] for d in top_districts), default=1)
    for d in top_districts:
        d["bar_pct"] = round(d["total"] / max_dist * 100) if max_dist else 0

    # ── 9. Recent places ─────────────────────────────────────────────────
    recent_places = list(places_qs.order_by("-created_at").select_related()[:5])

    # ── 10. Detailed tables (weekly/monthly) ─────────────────────────────
    # Use a longer lookback for detailed data regardless of selected period
    detailed_start = today - timedelta(days=364)
    weekly_visits = _build_weekly_visits(visits_qs, detailed_start)
    monthly_visits = _build_monthly_visits(visits_qs, detailed_start)
    weekly_funnel = _build_weekly_funnel_stats(events_qs, detailed_start)
    monthly_funnel = _build_monthly_funnel_stats(events_qs, detailed_start)
    funnel_steps = _build_funnel_steps(funnel_current)

    # ── 11. GA4 ───────────────────────────────────────────────────────────
    ga4 = build_google_analytics_context()

    return {
        "period_days": period_days,
        "period_start": current_start,
        "period_end": today,
        "kpi": kpi,
        "kpi_cards": kpi_cards,
        "open_per_search_display": open_per_search_display,
        "catalog_state": catalog_state,
        "visits_daily_chart": visits_daily_chart,
        "funnel_current": funnel_current,
        "funnel_steps": funnel_steps,
        "top_cta_places": top_cta_places,
        "top_categories": top_categories,
        "top_districts": top_districts,
        "recent_places": recent_places,
        "weekly_visits": weekly_visits,
        "monthly_visits": monthly_visits,
        "weekly_funnel": weekly_funnel,
        "monthly_funnel": monthly_funnel,
        "ga4": ga4,
    }


# ---------------------------------------------------------------------------
# Legacy function kept for backward compatibility (existing tests use it)
# ---------------------------------------------------------------------------

def _build_period_funnel_stats(events_qs):
    today = timezone.localdate()
    period_starts = {
        "day": today,
        "week": today - timedelta(days=6),
        "month": today - timedelta(days=29),
        "year": today - timedelta(days=364),
    }

    stats = {}
    for period_name, start_day in period_starts.items():
        period_rows = (
            events_qs.filter(day__gte=start_day)
            .values("event_type")
            .annotate(total=Count("id"))
            .order_by()
        )
        totals = {row["event_type"]: int(row.get("total") or 0) for row in period_rows}

        search = totals.get(FunnelEvent.EVENT_CATALOG_SEARCH, 0)
        catalog_filter = totals.get(FunnelEvent.EVENT_CATALOG_FILTER, 0)
        place_open = totals.get(FunnelEvent.EVENT_PLACE_OPEN, 0)
        cta_call = totals.get(FunnelEvent.EVENT_CTA_CALL, 0)
        cta_whatsapp = totals.get(FunnelEvent.EVENT_CTA_WHATSAPP, 0)
        cta_instagram = totals.get(FunnelEvent.EVENT_CTA_INSTAGRAM, 0)
        cta_total = cta_call + cta_whatsapp + cta_instagram

        open_per_search = _safe_ratio(place_open, search)
        cta_from_open_pct = _safe_pct(cta_total, place_open)

        stats[period_name] = {
            "search": search,
            "filter": catalog_filter,
            "open": place_open,
            "cta_call": cta_call,
            "cta_whatsapp": cta_whatsapp,
            "cta_instagram": cta_instagram,
            "cta_total": cta_total,
            "open_per_search": open_per_search,
            # Keep old key for backwards-compat with existing tests
            "open_from_search_pct": round(place_open / search * 100, 1) if search else 0.0,
            "cta_from_open_pct": cta_from_open_pct if cta_from_open_pct is not None else 0.0,
        }

    return stats


def build_site_analytics_context() -> dict:
    """Legacy function — kept for backward compatibility. Prefer build_statistics_context()."""
    now = timezone.now()
    cutoff_7 = now - timedelta(days=7)
    cutoff_30 = now - timedelta(days=30)

    places_qs = Place.objects.all()
    place_reviews_qs = PlaceReview.objects.all()
    site_reviews_qs = SiteReview.objects.all()
    visits_qs = SiteVisit.objects.all()
    events_qs = FunnelEvent.objects.all()

    places_stats = {
        "total": places_qs.count(),
        "active": places_qs.filter(is_active=True).count(),
        "verified": places_qs.filter(is_verified=True).count(),
        "new_7": places_qs.filter(created_at__gte=cutoff_7).count(),
        "new_30": places_qs.filter(created_at__gte=cutoff_30).count(),
        "likes_total": places_qs.aggregate(total=Sum("likes_count")).get("total") or 0,
        "avg_rating": round(float(places_qs.aggregate(avg=Avg("rating_avg")).get("avg") or 0), 2),
    }

    place_reviews_stats = {
        "total": place_reviews_qs.count(),
        "avg_rating": round(float(place_reviews_qs.aggregate(avg=Avg("rating")).get("avg") or 0), 2),
    }

    site_reviews_stats = {
        "total": site_reviews_qs.count(),
        "avg_rating": round(float(site_reviews_qs.aggregate(avg=Avg("rating")).get("avg") or 0), 2),
    }

    visits_stats = {}
    today = timezone.localdate()
    periods = {
        "day": today,
        "week": today - timedelta(days=6),
        "month": today - timedelta(days=29),
        "year": today - timedelta(days=364),
    }
    for key, start_day in periods.items():
        period_qs = visits_qs.filter(day__gte=start_day)
        visits_stats[key] = {
            "unique_sessions": period_qs.values("session_key").distinct().count(),
            "page_views": period_qs.aggregate(total=Sum("hits")).get("total") or 0,
        }

    top_categories = places_qs.values("category").annotate(total=Count("id")).order_by("-total")[:7]
    category_labels = {c.code: c.name_i18n() for c in Category.objects.all()}
    top_categories = [
        {"name": category_labels.get(item["category"], item["category"]), "total": item["total"]}
        for item in top_categories
    ]

    top_districts = (
        places_qs.exclude(district__isnull=True)
        .exclude(district="")
        .values("district")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    top_cta_places = (
        events_qs.filter(
            day__gte=today - timedelta(days=29),
            event_type__in=(
                FunnelEvent.EVENT_CTA_CALL,
                FunnelEvent.EVENT_CTA_WHATSAPP,
                FunnelEvent.EVENT_CTA_INSTAGRAM,
            ),
            place__isnull=False,
        )
        .values("place_id", "place__name_ru", "place__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    recent_places = places_qs.order_by("-created_at")[:8]

    funnel_stats = _build_period_funnel_stats(events_qs)

    today_start = today
    year_start = today - timedelta(days=364)
    visits_daily_chart = _build_daily_visits_chart(visits_qs, today - timedelta(days=29), today)
    funnel_daily_chart = _build_daily_visits_chart(visits_qs, today - timedelta(days=29), today)
    weekly_visits = _build_weekly_visits(visits_qs, year_start)
    monthly_visits = _build_monthly_visits(visits_qs, year_start)
    weekly_funnel = _build_weekly_funnel_stats(events_qs, year_start)
    monthly_funnel = _build_monthly_funnel_stats(events_qs, year_start)
    ga4 = build_google_analytics_context()

    # build legacy period chart data
    visits_period_chart = {
        "labels": ["1d", "7d", "30d", "365d"],
        "unique_sessions": [
            int((visits_stats.get("day") or {}).get("unique_sessions") or 0),
            int((visits_stats.get("week") or {}).get("unique_sessions") or 0),
            int((visits_stats.get("month") or {}).get("unique_sessions") or 0),
            int((visits_stats.get("year") or {}).get("unique_sessions") or 0),
        ],
        "page_views": [
            int((visits_stats.get("day") or {}).get("page_views") or 0),
            int((visits_stats.get("week") or {}).get("page_views") or 0),
            int((visits_stats.get("month") or {}).get("page_views") or 0),
            int((visits_stats.get("year") or {}).get("page_views") or 0),
        ],
    }
    funnel_period_chart = {
        "labels": ["1d", "7d", "30d", "365d"],
        "search": [
            int((funnel_stats.get("day") or {}).get("search") or 0),
            int((funnel_stats.get("week") or {}).get("search") or 0),
            int((funnel_stats.get("month") or {}).get("search") or 0),
            int((funnel_stats.get("year") or {}).get("search") or 0),
        ],
        "filter": [
            int((funnel_stats.get("day") or {}).get("filter") or 0),
            int((funnel_stats.get("week") or {}).get("filter") or 0),
            int((funnel_stats.get("month") or {}).get("filter") or 0),
            int((funnel_stats.get("year") or {}).get("filter") or 0),
        ],
        "open": [
            int((funnel_stats.get("day") or {}).get("open") or 0),
            int((funnel_stats.get("week") or {}).get("open") or 0),
            int((funnel_stats.get("month") or {}).get("open") or 0),
            int((funnel_stats.get("year") or {}).get("open") or 0),
        ],
        "cta": [
            int((funnel_stats.get("day") or {}).get("cta_total") or 0),
            int((funnel_stats.get("week") or {}).get("cta_total") or 0),
            int((funnel_stats.get("month") or {}).get("cta_total") or 0),
            int((funnel_stats.get("year") or {}).get("cta_total") or 0),
        ],
    }

    return {
        "places_stats": places_stats,
        "place_reviews_stats": place_reviews_stats,
        "site_reviews_stats": site_reviews_stats,
        "visits_stats": visits_stats,
        "top_categories": top_categories,
        "top_districts": top_districts,
        "top_cta_places": top_cta_places,
        "recent_places": recent_places,
        "funnel_stats": funnel_stats,
        "visits_daily_chart": visits_daily_chart,
        "funnel_daily_chart": funnel_daily_chart,
        "visits_period_chart": visits_period_chart,
        "funnel_period_chart": funnel_period_chart,
        "weekly_visits": weekly_visits,
        "monthly_visits": monthly_visits,
        "weekly_funnel": weekly_funnel,
        "monthly_funnel": monthly_funnel,
        "ga4": ga4,
    }
