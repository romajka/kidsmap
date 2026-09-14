from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils.translation import override

from catalog.context_processors import seo_urls
from catalog.models import Place
from catalog.services.indexnow import place_canonical_urls
from catalog.testcases.utils import create_quality_place


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True, PUBLIC_BASE_URL='https://kidsmap.az')
class LocalizedPlaceSeoUnitTests(SimpleTestCase):
    def setUp(self):
        self.place = Place(pk=987, name='Museum', slug='legacy')
        self.place.slug_az = 'oyuncaq-muzeyi'
        self.place.slug_ru = 'muzei-igrushek'
        self.place.slug_en = 'toy-museum'

    def test_indexnow_uses_each_language_slug(self):
        self.assertEqual(set(place_canonical_urls(self.place)), {
            'https://kidsmap.az/place/987-oyuncaq-muzeyi/',
            'https://kidsmap.az/ru/place/987-muzei-igrushek/',
            'https://kidsmap.az/en/place/987-toy-museum/',
        })

    def test_context_uses_resolved_place_without_database_lookup(self):
        request = RequestFactory().get('/ru/place/987-muzei-igrushek/')
        request.resolver_match = SimpleNamespace(url_name='place_detail')
        request._seo_place = self.place
        with override('ru'):
            context = seo_urls(request)
        self.assertEqual(context['alternate_urls']['en'], 'https://kidsmap.az/en/place/987-toy-museum/')
        self.assertEqual(context['x_default_url'], 'https://kidsmap.az/place/987-oyuncaq-muzeyi/')
        self.assertEqual(context['canonical_url'], 'https://kidsmap.az/ru/place/987-muzei-igrushek/')


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True, PUBLIC_BASE_URL='https://kidsmap.az')
class LocalizedPlaceSeoTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(name_az='Oyuncaq Muzeyi', name_ru='Музей игрушек', name_en='Toy Museum')

    def test_old_and_wrong_language_slugs_redirect_directly(self):
        for language in ('az', 'ru', 'en'):
            with override(language):
                expected = self.place.get_absolute_url()
            prefix = '' if language == 'az' else '/' + language
            for suffix in (self.place.slug, 'wrong', self.place.slug_en):
                path = f'{prefix}/place/{self.place.pk}-{suffix}/'
                if path == expected:
                    continue
                response = self.client.get(path)
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response['Location'], expected)
            response = self.client.get(f'{prefix}/place/{self.place.pk}/')
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'], expected)

    def test_canonical_pages_render_reciprocal_metadata(self):
        for language in ('az', 'ru', 'en'):
            with override(language):
                path = self.place.get_absolute_url()
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + path)
            for alternate in ('az', 'ru', 'en'):
                with override(alternate):
                    expected = 'https://kidsmap.az' + self.place.get_absolute_url()
                self.assertEqual(response.context['alternate_urls'][alternate], expected)
                self.assertContains(response, f'<link rel="alternate" hreflang="{alternate}" href="{expected}"', html=False)
            self.assertContains(response, f'<link rel="canonical" href="https://kidsmap.az{path}"', html=False)
            import json
            schema = json.loads(response.context['place_schema_json'])
            self.assertEqual(schema['url'], 'https://kidsmap.az' + path)

    def test_hidden_place_does_not_disclose_canonical_slug(self):
        Place.objects.filter(pk=self.place.pk).update(is_active=False)
        response = self.client.get(f'/ru/place/{self.place.pk}-wrong/')
        self.assertEqual(response.status_code, 404)
        self.assertNotIn('Location', response)

    def test_sitemap_contains_final_localized_urls(self):
        from catalog.sitemaps import PlaceSitemap
        entries = PlaceSitemap().get_urls(site=SimpleNamespace(domain='kidsmap.az'))
        locations = {entry['location'] for entry in entries}
        for language in ('az', 'ru', 'en'):
            with override(language):
                self.assertIn('https://kidsmap.az' + self.place.get_absolute_url(), locations)

    @override_settings(INDEXNOW_KEY='local-test-key')
    def test_delete_notifies_saved_localized_urls(self):
        expected = set(place_canonical_urls(self.place))
        with patch('catalog.indexnow_signals.enqueue_indexnow_urls') as enqueue:
            with self.captureOnCommitCallbacks(execute=True):
                self.place.delete()
        submitted = {url for call in enqueue.call_args_list for url in call.args[0]}
        self.assertTrue(expected.issubset(submitted))

    @override_settings(INDEXNOW_KEY='local-test-key')
    def test_new_translation_notifies_old_fallback_and_new_url(self):
        Place.objects.filter(pk=self.place.pk).update(name_en='', slug_en='')
        self.place.refresh_from_db()
        old_urls = set(place_canonical_urls(self.place))
        with patch('catalog.indexnow_signals.enqueue_indexnow_urls') as enqueue:
            with self.captureOnCommitCallbacks(execute=True):
                self.place.name_en = 'Toy Museum'
                self.place.save(update_fields={'name_en'})
        self.place.refresh_from_db()
        submitted = {url for call in enqueue.call_args_list for url in call.args[0]}
        self.assertTrue((old_urls | set(place_canonical_urls(self.place))).issubset(submitted))

    @override_settings(LOCALIZED_PLACE_URLS_ENABLED=False)
    def test_disabled_flag_preserves_legacy_public_urls(self):
        for language in ('az', 'ru', 'en'):
            prefix = '' if language == 'az' else '/' + language
            response = self.client.get(f'{prefix}/place/{self.place.pk}-{self.place.slug}/')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['alternate_urls']['en'], f'https://kidsmap.az/en/place/{self.place.pk}-{self.place.slug}/')

    def test_pricing_api_retains_legacy_identifier(self):
        from catalog.views import place_pricing_api
        import json
        request = RequestFactory().get('/api/places/pricing/?lang=en')
        response = place_pricing_api(request, slug=self.place.slug)
        payload = json.loads(response.content)
        self.assertEqual(payload['place']['id'], self.place.pk)
        self.assertEqual(payload['place']['slug'], self.place.slug)

    def test_query_and_default_language_prefix_redirects_terminate(self):
        with override('az'):
            canonical = self.place.get_absolute_url()
        for path, hops in ((canonical + '?utm_source=test', 1), ('/az' + canonical, 1),
                           (f'/az/place/{self.place.pk}-wrong/?utm_source=test', 2)):
            response = self.client.get(path, follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.redirect_chain), hops)
            self.assertEqual(response.request['PATH_INFO'], canonical)

    @override_settings(INDEXNOW_KEY='local-test-key')
    def test_publication_and_unpublication_submit_correct_urls(self):
        expected = set(place_canonical_urls(self.place))
        for active in (False, True):
            with patch('catalog.indexnow_signals.enqueue_indexnow_urls') as enqueue:
                with self.captureOnCommitCallbacks(execute=True):
                    self.place.is_active = active
                    self.place.save(update_fields={'is_active'})
            submitted = {url for call in enqueue.call_args_list for url in call.args[0]}
            self.assertTrue(expected.issubset(submitted))

    @override_settings(INDEXNOW_KEY='local-test-key')
    def test_creation_submits_public_urls_but_not_draft(self):
        for status in (Place.STATUS_PUBLISHED, Place.STATUS_DRAFT):
            with patch('catalog.indexnow_signals.enqueue_indexnow_urls') as enqueue:
                with self.captureOnCommitCallbacks(execute=True):
                    place = create_quality_place(name_en='Science Museum', name_ru='Музей науки', status=status)
            submitted = {url for call in enqueue.call_args_list for url in call.args[0]}
            urls = set(place_canonical_urls(place))
            if status == Place.STATUS_PUBLISHED:
                self.assertTrue(urls.issubset(submitted))
            else:
                self.assertFalse(urls & submitted)

    def test_legacy_get_rating_refresh_does_not_generate_urls(self):
        Place.objects.filter(pk=self.place.pk).update(slug_az='', slug_ru='', slug_en='', rating_count=3)
        path = f'/ru/place/{self.place.pk}-{self.place.slug}/'
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual((self.place.slug_az, self.place.slug_ru, self.place.slug_en), ('', '', ''))
        self.assertEqual(response.context['canonical_url'], 'https://kidsmap.az' + path)
        import json
        self.assertEqual(json.loads(response.context['place_schema_json'])['url'], 'https://kidsmap.az' + path)
