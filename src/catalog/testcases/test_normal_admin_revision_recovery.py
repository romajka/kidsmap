"""Normal admin must explicitly recover stale candidates without discarding evidence."""
import json
from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.volunteer_places import base_token, live_snapshot, token_matches
from catalog.testcases.utils import create_ready_place


class NormalAdminRevisionRecoveryTests(TestCase):
    def setUp(self):
        self.admin=get_user_model().objects.create_superuser('normal-recovery-admin','','synthetic')
        self.place=create_ready_place(created_by=self.admin)
        self.photo=default_storage.save('places/recovery-candidate.txt',ContentFile(b'preserve candidate bytes'))
        self.revision=publication.propose(actor=self.admin,target_type='place',target_id=self.place.pk,
            patch={'name_az':'Candidate name','photo':self.photo},schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version,submit=False)
        Place.objects.filter(pk=self.place.pk).update(name_az='Current name')
        self.place.refresh_from_db()
        self.url=reverse('admin:catalog_place_change',args=[self.place.pk])
        self.client.force_login(self.admin)

    def data(self):
        return {'_restart_working_revision':'1','revision_version':self.revision.version,
                'base_token':base_token(self.place)}

    def assert_preserved(self):
        self.revision.refresh_from_db()
        self.assertEqual(self.revision.payload['name_az'],'Candidate name')
        self.assertFalse(PlaceChangeAudit.objects.filter(field_name='working_revision_restart').exists())
        self.assertTrue(default_storage.exists(self.photo))

    def test_get_offers_standalone_recovery_with_current_live_token_without_writes(self):
        response=self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'data-normal-revision-restart')
        recovery=response.context['km_place_revision_recovery']
        self.assertTrue(token_matches(recovery['base_token'],self.place))
        html=response.content.decode()
        self.assertLess(html.index('data-normal-revision-restart'),html.index('id="place_form"'))
        self.assert_preserved()

    def test_explicit_restart_archives_payload_and_photo_and_keeps_live_unchanged(self):
        old_payload=deepcopy(self.revision.payload)
        old_live=live_snapshot(self.place)
        with patch.object(default_storage,'delete') as delete:
            response=self.client.post(self.url,self.data())
            self.assertEqual(response.status_code,302)
            delete.assert_not_called()
        self.revision.refresh_from_db();self.place.refresh_from_db()
        self.assertEqual(live_snapshot(self.place),old_live)
        self.assertEqual(self.revision.payload,{})
        self.assertEqual(self.revision.status,'draft')
        self.assertEqual(self.revision.author_id,self.admin.pk)
        audit=PlaceChangeAudit.objects.get(field_name='working_revision_restart')
        self.assertEqual(json.loads(audit.old_value)['payload'],old_payload)
        self.assertTrue(default_storage.exists(self.photo))
        response=self.client.get(self.url)
        self.assertNotContains(response,'data-normal-revision-restart')
        # A fresh edit can now save through the ordinary publication service.
        revision=publication.propose(actor=self.admin,target_type='place',target_id=self.place.pk,
            patch={'name_az':'Recovered edit'},schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version,revision_version=self.revision.version,submit=False)
        self.assertEqual(revision.payload['name_az'],'Recovered edit')

    def test_stale_version_and_forged_token_do_not_restart(self):
        for overrides in ({'revision_version':0},{'base_token':'forged'},{'base_token':''}):
            with self.subTest(overrides=overrides):
                self.assertEqual(self.client.post(self.url,{**self.data(),**overrides}).status_code,302)
                self.assert_preserved()

    def test_changed_live_after_confirmation_does_not_restart(self):
        data=self.data()
        Place.objects.filter(pk=self.place.pk).update(address='Concurrent address')
        self.assertEqual(self.client.post(self.url,data).status_code,302)
        self.assert_preserved()

    def test_ordinary_get_and_draft_post_never_reset_conflict_implicitly(self):
        self.client.get(self.url)
        self.client.post(self.url,{'_save_draft':'1'})
        self.assert_preserved()

    def test_anonymous_limited_staff_and_volunteer_cannot_restart_normal_admin(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url,self.data()).status_code,302)
        limited=get_user_model().objects.create_user('normal-limited',is_staff=True)
        volunteer=get_user_model().objects.create_user('normal-volunteer',is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        for user in (limited,volunteer):
            self.client.force_login(user)
            self.assertEqual(self.client.post(self.url,self.data()).status_code,403)
        self.assert_preserved()
