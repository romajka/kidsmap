import json
import re
from io import BytesIO
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, connections
from django.test import TransactionTestCase
from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.urls import reverse
from django.conf import settings
from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision, Subcategory
from catalog.testcases.utils import create_ready_place


User = get_user_model()


class VolunteerAccessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("volunteer", is_staff=True)
        self.user.groups.add(Group.objects.create(name="KidsMap Volunteers"))
        self.client.force_login(self.user)

    def editor_data(self, url, **overrides):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        data = {name: form[name].value() if form[name].value() is not None else ''
                for name, field in form.fields.items() if not isinstance(field, forms.FileField)}
        data.update(action='submit', **overrides)
        return data

    def submit(self, place, **overrides):
        url = f'/admin/volunteer/{place.pk}/edit/'
        response = self.client.post(url, self.editor_data(url, **overrides))
        self.assertEqual(response.status_code, 302, response.context['form'].errors if response.status_code == 200 else '')
        return VolunteerPlaceRevision.objects.get(place=place)

    def root_login(self):
        root, _ = User.objects.get_or_create(username='root', defaults={'is_staff': True, 'is_superuser': True})
        self.client.force_login(root)
        return root

    def test_admin_home_redirects_to_own_workspace(self):
        response = self.client.get("/admin/")
        self.assertRedirects(response, "/admin/volunteer/", fetch_redirect_response=False)

    def test_direct_admin_routes_denied_even_with_accidental_permissions(self):
        self.user.user_permissions.set(Permission.objects.all())
        for prefix in ("", "/ru", "/en"):
            for route in ("auth/user/", "catalog/staffaccessuser/", "catalog/place/", "catalog/place/add/", "autocomplete/"):
                for method in (self.client.get, self.client.post):
                    with self.subTest(prefix=prefix, route=route, method=method.__name__):
                        self.assertEqual(method(f"{prefix}/admin/{route}").status_code, 403)

    def test_owner_create_route_cannot_bypass_review(self):
        response = self.client.post(reverse("owner_place_create"), {"name": "Bypass"})
        self.assertEqual(response.status_code, 403)

    def test_staff_flag_does_not_grant_specialist_document_access(self):
        response = self.client.get(reverse('serve_specialist_document', args=[999]))
        self.assertEqual(response.status_code, 403)

    def test_staff_creation_offers_volunteer_role(self):
        root = User.objects.create_superuser("root", "root@example.test", "password")
        self.client.force_login(root)
        response = self.client.get(reverse("admin:catalog_staffaccessuser_add"))
        self.assertIn('value="volunteer"', response.content.decode(), 'Volunteer role missing')

    def test_new_submission_is_private_and_cannot_spoof_author_or_publish(self):
        response = self.client.post('/admin/volunteer/add/', {**self.editor_data('/admin/volunteer/add/'),
            'name_az': 'Volunteer new place', 'category': 'EDU',
            'action': 'submit', 'revision_version': 0,
            'status': 'published', 'is_active': 'on', 'created_by': 999,
            'owner': 999, 'is_verified': 'on',
        })
        self.assertEqual(response.status_code, 302)
        place = Place.objects.get(created_by=self.user)
        self.assertFalse(place.is_active)
        self.assertEqual(place.status, Place.STATUS_DRAFT)
        self.assertIsNone(place.owner_id)
        self.assertFalse(place.is_verified)
        self.assertEqual(place.volunteer_revision.status, 'pending')

    def test_published_changes_stay_private_until_review(self):
        place = Place.objects.create(name='Before', name_az='Before', category='EDU', created_by=self.user)
        response = self.client.post(f'/admin/volunteer/{place.pk}/edit/', {**self.editor_data(f'/admin/volunteer/{place.pk}/edit/'),
            'name_az': 'After', 'category': 'EDU', 'action': 'submit', 'revision_version': 0,
        })
        self.assertEqual(response.status_code, 302)
        place.refresh_from_db()
        self.assertEqual(place.name_az, 'Before')
        self.assertTrue(place.is_active)
        self.assertEqual(place.volunteer_revision.payload['name_az'], 'After')

    def test_foreign_place_not_listed_or_editable(self):
        place = Place.objects.create(name='FOREIGN SECRET DRAFT', category='EDU', status='draft', is_active=False)
        response = self.client.get('/admin/volunteer/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(place.name, response.content.decode())
        for method in (self.client.get, self.client.post):
            self.assertEqual(method(f'/admin/volunteer/{place.pk}/edit/').status_code, 404)

    def test_workspace_excludes_anonymous_and_nonstaff(self):
        self.client.logout()
        self.assertEqual(self.client.get('/admin/volunteer/').status_code, 302)
        ordinary = User.objects.create_user('ordinary')
        self.client.force_login(ordinary)
        self.assertEqual(self.client.get('/admin/volunteer/').status_code, 302)

    def test_volunteer_cannot_review(self):
        self.assertEqual(self.client.get('/admin/volunteer/review/').status_code, 403)
        self.assertEqual(self.client.post('/admin/volunteer/review/1/').status_code, 403)

    def test_superadmin_approval_publishes_valid_proposal_and_audits_changes(self):
        place = create_ready_place(created_by=self.user, status='draft', is_active=False)
        revision = self.submit(place, name_az='Approved change')
        root = self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        self.assertEqual(response.status_code, 302, response.context['error'] if response.status_code == 200 else '')
        place.refresh_from_db()
        self.assertEqual(place.name_az, 'Approved change')
        self.assertTrue(place.is_active)
        self.assertEqual(place.status, 'published')
        self.assertTrue(PlaceChangeAudit.objects.filter(place=place, changed_by=root, field_name='name_az').exists())

    def test_public_page_shows_old_content_until_approval(self):
        place = create_ready_place(created_by=self.user, name_az='Public before')
        revision = self.submit(place, name_az='Proposed after')
        public = Client()
        response = public.get(place.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertIn('Public before', response.content.decode())
        self.assertNotIn('Proposed after', response.content.decode())
        self.root_login()
        self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        response = public.get(place.get_absolute_url())
        self.assertIn('Proposed after', response.content.decode())

    def test_rejection_preserves_live_and_allows_resubmission(self):
        place = create_ready_place(created_by=self.user, name_az='Original')
        revision = self.submit(place, name_az='Needs correction')
        self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'reject', 'version': revision.version, 'note': 'Correct the name'})
        self.assertEqual(response.status_code, 302)
        place.refresh_from_db()
        self.assertEqual(place.name_az, 'Original')
        self.client.force_login(self.user)
        response = self.client.get(f'/admin/volunteer/{place.pk}/edit/')
        self.assertIn('Correct the name', response.content.decode())
        revision = self.submit(place, name_az='Corrected name')
        self.assertEqual(revision.status, 'pending')

    def test_not_ready_cannot_publish_by_direct_post(self):
        place = Place.objects.create(created_by=self.user, name='Incomplete', category='EDU', status='draft', is_active=False)
        revision = self.submit(place, name_az='Incomplete')
        self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['error'])
        place.refresh_from_db()
        self.assertFalse(place.is_active)
        self.assertEqual(place.volunteer_revision.status, 'pending')

    def test_stale_edit_and_stale_approval_do_not_overwrite(self):
        place = create_ready_place(created_by=self.user)
        url = f'/admin/volunteer/{place.pk}/edit/'
        stale = self.editor_data(url, name_az='Stale')
        revision = self.submit(place, name_az='First')
        response = self.client.post(url, stale)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        old_version = revision.version
        self.submit(place, name_az='Second')
        self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': old_version})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['error'])
        place.refresh_from_db()
        self.assertNotEqual(place.name_az, 'First')

    def test_concurrent_admin_edit_requires_explicit_restart(self):
        place = create_ready_place(created_by=self.user)
        revision = self.submit(place, name_az='Volunteer proposal')
        Place.objects.filter(pk=place.pk).update(name_az='Admin correction')
        self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        self.assertTrue(response.context['error'])
        self.client.force_login(self.user)
        url = f'/admin/volunteer/{place.pk}/edit/'
        response = self.client.post(url, self.editor_data(url))
        self.assertTrue(response.context['form'].errors)
        response = self.client.post(url, {'action': 'restart', 'revision_version': revision.version})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(VolunteerPlaceRevision.objects.get(pk=revision.pk).payload['name_az'], 'Admin correction')

    def test_owner_handover_removes_volunteer_access_and_blocks_approval(self):
        place = create_ready_place(created_by=self.user)
        revision = self.submit(place)
        owner = User.objects.create_user('business-owner')
        Place.objects.filter(pk=place.pk).update(owner=owner)
        self.assertEqual(self.client.get(f'/admin/volunteer/{place.pk}/edit/').status_code, 404)
        self.root_login()
        response = self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        self.assertTrue(response.context['error'])

    def test_photo_is_pending_and_live_photo_file_is_unchanged(self):
        from PIL import Image
        place = create_ready_place(created_by=self.user)
        old_photo = place.photo.name
        buf = BytesIO()
        Image.new('RGB', (40, 40), 'green').save(buf, format='PNG')
        revision = self.submit(place, photo=SimpleUploadedFile('new.png', buf.getvalue(), content_type='image/png'))
        place.refresh_from_db()
        self.assertEqual(place.photo.name, old_photo)
        self.assertTrue(revision.payload['photo'].endswith('.webp'))
        self.root_login()
        self.client.post(f'/admin/volunteer/review/{place.pk}/', {'action': 'approve', 'version': revision.version})
        place.refresh_from_db()
        self.assertEqual(place.photo.name, revision.payload['photo'])

    def test_csrf_required_and_ui_does_not_offer_publication_or_other_sections(self):
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post('/admin/volunteer/add/', {'action': 'submit'}).status_code, 403)
        self.user.user_permissions.set(Permission.objects.all())
        html = self.client.get('/admin/volunteer/add/').content.decode()
        for forbidden in ('name="owner"', 'name="status"', 'name="is_active"', 'name="is_superuser"', '/admin/catalog/staffaccessuser/', f'/admin/auth/user/{self.user.pk}/change/', 'value="approve"'):
            self.assertNotIn(forbidden, html)

    def test_foreign_subcategory_and_invalid_image_rejected(self):
        other = Subcategory.objects.exclude(category_id='EDU').first()
        url = '/admin/volunteer/add/'
        data = self.editor_data(url, category='EDU', name_az='Wrong category', subcategory=other.pk)
        data['photo'] = SimpleUploadedFile('bad.jpg', b'not an image', content_type='image/jpeg')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('subcategory', response.context['form'].errors)
        self.assertIn('photo', response.context['form'].errors)
        self.assertFalse(Place.objects.filter(created_by=self.user).exists())

    def test_malformed_schedule_is_a_form_error_not_server_error(self):
        url = '/admin/volunteer/add/'
        data = self.editor_data(url, category='EDU', name_az='Invalid schedule')
        self.client.raise_request_exception = False
        for raw in ('[null]', '["invalid"]', '[{}]', '{"unexpected":1}'):
            with self.subTest(raw=raw):
                response = self.client.post(url, {**data, 'structured_schedule': raw})
                self.assertEqual(response.status_code, 200)
                self.assertIn('structured_schedule', response.context['form'].errors)
        self.assertFalse(Place.objects.filter(created_by=self.user).exists())

    def test_add_form_has_subcategories_for_dynamic_category_picker(self):
        form = self.client.get('/admin/volunteer/add/').context['form']
        self.assertTrue(form.fields['subcategory'].queryset.exists())

    def test_browser_form_preserves_selected_subcategory(self):
        place = create_ready_place(created_by=self.user)
        form = self.client.get(f'/admin/volunteer/{place.pk}/edit/').context['form']
        self.assertIn(f'value="{place.subcategory_id}" selected', str(form['subcategory']))

    def test_azerbaijani_workspace_language_is_not_overridden_by_default_admin_russian(self):
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = 'az'
        response = self.client.get('/admin/volunteer/add/')
        self.assertEqual(response.context['admin_current_language'], 'az')

    def test_role_membership_is_queried_only_once_per_request(self):
        with CaptureQueriesContext(connection) as captured:
            self.client.get('/admin/volunteer/')
        lookups = [q for q in captured.captured_queries if 'KidsMap Volunteers' in q['sql']]
        self.assertEqual(len(lookups), 1)

    def test_schedule_and_price_controls_are_not_rendered_twice(self):
        html = self.client.get('/admin/volunteer/add/').content.decode()
        for name in ('schedule_mode', 'schedule_note_az', 'schedule_note_ru', 'schedule_note_en', 'custom_price_badge_az'):
            with self.subTest(name=name):
                self.assertEqual(html.count(f'id="id_{name}"'), 1)

    def test_workspace_submit_button_uses_selected_language_without_fallback(self):
        for lang, prefix, label in (('az', '', 'Yoxlamaya göndər'), ('en', '/en', 'Submit for review'), ('ru', '/ru', 'Отправить на проверку')):
            with self.subTest(lang=lang):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
                html = self.client.get(f'{prefix}/admin/volunteer/add/').content.decode()
                button = re.search(r'value="submit"[^>]*>([^<]+)<', html)
                self.assertEqual(button.group(1), label)

    def test_superadmin_creates_volunteer_without_global_permissions(self):
        self.root_login()
        response = self.client.post(reverse('admin:catalog_staffaccessuser_add'), {
            'username': 'new-volunteer', 'email': 'new-volunteer@example.test',
            'password1': 'StrongPass123!!', 'password2': 'StrongPass123!!',
            'admin_role': 'volunteer', 'is_superuser': 'on',
            'profile-TOTAL_FORMS': '1', 'profile-INITIAL_FORMS': '0',
            'profile-MIN_NUM_FORMS': '0', 'profile-MAX_NUM_FORMS': '1',
            'profile-0-phone': '', 'profile-0-gender': 'U', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='new-volunteer')
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.groups.filter(name='KidsMap Volunteers').exists())
        self.assertEqual(user.get_all_permissions(), set())

    def test_stale_restart_is_rejected_without_server_error(self):
        place = create_ready_place(created_by=self.user)
        revision = self.submit(place)
        self.client.raise_request_exception = False
        response = self.client.post(f'/admin/volunteer/{place.pk}/edit/', {'action': 'restart', 'revision_version': revision.version - 1})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(VolunteerPlaceRevision.objects.get(pk=revision.pk).status, 'pending')

    def test_invalid_contact_number_is_rejected(self):
        url = '/admin/volunteer/add/'
        data = self.editor_data(url, name_az='Invalid contact', category='EDU', phone1='abc')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('phone1', response.context['form'].errors)

    def test_owner_permission_service_cannot_bypass_workspace(self):
        from catalog.services.place_access import has_place_permission, PLACE_PERMISSION_EDIT, PLACE_PERMISSION_PUBLISH
        place = create_ready_place(created_by=self.user)
        self.user.user_permissions.set(Permission.objects.all())
        self.assertFalse(has_place_permission(user=self.user, place=place, permission_code=PLACE_PERMISSION_EDIT))
        self.assertFalse(has_place_permission(user=self.user, place=place, permission_code=PLACE_PERMISSION_PUBLISH))

    def test_repeated_approval_and_get_never_publish(self):
        place = create_ready_place(created_by=self.user, status='draft', is_active=False)
        revision = self.submit(place)
        self.root_login()
        url = f'/admin/volunteer/review/{place.pk}/'
        self.client.get(url, {'action': 'approve', 'version': revision.version})
        place.refresh_from_db()
        self.assertFalse(place.is_active)
        self.assertEqual(self.client.post(url, {'action': 'approve', 'version': revision.version}).status_code, 302)
        audit_count = PlaceChangeAudit.objects.filter(place=place).count()
        self.assertEqual(self.client.post(url, {'action': 'approve', 'version': revision.version}).status_code, 200)
        self.assertEqual(PlaceChangeAudit.objects.filter(place=place).count(), audit_count)


@skipUnless(connection.vendor == 'postgresql', 'Row-lock concurrency requires PostgreSQL')
class VolunteerConcurrencyTests(TransactionTestCase):
    def test_two_reviewers_cannot_apply_the_same_revision_twice(self):
        from catalog.services.volunteer_places import content_snapshot, live_snapshot, review_proposal
        from django.core.exceptions import ValidationError
        vol = User.objects.create_user('concurrent-volunteer', is_staff=True)
        root = User.objects.create_superuser('concurrent-root', 'root@concurrent.test', 'password')
        place = create_ready_place(created_by=vol, status='draft', is_active=False)
        revision = VolunteerPlaceRevision.objects.create(place=place, author=vol, payload=content_snapshot(place), base_snapshot=live_snapshot(place), status='pending')
        barrier = Barrier(2)

        def approve():
            try:
                actor = User.objects.get(pk=root.pk)
                barrier.wait(timeout=10)
                try:
                    review_proposal(user=actor, place_id=place.pk, version=revision.version, approve=True)
                    return 'approved'
                except ValidationError:
                    return 'stale'
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(approve) for _ in range(2)]
            self.assertEqual(sorted(f.result(timeout=30) for f in futures), ['approved', 'stale'])
        self.assertEqual(PlaceChangeAudit.objects.filter(place=place, field_name='status').count(), 1)
