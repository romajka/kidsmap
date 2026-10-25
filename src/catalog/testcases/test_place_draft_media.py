"""Private multi-photo drafts: retry, versioning, isolation and role boundaries."""
import json
import tempfile
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from catalog.models import Place, ServerDraft
from catalog.services import server_drafts
from catalog.services.staff_roles import VOLUNTEER_GROUP
from catalog.testcases.utils import create_quality_place


class DraftMediaTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = override_settings(MEDIA_ROOT=self.directory.name + '/public',
                                       PRIVATE_DRAFT_MEDIA_ROOT=self.directory.name + '/private')
        self.config.enable()
        self.addCleanup(self.config.disable)
        self.actor = get_user_model().objects.create_user(username='media-owner')
        self.other = get_user_model().objects.create_user(username='media-other')
        self.client.force_login(self.actor)
        self.draft = self.create_draft()
        self.url = '/api/drafts/' + self.draft['draft_id'] + '/media/'

    def create_draft(self, target=None, client=None):
        data = {'target_type': 'place', 'schema_version': 1, 'expected_version': 0, 'fields': {}}
        if target:
            data.update(target_id=target.pk, source_version=target.content_version)
        result = (client or self.client).post(reverse('server_draft_collection'),
                json.dumps(data), content_type='application/json')
        self.assertIn(result.status_code, (200, 201), result.content)
        return result.json()

    def upload(self, version=1, identifier=None, color='blue', client=None, url=None):
        buffer = BytesIO()
        Image.new('RGB', (30, 30), color).save(buffer, 'PNG')
        return (client or self.client).post(url or self.url, {'expected_version': str(version),
            'media_id': str(identifier or uuid4()),
            'photo': SimpleUploadedFile('picture.png', buffer.getvalue(), content_type='image/png')})

    def manifest(self, version, items, client=None):
        return (client or self.client).put(self.url, json.dumps({'expected_version': version, 'items': items}),
                                          content_type='application/json')

    def test_upload_restore_private_manifest_no_live_writes(self):
        identifier = str(uuid4())
        result = self.upload(identifier=identifier)
        self.assertEqual(result.status_code, 200, result.content)
        row = result.json()['media_manifest'][0]
        self.assertEqual((row['id'], row['role']), (identifier, 'pending'))
        self.assertNotIn('path', row)
        self.assertEqual(result.json()['version'], 2)
        committed = self.manifest(2, [{'id': identifier, 'role': 'main', 'order': 0}])
        self.assertEqual(committed.status_code, 200, committed.content)
        resumed = self.client.get(reverse('server_draft_detail', args=[self.draft['draft_id']])).json()
        self.assertEqual(resumed['media_manifest'][0]['role'], 'main')
        response = self.client.get(row['url'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/webp')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertNotIn('public', row['url'])
        self.assertEqual(Place.objects.count(), 0)
        self.assertFalse(list(Path(self.directory.name + '/public').glob('**/*')))

    def test_same_upload_id_retry_is_idempotent_even_with_original_version(self):
        identifier = str(uuid4())
        first = self.upload(identifier=identifier)
        self.assertEqual(first.status_code, 200, first.content)
        second = self.upload(identifier=identifier)
        self.assertEqual(second.status_code, 200, second.content)
        self.assertEqual(second.json()['version'], 2)
        self.assertEqual(len(second.json()['media_manifest']), 1)
        self.assertEqual(self.upload(identifier=identifier, color='red').status_code, 409)

    def test_interrupted_upload_preserves_desired_role_for_reload_before_commit(self):
        identifier = str(uuid4())
        buffer = BytesIO()
        Image.new('RGB', (30, 30), 'blue').save(buffer, 'PNG')
        def stage(version=1, role='gallery', order='0'):
            return self.client.post(self.url, {'expected_version': str(version), 'media_id': identifier,
                'desired_role': role, 'desired_order': order,
                'photo': SimpleUploadedFile('staged.png', buffer.getvalue(), content_type='image/png')})
        uploaded = stage()
        self.assertEqual(uploaded.status_code, 200, uploaded.content)
        # Reload after upload committed, before final role/order PUT.
        detail = self.client.get(reverse('server_draft_detail', args=[self.draft['draft_id']])).json()
        row = detail['media_manifest'][0]
        self.assertEqual((row['role'], row['desired_role'], row['desired_order']), ('pending', 'gallery', 0))
        self.assertEqual(self.client.get(row['url']).status_code, 200)
        retry = stage()
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.json()['version'], detail['version'])
        self.assertEqual(stage(role='main').status_code, 409)
        committed = self.manifest(detail['version'], [{'id': identifier, 'role': 'gallery', 'order': 0}])
        self.assertEqual(committed.status_code, 200, committed.content)
        self.assertEqual(committed.json()['media_manifest'][0]['role'], 'gallery')
        self.assertNotIn('desired_role', committed.json()['media_manifest'][0])

    def test_staged_metadata_is_bounded_and_pair_required(self):
        for extra in ({'desired_role': 'gallery'}, {'desired_order': '0'},
                      {'desired_role': 'gallery', 'desired_order': '10'},
                      {'desired_role': 'main', 'desired_order': '1'},
                      {'desired_role': 'unknown', 'desired_order': '0'}):
            buffer = BytesIO()
            Image.new('RGB', (30, 30), 'blue').save(buffer, 'PNG')
            response = self.client.post(self.url, {'expected_version': '1', 'media_id': str(uuid4()), **extra,
                'photo': SimpleUploadedFile('staged.png', buffer.getvalue(), content_type='image/png')})
            self.assertEqual(response.status_code, 422)
        self.assertEqual(ServerDraft.objects.get(pk=self.draft['draft_id']).version, 1)

    def test_manifest_roles_order_delete_and_retry(self):
        identifiers = [str(uuid4()) for _ in range(3)]
        for index, identifier in enumerate(identifiers):
            response = self.upload(version=index + 1, identifier=identifier)
            self.assertEqual(response.status_code, 200, response.content)
        items = [{'id': identifiers[2], 'role': 'main', 'order': 0},
                 {'id': identifiers[0], 'role': 'gallery', 'order': 0}]
        with self.captureOnCommitCallbacks(execute=True):
            response = self.manifest(4, items)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['version'], 5)
        self.assertEqual([row['id'] for row in response.json()['media_manifest']], [identifiers[2], identifiers[0]])
        retry = self.manifest(4, items)
        self.assertEqual(retry.status_code, 200, retry.content)
        self.assertEqual(retry.json()['version'], 5)
        self.assertEqual(self.client.get(self.url + identifiers[1] + '/').status_code, 404)
        self.assertEqual(self.upload(version=5, identifier=identifiers[1]).status_code, 409)

    def test_conflict_does_not_drop_media_or_text(self):
        response = self.upload()
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.manifest(1, []).status_code, 409)
        self.assertEqual(len(self.client.get(self.url).json()['media_manifest']), 1)

    def test_foreign_and_revoked_actor_cannot_read_or_mutate(self):
        result = self.upload()
        self.assertEqual(result.status_code, 200, result.content)
        foreign = Client()
        foreign.force_login(self.other)
        self.assertEqual(foreign.get(self.url).status_code, 403)
        self.assertEqual(foreign.get(result.json()['media_manifest'][0]['url']).status_code, 403)
        self.assertEqual(self.upload(client=foreign).status_code, 403)
        self.assertEqual(self.manifest(2, [], client=foreign).status_code, 403)
        self.actor.is_active = False
        self.actor.save(update_fields=['is_active'])
        self.assertIn(self.client.get(self.url).status_code, (302, 403))

    def test_invalid_upload_and_manifest_do_not_change_version(self):
        bad = self.client.post(self.url, {'expected_version': '1', 'media_id': str(uuid4()),
            'photo': SimpleUploadedFile('bad.png', b'garbage', content_type='image/png')})
        self.assertEqual(bad.status_code, 422)
        self.assertEqual(self.manifest(1, [{'id': '../../secret', 'role': 'main', 'order': 0}]).status_code, 422)
        self.assertEqual(self.manifest(True, []).status_code, 422)
        self.assertEqual(self.manifest(1, [{'id': str(uuid4()), 'role': 'main', 'order': 0, 'path': '/secret'}]).status_code, 422)
        self.assertEqual(ServerDraft.objects.get(pk=self.draft['draft_id']).version, 1)

    def test_duplicate_roles_and_ids_rejected(self):
        identifiers = [str(uuid4()), str(uuid4())]
        for index, identifier in enumerate(identifiers):
            self.assertEqual(self.upload(version=index + 1, identifier=identifier).status_code, 200)
        self.assertEqual(self.manifest(3, [{'id': identifier, 'role': 'main', 'order': 0}
                                         for identifier in identifiers]).status_code, 422)
        item = {'id': identifiers[0], 'role': 'gallery', 'order': 0}
        self.assertEqual(self.manifest(3, [item, item]).status_code, 422)

    def test_changed_target_version_blocks_read_upload_and_manifest(self):
        place = create_quality_place(owner=self.actor, created_by=self.actor)
        data = self.create_draft(place)
        self.url = '/api/drafts/' + data['draft_id'] + '/media/'
        uploaded = self.upload()
        self.assertEqual(uploaded.status_code, 200, uploaded.content)
        Place.objects.filter(pk=place.pk).update(content_version=place.content_version + 1)
        self.assertEqual(self.client.get(self.url).status_code, 409)
        self.assertEqual(self.client.get(uploaded.json()['media_manifest'][0]['url']).status_code, 409)
        self.assertEqual(self.upload(version=2).status_code, 409)
        self.assertEqual(self.manifest(2, []).status_code, 409)

    def test_volunteer_new_and_owned_scope_only(self):
        volunteer = get_user_model().objects.create_user(username='media-volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        client = Client()
        client.force_login(volunteer)
        data = self.create_draft(client=client)
        url = '/api/drafts/' + data['draft_id'] + '/media/'
        self.assertEqual(self.upload(client=client, url=url).status_code, 200)
        own = create_quality_place(created_by=volunteer, owner=None)
        owned = self.create_draft(own, client=client)
        own.owner = self.actor
        own.save(update_fields=['owner'])
        self.assertEqual(client.get('/api/drafts/' + owned['draft_id'] + '/media/').status_code, 403)
        self.assertEqual(client.get(self.url).status_code, 403)

    def test_bounded_saved_photo_controls_and_legacy_photo_survive(self):
        body = {'draft_id': self.draft['draft_id'], 'target_type': 'place', 'schema_version': 1,
            'expected_version': 1, 'fields': {'photo-clear': True, 'cover_photo-clear': False,
            'delete_gallery_ids': ['42'], 'gallery_order': '["saved:43","new:0"]'}}
        response = self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['fields']['gallery_order'], ['saved:43', 'new:0'])
        body['expected_version'] = 2
        body['fields']['delete_gallery_ids'] = ['../private/image.webp']
        self.assertEqual(self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json').status_code, 400)
        self.assertEqual(self.client.get(reverse('server_draft_photo', args=[self.draft['draft_id']])).status_code, 404)

    def test_csrf_is_required_for_upload_and_manifest(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.actor)
        self.assertEqual(self.upload(client=client).status_code, 403)
        self.assertEqual(self.manifest(1, [], client=client).status_code, 403)

    def test_volunteer_new_working_copies_visible_and_paginated(self):
        volunteer = get_user_model().objects.create_user(username='working-volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.client.force_login(volunteer)
        for index in range(14):
            server_drafts.save(user=volunteer, data={'target_type': 'place', 'schema_version': 1,
                'expected_version': 0, 'fields': {'name_az': f'Draft {index}'}})
        response = self.client.get(reverse('admin:volunteer_index'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context.get('working_drafts_page'))
        self.assertEqual(response.context['working_drafts_page'].paginator.count, 14)
        self.assertContains(response, 'draft_id=')
        self.assertEqual(len(response.context['working_drafts_page']), 12)
        page_two = self.client.get(reverse('admin:volunteer_index') + '?draft_page=2')
        self.assertEqual(len(page_two.context['working_drafts_page']), 2)

    def test_staff_config_uses_actor_and_server_field_allowlist(self):
        staff = get_user_model().objects.create_superuser(username='draft-admin', password='synthetic')
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:catalog_place_add') + '?type=permanent')
        self.assertEqual(response.status_code, 200)
        config = response.context.get('km_place_draft_config')
        self.assertIsNotNone(config)
        self.assertEqual(config['actorId'], staff.pk)
        self.assertEqual(config['sourceVersion'], 0)
        self.assertIn('pricing_plans', config['fields'])
        self.assertIn('_editor_base_signature', config['fields'])
        self.assertNotIn('is_active', config['fields'])
        self.assertEqual(len(config['baseSignature']), 64)

    def test_changed_candidate_conflicts_but_keeps_working_copy_visible(self):
        from catalog.models import VolunteerPlaceRevision
        from catalog.services.place_editor_drafts import working_draft_rows
        volunteer = get_user_model().objects.create_user(username='candidate-volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        place = create_quality_place(created_by=volunteer, owner=None)
        self.client.force_login(volunteer)
        response = self.client.get(reverse('admin:volunteer_edit', args=[place.pk]))
        self.assertEqual(response.status_code, 200)
        config = response.context['km_place_draft_config']
        data = {'target_type': 'place', 'target_id': place.pk, 'source_version': place.content_version,
            'schema_version': 1, 'expected_version': 0,
            'fields': {'name_az': 'Private unfinished', '_editor_base_signature': config['baseSignature']}}
        result = self.client.post(reverse('server_draft_collection'), json.dumps(data), content_type='application/json')
        self.assertEqual(result.status_code, 201, result.content)
        VolunteerPlaceRevision.objects.create(place=place, author=volunteer)
        identifier = result.json()['draft_id']
        self.assertEqual(self.client.get(reverse('server_draft_detail', args=[identifier])).status_code, 409)
        rows = list(working_draft_rows(user=volunteer, surface='volunteer'))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['needs_review'])
        self.assertEqual(rows[0]['title'], 'Private unfinished')
        listed = self.client.get(reverse('server_draft_collection')).json()['drafts']
        self.assertTrue(listed[0]['needs_review'])

    def test_retry_does_not_accept_a_future_version(self):
        identifier = str(uuid4())
        self.assertEqual(self.upload(identifier=identifier).status_code, 200)
        self.assertEqual(self.upload(version=999, identifier=identifier).status_code, 409)
        items = [{'id': identifier, 'role': 'main', 'order': 0}]
        self.assertEqual(self.manifest(2, items).status_code, 200)
        self.assertEqual(self.manifest(999, items).status_code, 409)

    def test_delete_private_draft_checks_actor_version_csrf_and_removes_only_private_files(self):
        result = self.upload()
        self.assertEqual(result.status_code, 200)
        url = reverse('server_draft_detail', args=[self.draft['draft_id']])
        foreign = Client()
        foreign.force_login(self.other)
        body = json.dumps({'expected_version': 2})
        self.assertEqual(foreign.delete(url, body, content_type='application/json').status_code, 403)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.actor)
        self.assertEqual(csrf.delete(url, body, content_type='application/json').status_code, 403)
        self.assertEqual(self.client.delete(url, json.dumps({'expected_version': 1}), content_type='application/json').status_code, 409)
        with self.captureOnCommitCallbacks(execute=True):
            deleted = self.client.delete(url, body, content_type='application/json')
        self.assertEqual(deleted.status_code, 200, deleted.content)
        self.assertFalse(ServerDraft.objects.filter(pk=self.draft['draft_id']).exists())
        self.assertFalse(list(Path(self.directory.name + '/private').rglob('*.webp')))
        self.assertEqual(Place.objects.count(), 0)

    def test_admin_private_draft_page_preserves_filters(self):
        staff = get_user_model().objects.create_superuser(username='list-admin', password='synthetic')
        self.client.force_login(staff)
        for index in range(14):
            server_drafts.save(user=staff, data={'target_type': 'place', 'schema_version': 1,
                'expected_version': 0, 'fields': {'name_az': f'Private {index}'}})
        response = self.client.get(reverse('admin:catalog_place_changelist') + '?draft_page=2&q=Private')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['working_drafts_page']), 2)
        self.assertContains(response, 'data-draft-delete')
        self.assertIn('q=Private', response.context['working_drafts_previous_url'])
        self.assertNotIn('draft_page', response.context['cl'].params)

    def test_stale_private_copy_can_be_discarded_but_materialized_copy_cannot(self):
        place = create_quality_place(owner=self.actor, created_by=self.actor)
        data = self.create_draft(place)
        Place.objects.filter(pk=place.pk).update(content_version=place.content_version + 1)
        url = reverse('server_draft_detail', args=[data['draft_id']])
        self.assertEqual(self.client.get(url).status_code, 409)
        self.assertEqual(self.client.delete(url, json.dumps({'expected_version': 1}), content_type='application/json').status_code, 200)
        self.assertTrue(Place.objects.filter(pk=place.pk).exists())
        ServerDraft.objects.filter(pk=self.draft['draft_id']).update(materialized_place=place)
        url = reverse('server_draft_detail', args=[self.draft['draft_id']])
        self.assertEqual(self.client.delete(url, json.dumps({'expected_version': 1}), content_type='application/json').status_code, 409)

    def test_caption_metadata_has_bounded_keys_and_lengths(self):
        body = {'draft_id': self.draft['draft_id'], 'target_type': 'place', 'schema_version': 1,
            'expected_version': 1, 'fields': {'gallery_captions': {'saved:42': 'Entrance', 'new:0': 'Play room'}}}
        response = self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json')
        self.assertEqual(response.status_code, 200, response.content)
        body['expected_version'] = 2
        for value in ({'../file': 'Caption'}, {'new:0': 'a' * 256}, {'new:0': {'bad': 'type'}}):
            body['fields']['gallery_captions'] = value
            self.assertEqual(self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json').status_code, 400)

    def test_volunteer_explicit_save_closes_only_matching_private_copy(self):
        from django import forms
        volunteer = get_user_model().objects.create_user(username='save-volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.client.force_login(volunteer)
        draft = self.create_draft(client=self.client)
        other = self.create_draft(client=self.client)
        url = reverse('admin:volunteer_add')
        form = self.client.get(url).context['form']
        data = {name: form[name].value() if form[name].value() is not None else ''
            for name, field in form.fields.items() if not isinstance(field, forms.FileField)}
        data.update(name_az='Saved working copy', category='EDU', action='draft',
            server_draft_id=draft['draft_id'], server_draft_version=draft['version'])
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.content[:1000])
        place = Place.objects.get(created_by=volunteer)
        self.assertEqual(ServerDraft.objects.get(pk=draft['draft_id']).materialized_place_id, place.pk)
        self.assertIsNone(ServerDraft.objects.get(pk=other['draft_id']).materialized_place_id)
        self.assertFalse(place.is_active)

    def test_close_version_conflict_preserves_newer_work(self):
        place = create_quality_place(owner=self.actor, created_by=self.actor)
        draft = ServerDraft.objects.get(pk=self.draft['draft_id'])
        self.assertFalse(server_drafts.mark_explicit_save(user=self.actor, draft_id=draft.pk,
            expected_version='0', place=place, target_id=None))
        draft.refresh_from_db()
        self.assertIsNone(draft.materialized_place_id)

    def test_lost_text_reply_retry_is_idempotent_only_for_exact_last_payload(self):
        body = {'draft_id': self.draft['draft_id'], 'target_type': 'place', 'schema_version': 1,
            'expected_version': 1, 'fields': {'name_az': 'Working copy'}}
        first = self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json')
        self.assertEqual(first.status_code, 200, first.content)
        retry = self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json')
        self.assertEqual(retry.status_code, 200, retry.content)
        self.assertEqual(retry.json()['version'], 2)
        body['fields']['name_az'] = 'Different stale input'
        self.assertEqual(self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json').status_code, 409)
        self.assertEqual(ServerDraft.objects.get(pk=self.draft['draft_id']).fields['name_az'], 'Working copy')
        # An intervening media write advances the CAS; do not accept an older text packet.
        self.assertEqual(self.upload(version=2).status_code, 200)
        body['fields']['name_az'] = 'Working copy'
        self.assertEqual(self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json').status_code, 409)

    def test_media_selection_intent_survives_before_any_upload_with_strict_shape(self):
        main, gallery = str(uuid4()), str(uuid4())
        selection = [{'id': main, 'role': 'main', 'order': 0}, {'id': gallery, 'role': 'gallery', 'order': 0}]
        body = {'draft_id': self.draft['draft_id'], 'target_type': 'place', 'schema_version': 1,
            'expected_version': 1, 'fields': {'_draft_media_selection': selection}}
        result = self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json')
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()['fields']['_draft_media_selection'], selection)
        self.assertEqual(result.json()['media_manifest'], [])
        body['expected_version'] = 2
        invalid = [[selection[0], selection[0]], [{'id': gallery, 'role': 'gallery', 'order': 1}],
            [{'id': '../file', 'role': 'main', 'order': 0}], [{'id': main, 'role': 'main', 'order': 0, 'path': 'private'}],
            [{'id': str(uuid4()), 'role': 'gallery', 'order': n} for n in range(11)]]
        for value in invalid:
            body['fields']['_draft_media_selection'] = value
            self.assertEqual(self.client.post(reverse('server_draft_collection'), json.dumps(body), content_type='application/json').status_code, 400)
        self.assertEqual(ServerDraft.objects.get(pk=self.draft['draft_id']).version, 2)


class DraftMediaConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = override_settings(MEDIA_ROOT=self.directory.name + '/public',
                                       PRIVATE_DRAFT_MEDIA_ROOT=self.directory.name + '/private')
        self.config.enable()
        self.addCleanup(self.config.disable)
        self.actor = get_user_model().objects.create_user(username='media-race')
        self.draft = server_drafts.save(user=self.actor, data={
            'target_type': 'place', 'schema_version': 1, 'expected_version': 0, 'fields': {}})
        output = BytesIO()
        Image.new('RGB', (20, 20), 'blue').save(output, 'PNG')
        self.bytes = output.getvalue()

    def run_uploads(self, identifiers):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections
        barrier = Barrier(2)

        def upload(identifier):
            close_old_connections()
            barrier.wait(timeout=10)
            try:
                result = server_drafts.upload_media(user=self.actor, draft_id=self.draft.pk,
                    expected_version=1, media_id=identifier,
                    file=SimpleUploadedFile('race.png', self.bytes, content_type='image/png'))
                return ('saved', result.version)
            except server_drafts.DraftConflict:
                return ('conflict', None)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(upload, identifiers))

    def test_simultaneous_same_upload_id_has_one_file_and_one_increment(self):
        identifier = str(uuid4())
        self.assertEqual(self.run_uploads([identifier, identifier]), [('saved', 2), ('saved', 2)])
        self.draft.refresh_from_db()
        self.assertEqual(len(self.draft.media_manifest), 1)
        self.assertEqual(len(list(Path(self.directory.name + '/private').glob('**/*.webp'))), 1)

    def test_simultaneous_different_files_with_same_version_conflict(self):
        results = self.run_uploads([str(uuid4()), str(uuid4())])
        self.assertEqual(sorted(status for status, version in results), ['conflict', 'saved'])
        self.draft.refresh_from_db()
        self.assertEqual(len(self.draft.media_manifest), 1)
        self.assertEqual(self.draft.version, 2)
