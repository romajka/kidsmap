from __future__ import annotations

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import Category, Place, PlaceReview
from catalog.services.google_analytics_reporting import build_google_analytics_context


VALID_PERIODS = {7, 30, 90, 365}


def _delta_none() -> dict:
    return {
        "kind": "none",
        "class_name": "km-delta--none",
        "arrow": "",
        "text": str(_("Дельта недоступна в локальном режиме без хранения сырых событий")),
    }


def _build_kpi_card(*, key: str, label: str, value: int, icon: str, icon_class: str) -> dict:
    return {
        "key": key,
        "label": label,
        "value": int(value or 0),
        "formatted_value": "",
        "icon": icon,
        "icon_class": icon_class,
        "delta": _delta_none(),
    }


def _ga_period_key(period_days: int) -> str:
    if period_days <= 7:
        return "week"
    if period_days <= 30:
        return "month"
    return "year"


def _bar_items(rows: list[dict], *, key: str, label_key: str) -> list[dict]:
    max_total = max((int(item["total"]) for item in rows), default=1)
    result = []
    for item in rows:
        total = int(item["total"])
        result.append(
            {
                label_key: item[label_key],
                "total": total,
                "bar_pct": round(total / max_total * 100) if max_total else 0,
            }
        )
    return result


def build_statistics_context(period_days: int = 30) -> dict:
    if period_days not in VALID_PERIODS:
        period_days = 30

    today = timezone.localdate()
    current_start = today - timedelta(days=period_days - 1)
    ga4 = build_google_analytics_context()
    ga_period = _ga_period_key(period_days)
    ga_stats = ga4.get("period_stats", {}).get(ga_period, {})

    kpi_cards = [
        _build_kpi_card(
            key="unique_sessions",
            label=str(_("Активные пользователи")),
            value=int(ga_stats.get("active_users") or 0),
            icon="◔",
            icon_class="km-kpi-icon--blue",
        ),
        _build_kpi_card(
            key="sessions",
            label=str(_("Сессии")),
            value=int(ga_stats.get("sessions") or 0),
            icon="◎",
            icon_class="km-kpi-icon--teal",
        ),
        _build_kpi_card(
            key="page_views",
            label=str(_("Просмотры страниц")),
            value=int(ga_stats.get("page_views") or 0),
            icon="◈",
            icon_class="km-kpi-icon--green",
        ),
    ]

    chart = ga4.get("daily_chart") or {}
    visits_daily_chart = {
        "labels": list(chart.get("labels") or []),
        "unique_sessions": list(chart.get("active_users") or []),
        "page_views": list(chart.get("page_views") or []),
    }

    return {
        "period_days": period_days,
        "period_start": current_start,
        "period_end": today,
        "kpi": {
            "unique_sessions": int(ga_stats.get("active_users") or 0),
            "sessions": int(ga_stats.get("sessions") or 0),
            "page_views": int(ga_stats.get("page_views") or 0),
        },
        "kpi_cards": kpi_cards,
        "visits_chart_subtitle": str(_("GA4, последние 30 дней")),
        "visits_daily_chart": visits_daily_chart,
        "ga4_top_pages": list(ga4.get("top_pages") or []),
        "ga4_top_events": list(ga4.get("top_events") or []),
        "ga4": ga4,
    }


def build_site_analytics_context() -> dict:
    return build_statistics_context(period_days=30)
