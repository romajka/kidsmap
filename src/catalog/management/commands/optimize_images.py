from __future__ import annotations

from django.core.management.base import BaseCommand

from catalog.image_signals import MODEL_IMAGE_PROFILES
from catalog.models import Event, EventPhoto, Place, PlacePhoto, SiteGalleryImage, SiteSettings, Specialist, UserProfile
from catalog.services.images import generate_image_variants


BACKFILL_MODELS = (Place, PlacePhoto, Event, EventPhoto, Specialist, UserProfile, SiteGalleryImage, SiteSettings)


class Command(BaseCommand):
    help = "Generate optimized WebP variants for images that already exist in media storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            action="append",
            dest="models",
            help="Limit processing to a model label such as catalog.Place (repeatable).",
        )
        parser.add_argument("--limit", type=int, default=0, help="Maximum number of database objects per model.")
        parser.add_argument("--dry-run", action="store_true", help="List work without writing derivative files.")
        parser.add_argument("--force", action="store_true", help="Regenerate variants that already exist.")

    def handle(self, *args, **options):
        requested = {value.lower() for value in options["models"] or []}
        limit = max(options["limit"], 0)
        dry_run = options["dry_run"]
        force = options["force"]
        processed_files = 0
        generated_files = 0

        for model in BACKFILL_MODELS:
            label = model._meta.label
            if requested and label.lower() not in requested and model.__name__.lower() not in requested:
                continue
            queryset = model._base_manager.all().order_by("pk")
            if limit:
                queryset = queryset[:limit]
            instances = queryset.iterator() if not limit else queryset
            for instance in instances:
                for field_name, profile in MODEL_IMAGE_PROFILES[model].items():
                    file_field = getattr(instance, field_name, None)
                    if not file_field or not getattr(file_field, "name", ""):
                        continue
                    processed_files += 1
                    if dry_run:
                        continue
                    generated_files += len(generate_image_variants(file_field, profile, force=force))
            self.stdout.write(f"{label}: scanned")

        summary = f"Image files scanned: {processed_files}; variants generated: {generated_files}"
        if dry_run:
            summary += " (dry run)"
        self.stdout.write(self.style.SUCCESS(summary))
