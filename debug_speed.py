import sys
import os
import django
import time

sys.path.append('/app/src')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum
from catalog.models import SiteVisit

today = timezone.localdate()
current_start = today - timedelta(days=29)

print("Starting speed test...")

t0 = time.time()
period_qs = SiteVisit.objects.filter(day__gte=current_start)
row_distinct = period_qs.aggregate(
    unique_sessions=Count("session_key", distinct=True),
    page_views=Sum("hits"),
)
t1 = time.time()
print(f"Distinct query took: {t1 - t0:.3f}s. Result: {row_distinct}")

t0 = time.time()
period_qs = SiteVisit.objects.filter(day__gte=current_start)
row_count = period_qs.aggregate(
    unique_sessions=Count("id"),
    page_views=Sum("hits"),
)
t1 = time.time()
print(f"Count(id) query took: {t1 - t0:.3f}s. Result: {row_count}")
