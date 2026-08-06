"""Rollback an applied SEOChange on KidsMap.az.

Usage:
    python manage.py rollback_seo_change <CHANGE_ID>
"""

from django.core.management.base import BaseCommand, CommandError

from catalog.services.seo_fix_engine import SEOFixEngine


class Command(BaseCommand):
    help = "Rollback an applied SEOChange by ID"

    def add_arguments(self, parser):
        parser.add_argument("change_id", type=int, help="ID of the SEOChange to roll back")

    def handle(self, *args, **options):
        change_id = options["change_id"]
        engine = SEOFixEngine()

        try:
            change = engine.rollback_change(change_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Successfully rolled back SEOChange #{change.pk}: '{change.change_summary}'"
                )
            )
        except Exception as exc:
            raise CommandError(f"Failed to roll back SEOChange #{change_id}: {exc}")
