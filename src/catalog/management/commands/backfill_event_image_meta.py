"""Fill poster size, orientation and dominant colour for already uploaded event photos.

Usage:
    python manage.py backfill_event_image_meta            # only rows without facts
    python manage.py backfill_event_image_meta --force    # recompute every row
    python manage.py backfill_event_image_meta --dry-run  # count only

Also creates the WebP sizes (responsive-images) that event photos did not get
before. Source files are never modified; focus points are left as they are.
"""
from django.core.management.base import BaseCommand

from catalog.models import Event, EventPhoto
from catalog.services.event_images import refresh_meta


class Command(BaseCommand):
    help = 'Compute size/orientation/dominant colour (and WebP sizes) for event posters and gallery photos.'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Recompute rows that already have facts.')
        parser.add_argument('--dry-run', action='store_true', help='Only report how many rows would be processed.')

    def handle(self, *args, force=False, dry_run=False, **options):
        batches = (
            ('events', Event.objects.exclude(photo='').exclude(photo__isnull=True), 'photo_width'),
            ('gallery photos', EventPhoto.objects.exclude(image=''), 'width'),
        )
        for label, queryset, width_field in batches:
            if not force:
                queryset = queryset.filter(**{width_field + '__isnull': True})
            total = queryset.count()
            if dry_run:
                self.stdout.write(f'{label}: {total} to process')
                continue
            done = skipped = 0
            for instance in queryset.order_by('pk').iterator(chunk_size=100):
                if refresh_meta(instance, force=True):
                    done += 1
                else:
                    skipped += 1
            self.stdout.write(self.style.SUCCESS(f'{label}: {done} updated, {skipped} unreadable or missing files'))
