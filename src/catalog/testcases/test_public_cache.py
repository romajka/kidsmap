from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.test import Client, TransactionTestCase
from django.urls import reverse

from catalog.models import AnalyticsIngressDaily, Category, Place, ServerDraft, SiteSettings, SiteVisit
from catalog.services.filtering import PlaceListFilters
from catalog.testcases.utils import create_ready_place


class PublicCacheTests(TransactionTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)

    def test_price_limit_is_shared_across_filter_instances(self):
        SiteSettings.get_solo()
        create_ready_place()
        expected = PlaceListFilters(category='EDU').catalog_price_max
        self.assertGreater(expected, 0)
        with self.assertNumQueries(0):
            self.assertEqual(PlaceListFilters(category='EDU').catalog_price_max, expected)

    def test_catalog_models_bump_the_version_and_tracking_models_do_not(self):
        from catalog.services.public_cache import affects_public_data

        self.assertTrue(affects_public_data(Place))
        self.assertTrue(affects_public_data(Category))
        self.assertFalse(affects_public_data(AnalyticsIngressDaily))
        self.assertFalse(affects_public_data(ServerDraft))
        self.assertFalse(affects_public_data(SiteVisit))

    def test_a_saved_place_starts_a_new_generation(self):
        from catalog.services.public_cache import cached, data_version

        calls = []
        def build():
            calls.append(1)
            return len(calls)

        self.assertEqual(cached('probe', ('az',), build), 1)
        self.assertEqual(cached('probe', ('az',), build), 1)
        self.assertEqual(cached('probe', ('ru',), build), 2)
        before = data_version()
        create_ready_place()
        self.assertGreater(data_version(), before)
        self.assertEqual(cached('probe', ('az',), build), 3)

    def test_cache_outage_falls_back_to_building(self):
        from catalog.services.public_cache import cached

        with patch.object(cache, 'get', side_effect=RuntimeError('down')):
            self.assertEqual(cached('probe', (), lambda: 'fresh'), 'fresh')

    def test_rollback_neither_invalidates_nor_exposes_uncommitted_counts(self):
        from catalog.services.public_cache import cached, data_version

        create_ready_place()
        def count():
            return cached('probe_count', (), Place.objects.count)

        before_count = count()
        before_version = data_version()
        with transaction.atomic():
            create_ready_place()
            self.assertEqual(count(), before_count + 1)
            self.assertEqual(data_version(), before_version)
            transaction.set_rollback(True)
        self.assertEqual(data_version(), before_version)
        self.assertEqual(count(), before_count)

    def test_admin_withdrawal_refreshes_warm_home_and_catalog_maps_and_counters(self):
        place = create_ready_place()
        staff = get_user_model().objects.create_superuser('cache-admin', '', 'fictional')
        admin_client = Client()
        admin_client.force_login(staff)

        def public_counts(path, points_key, count_key, options_key):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            context = response.context
            points = context[points_key] if points_key else self.client.get('/ru/api/catalog/map/').json()['points']
            ids = {member['id'] for point in points for member in point['members']}
            category_count = next((c['count'] for c in context[options_key] if c['value'] == place.category_id), 0)
            return place.pk in ids, context[count_key], category_count

        pages = [
            ('/ru/', 'map_places', 'map_business_count', 'home_categories'),
            ('/ru/catalog/', None, 'catalog_places_total', 'categories'),
        ]
        for args in pages:
            self.assertEqual(public_counts(*args), (True, 1, 1))
            self.assertEqual(public_counts(*args), (True, 1, 1))
        response = admin_client.post(reverse('admin:catalog_place_changelist'), {
            'action': 'mark_draft', '_selected_action': [place.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Place.objects.get(pk=place.pk).is_public)
        for args in pages:
            self.assertEqual(public_counts(*args), (False, 0, 0))

    def test_admin_direct_updates_refresh_data_without_waiting_for_timeout(self):
        from catalog.services.public_cache import data_version

        place = create_ready_place(is_active=False)
        staff = get_user_model().objects.create_superuser('direct-cache-admin', '', 'fictional')
        self.client.force_login(staff)
        url = reverse('admin:catalog_place_changelist')
        for action in ('mark_active', 'mark_info_verified'):
            with self.subTest(action=action):
                before = data_version()
                response = self.client.post(url, {'action': action, '_selected_action': [place.pk]})
                self.assertEqual(response.status_code, 302)
                self.assertGreater(data_version(), before)
        place.refresh_from_db()
        self.assertTrue(place.is_active)
        self.assertIsNotNone(place.last_verified_at)
