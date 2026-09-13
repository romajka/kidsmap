from datetime import timedelta

from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from catalog.models import Place
from catalog.services.analytics_metrics import build_subject_metrics
from catalog.services.place_access import PLACE_PERMISSION_VIEW_STATS, has_place_permission


class OwnerAnalyticsController:
    def build_context(self, *, request, place_id: int) -> dict:
        if not getattr(settings, "OWNER_ANALYTICS_ENABLED", False):
            raise Http404
        place = Place.objects.filter(pk=place_id, deleted_at__isnull=True).first()
        if place is None or not has_place_permission(
            user=request.user, place=place, permission_code=PLACE_PERMISSION_VIEW_STATS
        ):
            raise Http404
        end = timezone.now()
        start = end - timedelta(days=30)
        metrics = build_subject_metrics(
            subject_type="place", subject_ids=[place.pk], start=start, end=end
        )
        collection_started = parse_datetime(str(getattr(settings, "ANALYTICS_COLLECTION_STARTED_AT", "") or ""))
        return {
            "place": place,
            "metrics": metrics,
            "period_start": start,
            "period_end": end,
            "collection_started_at": collection_started,
            "analytics_last_updated_at": end if metrics.available else None,
        }


owner_analytics_controller = OwnerAnalyticsController()
