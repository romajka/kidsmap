from django.core.management.base import BaseCommand

from catalog.services.indexnow import retry_indexnow_urls


class Command(BaseCommand):
    help = "Deliver a batch of due IndexNow retries."

    def handle(self, *args, **options):
        result = retry_indexnow_urls()
        self.stdout.write(f"IndexNow retries: submitted={result.submitted_count}, accepted={result.accepted}")
