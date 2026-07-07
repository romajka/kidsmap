import sys
import os
import django

# Setup django environment
sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import time
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncMonth, TruncWeek
from catalog.models import FunnelEvent, Place, PlaceReview, SiteReview, SiteVisit, Category
from catalog.services.google_analytics_reporting import build_google_analytics_context
from catalog.services.admin_analytics import _build_visits_for_period, _build_funnel_for_period, _build_daily_visits_chart, _build_weekly_visits, _build_monthly_visits, _build_weekly_funnel_stats, _build_monthly_funnel_stats, _build_funnel_steps, _safe_pct, _safe_ratio, _delta_pct, _build_delta_meta

def debug_statistics_context(period_days: int = 30):
    print("Starting debug_statistics_context...")
    t0 = time.time()
    
    today = timezone.localdate()
    current_start = today - timedelta(days=period_days - 1)
    prev_start = current_start - timedelta(days=period_days)
    prev_end = current_start - timedelta(days=1)
    
    print(f"Dates: today={today}, current_start={current_start}, prev_start={prev_start}, prev_end={prev_end}")

    visits_qs = SiteVisit.objects.all()
    events_qs = FunnelEvent.objects.all()
    places_qs = Place.objects.all()
    place_reviews_qs = PlaceReview.objects.all()

    # ── 1. Visits ──
    print("1. Querying visits current...")
    t = time.time()
    visits_current = _build_visits_for_period(visits_qs, current_start)
    print(f"   Done in {time.time() - t:.3f}s: {visits_current}")
    
    print("1. Querying visits prev...")
    t = time.time()
    visits_prev = _build_visits_for_period(visits_qs.filter(day__lte=prev_end), prev_start)
    print(f"   Done in {time.time() - t:.3f}s: {visits_prev}")

    # ── 2. Funnel ──
    print("2. Querying funnel current...")
    t = time.time()
    funnel_current = _build_funnel_for_period(events_qs.filter(day__gte=current_start), current_start)
    print(f"   Done in {time.time() - t:.3f}s: {funnel_current}")
    
    print("2. Querying funnel prev...")
    t = time.time()
    funnel_prev = _build_funnel_for_period(
        events_qs.filter(day__gte=prev_start, day__lte=prev_end), prev_start
    )
    print(f"   Done in {time.time() - t:.3f}s: {funnel_prev}")

    # ── 3. KPI deltas ──
    print("3. Building KPI deltas...")
    # Just basic computations, no DB queries
    kpi = {
        "unique_sessions": visits_current["unique_sessions"],
        "page_views": visits_current["page_views"],
        "searches": funnel_current["search"],
        "place_opens": funnel_current["open"],
        "cta_total": funnel_current["cta_total"],
        "cta_from_open_pct": funnel_current["cta_from_open_pct"],
        "open_per_search": funnel_current["open_per_search"],
    }
    print("   Done.")

    # ── 4. Daily chart ──
    print("4. Querying daily visits chart...")
    t = time.time()
    visits_daily_chart = _build_daily_visits_chart(visits_qs, current_start, today)
    print(f"   Done in {time.time() - t:.3f}s (points count: {len(visits_daily_chart['labels'])})")

    # ── 5. Places ──
    print("5. Querying places aggregation...")
    t = time.time()
    places_agg = places_qs.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        verified=Count("id", filter=Q(is_verified=True)),
        pending=Count("id", filter=Q(status=Place.STATUS_PENDING)),
        no_coords=Count("id", filter=Q(lat__isnull=True) | Q(lng__isnull=True)),
    )
    print(f"   Done in {time.time() - t:.3f}s: {places_agg}")
    
    print("5. Querying place reviews aggregation...")
    t = time.time()
    place_reviews_agg = place_reviews_qs.aggregate(
        total=Count("id"),
        avg_rating=Avg("rating"),
    )
    print(f"   Done in {time.time() - t:.3f}s: {place_reviews_agg}")

    # ── 6. Top CTA places ──
    print("6. Querying top CTA places...")
    t = time.time()
    cta_events_period = events_qs.filter(
        day__gte=current_start,
        event_type__in=(
            FunnelEvent.EVENT_CTA_CALL,
            FunnelEvent.EVENT_CTA_WHATSAPP,
            FunnelEvent.EVENT_CTA_INSTAGRAM,
        ),
        place__isnull=False,
    )
    cta_by_place = list(
        cta_events_period
        .values("place_id", "place__name_ru", "place__name", "place__category", "place__district")
        .annotate(cta_count=Count("id"))
        .order_by("-cta_count")[:5]
    )
    print(f"   Done CTA query in {time.time() - t:.3f}s, count={len(cta_by_place)}")

    print("6. Querying opens by place...")
    t = time.time()
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
    print(f"   Done opens query in {time.time() - t:.3f}s")

    # ── 7. Top categories ──
    print("7. Querying top categories...")
    t = time.time()
    top_categories_qs = list(
        places_qs
        .values("category")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    print(f"   Done in {time.time() - t:.3f}s: {top_categories_qs}")

    # ── 8. Top districts ──
    print("8. Querying top districts...")
    t = time.time()
    top_districts_qs = list(
        places_qs
        .exclude(district__isnull=True)
        .exclude(district="")
        .values("district")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    print(f"   Done in {time.time() - t:.3f}s: {top_districts_qs}")

    # ── 9. Recent places ──
    print("9. Querying recent places...")
    t = time.time()
    recent_places = list(places_qs.order_by("-created_at").select_related()[:5])
    print(f"   Done in {time.time() - t:.3f}s: {[p.name for p in recent_places]}")

    # ── 10. Detailed tables ──
    print("10. Querying detailed tables (weekly visits)...")
    detailed_start = today - timedelta(days=364)
    t = time.time()
    weekly_visits = _build_weekly_visits(visits_qs, detailed_start)
    print(f"    Done in {time.time() - t:.3f}s, count={len(weekly_visits)}")

    print("10. Querying detailed tables (monthly visits)...")
    t = time.time()
    monthly_visits = _build_monthly_visits(visits_qs, detailed_start)
    print(f"    Done in {time.time() - t:.3f}s, count={len(monthly_visits)}")

    print("10. Querying detailed tables (weekly funnel)...")
    t = time.time()
    weekly_funnel = _build_weekly_funnel_stats(events_qs, detailed_start)
    print(f"    Done in {time.time() - t:.3f}s, count={len(weekly_funnel)}")

    print("10. Querying detailed tables (monthly funnel)...")
    t = time.time()
    monthly_funnel = _build_monthly_funnel_stats(events_qs, detailed_start)
    print(f"    Done in {time.time() - t:.3f}s, count={len(monthly_funnel)}")

    # ── 11. GA4 ──
    print("11. Querying GA4...")
    t = time.time()
    ga4 = build_google_analytics_context()
    print(f"    Done in {time.time() - t:.3f}s")
    
    print(f"ALL STEPS COMPLETED in {time.time() - t0:.3f}s!")

if __name__ == '__main__':
    debug_statistics_context()
