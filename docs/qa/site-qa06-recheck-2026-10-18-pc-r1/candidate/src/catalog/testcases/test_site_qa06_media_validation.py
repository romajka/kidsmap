import hashlib
import io
import re
import tempfile
from pathlib import Path

from PIL import Image
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.models import SiteSettings, SiteGalleryImage
from catalog.models.site import clear_singleton_caches


class Site06MediaValidationTests(TestCase):
    """Real admin ingress: invalid media must not alter rows, files or admin logs."""

    def setUp(self):
        assert settings.TESTING
        self.temp = tempfile.TemporaryDirectory(prefix='site06-')
        self.addCleanup(self.temp.cleanup)
        media = override_settings(MEDIA_ROOT=self.temp.name)
        media.enable()
        self.addCleanup(media.disable)
        clear_singleton_caches()
        self.user = get_user_model().objects.create_superuser('site06_actor', 'site06@example.invalid', 'fictional')
        self.client.force_login(self.user)
        self.client.cookies['django_language'] = 'ru'
        self.site = SiteSettings.get_solo()
        self.site.logo = self.upload('before.png', self.raster())
        self.site.save()
        self.ajax = reverse('admin:catalog_sitegalleryimage_ajax_upload')

    def raster(self, fmt='PNG', size=(16, 16), mode='RGBA'):
        buffer = io.BytesIO()
        with Image.new(mode, size, 0) as image:
            image.save(buffer, fmt)
        return buffer.getvalue()

    def upload(self, name, data, mime='image/png'):
        return SimpleUploadedFile(name, data, content_type=mime)

    def svg(self, inner='<path d="M0 0L10 10" fill="none" stroke="green"/>'):
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">' + inner + '</svg>').encode()

    def snapshot(self):
        from django.contrib.admin.models import LogEntry
        return {
            'row': list(SiteSettings.objects.filter(pk=self.site.pk).values()),
            'gallery': list(SiteGalleryImage.objects.order_by('pk').values()),
            'files': {p.relative_to(self.temp.name).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in Path(self.temp.name).rglob('*') if p.is_file()},
            'logs': LogEntry.objects.count(),
        }

    def reject(self, upload, target=None, expected=400, url=None, data=None):
        before = self.snapshot()
        response = self.client.post(url or self.ajax, data or {**(target or {'field': 'logo'}), 'image': upload})
        with self.subTest(contract='status'):
            self.assertEqual(response.status_code, expected)
        with self.subTest(contract='no-row-file-log-write'):
            self.assertEqual(self.snapshot(), before)
        if expected == 400:
            with self.subTest(contract='useful-error'):
                self.assertFalse(response.json().get('success'))
                self.assertTrue(response.json().get('error'))
        return response

    def payload(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        data = {'_continue': '1'}
        for name, field in form.fields.items():
            if isinstance(field, forms.FileField):
                continue
            value = form[name].value()
            if isinstance(field, forms.BooleanField):
                if value:
                    data[name] = 'on'
            else:
                data[name] = '' if value is None else value
        token = re.search(r'name="settings_revision" value="([^"]+)"', response.content.decode())
        if token:
            import html
            data['settings_revision'] = html.unescape(token.group(1))
        return data

    def test_corrupt_png_main_does_not_replace_logo(self):
        self.reject(self.upload('broken.png', b'not a png'))

    def test_corrupt_png_gallery_does_not_create_row_or_file(self):
        self.reject(self.upload('broken.png', b'not a png'), {'placement': 'HOME_HERO'})

    def test_declared_extension_must_match_decoded_format(self):
        self.reject(self.upload('disguised.jpg', self.raster()))

    def test_declared_mime_must_match_decoded_format(self):
        self.reject(self.upload('disguised.png', self.raster(), 'image/jpeg'))

    def test_unsupported_real_gif_is_rejected(self):
        self.reject(self.upload('unsupported.gif', self.raster('GIF', mode='RGB'), 'image/gif'))

    def test_truncated_raster_after_a_real_header_is_rejected(self):
        for fmt, ext, mime in [('PNG', 'png', 'image/png'), ('JPEG', 'jpg', 'image/jpeg')]:
            with self.subTest(format=fmt):
                raw = self.raster(fmt, size=(32, 32), mode='RGB')
                self.reject(self.upload('truncated.' + ext, raw[:len(raw) // 2], mime))

    def test_animated_png_is_rejected_by_static_media_policy(self):
        buffer = io.BytesIO()
        with Image.new('RGB', (16, 16), 'green') as first, Image.new('RGB', (16, 16), 'blue') as second:
            first.save(buffer, 'PNG', save_all=True, append_images=[second], duration=100)
        self.reject(self.upload('animated.png', buffer.getvalue()))

    def test_empty_file_is_rejected_without_write(self):
        self.reject(self.upload('empty.png', b''))

    def test_logo_over_500kib_is_rejected(self):
        self.reject(self.upload('large.png', self.raster().ljust(500 * 1024 + 1, b' ')))

    def test_partner_over_500kib_is_rejected(self):
        self.reject(self.upload('large.png', self.raster().ljust(500 * 1024 + 1, b' ')), {'placement': 'HOME_PARTNERS'})

    def test_other_media_over_2mib_is_rejected(self):
        self.reject(self.upload('large.png', self.raster().ljust(2 * 1024 * 1024 + 1, b' ')), {'field': 'home_hero_image'})

    def test_dimension_over_12000_is_rejected_before_storage(self):
        self.reject(self.upload('wide.png', self.raster(size=(12001, 1), mode='L')), {'field': 'home_hero_image'})

    def test_pixels_over_50million_are_rejected_before_storage(self):
        self.reject(self.upload('many-pixels.png', self.raster(size=(7100, 7100), mode='1')), {'field': 'home_hero_image'})

    def test_valid_png_jpeg_webp_preserve_the_original_bytes(self):
        for fmt, ext, mime, mode in [('PNG', 'png', 'image/png', 'RGBA'), ('JPEG', 'jpg', 'image/jpeg', 'RGB'), ('WEBP', 'webp', 'image/webp', 'RGBA')]:
            with self.subTest(format=fmt):
                raw = self.raster(fmt, mode=mode)
                response = self.client.post(self.ajax, {'field': 'logo', 'image': self.upload('valid.' + ext, raw, mime)})
                self.assertEqual(response.status_code, 200)
                self.site.refresh_from_db()
                with self.site.logo.open('rb') as stored:
                    self.assertEqual(stored.read(), raw)

    def test_logo_exact_500kib_is_accepted(self):
        raw = self.raster().ljust(500 * 1024, b' ')
        self.assertEqual(self.client.post(self.ajax, {'field': 'logo', 'image': self.upload('exact.png', raw)}).status_code, 200)

    def test_static_svg_with_local_gradient_is_allowed_for_logo_and_partners(self):
        raw = self.svg('<defs><linearGradient id="g"><stop offset="0" stop-color="green"/></linearGradient></defs><rect width="16" height="16" fill="url(#g)"/>')
        for target in [{'field': 'logo'}, {'placement': 'HOME_PARTNERS'}]:
            with self.subTest(target=target):
                self.assertEqual(self.client.post(self.ajax, {**target, 'image': self.upload('safe.svg', raw, 'image/svg+xml')}).status_code, 200)

    def test_svg_is_rejected_for_other_destinations(self):
        for target in [{'field': 'home_hero_image'}, {'placement': 'HOME_HERO'}]:
            with self.subTest(target=target):
                self.reject(self.upload('safe.svg', self.svg(), 'image/svg+xml'), target)

    def test_active_or_external_svg_is_rejected_without_parsing_side_effects(self):
        bodies = [
            self.svg('<script>void 0</script>'),
            self.svg('<rect onload="void 0"/>'),
            self.svg('<foreignObject><div>fixture</div></foreignObject>'),
            self.svg('<image href="https://example.invalid/image.png"/>'),
            self.svg('<image href="data:image/png;base64,AA=="/>'),
            self.svg('<use href="https://example.invalid/sprite.svg#x"/>'),
            self.svg('<path style="fill:red" d="M0 0"/>'),
            self.svg('<path fill="url(https://example.invalid/a)" d="M0 0"/>'),
            self.svg('<style>@import "https://example.invalid/x";</style>'),
            b'<!DOCTYPE svg [<!ENTITY x "fixture">]>' + self.svg('<text>&x;</text>'),
            b'<?xml-stylesheet href="https://example.invalid/x"?>' + self.svg(),
        ]
        for index, raw in enumerate(bodies):
            with self.subTest(case=index):
                self.reject(self.upload('unsafe.svg', raw, 'image/svg+xml'))

    def test_malformed_svg_is_rejected(self):
        self.reject(self.upload('broken.svg', b'<svg xmlns="http://www.w3.org/2000/svg"><path>', 'image/svg+xml'))

    def test_unknown_gallery_placement_cannot_create_media(self):
        self.reject(self.upload('valid.png', self.raster()), {'placement': 'UNKNOWN'})

    def test_branding_form_rejects_corrupt_file_and_keeps_stored_logo(self):
        url = reverse('admin:catalog_sitebrandingsettings_change', args=[self.site.pk])
        data = self.payload(url)
        data['logo'] = self.upload('broken.png', b'not a png')
        response = self.reject(None, expected=200, url=url, data=data)
        self.assertIsNotNone(response.context)
        self.assertIn('logo', response.context['adminform'].form.errors)

    def test_direct_analytics_form_cannot_bypass_file_validation(self):
        url = reverse('admin:catalog_siteanalytics_change', args=[self.site.pk])
        data = self.payload(url)
        data['logo'] = self.upload('broken.png', b'not a png')
        response = self.reject(None, expected=200, url=url, data=data)
        self.assertIsNotNone(response.context)
        self.assertIn('logo', response.context['adminform'].form.errors)

    def test_gallery_add_form_rejects_corrupt_file(self):
        url = reverse('admin:catalog_sitegalleryimage_add')
        data = self.payload(url)
        data.update(placement='HOME_HERO', image=self.upload('broken.png', b'not a png'))
        response = self.reject(None, expected=200, url=url, data=data)
        self.assertIsNotNone(response.context)
        self.assertIn('image', response.context['adminform'].form.errors)

    def test_static_svg_is_still_accepted_by_branding_form(self):
        url = reverse('admin:catalog_sitebrandingsettings_change', args=[self.site.pk])
        data = self.payload(url)
        data['logo'] = self.upload('safe.svg', self.svg(), 'image/svg+xml')
        self.assertEqual(self.client.post(url, data).status_code, 302)

    def test_static_svg_is_still_accepted_by_partner_form(self):
        url = reverse('admin:catalog_sitegalleryimage_add')
        data = self.payload(url)
        data.update(placement='HOME_PARTNERS', image=self.upload('safe.svg', self.svg(), 'image/svg+xml'))
        self.assertEqual(self.client.post(url, data).status_code, 302)

    def test_errors_are_localized_in_ru_az_en(self):
        values = []
        for lang in ['ru', 'az', 'en']:
            self.client.cookies['django_language'] = lang
            with self.subTest(lang=lang):
                response = self.reject(self.upload('broken.png', b'not a png'))
                values.append(response.json().get('error', ''))
        self.assertEqual(len(set(values)), 3)

    def test_permissions_precede_validation_of_bad_files(self):
        denied = get_user_model().objects.create_user('site06_denied', 'denied@example.invalid', is_staff=True)
        self.client.force_login(denied)
        self.reject(self.upload('broken.png', b'not a png'), expected=403)

    def test_csrf_precedes_validation_of_bad_files(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.user)
        self.reject(self.upload('broken.png', b'not a png'), expected=403)

    def test_stale_revision_remains_409_even_with_a_bad_file(self):
        branding = reverse('admin:catalog_sitebrandingsettings_change', args=[self.site.pk])
        data = self.payload(branding)
        footer = reverse('admin:catalog_sitefootersettings_change', args=[self.site.pk])
        current = self.payload(footer)
        current['footer_phone'] = '+994500006006'
        self.assertEqual(self.client.post(footer, current).status_code, 302)
        data['logo'] = self.upload('broken.png', b'not a png')
        self.reject(None, expected=409, url=branding, data=data)
