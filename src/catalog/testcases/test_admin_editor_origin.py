"""Staff editor requests must stay on the admin host, including private media."""
import json
import re
from html import unescape
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog.models import Place, ServerDraft, VolunteerPlaceRevision
from catalog.services.place_editor_drafts import config_for, working_draft_rows
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.testcases.test_content_entry_final import CandidateMediaFixture


@override_settings(ADMIN_HOST='admin.kidsmap.test', PUBLIC_BASE_URL='https://kidsmap.test',
                   ALLOWED_HOSTS=['testserver', 'admin.kidsmap.test', 'kidsmap.test'])
class AdminEditorOriginTests(CandidateMediaFixture, TestCase):
    collection = '/admin/editor/drafts/'
    host = {'HTTP_HOST': 'admin.kidsmap.test', 'secure': True}

    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff)

    def post_json(self, url, data, client=None):
        return (client or self.client).post(url, json.dumps(data),
                                           content_type='application/json', **self.host)

    def create(self):
        response = self.post_json(self.collection, {'target_type': 'place',
            'schema_version': 1, 'expected_version': 0, 'fields': {'name_az': 'Origin regression'}})
        self.assertEqual(response.status_code, 201, response.content[:300])
        return response.json()

    def preview_action(self, url):
        response = self.client.get(url, **self.host)
        self.assertEqual(response.status_code, 200)
        action = re.search(r'data-km-preview[^>]*formaction="([^"]+)"', response.content.decode())
        self.assertIsNotNone(action)
        return unescape(action.group(1))

    def test_rendered_staff_autosave_config_posts_without_public_redirect(self):
        config = config_for(user=self.staff)
        result = self.post_json(config['collectionUrl'], {'target_type': 'place',
            'schema_version': 1, 'expected_version': 0, 'fields': {}})
        self.assertEqual(result.status_code, 201, dict(result.headers))
        self.assertTrue(config['collectionUrl'].startswith('/admin/editor/'))
        response = self.client.get('/ru/admin/catalog/place/add/?type=permanent', **self.host)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"collectionUrl": "/admin/editor/drafts/"')

    def test_rendered_new_and_existing_staff_check_returns_json_without_writes(self):
        for url in ('/ru/admin/catalog/place/add/?type=permanent',
                    f'/ru/admin/catalog/place/{self.place.pk}/change/'):
            with self.subTest(url=url):
                action = self.preview_action(url)
                before = (Place.objects.count(), VolunteerPlaceRevision.objects.count(), ServerDraft.objects.count())
                response = self.client.post(action, {'_km_check_required': '1'}, **self.host)
                self.assertEqual(response.status_code, 422, dict(response.headers))
                self.assertEqual(response['Content-Type'], 'application/json')
                self.assertTrue(response.json()['errors'])
                self.assertEqual(before, (Place.objects.count(), VolunteerPlaceRevision.objects.count(), ServerDraft.objects.count()))

    def test_admin_preview_is_read_only_and_surface_cannot_be_overridden(self):
        before = Place.objects.count()
        response = self.client.post('/admin/editor/places/preview/?surface=owner',
            {'name_az': 'Unsaved preview', 'description_az': 'Preview only', 'whatsapp_mode': 'none'}, **self.host)
        self.assertEqual(response.status_code, 200, response.content[:300])
        self.assertContains(response, 'Unsaved preview')
        self.assertEqual(Place.objects.count(), before)
        self.assertEqual(ServerDraft.objects.count(), 0)

    def test_media_restore_conflict_list_and_delete_stay_private_on_admin_host(self):
        draft = self.create()
        detail = self.collection + draft['draft_id'] + '/'
        uploaded = self.client.post(detail + 'media/', {'expected_version': '1', 'media_id': str(uuid4()),
            'photo': SimpleUploadedFile('qa.png', self.image(), 'image/png')}, **self.host)
        self.assertEqual(uploaded.status_code, 200, uploaded.content[:300])
        row = uploaded.json()['media_manifest'][0]
        self.assertTrue(row['url'].startswith('/admin/editor/drafts/'))
        for url in (detail, detail + 'media/'):
            restored = self.client.get(url, **self.host)
            self.assertEqual(restored.status_code, 200)
            self.assertEqual(restored.json()['media_manifest'][0]['url'], row['url'])
        committed = self.client.put(detail + 'media/', json.dumps({'expected_version': 2,
            'items': [{'id': row['id'], 'role': 'main', 'order': 0}]}), content_type='application/json', **self.host)
        self.assertEqual(committed.status_code, 200, committed.content[:300])
        conflict = self.post_json(self.collection, {'draft_id': draft['draft_id'], 'target_type': 'place',
            'schema_version': 1, 'expected_version': 1, 'fields': {'name_az': 'Stale input'}})
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.json()['media_manifest'][0]['url'], row['url'])
        self.assertEqual(conflict.json()['submitted_fields']['name_az'], 'Stale input')
        listed = self.client.get(self.collection, **self.host).json()['drafts']
        self.assertEqual(listed[0]['media_manifest'][0]['url'], row['url'])
        media = self.client.get(row['url'], **self.host)
        self.assertEqual(media.status_code, 200)
        self.assertEqual(media['Content-Type'], 'image/webp')
        self.assertIn('no-store', media['Cache-Control'])
        stranger = get_user_model().objects.create_superuser('other_admin_origin', password='synthetic')
        other = Client()
        other.force_login(stranger)
        self.assertEqual(other.get(row['url'], **self.host).status_code, 403)
        self.assertEqual(other.get(detail, **self.host).status_code, 403)
        self.assertEqual(self.post_json(detail + 'materialize/', {'expected_version': 3}, client=other).status_code, 403)
        self.assertEqual(Place.objects.count(), 1)
        working = list(working_draft_rows(user=self.staff))
        self.assertEqual(working[0]['delete_url'], detail)
        deleted = self.client.delete(working[0]['delete_url'], json.dumps({'expected_version': 3}),
                                    content_type='application/json', **self.host)
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get(detail, **self.host).status_code, 404)

    def test_csrf_required_and_admin_origin_accepted(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.staff)
        payload = {'target_type': 'place', 'schema_version': 1, 'expected_version': 0, 'fields': {}}
        self.assertEqual(self.post_json(self.collection, payload, client=client).status_code, 403)
        form = client.get('/admin/catalog/place/add/?type=permanent', **self.host)
        self.assertEqual(form.status_code, 200)
        token = client.cookies['csrftoken'].value
        good = client.post(self.collection, json.dumps(payload), content_type='application/json',
                           HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://admin.kidsmap.test', **self.host)
        self.assertEqual(good.status_code, 201, good.content[:300])
        bad = client.post(self.collection, json.dumps(payload), content_type='application/json',
                          HTTP_X_CSRFTOKEN=token, HTTP_ORIGIN='https://foreign.invalid', **self.host)
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(ServerDraft.objects.count(), 1)

    def test_materialize_retry_creates_only_one_unpublished_place(self):
        response = self.post_json(self.collection, {'target_type': 'place', 'schema_version': 1,
            'expected_version': 0, 'fields': {'name_az': 'New isolated park', 'category': str(self.place.category_id)}})
        self.assertEqual(response.status_code, 201, response.content[:300])
        url = self.collection + response.json()['draft_id'] + '/materialize/'
        first = self.post_json(url, {'expected_version': 1})
        self.assertEqual(first.status_code, 200, first.content[:300])
        repeated = self.post_json(url, {'expected_version': 1})
        self.assertEqual(repeated.status_code, 200, repeated.content[:300])
        self.assertEqual(first.json()['materialized_place_id'], repeated.json()['materialized_place_id'])
        place = Place.objects.get(pk=first.json()['materialized_place_id'])
        self.assertEqual(place.status, 'draft')
        self.assertFalse(place.is_active)
        self.assertEqual(Place.objects.count(), 2)

    def test_legacy_photo_upload_and_restore_use_admin_route(self):
        draft = self.create()
        url = self.collection + draft['draft_id'] + '/photo/'
        uploaded = self.client.post(url, {'expected_version': '1',
            'photo': SimpleUploadedFile('qa.png', self.image(), 'image/png')}, **self.host)
        self.assertEqual(uploaded.status_code, 200, uploaded.content[:300])
        self.assertTrue(uploaded.json()['photo_saved'])
        photo = self.client.get(url, **self.host)
        self.assertEqual(photo.status_code, 200)
        self.assertEqual(photo['Content-Type'], 'image/webp')

    def test_anonymous_owner_inactive_and_unprivileged_staff_cannot_use_admin_preview(self):
        for actor in (None, self.owner):
            client = Client()
            if actor:
                client.force_login(actor)
            for url in (self.collection, '/admin/editor/places/preview/'):
                response = client.get(url, **self.host)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/admin/login/', response['Location'])
        limited = get_user_model().objects.create_user('limited_editor_origin', is_staff=True)
        self.client.force_login(limited)
        self.assertEqual(self.client.post('/admin/editor/places/preview/', {}, **self.host).status_code, 403)
        self.staff.is_active = False
        self.staff.save(update_fields=['is_active'])
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(self.collection, **self.host).status_code, 302)

    def test_volunteer_has_own_preview_surface_and_cannot_switch_to_admin(self):
        volunteer = get_user_model().objects.create_user('volunteer_editor_origin', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.client.force_login(volunteer)
        self.assertEqual(config_for(user=volunteer, surface='volunteer')['collectionUrl'], self.collection)
        self.create()
        response = self.client.post('/admin/editor/volunteer/places/preview/?surface=admin',
                                    {'_km_check_required': '1'}, **self.host)
        self.assertEqual(response.status_code, 422, response.content[:300])
        self.assertEqual(self.client.post('/admin/editor/places/preview/?surface=volunteer',
                                         {'_km_check_required': '1'}, **self.host).status_code, 403)
        action = self.preview_action(reverse('admin:volunteer_add'))
        self.assertEqual(action, '/admin/editor/volunteer/places/preview/')

    @override_settings(TASK33_R1_WRITE_MODE='off')
    def test_admin_alias_does_not_bypass_maintenance_write_pause(self):
        response = self.post_json(self.collection, {'target_type': 'place', 'schema_version': 1,
                                                   'expected_version': 0, 'fields': {}})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'r1_writes_paused')
        self.assertEqual(ServerDraft.objects.count(), 0)

    def test_public_editor_and_host_separation_are_preserved(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('server_draft_collection'), json.dumps({'target_type': 'place',
            'schema_version': 1, 'expected_version': 0, 'fields': {}}), content_type='application/json',
            HTTP_HOST='kidsmap.test', secure=True)
        self.assertEqual(response.status_code, 201)
        moved = self.client.get('/admin/editor/drafts/', HTTP_HOST='kidsmap.test', secure=True)
        self.assertEqual(moved.status_code, 302)
        self.assertEqual(moved['Location'], 'https://admin.kidsmap.test/admin/editor/drafts/')
        public = self.client.get('/ru/account/places/preview/', **self.host)
        self.assertEqual(public.status_code, 301)
        self.assertEqual(public['Location'], 'https://kidsmap.test/ru/account/places/preview/')
