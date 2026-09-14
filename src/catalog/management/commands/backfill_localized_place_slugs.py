"""Explicit, resumable backfill. Default/dry-run is strictly read-only."""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Max

from catalog.models import Place
from catalog.services.slugs import build_ascii_slug


class Command(BaseCommand):
    help = 'Fill missing localized Place slugs; defaults to read-only dry-run.'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument('--dry-run', action='store_true')
        mode.add_argument('--apply', action='store_true')
        parser.add_argument('--batch-size', type=int, default=200)
        parser.add_argument('--after-pk', type=int, default=0)

    def handle(self, *args, **options):
        size, cursor = options['batch_size'], options['after_pk']
        if not 1 <= size <= 2000 or cursor < 0:
            raise CommandError('batch-size must be 1..2000 and after-pk must be nonnegative.')
        stats = dict(mode='apply' if options['apply'] else 'dry-run', examined=0,
                     would_change=0, changed=0, manual_review=0, preserved_az=0,
                     generated_ru=0, generated_en=0, fallback_ru=0, fallback_en=0,
                     unchanged=0, last_pk=cursor)
        upper = Place.objects.aggregate(last=Max('pk'))['last'] or 0
        fields = ('pk', 'slug', 'name_ru', 'name_en', 'slug_az', 'slug_ru', 'slug_en')
        while cursor < upper:
            rows = list(Place.objects.filter(pk__gt=cursor, pk__lte=upper).order_by('pk').values(*fields)[:size])
            if not rows:
                break
            updates = []
            for row in rows:
                stats['examined'] += 1
                values = {}
                if not row['slug_az'] and row['slug']:
                    values['slug_az'] = row['slug']
                    # Reject unexpected legacy values rather than truncate a live URL.
                    if len(row['slug']) > 60:
                        stats['manual_review'] += 1
                        continue
                    stats['preserved_az'] += 1
                for lang in ('ru', 'en'):
                    if row[f'slug_{lang}']:
                        continue
                    value = build_ascii_slug(row[f'name_{lang}'], fallback='')
                    if value:
                        values[f'slug_{lang}'] = value
                        stats[f'generated_{lang}'] += 1
                    else:
                        stats[f'fallback_{lang}'] += 1
                if values:
                    stats['would_change'] += 1
                    updates.append((row, values))
                else:
                    stats['unchanged'] += 1
            if options['apply']:
                with transaction.atomic():
                    if connection.vendor == 'postgresql':
                        with connection.cursor() as db_cursor:
                            db_cursor.execute("SET LOCAL lock_timeout = '2s'")
                            db_cursor.execute("SET LOCAL statement_timeout = '20s'")
                    for snapshot, values in updates:
                        # Compare sources AND outputs: concurrent edits are never overwritten.
                        changed = Place.objects.filter(**snapshot).update(**values)
                        stats['changed'] += changed
                        stats['manual_review'] += int(not changed)
            cursor = rows[-1]['pk']
            stats['last_pk'] = cursor
        self.stdout.write(json.dumps(stats, sort_keys=True))
