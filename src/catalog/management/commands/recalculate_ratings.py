"""
Management command to recalculate rating_avg and rating_count for all Places and Specialists.

Usage:
    python manage.py recalculate_ratings
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from catalog.models import Place, Specialist
from catalog.models.review import sync_place_rating_stats
from catalog.models.specialist import sync_specialist_rating_stats


class Command(BaseCommand):
    help = "Recalculate and synchronize rating_avg and rating_count for all Places and Specialists"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Starting rating stats recalculation..."))

        all_place_ids = list(Place.objects.values_list("id", flat=True))
        sync_place_rating_stats(all_place_ids)
        self.stdout.write(self.style.SUCCESS(f"Recalculated rating stats for {len(all_place_ids)} Place(s)."))

        all_specialist_ids = list(Specialist.objects.values_list("id", flat=True))
        sync_specialist_rating_stats(all_specialist_ids)
        self.stdout.write(self.style.SUCCESS(f"Recalculated rating stats for {len(all_specialist_ids)} Specialist(s)."))

        self.stdout.write(self.style.SUCCESS("Rating stats recalculation complete!"))
