"""Explicit local workflow email runner; dry run is the default."""
from django.core.management.base import BaseCommand, CommandError
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
            import json
            from catalog.services.workflow_email_delivery import preview
            report = preview()
            self.stdout.write(f'due={report["due"]}; delivery=disabled; limit={limit}; preview=' + json.dumps(report, sort_keys=True))
            return
        result = deliver_batch(limit=limit)
        self.stdout.write('; '.join(f'{key}={result[key]}' for key in ('sent', 'retry', 'failed', 'suppressed', 'notifications_sent')))
