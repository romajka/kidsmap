from django.core.management.base import BaseCommand

from catalog.services.favorite_metrics import reconcile_place_favorite_counts


class Command(BaseCommand):
    help = "Reconcile Place.likes_count with eligible registered-user favorites."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--place-id", action="append", type=int, dest="place_ids")

    def handle(self, *args, **options):
        result = reconcile_place_favorite_counts(place_ids=options["place_ids"], dry_run=options["dry_run"])
        self.stdout.write(f"checked={result.checked} changed={result.changed} dry_run={bool(options['dry_run'])}")
