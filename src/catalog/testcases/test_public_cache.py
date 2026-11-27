from django.core.cache import cache
from django.test import TestCase

from catalog.models import AnalyticsIngressDaily, Category, Place, ServerDraft
from catalog.services.public_cache import affects_public_data, cached, data_version


class PublicCacheTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_catalog_models_bump_the_version_and_tracking_models_do_not(self):
        self.assertTrue(affects_public_data(Place))
        self.assertTrue(affects_public_data(Category))
        self.assertFalse(affects_public_data(AnalyticsIngressDaily))
        self.assertFalse(affects_public_data(ServerDraft))

    def test_a_saved_place_starts_a_new_generation(self):
        calls = []
        build = lambda: calls.append(1) or len(calls)
        self.assertEqual(cached('probe', ('az',), build), 1)
        self.assertEqual(cached('probe', ('az',), build), 1)      # served from cache
        self.assertEqual(cached('probe', ('ru',), build), 2)      # other inputs, other entry
        before = data_version()
        Place.objects.create(name='Cache probe', category='EDU')
        self.assertGreater(data_version(), before)
        self.assertEqual(cached('probe', ('az',), build), 3)      # rebuilt after the save

    def test_cache_outage_falls_back_to_building(self):
        from unittest import mock
        with mock.patch('catalog.services.public_cache.cache.get', side_effect=RuntimeError('down')):
            self.assertEqual(cached('probe', (), lambda: 'fresh'), 'fresh')


class PlaceDetailCleanupTests(TestCase):
    def test_uniform_week_collapses_only_identical_open_days(self):
        from catalog.templatetags.place_detail_extras import uniform_week
        same = [{'lines': ['10:00–22:30'], 'is_closed': False} for _ in range(7)]
        self.assertEqual(uniform_week(same), '10:00–22:30')
        self.assertEqual(uniform_week(same[:6] + [{'lines': ['10:00–18:00'], 'is_closed': False}]), '')
        self.assertEqual(uniform_week(same[:6] + [{'lines': [], 'is_closed': True}]), '')
        self.assertEqual(uniform_week([]), '')
