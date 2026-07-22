from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction

from catalog.models import Event, Place, PlaceReview


class Command(BaseCommand):
    help = "Remove explicitly marked catalog demo rows from a PostgreSQL migration target."

    def add_arguments(self, parser):
        parser.add_argument("--database", default="default")
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--allow-production", action="store_true")

    def handle(self, *args, **options):
        alias = options["database"]
        connection = connections[alias]
        if connection.vendor != "postgresql":
            raise CommandError("Cleanup is allowed only on a PostgreSQL migration target.")
        database_name = str(connection.settings_dict.get("NAME", "")).lower()
        if options["apply"] and "test" not in database_name and not options["allow_production"]:
            raise CommandError(
                "Refusing cleanup outside a test database. "
                "Use --allow-production only after reviewing the dry-run output."
            )

        places = Place.objects.using(alias).filter(additional_info__startswith="seed:catalog-demo")
        reviews = PlaceReview.objects.using(alias).filter(
            session_key__startswith="seed:catalog-demo-review"
        )
        events = Event.objects.using(alias).filter(
            moderation_note__startswith="seed:catalog-demo-event"
        )
        counts = {
            "places": places.count(),
            "reviews": reviews.count(),
            "events": events.count(),
        }
        self.stdout.write(
            "Marked migration junk: "
            + ", ".join(f"{name}={count}" for name, count in counts.items())
        )
        if not options["apply"]:
            self.stdout.write("Dry run only; nothing was deleted. Add --apply after review.")
            return

        with transaction.atomic(using=alias):
            # Delete marker-specific children first, then the demo place graph.
            reviews.delete()
            events.delete()
            places.delete()
        self.stdout.write(self.style.SUCCESS("Marked demo data removed from migration target."))
