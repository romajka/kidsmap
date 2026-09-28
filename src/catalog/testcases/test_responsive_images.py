from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import SimpleTestCase, TestCase, override_settings
from PIL import Image

from catalog.controllers.home_controller import HomeController


class ResponsiveImageTests(SimpleTestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.storage = FileSystemStorage(location=self.directory.name, base_url='/media/')

    def photo(self, size=(1600, 800), name='gallery/photo.jpg', exif=None):
        data = BytesIO()
        Image.new('RGB', size, '#287a41').save(data, format='JPEG', **({'exif': exif} if exif else {}))
        self.storage.save(name, ContentFile(data.getvalue()))
        return SimpleNamespace(name=name, storage=self.storage, url=self.storage.url(name))

    def test_gallery_context_exposes_responsive_sizes(self):
        image = self.photo()
        item = SimpleNamespace(image=image, title_i18n=lambda lang: 'Family')
        slides = HomeController.build_default()._build_hero_gallery_slides(gallery_images=[item], language_code='az')
        self.assertIn('image_srcset', slides[0]['main'])

    def test_derivatives_preserve_original_and_aspect_ratio(self):
        from catalog.services.responsive_images import generate_variants, responsive_image
        image = self.photo()
        original = self.storage.open(image.name).read()
        generate_variants(image)
        result = responsive_image(image)
        self.assertIn('320w', result['srcset'])
        self.assertIn('640w', result['srcset'])
        for entry, expected in zip(result['srcset'].split(', '), [(320, 160), (640, 320), (960, 480), (1280, 640)]):
            name = entry.split(' ')[0].removeprefix('/media/')
            with self.storage.open(name) as f, Image.open(f) as decoded:
                self.assertEqual(decoded.size, expected)
                self.assertEqual(decoded.format, 'WEBP')
        self.assertEqual(self.storage.open(image.name).read(), original)

    def test_small_source_is_not_upscaled(self):
        from catalog.services.responsive_images import generate_variants, responsive_image
        image = self.photo(size=(200, 100))
        generate_variants(image)
        result = responsive_image(image)
        self.assertTrue(result['srcset'].endswith(' 200w'))
        self.assertNotIn('320w', result['srcset'])

    def test_rendering_without_variants_is_read_only(self):
        from catalog.services.responsive_images import responsive_image
        image = self.photo()
        before = self.storage.listdir('')
        result = responsive_image(image)
        self.assertEqual(result['src'], image.url)
        self.assertEqual(result['srcset'], '')
        self.assertEqual(self.storage.listdir(''), before)

    def test_exif_orientation_is_applied(self):
        from catalog.services.responsive_images import generate_variants, responsive_image
        exif = Image.Exif(); exif[274] = 6
        image = self.photo(size=(800, 1600), exif=exif)
        generate_variants(image)
        self.assertEqual((responsive_image(image)['width'], responsive_image(image)['height']), (1600, 800))

    def test_generation_reuses_existing_files(self):
        from catalog.services.responsive_images import generate_variants
        image = self.photo()
        first = generate_variants(image)
        second = generate_variants(image)
        self.assertEqual(first['srcset'], second['srcset'])
        self.assertFalse(second['generated'])

    def test_replaced_source_gets_new_derivative_urls(self):
        from catalog.services.responsive_images import generate_variants
        image = self.photo()
        first = generate_variants(image)
        self.storage.delete(image.name)
        image = self.photo(size=(1800, 900))
        second = generate_variants(image)
        self.assertNotEqual(first['src'], second['src'])

    def test_corrupt_source_falls_back_without_manifest(self):
        from catalog.services.responsive_images import generate_variants, responsive_image
        image = self.photo()
        self.storage.delete(image.name)
        self.storage.save(image.name, ContentFile(b'not an image'))
        with self.assertLogs('catalog.services.responsive_images', level='WARNING'):
            result = generate_variants(image)
        self.assertEqual(result['src'], image.url)
        self.assertEqual(responsive_image(image)['srcset'], '')

    def test_hero_markup_uses_derivatives_and_intrinsic_dimensions(self):
        from catalog.services.responsive_images import generate_variants
        from django.template.loader import render_to_string
        image = self.photo()
        generate_variants(image)
        item = SimpleNamespace(image=image, title_i18n=lambda lang: 'Family')
        slides = HomeController.build_default()._build_hero_gallery_slides(gallery_images=[item], language_code='az')
        html = render_to_string('catalog/includes/hero_photo.html', {'item': slides[0]['main'], 'sizes': '180px', 'high_priority': True})
        self.assertIn('srcset=', html)
        self.assertIn('sizes="180px"', html)
        self.assertIn('width="1600"', html)
        self.assertIn('height="800"', html)
        self.assertIn('fetchpriority="high"', html)
        self.assertNotIn(image.url, html)

    def test_missing_variant_falls_back_to_original(self):
        from catalog.services.responsive_images import generate_variants, responsive_image
        image = self.photo()
        result = generate_variants(image)
        self.storage.delete(result['preview'].removeprefix('/media/'))
        self.assertEqual(responsive_image(image)['src'], image.url)
        self.assertEqual(responsive_image(image)['srcset'], '')

    def test_animated_image_is_preserved(self):
        from catalog.services.responsive_images import generate_variants
        data = BytesIO()
        Image.new('RGB', (20, 20), 'red').save(data, format='GIF', save_all=True, append_images=[Image.new('RGB', (20, 20), 'blue')])
        self.storage.save('animation.gif', ContentFile(data.getvalue()))
        image = SimpleNamespace(name='animation.gif', storage=self.storage, url='/media/animation.gif')
        self.assertEqual(generate_variants(image)['srcset'], '')


class ResponsiveImageIntegrationTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.directory.name, INDEXNOW_KEY='')
        self.override.enable()
        self.addCleanup(self.override.disable)

    def gallery(self):
        from catalog.models import SiteGalleryImage
        data = BytesIO()
        Image.new('RGB', (1600, 800), '#287a41').save(data, format='JPEG')
        return SiteGalleryImage.objects.create(image=ContentFile(data.getvalue(), name='photo.jpg'))

    def test_upload_prepares_derivatives(self):
        from catalog.services.responsive_images import responsive_image
        gallery = self.gallery()
        self.assertIn('640w', responsive_image(gallery.image)['srcset'])

    def test_card_blur_and_image_use_derivatives(self):
        from catalog.models import Place, Category
        from django.template.loader import render_to_string
        gallery = self.gallery()
        category = Category.objects.create(code='responsive-test', name_ru='Family')
        place = Place.objects.create(name='Family', name_az='Family', category=category, photo=gallery.image.name)
        html = render_to_string('catalog/includes/place_card.html', {'place': place})
        self.assertIn('srcset=', html)
        self.assertIn('sizes=', html)
        self.assertIn('320.webp', html)
        self.assertNotIn(gallery.image.url, html)

    def test_dry_run_does_not_generate_files_and_apply_is_repeatable(self):
        from django.core.management import call_command
        from catalog.services.responsive_images import responsive_image
        import shutil
        from pathlib import Path
        gallery = self.gallery()
        shutil.rmtree(Path(self.directory.name) / 'responsive-images')
        from io import StringIO
        before = gallery.image.storage.open(gallery.image.name).read()
        call_command('generate_responsive_images', stdout=StringIO())
        self.assertFalse((Path(self.directory.name) / 'responsive-images').exists())
        call_command('generate_responsive_images', apply=True, stdout=StringIO())
        first = responsive_image(gallery.image)['srcset']
        self.assertTrue(first)
        call_command('generate_responsive_images', apply=True, stdout=StringIO())
        self.assertEqual(responsive_image(gallery.image)['srcset'], first)
        self.assertEqual(gallery.image.storage.open(gallery.image.name).read(), before)
