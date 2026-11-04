"""Preview images describe public page content, never a fabricated venue photo."""

import json
from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from urllib.parse import urljoin

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings

from catalog.testcases.test_parent_guide_images import ImageMarkup
from catalog.testcases.utils import create_quality_place


@override_settings(PUBLIC_BASE_URL='', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class SearchPreviewTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        override = override_settings(MEDIA_ROOT=media.name)
        override.enable()
        self.addCleanup(override.disable)

    def place(self, **kwargs):
        data = BytesIO()
        Image.new('RGB', (1280, 960), 'green').save(data, 'WEBP')
        return create_quality_place(photo=SimpleUploadedFile('venue.webp', data.getvalue(),
            content_type='image/webp'), **kwargs)

    def base(self, route, **context):
        request = RequestFactory().get('/ru/example/')
        request.LANGUAGE_CODE = 'ru'
        request.session = {}
        request.user = AnonymousUser()
        request.resolver_match = SimpleNamespace(url_name=route)
        return ImageMarkup(render_to_string('base.html', context, request=request))

    def assert_preview(self, markup, url):
        self.assertEqual(markup.meta.get('og:image'), url)
        self.assertEqual(markup.meta.get('twitter:image'), url)
        self.assertTrue(markup.meta.get('og:image:alt'))
        webpage = next(row for row in markup.schemas if row.get('@type') == 'WebPage')
        self.assertEqual(webpage['primaryImageOfPage']['url'], url)

    def test_place_without_a_photo_does_not_claim_the_site_logo_as_its_image(self):
        place = create_quality_place(photo='', cover_photo='')
        response = self.client.get(f'/ru/place/{place.pk}/', follow=True)
        self.assertEqual(response.status_code, 200)
        parsed = ImageMarkup(response.content.decode())
        self.assertNotIn('og:image', parsed.meta)
        self.assertNotIn('twitter:image', parsed.meta)
        business = next(row for row in parsed.schemas if row.get('@type') == 'LocalBusiness')
        self.assertNotIn('image', business)

    def test_place_photo_agrees_with_webpage_and_social_metadata(self):
        place = self.place(name_ru='Место "&" для семьи')
        for prefix in ('', '/ru', '/en'):
            with self.subTest(prefix=prefix):
                response = self.client.get(f'{prefix}/place/{place.pk}/', follow=True)
                self.assertEqual(response.status_code, 200)
                parsed = ImageMarkup(response.content.decode())
                self.assert_preview(parsed, 'http://testserver' + place.photo.url)

    def test_catalog_uses_a_visible_result_photo_and_respects_empty_filters(self):
        place = self.place(name_ru='Фотография из подборки', category='FUN')
        parsed = ImageMarkup(self.client.get('/ru/catalog/?category=FUN').content.decode())
        self.assert_preview(parsed, 'http://testserver' + place.photo.url)
        empty = ImageMarkup(self.client.get('/ru/catalog/?q=nonexistent-preview-fixture').content.decode())
        self.assertNotIn('og:image', empty.meta)

    def test_home_uses_the_rendered_gallery_artwork(self):
        response = self.client.get('/ru/')
        parsed = ImageMarkup(response.content.decode())
        self.assertNotIn('logo', parsed.meta.get('og:image', ''))
        self.assertTrue(parsed.meta.get('og:image'))
        main = response.context['hero_gallery_slides'][0]['main']
        self.assert_preview(parsed, urljoin('http://testserver', main['image_url']))

    def test_text_only_and_private_pages_do_not_advertise_a_generic_image(self):
        for url in ('/ru/about/', '/ru/privacy/', '/ru/auth/login/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                parsed = ImageMarkup(response.content.decode())
                self.assertNotIn('og:image', parsed.meta)
                self.assertEqual(parsed.meta.get('twitter:card'), 'summary')

    def test_shared_detail_contract_handles_absolute_cdn_urls_and_missing_photos(self):
        for route in ('event_detail', 'specialist_detail', 'organization_detail', 'activity_detail'):
            with self.subTest(route=route):
                parsed = self.base(route, seo_image_url='https://cdn.example.test/photo.webp',
                    seo_title='Название "&" </script>', meta_description='Описание')
                self.assert_preview(parsed, 'https://cdn.example.test/photo.webp')
                self.assertNotIn('og:image', self.base(route, seo_image_url='').meta)

    def test_directory_previews_use_only_the_rendered_page_items(self):
        photo = SimpleNamespace(url='/media/visible.webp')
        cases = [
            ('organization_list', {'cards': [{'photos': [{'url':photo.url, 'name':'Visible branch'}]}]}),
            ('specialist_list', {'specialists': [SimpleNamespace(photo=photo, has_valid_photo=True, name='Visible educator')]}),
            ('events_landing', {'events': [SimpleNamespace(photo=photo, name_i18n=lambda lang:'Visible event')]}),
        ]
        for route, context in cases:
            with self.subTest(route=route):
                self.assert_preview(self.base(route, **context), 'http://testserver/media/visible.webp')
                self.assertNotIn('og:image', self.base(route).meta)

    def test_landing_photos_follow_public_category_filters_in_all_languages(self):
        from catalog.models import CatalogContentSettings
        from catalog.testcases.test_seo_landing_visibility import SeoLandingIndexabilityTests
        settings = CatalogContentSettings.get_solo()
        settings.seo_pages_json = {lang: {'photo-selection':
            SeoLandingIndexabilityTests._page(title='Family selection', catalog_query='?category=FUN')}
            for lang in ('az', 'ru', 'en')}
        settings.save(update_fields=['seo_pages_json', 'updated_at'])
        matching = self.place(category='FUN', name_ru='Подходящее место')
        other = self.place(category='EDU', name_ru='Другая категория')
        hidden = self.place(category='FUN', status='draft')
        for prefix in ('', '/ru', '/en'):
            response = self.client.get(f'{prefix}/catalog/photo-selection/')
            self.assertEqual(response.status_code, 200)
            markup = ImageMarkup(response.content.decode())
            self.assert_preview(markup, 'http://testserver' + matching.photo.url)
            self.assertContains(response, matching.photo.url)
            self.assertNotContains(response, other.photo.url)
            self.assertNotContains(response, hidden.photo.url)
        matching.photo.delete(save=True)
        empty = self.client.get('/ru/catalog/photo-selection/')
        self.assertNotIn('og:image', ImageMarkup(empty.content.decode()).meta)
        self.assertNotContains(empty, 'class="seo-featured-places"')
