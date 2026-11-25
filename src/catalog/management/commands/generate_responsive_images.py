"""Generate media derivatives only; never change database rows or originals."""
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.db import connection, transaction

from catalog.models import Place, SiteGalleryImage
from catalog.services.responsive_images import generate_variants, responsive_image, static_photo
from catalog.services.specialist_portraits import public_portraits


class Command(BaseCommand):
    help = 'Inspect responsive photos; use --apply to generate missing WebP sizes.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--specialists-only', action='store_true', help='Process only published specialist photos.')

    def handle(self, *args, **options):
        counts = dict(sources=0, ready=0, generated=0, pending=0, failed=0)
        seen = set()

        def process(image, target=None, *, portrait=False):
            if not image or not image.name or (image.name, portrait) in seen:
                return
            seen.add((image.name, portrait))
            counts['sources'] += 1
            ready = responsive_image(image, target_storage=target, portrait=portrait)
            if ready['srcset']:
                counts['ready'] += 1
            elif not options['apply']:
                counts['pending'] += 1
            else:
                result = generate_variants(image, target_storage=target, portrait=portrait)
                counts['generated' if result['srcset'] else 'failed'] += 1

        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
                    cursor.execute("SET LOCAL statement_timeout = '15s'")
                    cursor.execute("SET LOCAL lock_timeout = '2s'")
            photos = []
            if not options['specialists_only']:
                photos = [photo for place in Place.objects.only('photo', 'cover_photo').iterator(chunk_size=100)
                          for photo in (place.photo, place.cover_photo) if photo]
                photos.extend(item.image for item in SiteGalleryImage.objects.only('image').iterator(chunk_size=100) if item.image)
            portraits = [person.photo for person in public_portraits().iterator(chunk_size=100)]

        # Close the read-only database transaction before encoding photos.
        for photo in photos:
            process(photo)
        for photo in portraits:
            process(photo, portrait=True)

        if not options['specialists_only']:
            for filename in ('family-studio', 'kids-craft', 'music-lesson', 'family-balloons', 'art-class', 'sports-class', 'family-park', 'art-drawing', 'team-hands'):
                process(static_photo(f'img/home/photos/{filename}.jpg'), default_storage)
        self.stdout.write(('APPLY' if options['apply'] else 'DRY RUN') + ' ' + ' '.join(f'{k}={v}' for k, v in counts.items()))
