from django.core.management.base import BaseCommand
from django.db.models import Q

from catalog.models import Place
from catalog.services.geocoding import PlaceGeocodingService


class Command(BaseCommand):
    help = "Populate missing or outdated place coordinates from address data."

    def add_arguments(self, parser):
        parser.add_argument("--place-id", type=int, dest="place_id", help="Geocode only one place by id.")
        parser.add_argument("--limit", type=int, default=0, help="Max number of places to process.")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-geocode even places that already have coordinates.",
        )

    def handle(self, *args, **options):
        place_id = options.get("place_id")
        force = bool(options.get("force"))
        limit = max(int(options.get("limit") or 0), 0)

        queryset = Place.objects.filter(deleted_at__isnull=True).exclude(address="").order_by("id")
        if place_id:
            queryset = queryset.filter(id=place_id)
        if not force:
            queryset = queryset.filter(Q(lat__isnull=True) | Q(lng__isnull=True))

        places = list(queryset[:limit] if limit else queryset)
        service = PlaceGeocodingService.build_default()

        updated = 0
        skipped = 0

        for place in places:
            result = service.geocode_place(place=place, overwrite=force)
            if result.updated:
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"[UPDATED] #{place.id} {place.name_i18n()}"))
            else:
                skipped += 1
                self.stdout.write(f"[SKIPPED:{result.reason}] #{place.id} {place.name_i18n()}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Geocoding completed. Processed: {len(places)}, Updated: {updated}, Skipped: {skipped}"
            )
        )
