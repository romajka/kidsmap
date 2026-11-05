"""A redundant legacy claim can close without granting or replacing ownership."""
import importlib.util
import json
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command, get_commands
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone

from catalog.models import Place, PlaceOwnershipRequest, PlaceOwnershipRequestAudit, VolunteerPlaceRevision
from catalog.services import publication
from catalog.testcases.utils import create_ready_place


class LegacyPlaceRequestReconciliationTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('fulfilled-owner')
        self.other = users.objects.create_user('unrelated-owner')
        self.staff = users.objects.create_superuser('reconcile-staff', 'staff@example.invalid', 'fictional')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner, district='baku_nasimi')
        self.item = PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.owner, request_kind='CLAIM')
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(base_owner_id=None, base_ownership_version=None)
        Place.objects.filter(pk=self.place.pk).update(moderated_by=self.staff, moderated_at=timezone.now(), published_at=timezone.now())
        self.item.refresh_from_db(); self.place.refresh_from_db()

    def service(self):
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.place_request_reconciliation'),
                             'Missing safe legacy request reconciliation service')
        from catalog.services import place_request_reconciliation
        return place_request_reconciliation

    def test_plan_is_read_only_and_does_not_disclose_identity(self):
        service = self.service()
        with CaptureQueriesContext(connection) as queries:
            plan = service.plan_request(self.item.pk)
        self.assertTrue(plan['eligible'])
        self.assertEqual(plan['reason'], 'already_fulfilled_claim')
        self.assertEqual(plan['request_id'], self.item.pk)
        self.assertIn('token', plan)
        self.assertNotIn(self.owner.username, json.dumps(plan))
        self.assertNotIn('applicant_id', plan)
        self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')) for q in queries))

    def test_apply_closes_only_reviewed_request_without_granting_rights(self):
        service = self.service(); plan = service.plan_request(self.item.pk)
        before = (self.place.owner_id, self.place.ownership_version, self.place.content_version, self.place.updated_at)
        original_audits = self.item.audit_entries.count()
        service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Verified legacy creation history')
        self.item.refresh_from_db(); self.place.refresh_from_db()
        self.assertEqual(self.item.status, 'APPROVED')
        self.assertEqual(self.item.request_kind, 'CLAIM')
        self.assertIsNone(self.item.base_ownership_version)
        self.assertEqual((self.place.owner_id, self.place.ownership_version, self.place.content_version, self.place.updated_at), before)
        self.assertEqual(self.item.audit_entries.count(), original_audits + 1)
        self.assertIn('Verified legacy creation history', self.item.moderation_note)
        self.assertEqual(self.item.moderated_by_id, self.staff.pk)

    def test_published_place_alone_never_confirms_foreign_claim(self):
        service = self.service()
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(applicant=self.other)
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])

    def test_inactive_or_transferred_creator_requires_manual_review(self):
        service = self.service()
        self.owner.is_active = False; self.owner.save(update_fields=['is_active'])
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])
        self.owner.is_active = True; self.owner.save(update_fields=['is_active'])
        Place.objects.filter(pk=self.place.pk).update(created_by=self.other)
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])

    def test_real_pending_changes_are_not_discarded(self):
        service = self.service()
        revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'description_az': 'A genuine pending change'}, schema_version=1,
            expected_version=self.place.content_version)
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(revision.payload, {'description_az': 'A genuine pending change'})

    def test_missing_or_older_moderation_evidence_requires_manual_review(self):
        service = self.service()
        Place.objects.filter(pk=self.place.pk).update(moderated_at=None)
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])
        Place.objects.filter(pk=self.place.pk).update(moderated_at=self.item.created_at - timedelta(days=1))
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])

    def test_competing_claim_or_publication_request_requires_manual_review(self):
        service = self.service()
        PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.other, request_kind='CLAIM')
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(request_kind='PUBLICATION')
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])

    def test_stale_token_and_unauthorized_actor_cannot_close_request(self):
        service = self.service(); plan = service.plan_request(self.item.pk)
        with self.assertRaises(PermissionDenied):
            service.apply_request(actor=self.owner, request_id=self.item.pk, token=plan['token'], note='Not a reviewer')
        Place.objects.filter(pk=self.place.pk).update(content_version=self.place.content_version + 1)
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Stale plan')
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'PENDING')

    def test_other_request_token_and_blank_reason_are_denied(self):
        service = self.service(); plan = service.plan_request(self.item.pk)
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note=' ')
        other_place = create_ready_place(owner=self.owner, created_by=self.owner)
        other = PlaceOwnershipRequest.objects.create(place=other_place, applicant=self.owner, request_kind='CLAIM')
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=other.pk, token=plan['token'], note='Wrong identity')
        self.item.refresh_from_db(); other.refresh_from_db()
        self.assertEqual((self.item.status, other.status), ('PENDING', 'PENDING'))

    def test_failed_audit_rolls_back_closure_and_replay_does_not_duplicate(self):
        service = self.service(); plan = service.plan_request(self.item.pk)
        with patch.object(PlaceOwnershipRequestAudit, 'log_event', side_effect=RuntimeError('Audit unavailable')):
            with self.assertRaises(RuntimeError):
                service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Reviewed')
        self.item.refresh_from_db(); self.assertEqual(self.item.status, 'PENDING')
        service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Reviewed')
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Replay')
        self.assertEqual(self.item.audit_entries.filter(action='APPROVED').count(), 1)

    def test_command_defaults_to_dry_run_and_apply_requires_explicit_identity(self):
        self.assertIn('reconcile_place_requests', get_commands(), 'Missing reviewable default-dry-run command')
        output = StringIO()
        call_command('reconcile_place_requests', request_ids=[self.item.pk], stdout=output)
        plan = json.loads(output.getvalue())['results'][0]
        self.assertTrue(plan['eligible'])
        self.item.refresh_from_db(); self.assertEqual(self.item.status, 'PENDING')
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('reconcile_place_requests', apply=True, request_ids=[self.item.pk], stdout=StringIO())
        call_command('reconcile_place_requests', apply=True, request_ids=[self.item.pk],
                     token=plan['token'], actor_id=self.staff.pk, note='Explicit reviewed closure', stdout=StringIO())
        self.item.refresh_from_db(); self.assertEqual(self.item.status, 'APPROVED')


    def test_plan_cannot_apply_after_request_note_changes_without_version_increment(self):
        service = self.service(); plan = service.plan_request(self.item.pk)
        PlaceOwnershipRequest.objects.filter(pk=self.item.pk).update(note='New evidence requiring another review')
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Old review')
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'PENDING')

    def test_expired_plan_and_withdrawn_publication_are_refused(self):
        import time
        service = self.service(); plan = service.plan_request(self.item.pk)
        with patch('django.core.signing.time.time', return_value=time.time() + 2 * 24 * 60 * 60):
            with self.assertRaises(ValidationError):
                service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Expired')
        Place.objects.filter(pk=self.place.pk).update(is_active=False)
        self.assertFalse(service.plan_request(self.item.pk)['eligible'])
        with self.assertRaises(ValidationError):
            service.apply_request(actor=self.staff, request_id=self.item.pk, token=plan['token'], note='Withdrawn')
        self.item.refresh_from_db()
        self.assertEqual(self.item.status, 'PENDING')
