"""Public URLs identify the correct place without exposing its database ID."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import SimpleTestCase, TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Category, Place
from catalog.services.indexnow import canonical_indexnow_url, place_canonical_urls
from catalog.sitemaps import PlaceSitemap
from catalog.testcases.utils import create_quality_place


class CleanPlaceSlugNormalizationTests(SimpleTestCase):
    def test_readable_slugs_use_hyphens_instead_of_underscores(self):
        from catalog.services.place_urls import build_place_public_slug
        self.assertEqual(build_place_public_slug('Kids_Club'), 'kids-club')


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True, PUBLIC_BASE_URL='https://kidsmap.az')
class CleanPlaceUrlTests(TestCase):
    def make_place(self, **changes):
        values = dict(name='Toy Museum', name_az='Oyuncaq Muzeyi',
                      name_ru='Музей игрушек', name_en='Toy Museum',
                      description_ru='Музей игрушек для детей',
                      description_en='A toy museum for children')
        values.update(changes)
        return create_quality_place(**values)

    def test_new_published_place_has_readable_localized_urls(self):
        place = self.make_place()
        for language, expected in (
            ('az', '/place/oyuncaq-muzeyi/'),
            ('ru', '/ru/place/muzei-igrushek/'),
            ('en', '/en/place/toy-museum/'),
        ):
            with self.subTest(language=language), override(language), self.assertNumQueries(0):
                self.assertEqual(place.get_absolute_url(), expected)
            response = self.client.get(expected)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['place'].pk, place.pk)

    def test_draft_uses_completed_name_when_first_published(self):
        place = self.make_place(status=Place.STATUS_DRAFT, is_active=False,
                                name_en='Draft placeholder')
        place.name_en = 'Final Toy Museum'
        place.status = Place.STATUS_PUBLISHED
        place.is_active = True
        place.save(update_fields={'name_en', 'status', 'is_active'})
        place.refresh_from_db()
        with override('en'):
            self.assertEqual(place.get_absolute_url(), '/en/place/final-toy-museum/')
        self.assertEqual(self.client.get('/en/place/final-toy-museum/').status_code, 200)

    def test_rename_and_stale_instance_keep_first_published_url(self):
        place = self.make_place()
        stale = Place.objects.get(pk=place.pk)
        place.name_en = 'Renamed Museum'
        place.save(update_fields={'name_en'})
        stale.name_en = 'Another Name'
        stale.save()
        stale.refresh_from_db()
        with override('en'):
            self.assertEqual(stale.get_absolute_url(), '/en/place/toy-museum/')

    def test_missing_translation_keeps_persisted_fallback_after_translation(self):
        place = self.make_place(name_en='')
        with override('en'):
            self.assertEqual(place.get_absolute_url(), '/en/place/oyuncaq-muzeyi/')
        place.name_en = 'Toy Museum'
        place.save(update_fields={'name_en'})
        place.refresh_from_db()
        with override('en'):
            self.assertEqual(place.get_absolute_url(), '/en/place/oyuncaq-muzeyi/')

    @override_settings(LOCALIZED_PLACE_URLS_ENABLED=False)
    def test_new_urls_do_not_depend_on_legacy_localization_switch(self):
        place = self.make_place()
        with override('en'):
            self.assertEqual(place.get_absolute_url(), '/en/place/toy-museum/')
        self.assertEqual(self.client.get('/en/place/toy-museum/').status_code, 200)

    def test_duplicate_names_receive_distinct_links_to_correct_places(self):
        first = self.make_place()
        second = self.make_place()
        with override('en'):
            self.assertEqual(first.get_absolute_url(), '/en/place/toy-museum/')
            self.assertNotEqual(first.get_absolute_url(), second.get_absolute_url())
            self.assertNotIn(f'/place/{second.pk}-', second.get_absolute_url())
            response = self.client.get(second.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['place'].pk, second.pk)

    def test_digit_prefix_cannot_be_mistaken_for_legacy_record_id(self):
        for name, suffix in [('123 Park', 'place-123-park'), ('123', 'place-123')]:
            with self.subTest(name=name):
                place = self.make_place(name_en=name)
                with override('en'):
                    self.assertEqual(place.get_absolute_url(), f'/en/place/{suffix}/')
                response = self.client.get(f'/en/place/{suffix}/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['place'].pk, place.pk)

    def test_hidden_and_deleted_places_remain_404_without_redirect(self):
        place = self.make_place()
        for changes in ({'status': Place.STATUS_DRAFT}, {'is_active': False},
                        {'deleted_at': timezone.now()}):
            Place.objects.filter(pk=place.pk).update(status=Place.STATUS_PUBLISHED,
                                                     is_active=True, deleted_at=None)
            Place.objects.filter(pk=place.pk).update(**changes)
            for url in ('/en/place/toy-museum/', '/en/place/toy-museum/?next=/account/',
                        f'/en/place/{place.pk}-wrong/?next=/account/'):
                with self.subTest(changes=changes, url=url):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 404)
                    self.assertNotIn('Location', response)

    def test_id_links_and_queries_redirect_once_to_clean_url(self):
        place = self.make_place()
        for url in (f'/en/place/{place.pk}-toy-museum/', f'/en/place/{place.pk}-wrong/?x=1',
                    f'/en/place/{place.pk}/', f'/en/{place.pk}-old/',
                    '/en/place/toy-museum/?next=/account/'):
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertEqual(response.redirect_chain, [('/en/place/toy-museum/', 301)])
                self.assertEqual(response.status_code, 200)

    def test_clean_page_head_and_metadata_use_saved_addresses(self):
        self.make_place()
        response = self.client.get('/ru/place/muzei-igrushek/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<link rel="canonical" href="https://kidsmap.az/ru/place/muzei-igrushek/"')
        self.assertContains(response, 'hreflang="en" href="https://kidsmap.az/en/place/toy-museum/"')
        self.assertEqual(json.loads(response.context['place_schema_json'])['url'],
                         'https://kidsmap.az/ru/place/muzei-igrushek/')
        self.assertEqual(self.client.head('/ru/place/muzei-igrushek/').status_code, 200)

    def test_sitemap_and_indexnow_use_clean_localized_urls(self):
        place = self.make_place()
        expected = {'https://kidsmap.az/place/oyuncaq-muzeyi/',
                    'https://kidsmap.az/ru/place/muzei-igrushek/',
                    'https://kidsmap.az/en/place/toy-museum/'}
        self.assertEqual(set(place_canonical_urls(place)), expected)
        locations = {item['location'] for item in PlaceSitemap().get_urls(
            site=SimpleNamespace(domain='kidsmap.az'))}
        self.assertEqual(locations, expected)

    def test_unknown_clean_slug_is_404(self):
        self.assertEqual(self.client.get('/en/place/no-such-museum/').status_code, 404)

    def test_existing_cohort_cannot_be_switched_by_an_ordinary_save(self):
        place = self.make_place(uses_slug_only_urls=False)
        with override('en'):
            expected = f'/en/place/{place.pk}-toy-museum/'
            self.assertEqual(place.get_absolute_url(), expected)
            place.uses_slug_only_urls = True
            place.public_slug_en = 'injected'
            place.name_en = 'Renamed'
            place.save()
            place.refresh_from_db()
            self.assertEqual(place.get_absolute_url(), expected)
        self.assertIsNone(place.public_slug_en)
        self.assertEqual(self.client.get(expected).status_code, 200)
        self.assertEqual(self.client.get('/en/place/toy-museum/').status_code, 404)

    @override_settings(LOCALIZED_PLACE_URLS_ENABLED=False)
    def test_legacy_unicode_slug_does_not_redirect_to_itself(self):
        place = self.make_place(uses_slug_only_urls=False)
        Place.objects.filter(pk=place.pk).update(slug='музей')
        expected = f'/en/place/{place.pk}-%D0%BC%D1%83%D0%B7%D0%B5%D0%B9/'
        response = self.client.get(expected, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain, [])

    def test_saved_public_slug_cannot_be_replaced_by_partial_save(self):
        place = self.make_place()
        place.public_slug_en = 'injected'
        place.save(update_fields={'public_slug_en'})
        place.refresh_from_db()
        self.assertEqual(place.public_slug_en, 'toy-museum')

    def test_partial_save_does_not_publish_unsaved_status_or_names(self):
        place = self.make_place(status=Place.STATUS_DRAFT, is_active=False)
        place.status = Place.STATUS_PUBLISHED
        place.name_en = 'Unsaved Name'
        place.save(update_fields={'rating_count'})
        place.refresh_from_db()
        self.assertIsNone(place.public_slug_en)
        place.status = Place.STATUS_PUBLISHED
        place.name_en = 'Unsaved Name'
        place.save(update_fields={'status'})
        place.refresh_from_db()
        self.assertEqual(place.public_slug_en, 'toy-museum')

    def test_temporary_places_keep_legacy_paths(self):
        place = self.make_place(is_temporary=True)
        with override('en'):
            self.assertEqual(place.get_absolute_url(), f'/en/place/{place.pk}-toy-museum/')

    def test_duplicate_without_location_uses_bounded_unique_suffix(self):
        places = [self.make_place(district='', address='', lat=None, lng=None,
                                  name_en='a' * 100) for _ in range(3)]
        self.assertEqual([place.public_slug_en for place in places],
                         ['a' * 60, 'a' * 58 + '-2', 'a' * 58 + '-3'])

    def test_hidden_reservations_are_not_reused(self):
        place = self.make_place()
        place.soft_delete()
        other = self.make_place()
        self.assertNotEqual(other.public_slug_en, 'toy-museum')
        self.assertEqual(self.client.get('/en/place/toy-museum/').status_code, 404)

    def test_database_rejects_duplicate_public_slug(self):
        self.make_place()
        other = self.make_place()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Place.objects.filter(pk=other.pk).update(public_slug_en='toy-museum')

    def test_indexnow_still_rejects_numeric_redirect_urls(self):
        self.assertEqual(canonical_indexnow_url('/en/place/123/'), '')

    def test_staff_publication_reserves_clean_urls(self):
        from catalog.services import publication
        staff = get_user_model().objects.create_superuser('clean-url-publisher', password='local-test')
        place = self.make_place(status=Place.STATUS_DRAFT, is_active=False,
                                with_subcategory=True, with_pricing_plan=True, with_schedule_days=True)
        published = publication.publish(actor=staff, place_id=place.pk, expected_version=place.content_version)
        with override('en'):
            self.assertEqual(published.get_absolute_url(), '/en/place/toy-museum/')
        self.assertEqual(self.client.get('/en/place/toy-museum/').status_code, 200)

    def test_moderation_approval_reserves_final_candidate_name(self):
        from catalog.services import publication
        staff = get_user_model().objects.create_superuser('clean-url-reviewer', password='local-test')
        place = self.make_place(status=Place.STATUS_DRAFT, is_active=False,
                                with_subcategory=True, with_pricing_plan=True, with_schedule_days=True)
        revision = publication.propose(actor=staff, target_type='place', target_id=place.pk,
            patch={'name_en': 'Final Toy Museum'}, schema_version=1,
            expected_version=place.content_version, revision_version=0, submit=True, explicit_save=True)
        publication.review(actor=staff, revision_id=revision.pk, version=revision.version, approve=True)
        place.refresh_from_db()
        with override('en'):
            self.assertEqual(place.get_absolute_url(), '/en/place/final-toy-museum/')
        self.assertEqual(self.client.get('/en/place/final-toy-museum/').status_code, 200)


class ConcurrentCleanPlaceUrlTests(TransactionTestCase):
    def setUp(self):
        Category.objects.get_or_create(code='EDU', defaults={'name': 'Education'})

    @skipUnlessDBFeature('has_select_for_update')
    def test_simultaneous_same_name_publications_reserve_distinct_urls(self):
        # Separate drafts have non-conflicting internal slugs, but their final
        # English names coincide. Locking each draft row alone is insufficient.
        places = [Place.objects.create(name=f'Draft {index}', name_en='Toy Museum',
                                        lat=40.4093, lng=49.8671,
                                        category='EDU', status=Place.STATUS_DRAFT)
                  for index in range(2)]
        barrier = Barrier(2)

        def publish(pk):
            close_old_connections()
            try:
                place = Place.objects.get(pk=pk)
                barrier.wait(timeout=10)
                place.status = Place.STATUS_PUBLISHED
                place.save(update_fields={'status'})
                return place.public_slug_en
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(publish, [place.pk for place in places]))
        self.assertEqual(len(set(results)), 2)
        self.assertIn('toy-museum', results)
        self.assertEqual(set(Place.objects.values_list('public_slug_en', flat=True)), set(results))


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True)
class CleanPlaceUrlMigrationTests(TransactionTestCase):
    def test_existing_public_and_draft_rows_and_old_image_inserts_stay_legacy(self):
        before = [('catalog', '0151_place_age_varies_by_program')]
        after = [('catalog', '0152_place_clean_public_urls')]
        executor = MigrationExecutor(connection)
        executor.migrate(before)
        try:
            old_apps = executor.loader.project_state(before).apps
            OldPlace = old_apps.get_model('catalog', 'Place')
            old_apps.get_model('catalog', 'Category').objects.get_or_create(
                code='EDU', defaults={'name': 'Education'})
            rows = [OldPlace.objects.create(name=f'Old {status}', slug=f'old-{status}',
                    slug_en=f'old-{status}', category_id='EDU', status=status,
                    lat=40.4093, lng=49.8671)
                    for status in (Place.STATUS_PUBLISHED, Place.STATUS_DRAFT)]
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            for row in rows:
                place = Place.objects.get(pk=row.pk)
                self.assertFalse(place.uses_slug_only_urls)
                self.assertIsNone(place.public_slug_en)
                place.status = Place.STATUS_PUBLISHED
                place.save(update_fields={'status'})
                with override('en'):
                    self.assertEqual(place.get_absolute_url(), f'/en/place/{row.pk}-old-{row.status}/')
            # The old historical model omits the new columns in INSERT; its
            # database default must preserve rollback/rolling-release safety.
            old_insert = OldPlace.objects.create(name='Old image', slug='old-image', category_id='EDU')
            self.assertFalse(Place.objects.get(pk=old_insert.pk).uses_slug_only_urls)
            new = Place.objects.create(name='New Museum', name_en='New Museum',
                                       category='EDU', status=Place.STATUS_PUBLISHED)
            with override('en'):
                self.assertEqual(new.get_absolute_url(), '/en/place/new-museum/')
        finally:
            MigrationExecutor(connection).migrate(after)
