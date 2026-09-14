from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils.translation import override

from catalog.models import Place


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True)
class LocalizedPlaceUrlTests(TestCase):
    def make_place(self, **kwargs):
        return Place.objects.create(name='Toy Museum', name_az='Oyuncaq Muzeyi',
                                    name_ru='Музей игрушек', name_en='Toy Museum',
                                    category='EDU', status='draft', is_active=False, **kwargs)

    def test_language_paths_are_derived_from_each_name(self):
        place = self.make_place()
        for lang, suffix in [('az', 'oyuncaq-muzeyi'), ('ru', 'muzei-igrushek'), ('en', 'toy-museum')]:
            with self.subTest(lang=lang), override(lang):
                prefix = '' if lang == 'az' else f'/{lang}'
                self.assertEqual(place.get_absolute_url(), f'{prefix}/place/{place.pk}-{suffix}/')

    def test_rename_and_injected_slug_do_not_change_saved_url(self):
        place = self.make_place()
        with override('en'):
            before = place.get_absolute_url()
            place.name_en = 'New Name'
            place.slug_en = 'injected'
            place.save()
            place.refresh_from_db()
            self.assertEqual(place.get_absolute_url(), before)

    def test_creation_ignores_supplied_localized_slug(self):
        place = self.make_place(slug_en='injected')
        with override('en'):
            self.assertEqual(place.get_absolute_url(), f'/en/place/{place.pk}-toy-museum/')

    def test_existing_az_url_is_preserved_before_backfill(self):
        place = self.make_place()
        Place.objects.filter(pk=place.pk).update(slug='legacy-address', slug_az='', slug_ru='', slug_en='')
        place.refresh_from_db()
        place.save(update_fields={'name_en'})
        place.refresh_from_db()
        self.assertEqual(place.slug_az, 'legacy-address')
        self.assertEqual(place.slug_en, 'toy-museum')

    def test_partial_save_does_not_use_unsaved_translation(self):
        place = self.make_place()
        Place.objects.filter(pk=place.pk).update(name_en='', slug_en='')
        place.refresh_from_db()
        place.name_en = 'Unsaved Name'
        place.save(update_fields={'rating_count'})
        place.refresh_from_db()
        self.assertEqual(place.name_en, '')
        self.assertEqual(place.slug_en, '')

    def test_new_translation_fills_missing_slug_only(self):
        place = self.make_place()
        Place.objects.filter(pk=place.pk).update(name_en='', slug_en='')
        place.refresh_from_db()
        place.name_en = 'New Translation'
        place.save(update_fields={'name_en'})
        place.refresh_from_db()
        self.assertEqual(place.slug_en, 'new-translation')

    def test_stale_instance_cannot_replace_first_slug(self):
        place = self.make_place()
        Place.objects.filter(pk=place.pk).update(name_en='', slug_en='')
        first = Place.objects.get(pk=place.pk)
        stale = Place.objects.get(pk=place.pk)
        first.name_en = 'First Name'
        first.save(update_fields={'name_en'})
        stale.name_en = 'Second Name'
        stale.save(update_fields={'name_en'})
        stale.refresh_from_db()
        self.assertEqual(stale.slug_en, 'first-name')

    @override_settings(LOCALIZED_PLACE_URLS_ENABLED=False)
    def test_disabled_flag_retains_legacy_paths(self):
        place = self.make_place()
        with override('en'):
            self.assertEqual(place.get_absolute_url(), f'/en/place/{place.pk}-{place.slug}/')

    def test_missing_translation_uses_legacy_without_read_write(self):
        place = Place.objects.create(name='Brand', name_az='Brand', category='EDU')
        with self.assertNumQueries(0), override('en'):
            self.assertEqual(place.get_absolute_url(), f'/en/place/{place.pk}-brand/')

    def test_empty_update_fields_is_noop(self):
        place = self.make_place()
        Place.objects.filter(pk=place.pk).update(slug_en='')
        place.save(update_fields=[])
        place.refresh_from_db()
        self.assertEqual(place.slug_en, '')

    def test_long_legacy_slug_remains_usable(self):
        place = self.make_place()
        legacy = 'a' * 80
        Place.objects.filter(pk=place.pk).update(slug=legacy, slug_az='')
        place.refresh_from_db()
        place.save(update_fields={'name_en'})
        with override('az'):
            self.assertEqual(place.get_absolute_url(), f'/place/{place.pk}-{legacy}/')

    def test_normalization_and_duplicate_names(self):
        place = Place.objects.create(name='Brand', name_az='Əşya Çığırı', name_en='Kids Planet', category='EDU')
        other = Place.objects.create(name='Brand', name_en='Kids Planet', category='EDU')
        self.assertEqual(place.slug_az, 'esya-cigiri')
        self.assertEqual(place.slug_en, other.slug_en)
        self.assertNotEqual(place.pk, other.pk)
        place = Place.objects.create(name='Long', name_en='a' * 100, name_ru='!!!', category='EDU')
        self.assertEqual(place.slug_en, 'a' * 60)
        self.assertEqual(place.slug_ru, '')


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True)
class ConcurrentLocalizedPlaceUrlTests(TransactionTestCase):
    @skipUnlessDBFeature('has_select_for_update')
    def test_concurrent_first_translation_keeps_one_stable_url(self):
        place = Place.objects.create(name='Concurrent', category='EDU')
        barrier = Barrier(2)

        def write_name(name):
            close_old_connections()
            try:
                stale = Place.objects.get(pk=place.pk)
                barrier.wait(timeout=10)
                stale.name_en = name
                stale.save(update_fields={'name_en'})
                return stale.slug_en
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(write_name, 'First Name')
            second = pool.submit(write_name, 'Second Name')
            results = [first.result(timeout=15), second.result(timeout=15)]
        place.refresh_from_db()
        self.assertIn(place.slug_en, {'first-name', 'second-name'})
        self.assertEqual(results, [place.slug_en, place.slug_en])
