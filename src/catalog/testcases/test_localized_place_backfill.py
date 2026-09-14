import io
import json

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Place


class LocalizedPlaceBackfillTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(name='Museum', name_en='Toy Museum', category='EDU')
        Place.objects.filter(pk=self.place.pk).update(slug='old-address', slug_az='', slug_ru='', slug_en='')

    def run_command(self, *args):
        out = io.StringIO()
        call_command('backfill_localized_place_slugs', *args, stdout=out)
        return json.loads(out.getvalue())

    def test_default_dry_run_does_not_write(self):
        before = list(Place.objects.values())
        result = self.run_command()
        self.assertEqual(result['would_change'], 1)
        self.assertEqual(result['changed'], 0)
        self.assertEqual(list(Place.objects.values()), before)

    def test_apply_preserves_az_and_fills_translation_idempotently(self):
        before = Place.objects.get(pk=self.place.pk).updated_at
        result = self.run_command('--apply', '--batch-size', '1')
        self.assertEqual(result['changed'], 1)
        self.place.refresh_from_db()
        self.assertEqual(self.place.slug_az, 'old-address')
        self.assertEqual(self.place.slug_en, 'toy-museum')
        self.assertEqual(self.place.slug_ru, '')
        self.assertEqual(self.place.updated_at, before)
        self.assertEqual(self.run_command('--apply')['changed'], 0)

    def test_resume_does_not_touch_earlier_record(self):
        self.assertEqual(self.run_command('--apply', '--after-pk', str(self.place.pk))['changed'], 0)
        self.place.refresh_from_db()
        self.assertEqual(self.place.slug_en, '')

    def test_existing_slugs_never_rewritten(self):
        Place.objects.filter(pk=self.place.pk).update(slug_en='already-stable')
        self.run_command('--apply')
        self.place.refresh_from_db()
        self.assertEqual(self.place.slug_en, 'already-stable')
