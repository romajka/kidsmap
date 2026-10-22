"""Read-only manual-review inventory. Never infer missing digits or rewrite data."""
from collections import Counter
from copy import deepcopy
import json

from django.core.management.base import BaseCommand
from django.db import connections, transaction
from catalog.models import Place, Organization
from catalog.services.phone_numbers import normalize_whatsapp, safe_phone
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Read-only counts of invalid/noncanonical contact numbers. No number repairs.'

    def add_arguments(self, parser):
        parser.add_argument('--include-ids', action='store_true', help='Include place/organization IDs for manual review; never raw numbers.')

    def handle(self, *args, **options):
        alias = 'phone_contacts_readonly'
        connections.databases[alias] = deepcopy(connections['default'].settings_dict)
        connection = connections[alias]
        counts, review = Counter(), []
        try:
            with transaction.atomic(using=alias):
                with connection.cursor() as cursor:
                    if connection.vendor == 'postgresql':
                        cursor.execute('SET TRANSACTION READ ONLY')
                        cursor.execute("SET LOCAL statement_timeout = '20s'")
                        cursor.execute("SET LOCAL lock_timeout = '2s'")
                    elif connection.vendor == 'sqlite':
                        cursor.execute('PRAGMA query_only = ON')
                    else:
                        raise RuntimeError('Read-only audit supports PostgreSQL and SQLite only.')
                for kind, model, fields in [
                    ('place', Place, ['phone1', 'phone2', 'phone3', 'whatsapp_number']),
                    ('organization', Organization, ['phone', 'whatsapp']),
                ]:
                    extra = ['phone_country', 'whatsapp_mode'] if kind == 'place' else []
                    for row in model.objects.using(alias).values('pk', *fields, *extra).iterator(chunk_size=500):
                        counts[kind + '_scanned'] += 1
                        if row.get('whatsapp_mode') == 'legacy':
                            counts['place_legacy_mode'] += 1
                        for name in fields:
                            raw = row[name]
                            if not raw:
                                if name == 'whatsapp_number' and row.get('whatsapp_mode') == 'separate':
                                    reason = 'missing_separate_whatsapp'
                                else:
                                    continue
                            else:
                                if name in {'whatsapp_number', 'whatsapp'}:
                                    try:
                                        canonical = normalize_whatsapp(raw, default_region=row.get('phone_country', 'AZ'))
                                    except ValidationError:
                                        canonical = ''
                                else:
                                    canonical = safe_phone(raw, default_region=row.get('phone_country', 'AZ'))
                                reason = 'invalid_manual_review' if not canonical else 'noncanonical' if raw != canonical else ''
                            if reason:
                                counts[f'{kind}.{name}.{reason}'] += 1
                                if options['include_ids']:
                                    review.append({'kind': kind, 'id': row['pk'], 'field': name, 'reason': reason})
        finally:
            connection.close()
            del connections[alias]
            connections.databases.pop(alias, None)
        self.stdout.write(json.dumps({'read_only': True, 'counts': dict(sorted(counts.items())),
                                      'manual_review': review, 'repairs': 0}, ensure_ascii=False))
