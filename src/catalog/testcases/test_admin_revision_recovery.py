"""An explicit restart preserves conflicting work without overwriting live content."""
import json
from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, PlaceChangeAudit, VolunteerPlaceRevision
from catalog.services.volunteer_places import base_token, live_snapshot
from catalog.testcases.utils import create_ready_place


class AdminRevisionRecoveryTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.volunteer = users.objects.create_user('recovery-volunteer', is_staff=True)
        self.volunteer.groups.add(Group.objects.create(name='KidsMap Volunteers'))
        self.admin = users.objects.create_superuser('recovery-admin', '', 'test-password')
        self.place = create_ready_place(created_by=self.volunteer, owner=None)
        self.revision = VolunteerPlaceRevision.objects.create(
            place=self.place, author=self.volunteer, status='pending',
            payload={'name_az': 'Unsaved proposed name', 'description_ru': 'Preserve these proposed details'},
            base_snapshot=live_snapshot(self.place), review_note='Previous review note',
        )
        Place.objects.filter(pk=self.place.pk).update(name_az='Current administrator correction')
        self.place.refresh_from_db()
        self.url = reverse('admin:catalog_place_change', args=[self.place.pk])
        self.client.force_login(self.admin)

    def restart_data(self):
        return {'action': 'restart', 'revision_version': self.revision.version,
                'base_token': base_token(self.place)}

    def assert_preserved(self, payload, version):
        self.revision.refresh_from_db()
        self.assertEqual(self.revision.payload, payload)
        self.assertEqual(self.revision.version, version)
        self.assertFalse(PlaceChangeAudit.objects.filter(field_name='working_revision_restart').exists())

    def test_conflict_editor_offers_explicit_restart_without_writes(self):
        old_payload = deepcopy(self.revision.payload)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-revision-restart')
        self.assertContains(response, 'value="restart"')
        self.assert_preserved(old_payload, self.revision.version)

    def test_admin_restart_archives_old_work_and_preserves_author_and_live_content(self):
        old_payload = deepcopy(self.revision.payload)
        old_base = deepcopy(self.revision.base_snapshot)
        old_version = self.revision.version
        old_live = live_snapshot(self.place)
        response = self.client.post(self.url, self.restart_data())
        self.assertEqual(response.status_code, 302)
        self.revision.refresh_from_db()
        self.place.refresh_from_db()
        self.assertEqual(live_snapshot(self.place), old_live)
        self.assertEqual(self.revision.payload, {})
        self.assertEqual(self.revision.status, 'draft')
        self.assertEqual(self.revision.version, old_version + 1)
        self.assertEqual(self.revision.author, self.volunteer)
        self.assertEqual(self.revision.base_snapshot['name_az'], self.place.name_az)
        audit = PlaceChangeAudit.objects.get(field_name='working_revision_restart')
        self.assertEqual(audit.changed_by, self.admin)
        self.assertEqual(audit.source, PlaceChangeAudit.SOURCE_ADMIN)
        archived = json.loads(audit.old_value)
        self.assertEqual(archived['payload'], old_payload)
        self.assertEqual(archived['base_snapshot'], old_base)
        self.assertEqual(archived['status'], 'pending')
        self.assertEqual(archived['author_id'], self.volunteer.pk)
        self.assertEqual(archived['review_note'], 'Previous review note')
        self.assertEqual(json.loads(audit.new_value)['version'], old_version + 1)
        editor = self.client.get(self.url)
        self.assertEqual(editor.context['form']['name_az'].value(), self.place.name_az)
        self.assertFalse(editor.context['conflict'])

    def test_stale_revision_version_cannot_restart(self):
        data = self.restart_data()
        self.revision.version += 1
        self.revision.save(update_fields=['version'])
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assert_preserved(self.revision.payload, self.revision.version)

    def test_changed_live_content_after_confirmation_cannot_restart(self):
        data = self.restart_data()
        Place.objects.filter(pk=self.place.pk).update(address='A newer address')
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assert_preserved(self.revision.payload, self.revision.version)

    def test_missing_or_forged_base_token_cannot_restart(self):
        for token in ('', 'forged'):
            with self.subTest(token=token):
                data = self.restart_data()
                data['base_token'] = token
                self.assertEqual(self.client.post(self.url, data).status_code, 302)
                self.assert_preserved(self.revision.payload, self.revision.version)

    def test_unconflicted_revision_cannot_be_discarded_by_restart(self):
        self.revision.base_snapshot = live_snapshot(self.place)
        self.revision.save(update_fields=['base_snapshot'])
        self.assertEqual(self.client.post(self.url, self.restart_data()).status_code, 302)
        self.assert_preserved(self.revision.payload, self.revision.version)

    def test_anonymous_staff_without_permission_and_other_volunteer_denied(self):
        payload, version = deepcopy(self.revision.payload), self.revision.version
        self.client.logout()
        self.assertEqual(self.client.post(self.url, self.restart_data()).status_code, 302)
        staff = get_user_model().objects.create_user('limited-recovery-staff', is_staff=True)
        other = get_user_model().objects.create_user('other-recovery-volunteer', is_staff=True)
        other.groups.add(self.volunteer.groups.get())
        for user in (staff, other):
            self.client.force_login(user)
            self.assertEqual(self.client.post(self.url, self.restart_data()).status_code, 403)
        self.assert_preserved(payload, version)

    def test_volunteer_restart_uses_same_archive_and_token_protection(self):
        self.client.force_login(self.volunteer)
        url = reverse('admin:volunteer_edit', args=[self.place.pk])
        old_payload = deepcopy(self.revision.payload)
        response = self.client.post(url, self.restart_data())
        self.assertEqual(response.status_code, 302)
        audit = PlaceChangeAudit.objects.get(field_name='working_revision_restart')
        self.assertEqual(audit.source, PlaceChangeAudit.SOURCE_VOLUNTEER)
        self.assertEqual(json.loads(audit.old_value)['payload'], old_payload)

    def test_audit_failure_rolls_back_the_restart(self):
        from catalog.services.volunteer_places import restart_working_revision
        with patch.object(PlaceChangeAudit.objects, 'create', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(RuntimeError):
                restart_working_revision(user=self.admin, place_id=self.place.pk,
                    version=self.revision.version, token=base_token(self.place), source=PlaceChangeAudit.SOURCE_ADMIN)
        self.assert_preserved(self.revision.payload, self.revision.version)

    def test_revoked_admin_permission_is_checked_again_in_service(self):
        from django.core.exceptions import PermissionDenied
        from catalog.services.volunteer_places import restart_working_revision
        get_user_model().objects.filter(pk=self.admin.pk).update(is_superuser=False, is_staff=False)
        with self.assertRaises(PermissionDenied):
            restart_working_revision(user=self.admin, place_id=self.place.pk,
                version=self.revision.version, token=base_token(self.place), source=PlaceChangeAudit.SOURCE_ADMIN)
        self.assert_preserved(self.revision.payload, self.revision.version)

    def test_other_volunteer_cannot_use_restart_service_on_this_place(self):
        from django.core.exceptions import PermissionDenied
        from catalog.services.volunteer_places import restart_working_revision
        other = get_user_model().objects.create_user('foreign-recovery-volunteer', is_staff=True)
        other.groups.add(self.volunteer.groups.get())
        with self.assertRaises(PermissionDenied):
            restart_working_revision(user=other, place_id=self.place.pk,
                version=self.revision.version, token=base_token(self.place), source=PlaceChangeAudit.SOURCE_VOLUNTEER)
        self.assert_preserved(self.revision.payload, self.revision.version)
