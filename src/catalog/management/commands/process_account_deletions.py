from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone

from catalog.models import AccountDeletionAudit, AccountDeletionRequest
from catalog.services.account_deletion import finalize_account_deletion


class Command(BaseCommand):
    help = "Process due account-deletion requests without emitting personal data."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Count due requests without changing data.")
        parser.add_argument("--limit", type=int, default=100, help="Maximum requests to process (1-1000).")

    def handle(self, *args, **options):
        limit = int(options["limit"])
        if limit < 1 or limit > 1000:
            raise CommandError("--limit must be between 1 and 1000")
        now = timezone.now()
        due = AccountDeletionRequest.objects.filter(
            status__in=(AccountDeletionRequest.Status.SCHEDULED, AccountDeletionRequest.Status.FAILED),
            scheduled_for__isnull=False,
            scheduled_for__lte=now,
        ).order_by("scheduled_for", "id")
        held = AccountDeletionRequest.objects.filter(
            Q(status=AccountDeletionRequest.Status.HELD) | ~Q(hold_code="")
        ).count()
        future = AccountDeletionRequest.objects.filter(
            status__in=(AccountDeletionRequest.Status.SCHEDULED, AccountDeletionRequest.Status.FAILED),
            scheduled_for__gt=now,
        ).count()
        due_ids = list(due.values_list("id", flat=True)[:limit])
        expired_audits = AccountDeletionAudit.objects.filter(retain_until__lte=now)
        expired_requests = AccountDeletionRequest.objects.filter(
            status__in=(AccountDeletionRequest.Status.COMPLETED, AccountDeletionRequest.Status.CANCELED),
            purge_after__isnull=False,
            purge_after__lte=now,
        )
        if options["dry_run"]:
            self.stdout.write(
                f"dry_run=1 processed=0 completed=0 held={held} failed=0 skipped={future} due={len(due_ids)} "
                f"audits_due_for_purge={expired_audits.count()} requests_due_for_purge={expired_requests.count()}"
            )
            return

        counts = {"processed": 0, "completed": 0, "held": 0, "failed": 0, "skipped": future}
        for request_id in due_ids:
            result = finalize_account_deletion(request_id, now=now)
            counts["processed"] += 1
            if result.outcome in counts:
                counts[result.outcome] += 1
            else:
                counts["skipped"] += 1
        counts["held"] += held
        audits_purged = int(expired_audits.delete()[0])
        requests_purged = int(expired_requests.delete()[0])
        self.stdout.write(
            " ".join(
                f"{key}={counts[key]}"
                for key in ("processed", "completed", "held", "failed", "skipped")
            )
            + f" audits_purged={audits_purged} requests_purged={requests_purged}"
        )
        if counts["failed"]:
            raise CommandError("One or more account-deletion requests failed; see pseudonymous audit records.")
