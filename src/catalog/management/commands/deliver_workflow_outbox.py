"""Explicit local workflow email runner; dry run is the default."""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from catalog.models import EmailOutbox
from catalog.services.workflow_notifications import deliver_batch


class Command(BaseCommand):
    help = 'Preview or deliver due service notification emails. --send is required to send.'

    def add_arguments(self, parser):
        parser.add_argument('--send', action='store_true')
        parser.add_argument('--limit', type=int, default=50)

    def handle(self, *args, **options):
        limit = options['limit']
        if not 1 <= limit <= 500:
            raise CommandError('limit must be between 1 and 500')
        if not options['send']:
            due = EmailOutbox.objects.filter(status__in=['pending', 'retry']).filter(
                Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=timezone.now())).count()
            self.stdout.write(f'due={due}; delivery=disabled; limit={limit}')
            return
        result = deliver_batch(limit=limit)
        self.stdout.write('; '.join(f'{key}={result[key]}' for key in ('sent', 'retry', 'failed', 'suppressed')))
