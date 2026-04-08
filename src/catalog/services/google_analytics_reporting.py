from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from django.conf import settings
from catalog.services.tracking import GA4_CONVERSION_EVENT_NAMES, GA4_TRACKED_EVENT_NAMES


def _empty_period_stats() -> dict[str, dict[str, int]]:
    empty = {"active_users": 0, "sessions": 0, "page_views": 0}
    return {
        "day": dict(empty),
        "week": dict(empty),
        "month": dict(empty),
        "year": dict(empty),
    }


def _empty_daily_chart() -> dict[str, list]:
    return {
        "labels": [],
        "active_users": [],
        "page_views": [],
    }


@dataclass(slots=True)
class GoogleAnalyticsAdminSnapshot:
    enabled: bool = False
    connected: bool = False
    measurement_id: str = ""
    property_id: str = ""
    credentials_path: str = ""
    error: str = ""
    period_stats: dict[str, dict[str, int]] = field(default_factory=_empty_period_stats)
    daily_chart: dict[str, list] = field(default_factory=_empty_daily_chart)
    top_pages: list[dict[str, Any]] = field(default_factory=list)
    top_events: list[dict[str, Any]] = field(default_factory=list)
    conversion_event_names: list[str] = field(default_factory=lambda: list(GA4_CONVERSION_EVENT_NAMES))

    def as_context(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "measurement_id": self.measurement_id,
            "property_id": self.property_id,
            "credentials_path": self.credentials_path,
            "error": self.error,
            "period_stats": self.period_stats,
            "daily_chart": self.daily_chart,
            "top_pages": self.top_pages,
            "top_events": self.top_events,
            "conversion_event_names": self.conversion_event_names,
        }


class GoogleAnalyticsAdminReportingService:
    PERIODS = {
        "day": "today",
        "week": "6daysAgo",
        "month": "29daysAgo",
        "year": "364daysAgo",
    }

    def build_snapshot(self) -> GoogleAnalyticsAdminSnapshot:
        snapshot = GoogleAnalyticsAdminSnapshot(
            enabled=bool(settings.GOOGLE_ANALYTICS_MEASUREMENT_ID or settings.GOOGLE_ANALYTICS_PROPERTY_ID),
            measurement_id=settings.GOOGLE_ANALYTICS_MEASUREMENT_ID,
            property_id=settings.GOOGLE_ANALYTICS_PROPERTY_ID,
            credentials_path=(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") or "").strip(),
        )
        if not snapshot.enabled:
            snapshot.error = "GA4 not configured."
            return snapshot
        if not snapshot.property_id:
            snapshot.error = "Set GOOGLE_ANALYTICS_PROPERTY_ID."
            return snapshot

        if snapshot.credentials_path and not os.path.exists(snapshot.credentials_path):
            snapshot.error = "GOOGLE_APPLICATION_CREDENTIALS points to a missing file."
            return snapshot

        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.analytics.data_v1beta.types import DateRange, Dimension, Filter, FilterExpression, Metric, OrderBy, RunReportRequest
            from google.auth.exceptions import DefaultCredentialsError
        except ImportError:
            snapshot.error = "google-analytics-data is not installed."
            return snapshot

        self._DateRange = DateRange
        self._Dimension = Dimension
        self._Filter = Filter
        self._FilterExpression = FilterExpression
        self._Metric = Metric
        self._OrderBy = OrderBy
        self._RunReportRequest = RunReportRequest

        try:
            client = BetaAnalyticsDataClient()
            snapshot.period_stats = self._build_period_stats(client)
            snapshot.daily_chart = self._build_daily_chart(client)
            snapshot.top_pages = self._build_top_pages(client)
            snapshot.top_events = self._build_top_events(client)
            snapshot.connected = True
            snapshot.error = ""
            return snapshot
        except DefaultCredentialsError:
            snapshot.error = "Set GOOGLE_APPLICATION_CREDENTIALS or configure default Google credentials."
            return snapshot
        except Exception as exc:
            snapshot.error = str(exc)[:300] or "Failed to load GA4 data."
            return snapshot

    def _property_name(self) -> str:
        return f"properties/{settings.GOOGLE_ANALYTICS_PROPERTY_ID}"

    def _run_report(
        self,
        client,
        *,
        start_date: str,
        end_date: str,
        metrics: list[str],
        dimensions: list[str] | None = None,
        dimension_filter=None,
        order_by_metric: str = "",
        limit: int = 0,
    ):
        order_bys = []
        if order_by_metric:
            order_bys.append(
                self._OrderBy(
                    metric=self._OrderBy.MetricOrderBy(metric_name=order_by_metric),
                    desc=True,
                )
            )

        request = self._RunReportRequest(
            property=self._property_name(),
            date_ranges=[self._DateRange(start_date=start_date, end_date=end_date)],
            metrics=[self._Metric(name=name) for name in metrics],
            dimensions=[self._Dimension(name=name) for name in (dimensions or [])],
            dimension_filter=dimension_filter,
            order_bys=order_bys,
            limit=limit or None,
        )
        return client.run_report(request)

    def _build_period_stats(self, client) -> dict[str, dict[str, int]]:
        stats = _empty_period_stats()
        for period_name, start_date in self.PERIODS.items():
            response = self._run_report(
                client,
                start_date=start_date,
                end_date="today",
                metrics=["activeUsers", "sessions", "screenPageViews"],
            )
            row = response.rows[0] if response.rows else None
            if row is None:
                continue
            metric_values = [int(value.value or 0) for value in row.metric_values]
            stats[period_name] = {
                "active_users": metric_values[0] if len(metric_values) > 0 else 0,
                "sessions": metric_values[1] if len(metric_values) > 1 else 0,
                "page_views": metric_values[2] if len(metric_values) > 2 else 0,
            }
        return stats

    def _build_daily_chart(self, client) -> dict[str, list]:
        response = self._run_report(
            client,
            start_date="29daysAgo",
            end_date="today",
            dimensions=["date"],
            metrics=["activeUsers", "screenPageViews"],
        )
        chart = _empty_daily_chart()
        for row in response.rows:
            raw_date = row.dimension_values[0].value
            parsed = datetime.strptime(raw_date, "%Y%m%d")
            chart["labels"].append(parsed.strftime("%d.%m"))
            chart["active_users"].append(int(row.metric_values[0].value or 0))
            chart["page_views"].append(int(row.metric_values[1].value or 0))
        return chart

    def _build_top_pages(self, client) -> list[dict[str, Any]]:
        response = self._run_report(
            client,
            start_date="29daysAgo",
            end_date="today",
            dimensions=["pagePath"],
            metrics=["screenPageViews"],
            order_by_metric="screenPageViews",
            limit=10,
        )
        items: list[dict[str, Any]] = []
        for row in response.rows:
            items.append(
                {
                    "page_path": row.dimension_values[0].value or "/",
                    "page_views": int(row.metric_values[0].value or 0),
                }
            )
        return items

    def _build_top_events(self, client) -> list[dict[str, Any]]:
        dimension_filter = self._FilterExpression(
            filter=self._Filter(
                field_name="eventName",
                in_list_filter=self._Filter.InListFilter(
                    values=list(GA4_TRACKED_EVENT_NAMES),
                    case_sensitive=False,
                ),
            )
        )
        response = self._run_report(
            client,
            start_date="29daysAgo",
            end_date="today",
            dimensions=["eventName"],
            metrics=["eventCount"],
            dimension_filter=dimension_filter,
            order_by_metric="eventCount",
            limit=20,
        )
        items: list[dict[str, Any]] = []
        for row in response.rows:
            items.append(
                {
                    "event_name": row.dimension_values[0].value or "",
                    "event_count": int(row.metric_values[0].value or 0),
                }
            )
        return items


def build_google_analytics_context() -> dict[str, Any]:
    service = GoogleAnalyticsAdminReportingService()
    return service.build_snapshot().as_context()
