from django.conf import settings
from django.db.models import F
from django.utils import timezone

from catalog.models import AnalyticsIngressDaily


def record_analytics_ingress(*, accepted: int = 0, rejected: int = 0, rate_limited: int = 0):
    if not getattr(settings, "LOCAL_ANALYTICS_STORAGE_ENABLED", False):
        return
    row, _ = AnalyticsIngressDaily.objects.get_or_create(day=timezone.localdate())
    AnalyticsIngressDaily.objects.filter(pk=row.pk).update(
        accepted_count=F("accepted_count") + max(int(accepted), 0),
        rejected_count=F("rejected_count") + max(int(rejected), 0),
        rate_limited_count=F("rate_limited_count") + max(int(rate_limited), 0),
    )
