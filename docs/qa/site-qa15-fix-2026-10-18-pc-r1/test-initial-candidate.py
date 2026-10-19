import hashlib
import html
import io
import re
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from catalog.models import SiteSettings, SiteGalleryImage
from catalog.models.site import clear_singleton_caches


class Site15FixtureMixin:
    def setUp(self):
        super().setUp()
        assert settings.TESTING
        self.temp = tempfile.TemporaryDirectory(prefix='site15-')
        self.addCleanup(self.temp.cleanup)
        override = override_settings(MEDIA_ROOT=self.temp.name)
        override.enable()
        self.addCleanup(override.disable)
        clear_singleton_caches()
        self.actor = get_user_model().objects.create_superuser(
            'site15_actor', 'site15-actor@example.invalid', 'fictional-password')
        self.client.force_login(self.actor)
        self.client.cookies['django_language'] = 'ru'
        self.site = SiteSettings.get_solo()
        self.site.footer_phone = '+994500001500'
        self.site.footer_email = 'site15-before@example.invalid'
        self.site.save()
        clear_singleton_caches()
        self.url = reverse('admin:catalog_sitefootersettings_change', args=[self.site.pk])

    def payload(self, url=None, client=None):
        response = (client or self.client).get(url or self.url)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        data = {'_continue': '1'}
        for name, field in form.fields.items():
            value = form[name].value()
            if isinstance(field, forms.FileField):
                continue
            if isinstance(field, forms.BooleanField):
                if value:
                    data[name] = 'on'
            else:
                data[name] = '' if value is None else value
        token = re.search(r'name="settings_revision" value="([^"]*)"', response.content.decode())
        data['settings_revision'] = html.unescape(token.group(1)) if token else 'missing-in-current-implementation'
        return data

    def snapshot(self):
        self.site.refresh_from_db()
        return {'row': {f.name: f.value_to_string(self.site) for f in self.site._meta.concrete_fields},
                'files': {p.relative_to(self.temp.name).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in Path(self.temp.name).rglob('*') if p.is_file()}}

    def image(self):
        buffer = io.BytesIO()
        Image.new('RGB', (12, 12), 'green').save(buffer, 'PNG')
        return SimpleUploadedFile('site15-fictional.png', buffer.getvalue(), content_type='image/png')

    def first_save(self):
        data = self.payload()
        data['footer_phone'] = '+994500001501'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)

    def assert_conflict(self, data, url=None):
        before = self.snapshot()
        response = self.client.post(url or self.url, data)
        with self.subTest(check='conflict409'):
            self.assertEqual(response.status_code, 409)
        with self.subTest(check='no-row-or-file-write'):
            self.assertEqual(self.snapshot(), before)
        return response


class Site15SettingsConflictTests(Site15FixtureMixin, TestCase):
    def test_form_includes_nonempty_revision(self):
        self.assertNotEqual(self.payload()['settings_revision'], 'missing-in-current-implementation')

    def test_fresh_valid_form_still_saves(self):
        data = self.payload()
        data['footer_email'] = 'site15-fresh@example.invalid'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)
        self.site.refresh_from_db()
        self.assertEqual(self.site.footer_email, 'site15-fresh@example.invalid')

    def test_missing_revision_cannot_write(self):
        data = self.payload()
        data.pop('settings_revision')
        data['footer_phone'] = '+994500001599'
        self.assert_conflict(data)

    def test_tampered_revision_cannot_write(self):
        data = self.payload()
        data['settings_revision'] += 'tampered'
        data['footer_phone'] = '+994500001599'
        self.assert_conflict(data)

    def test_two_tabs_same_field_rejects_second_save(self):
        data = self.payload()
        self.first_save()
        data['footer_phone'] = '+994500001502'
        response = self.assert_conflict(data)
        self.assertContains(response, '+994500001502', status_code=409)

    def test_two_tabs_disjoint_fields_preserves_first_and_second_draft(self):
        data = self.payload()
        self.first_save()
        data['footer_email'] = 'site15-draft-b@example.invalid'
        response = self.assert_conflict(data)
        self.assertContains(response, 'site15-draft-b@example.invalid', status_code=409)
        self.assertContains(response, 'target="_blank"', status_code=409)

    def test_change_in_another_section_conflicts_conservatively(self):
        data = self.payload()
        about = reverse('admin:catalog_siteaboutsettings_change', args=[self.site.pk])
        first = self.payload(about)
        first['about_text_ru'] = 'Fictional SITE15 saved about'
        self.assertEqual(self.client.post(about, first).status_code, 302)
        data['footer_email'] = 'site15-section-b@example.invalid'
        self.assert_conflict(data)

    def test_direct_analytics_editor_cannot_overwrite_a_newer_settings_row(self):
        url = reverse('admin:catalog_siteanalytics_change', args=[self.site.pk])
        data = self.payload(url)
        self.first_save()
        data['footer_email'] = 'site15-analytics-draft@example.invalid'
        self.assert_conflict(data, url)

    def test_repeated_stale_post_never_refreshes_revision_or_writes(self):
        data = self.payload()
        self.first_save()
        data['footer_email'] = 'site15-repeated@example.invalid'
        self.assert_conflict(data)
        self.assert_conflict(data)

    def test_revision_from_another_actor_is_rejected(self):
        data = self.payload()
        actor = get_user_model().objects.create_superuser('site15_actor_b', 'site15-actor-b@example.invalid', 'fictional')
        self.client.force_login(actor)
        data['footer_email'] = 'site15-other-actor@example.invalid'
        self.assert_conflict(data)

    def test_revision_from_another_section_is_rejected(self):
        footer = self.payload()
        url = reverse('admin:catalog_sitecontactssettings_change', args=[self.site.pk])
        data = self.payload(url)
        data['settings_revision'] = footer['settings_revision']
        data['contacts_text_ru'] = 'Fictional section-token mismatch'
        self.assert_conflict(data, url)

    def test_ajax_main_upload_invalidates_open_form_revision(self):
        data = self.payload()
        upload = reverse('admin:catalog_sitegalleryimage_ajax_upload')
        self.assertEqual(self.client.post(upload, {'field': 'logo', 'image': self.image()}).status_code, 200)
        data['footer_email'] = 'site15-after-upload@example.invalid'
        self.assert_conflict(data)

    def test_ajax_main_delete_invalidates_open_form_revision(self):
        self.site.logo = self.image()
        self.site.save()
        data = self.payload()
        delete = reverse('admin:catalog_sitegalleryimage_ajax_delete_main_image')
        self.assertEqual(self.client.post(delete, {'field': 'logo'}).status_code, 200)
        data['footer_email'] = 'site15-after-delete@example.invalid'
        self.assert_conflict(data)

    def test_gallery_creation_does_not_invalidate_settings_form(self):
        data = self.payload()
        upload = reverse('admin:catalog_sitegalleryimage_ajax_upload')
        self.assertEqual(self.client.post(upload, {'placement': SiteGalleryImage.PLACEMENT_HOME_HERO,
                                                  'image': self.image()}).status_code, 200)
        data['footer_email'] = 'site15-after-gallery@example.invalid'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)

    def test_invalid_email_retains_baseline_for_explicit_valid_retry(self):
        data = self.payload()
        data['footer_email'] = 'invalid-email'
        before = self.snapshot()
        self.assertEqual(self.client.post(self.url, data).status_code, 200)
        self.assertEqual(self.snapshot(), before)
        data['footer_email'] = 'site15-valid-retry@example.invalid'
        self.assertEqual(self.client.post(self.url, data).status_code, 302)

    def test_stale_uploaded_file_is_not_stored_and_requires_reselection(self):
        url = reverse('admin:catalog_sitebrandingsettings_change', args=[self.site.pk])
        data = self.payload(url)
        self.first_save()
        data['logo'] = self.image()
        response = self.assert_conflict(data, url)
        self.assertContains(response, 'Выбранные файлы', status_code=409)

    def test_draft_html_is_escaped_in_conflict_response(self):
        data = self.payload()
        self.first_save()
        data['footer_phone'] = '<script>alert("site15")</script>'
        response = self.assert_conflict(data)
        self.assertNotContains(response, '<script>alert("site15")</script>', status_code=409)
        self.assertContains(response, '&lt;script&gt;', status_code=409)

    def test_update_without_timestamp_still_invalidates_full_row_snapshot(self):
        data = self.payload()
        SiteSettings.objects.filter(pk=self.site.pk).update(footer_phone='+994500001577')
        data['footer_email'] = 'site15-no-timestamp@example.invalid'
        self.assert_conflict(data)

    def test_permission_denial_precedes_any_revision_write(self):
        data = self.payload()
        user = get_user_model().objects.create_user('site15_denied', 'site15-denied@example.invalid', is_staff=True)
        self.client.force_login(user)
        before = self.snapshot()
        self.assertEqual(self.client.post(self.url, data).status_code, 403)
        self.assertEqual(self.snapshot(), before)

    def test_csrf_is_required_with_a_valid_revision(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.actor)
        data = self.payload(client=client)
        before = self.snapshot()
        self.assertEqual(client.post(self.url, data).status_code, 403)
        self.assertEqual(self.snapshot(), before)


class Site15ConcurrentSettingsTests(Site15FixtureMixin, TransactionTestCase):
    def test_two_concurrent_forms_have_exactly_one_winner(self):
        data = self.payload()
        barrier = threading.Barrier(2)

        def submit(email):
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.actor)
                barrier.wait(timeout=10)
                return client.post(self.url, {**data, 'footer_email': email}).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(submit, email) for email in
                       ['site15-concurrent-a@example.invalid', 'site15-concurrent-b@example.invalid']]
            statuses = [f.result(timeout=20) for f in futures]
        self.assertEqual(sorted(statuses), [302, 409])
