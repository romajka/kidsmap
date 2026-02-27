from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone

from catalog.models import FunnelEvent, Place, PlaceReview, SiteReview, SiteVisit


def _date_range(start_day, end_day):
    day = start_day
    while day <= end_day:
        yield day
        day += timedelta(days=1)


def _build_daily_visits_chart(visits_qs, days: int = 30):
    today = timezone.localdate()
    start_day = today - timedelta(days=days - 1)

    raw_rows = (
        visits_qs.filter(day__gte=start_day)
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

    labels = []
    unique_values = []
    page_view_values = []
    for day in _date_range(start_day, today):
        point = by_day.get(day, {})
        labels.append(day.strftime("%d.%m"))
        unique_values.append(int(point.get("unique_sessions") or 0))
        page_view_values.append(int(point.get("page_views") or 0))

    return {
        "labels": labels,
        "unique_sessions": unique_values,
        "page_views": page_view_values,
    }


def _build_funnel_daily_chart(events_qs, days: int = 30):
    today = timezone.localdate()
    start_day = today - timedelta(days=days - 1)

    raw_rows = (
        events_qs.filter(day__gte=start_day)
        .values("day", "event_type")
        .annotate(total=Count("id"))
        .order_by("day", "event_type")
    )
    by_day_event: dict = {}
    for row in raw_rows:
        key = (row["day"], row["event_type"])
        by_day_event[key] = int(row.get("total") or 0)

    labels = []
    search_values = []
    filter_values = []
    open_values = []
    cta_values = []
    for day in _date_range(start_day, today):
        labels.append(day.strftime("%d.%m"))
        search = by_day_event.get((day, FunnelEvent.EVENT_CATALOG_SEARCH), 0)
        catalog_filter = by_day_event.get((day, FunnelEvent.EVENT_CATALOG_FILTER), 0)
        place_open = by_day_event.get((day, FunnelEvent.EVENT_PLACE_OPEN), 0)
        cta_total = (
            by_day_event.get((day, FunnelEvent.EVENT_CTA_CALL), 0)
            + by_day_event.get((day, FunnelEvent.EVENT_CTA_WHATSAPP), 0)
            + by_day_event.get((day, FunnelEvent.EVENT_CTA_INSTAGRAM), 0)
        )
        search_values.append(search)
        filter_values.append(catalog_filter)
        open_values.append(place_open)
        cta_values.append(cta_total)

    return {
        "labels": labels,
        "search": search_values,
        "filter": filter_values,
        "open": open_values,
        "cta": cta_values,
    }


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

        open_from_search_pct = round((place_open / search) * 100, 1) if search else 0.0
        cta_from_open_pct = round((cta_total / place_open) * 100, 1) if place_open else 0.0

        stats[period_name] = {
            "search": search,
            "filter": catalog_filter,
            "open": place_open,
            "cta_call": cta_call,
            "cta_whatsapp": cta_whatsapp,
            "cta_instagram": cta_instagram,
            "cta_total": cta_total,
            "open_from_search_pct": open_from_search_pct,
            "cta_from_open_pct": cta_from_open_pct,
        }

    return stats


def _build_weekly_visits(visits_qs):
    today = timezone.localdate()
    start_day = today - timedelta(days=7 * 12 - 1)
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


def _build_monthly_visits(visits_qs):
    today = timezone.localdate()
    start_day = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
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


def _build_period_visits_chart(visits_stats: dict) -> dict:
    return {
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


def _build_period_funnel_chart(funnel_stats: dict) -> dict:
    return {
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


def _build_weekly_funnel_stats(events_qs):
    today = timezone.localdate()
    start_day = today - timedelta(days=7 * 12 - 1)
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


def _build_monthly_funnel_stats(events_qs):
    today = timezone.localdate()
    start_day = (today.replace(day=1) - timedelta(days=365)).replace(day=1)
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


def build_site_analytics_context() -> dict:
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
    category_labels = dict(Place.CATEGORY_CHOICES)
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
    visits_daily_chart = _build_daily_visits_chart(visits_qs, days=30)
    funnel_daily_chart = _build_funnel_daily_chart(events_qs, days=30)
    visits_period_chart = _build_period_visits_chart(visits_stats)
    funnel_period_chart = _build_period_funnel_chart(funnel_stats)
    weekly_visits = _build_weekly_visits(visits_qs)
    monthly_visits = _build_monthly_visits(visits_qs)
    weekly_funnel = _build_weekly_funnel_stats(events_qs)
    monthly_funnel = _build_monthly_funnel_stats(events_qs)

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
    }
