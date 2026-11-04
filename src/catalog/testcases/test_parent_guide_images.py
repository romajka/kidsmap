"""Search/social previews must describe the actual visible editorial image."""

import json
import re
from io import BytesIO
from tempfile import TemporaryDirectory
from html.parser import HTMLParser
from urllib.parse import urljoin

from PIL import Image
from django.contrib.staticfiles import finders
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from catalog.testcases.utils import create_quality_place
from catalog.parent_guide_content import GUIDE_PAGES


class ImageMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.meta = {}
        self.images = []
        self.feed(html)
        self.schemas = [json.loads(value) for value in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S)]

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.meta[attrs.get('property') or attrs.get('name')] = attrs.get('content')
        elif tag == 'img':
            self.images.append(attrs)


@override_settings(PUBLIC_BASE_URL='https://kidsmap.az', LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class ParentGuideImageTests(TestCase):
    def test_search_and_social_previews_describe_the_visible_image_in_each_language(self):
        # Missing/contradictory dimensions or a fallback logo must fail this contract.
        for prefix in ('', '/ru', '/en'):
            for slug in GUIDE_PAGES:
                with self.subTest(prefix=prefix, slug=slug):
                    path = f'{prefix}/parents/{slug}/'
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    parsed = ImageMarkup(response.content.decode())
                    hero = next(img for img in parsed.images if img.get('fetchpriority') == 'high')
                    with Image.open(finders.find(hero['src'].removeprefix('/static/'))) as asset:
                        width, height = asset.size
                    self.assertEqual((int(hero['width']), int(hero['height'])), (width, height))
                    absolute = urljoin('https://kidsmap.az', hero['src'])
                    self.assertEqual(parsed.meta['og:image'], absolute)
                    self.assertEqual(parsed.meta['twitter:image'], absolute)
                    self.assertEqual(parsed.meta.get('og:image:width'), str(width))
                    self.assertEqual(parsed.meta.get('og:image:height'), str(height))
                    self.assertEqual(parsed.meta.get('og:image:type'), 'image/webp')
                    self.assertTrue(hero['alt'])
                    self.assertEqual(parsed.meta.get('og:image:alt'), hero['alt'])
                    self.assertEqual(parsed.meta.get('twitter:image:alt'), hero['alt'])
                    article = next(row for row in parsed.schemas if row.get('@type') == 'Article')
                    page = next(row for row in parsed.schemas if row.get('@type') == 'WebPage')
                    self.assertEqual(page['url'], 'https://kidsmap.az' + path)
                    self.assertEqual(article['mainEntityOfPage'], page['@id'])
                    self.assertEqual(page['primaryImageOfPage'], article['image'])
                    self.assertEqual(article['image'], {
                        '@type': 'ImageObject', 'url': absolute, 'contentUrl': absolute,
                        'width': width, 'height': height, 'caption': hero['alt'],
                    })
                    for directive in ('robots', 'googlebot'):
                        self.assertIn('max-image-preview:large', parsed.meta[directive])
                        self.assertNotIn('noimageindex', parsed.meta[directive])
                        self.assertNotIn('noindex', parsed.meta[directive])

    @override_settings(STATIC_URL='https://cdn.example.test/assets/')
    def test_absolute_static_url_is_not_prefixed_with_the_site_origin(self):
        response = self.client.get('/ru/parents/baku-with-kids/')
        parsed = ImageMarkup(response.content.decode())
        expected = 'https://cdn.example.test/assets/img/guides/family-hero.webp'
        self.assertEqual(parsed.meta['og:image'], expected)
        self.assertEqual(parsed.meta['twitter:image'], expected)

    def test_venue_photo_has_escaped_localized_alt_and_icons_remain_decorative(self):
        names = {'az': 'Ailə "&" məkanı', 'ru': 'Семейное место "&"', 'en': 'Family "&" venue'}
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        photo_bytes = BytesIO()
        Image.new('RGB', (32, 32), 'green').save(photo_bytes, format='WEBP')
        place = create_quality_place(category='FUN', name=names['az'], name_az=names['az'],
            name_ru=names['ru'], name_en=names['en'], photo=SimpleUploadedFile(
                'image-seo-fixture.webp', photo_bytes.getvalue(), content_type='image/webp'))
        for language, prefix in (('az', ''), ('ru', '/ru'), ('en', '/en')):
            with self.subTest(language=language):
                response = self.client.get(f'{prefix}/parents/baku-with-kids/')
                parsed = ImageMarkup(response.content.decode())
                photo = next(img for img in parsed.images if img['src'] == place.public_image_url)
                self.assertEqual(photo['alt'], names[language])
                self.assertTrue(any(img.get('alt') == '' for img in parsed.images))

    def test_production_manifest_renders_each_planning_section_once(self):
        from django.conf import settings
        from django.core.management import call_command
        storages = dict(settings.STORAGES)
        storages['staticfiles'] = {'BACKEND':'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'}
        with TemporaryDirectory() as static_root, override_settings(
            DEBUG=False, STATIC_ROOT=static_root, STORAGES=storages,
        ):
            call_command('collectstatic', interactive=False, verbosity=0)
            for prefix in ('', '/ru', '/en'):
                for slug in ('parks', 'museums', 'play-centers'):
                    with self.subTest(prefix=prefix, slug=slug):
                        response = self.client.get(f'{prefix}/parents/{slug}/')
                        self.assertEqual(response.status_code, 200)
                        html = response.content.decode()
                        self.assertEqual(html.count('id="guide-planning"'), 1)
                        self.assertEqual(html.count('href="#guide-planning"'), 1)
                        parsed = ImageMarkup(html)
                        self.assertTrue(all(image.get('src') not in ('', '/static/') for image in parsed.images))
                        if slug == 'parks':
                            self.assertNotIn('museum-planning__card', html)
                            self.assertNotIn('museums_guide.', html)
                            self.assertIn('pg-planning-card', html)
                        else:
                            self.assertIn('museum-planning__card', html)
