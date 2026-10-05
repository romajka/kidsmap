"""External QA-only causal replay of the unchanged legacy sitemap assertion."""
from datetime import datetime,timezone as datetime_timezone
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from catalog.testcases import public as legacy

class SitemapClockProbe(TestCase):
    def replay(self,zone):
        original=legacy.create_quality_place
        fixed=datetime(2026,10,3,21,30,tzinfo=datetime_timezone.utc)
        def fixed_place(*args,**kwargs):
            place=original(*args,**kwargs)
            type(place).objects.filter(pk=place.pk).update(updated_at=fixed)
            place.refresh_from_db()
            self.assertEqual(place.updated_at,fixed)
            return place
        with timezone.override(zone),patch.object(legacy,'create_quality_place',fixed_place):
            legacy.TestPublicPagesSmoke.test_sitemap_lastmod_matches_model_updated_at(self)
    def test_original_assertion_rejects_correct_local_date_after_midnight(self):
        with self.assertRaisesRegex(AssertionError,'lastmod 2026-10-04 should start with 2026-10-03'):
            self.replay('Asia/Baku')
    def test_same_original_assertion_passes_when_active_timezone_is_utc(self):
        self.replay('UTC')
