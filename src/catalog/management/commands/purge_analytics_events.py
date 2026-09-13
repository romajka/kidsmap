from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from catalog.models import FunnelEvent


class Command(BaseCommand):
    help = "Delete raw analytics events older than the approved retention period."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--batch-size", type=int, default=1000)

    def handle(self, *args, **options):
        retention = getattr(settings, "ANALYTICS_RAW_EVENT_RETENTION_DAYS", None)
        if not isinstance(retention, int) or retention < 1:
            raise CommandError("ANALYTICS_RAW_EVENT_RETENTION_DAYS must be a positive approved value")
        batch_size = int(options["batch_size"])
        if batch_size < 1:
            raise CommandError("--batch-size must be positive")
        cutoff = timezone.now() - timedelta(days=retention)
        eligible = FunnelEvent.objects.filter(
            Q(schema_version=2, occurred_at__lt=cutoff) | Q(schema_version=1, created_at__lt=cutoff)
        )
        total = eligible.count()
        deleted = 0
        if not options["dry_run"]:
            while True:
                ids = list(eligible.order_by("pk").values_list("pk", flat=True)[:batch_size])
                if not ids:
                    break
                deleted += FunnelEvent.objects.filter(pk__in=ids).delete()[0]
        self.stdout.write(f"eligible={total} deleted={deleted} dry_run={bool(options['dry_run'])}")
