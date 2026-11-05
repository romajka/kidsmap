"""Publishing a card also completes only the request for that approved version."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place, PlaceOwnershipRequest, PlaceOwnershipRequestAudit, VolunteerPlaceRevision
from catalog.services import publication
from catalog.services.organization_ownership import moderate_place_request
from catalog.testcases.utils import create_ready_place


class PublicationRequestCompletionTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.owner = users.objects.create_user('request-owner')
        self.other = users.objects.create_user('request-other')
        self.staff = users.objects.create_superuser('request-staff', 'staff@example.invalid', 'fictional')
        self.place = create_ready_place(owner=self.owner, created_by=self.owner, district='baku_nasimi')

    def propose(self):
        previous = VolunteerPlaceRevision.objects.filter(place=self.place).first()
        return publication.propose(
            actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'description_az': 'Yeni dərslər və yaşa uyğun oyunlar.'},
            schema_version=1, expected_version=self.place.content_version,
            revision_version=previous.version if previous else 0)

    def request(self, **kwargs):
        return PlaceOwnershipRequest.objects.create(
            place=self.place, applicant=kwargs.pop('applicant', self.owner),
            request_kind=kwargs.pop('request_kind', 'PUBLICATION'), **kwargs)

    def approve(self, revision, **kwargs):
        return publication.review(actor=self.staff, revision_id=revision.pk,
                                  version=revision.version, approve=True, **kwargs)

    def approval_audits(self, item):
        return PlaceOwnershipRequestAudit.objects.filter(ownership_request=item, action='APPROVED')

    def assert_approved(self, item, note=''):
        item.refresh_from_db()
        self.assertEqual(item.status, 'APPROVED')
        self.assertEqual(item.moderated_by_id, self.staff.pk)
        self.assertIsNotNone(item.moderated_at)
        self.assertEqual(item.moderation_note, note)
        self.assertEqual(self.approval_audits(item).count(), 1)

    def test_revision_approval_completes_matching_request(self):
        revision = self.propose(); item = self.request()
        self.approve(revision, note='Reviewed together')
        self.assert_approved(item, 'Reviewed together')
        self.place.refresh_from_db()
        self.assertEqual(self.place.description_az, 'Yeni dərslər və yaşa uyğun oyunlar.')

    def test_publish_card_completes_request_and_replay_does_not_duplicate_audit(self):
        self.propose(); item = self.request()
        publication.publish(actor=self.staff, place_id=self.place.pk,
                            expected_version=self.place.content_version)
        self.assert_approved(item)
        self.place.refresh_from_db()
        publication.publish(actor=self.staff, place_id=self.place.pk,
                            expected_version=self.place.content_version)
        self.assert_approved(item)

    def test_publish_without_revision_completes_exact_live_request(self):
        item = self.request()
        publication.publish(actor=self.staff, place_id=self.place.pk,
                            expected_version=self.place.content_version)
        self.assert_approved(item)

    def test_request_entry_preserves_note_and_has_only_one_decision_audit(self):
        self.propose(); item = self.request()
        result = moderate_place_request(actor=self.staff, request_id=item.pk,
                                        new_status='APPROVED', note='Confirmed version')
        self.assertEqual(result.status, 'APPROVED')
        self.assert_approved(item, 'Confirmed version')

    def test_unrelated_claim_or_other_applicant_is_not_approved(self):
        revision = self.propose()
        claim = self.request(request_kind='CLAIM')
        other = self.request(applicant=self.other)
        self.approve(revision)
        for item in (claim, other):
            item.refresh_from_db()
            self.assertEqual(item.status, 'PENDING')
            self.assertFalse(self.approval_audits(item).exists())
        self.place.refresh_from_db()
        self.assertEqual(self.place.owner_id, self.owner.pk)

    def test_stale_request_versions_are_not_auto_approved(self):
        for field in ('base_content_version', 'base_candidate_version', 'base_ownership_version', 'base_owner_id'):
            with self.subTest(field=field):
                revision = self.propose(); item = self.request()
                PlaceOwnershipRequest.objects.filter(pk=item.pk).update(**{field: 999999})
                self.approve(revision)
                item.refresh_from_db()
                self.assertEqual(item.status, 'PENDING')
                self.assertFalse(self.approval_audits(item).exists())
                item.delete(); self.place.refresh_from_db()
                # Next proposal must actually differ from the now approved text.
                Place.objects.filter(pk=self.place.pk).update(description_az='Əvvəlki təsvir')
                self.place.refresh_from_db()

    def test_unsent_draft_request_is_not_completed_by_live_publication(self):
        revision = self.propose()
        type(revision).objects.filter(pk=revision.pk).update(status='draft')
        item = self.request()
        publication.publish(actor=self.staff, place_id=self.place.pk,
                            expected_version=self.place.content_version)
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')
        self.assertFalse(self.approval_audits(item).exists())

    def test_request_approval_cannot_publish_live_data_instead_of_unsent_candidate(self):
        revision = self.propose()
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='draft')
        item = self.request()
        with self.assertRaises(ValidationError):
            moderate_place_request(actor=self.staff, request_id=item.pk, new_status='APPROVED')
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')

    def test_failed_audit_rolls_back_approval_card_and_revision(self):
        revision = self.propose(); item = self.request()
        before = self.place.description_az
        with patch.object(PlaceOwnershipRequestAudit, 'log_event', side_effect=RuntimeError('audit unavailable')):
            with self.assertRaises(RuntimeError):
                self.approve(revision)
        self.place.refresh_from_db(); revision.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(self.place.description_az, before)
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(item.status, 'PENDING')

    def test_denied_review_leaves_pending_but_return_closes_matching_request(self):
        revision = self.propose(); item = self.request()
        with self.assertRaises(PermissionDenied):
            publication.review(actor=self.owner, revision_id=revision.pk,
                               version=revision.version, approve=True)
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')
        publication.review(actor=self.staff, revision_id=revision.pk,
                           version=revision.version, approve=False, note='Needs correction')
        item.refresh_from_db()
        self.assertEqual(item.status, 'REJECTED')
        self.assertEqual(item.moderation_note, 'Needs correction')

    def test_source_conflict_never_completes_request(self):
        revision = self.propose(); item = self.request()
        Place.objects.filter(pk=self.place.pk).update(description_az='Concurrent change')
        with self.assertRaises(ValidationError):
            self.approve(revision)
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')

    def test_publish_from_actual_admin_form_completes_reviewed_request(self):
        self.propose(); item = self.request()
        self.publish_admin_form()
        self.assert_approved(item)

    def test_admin_form_publish_does_not_complete_preexisting_stale_request(self):
        self.propose(); item = self.request()
        PlaceOwnershipRequest.objects.filter(pk=item.pk).update(base_candidate_version=999999)
        self.publish_admin_form()
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')
        self.assertFalse(self.approval_audits(item).exists())

    def publish_admin_form(self, action="_publish_place"):
        self.client.force_login(self.staff)
        url = reverse('admin:catalog_place_change', args=[self.place.pk])
        page = self.client.get(url)
        form = page.context['adminform'].form
        data = {}
        def carry(bound):
            for field in bound:
                if isinstance(field.field, forms.FileField):
                    continue
                value = field.value()
                if isinstance(field.field, forms.BooleanField):
                    if value: data[field.html_name] = 'on'
                elif value is not None:
                    data[field.html_name] = value
        carry(form)
        for inline in page.context['inline_admin_formsets']:
            carry(inline.formset.management_form)
            for inline_form in inline.formset.forms:
                carry(inline_form)
        data[action] = '1'
        response = self.client.post(url, data)
        if response.status_code == 200:
            self.fail(str(response.context['adminform'].form.errors))
        self.assertEqual(response.status_code, 302)


    def test_unchanged_admin_save_preserves_approved_decision(self):
        revision = self.propose()
        approved = self.approve(revision, note='Reviewed content')
        before = (approved.version, approved.reviewed_by_id, approved.review_note, approved.moderated_at)
        self.publish_admin_form(action='_save')
        approved.refresh_from_db()
        self.assertEqual(approved.status, 'approved')
        self.assertEqual((approved.version, approved.reviewed_by_id, approved.review_note, approved.moderated_at), before)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)

    def test_unchanged_published_place_without_revision_is_not_pending(self):
        publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={}, schema_version=1, expected_version=self.place.content_version)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place, status='pending').exists())
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)

    def test_unpublished_place_can_submit_empty_patch_for_first_publication(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False)
        revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={}, schema_version=1, expected_version=self.place.content_version)
        self.assertEqual(revision.status, 'pending')
        self.approve(revision)
        self.place.refresh_from_db()
        self.assertTrue(self.place.is_public)

    def test_unchanged_save_keeps_real_pending_candidate(self):
        revision = self.propose()
        saved = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={}, schema_version=1, expected_version=self.place.content_version,
            revision_version=revision.version)
        self.assertEqual(saved.status, 'pending')
        self.assertEqual(saved.payload, {'description_az': 'Yeni dərslər və yaşa uyğun oyunlar.'})
        self.place.refresh_from_db()
        self.assertNotEqual(self.place.description_az, saved.payload['description_az'])

    def test_empty_pending_edit_leaves_queue_after_actual_admin_save(self):
        revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={}, schema_version=1, expected_version=self.place.content_version)
        VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status='pending')
        before = (self.place.owner_id, self.place.ownership_version, self.place.content_version)
        self.publish_admin_form(action='_save')
        revision.refresh_from_db(); self.place.refresh_from_db()
        self.assertEqual(revision.status, 'draft')
        self.assertEqual(revision.payload, {})
        self.assertTrue(self.place.is_public)
        self.assertEqual((self.place.owner_id, self.place.ownership_version, self.place.content_version), before)

    def test_request_rejection_also_rejects_exact_pending_candidate(self):
        revision = self.propose(); item = self.request()
        moderate_place_request(actor=self.staff, request_id=item.pk, new_status='REJECTED', note='Not accepted')
        revision.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(revision.status, 'declined')
        self.assertEqual(revision.review_note, 'Not accepted')
        self.assertEqual(item.status, 'REJECTED')
        self.assertEqual(item.audit_entries.filter(action='REJECTED').count(), 1)

    def test_stale_request_rejection_does_not_reject_new_candidate(self):
        revision = self.propose(); item = self.request()
        PlaceOwnershipRequest.objects.filter(pk=item.pk).update(base_candidate_version=999999)
        moderate_place_request(actor=self.staff, request_id=item.pk, new_status='REJECTED', note='Obsolete request')
        revision.refresh_from_db(); item.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(item.status, 'REJECTED')

    def test_candidate_return_does_not_reject_claim_or_other_applicant(self):
        revision = self.propose()
        claim = self.request(request_kind='CLAIM')
        other = self.request(applicant=self.other)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
                           approve=False, note='Needs correction')
        for item in (claim, other):
            item.refresh_from_db()
            self.assertEqual(item.status, 'PENDING')

    def test_return_resubmit_approve_keeps_old_request_terminal(self):
        revision = self.propose(); item = self.request()
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
                           approve=False, note='Needs correction')
        revision.refresh_from_db()
        next_revision = publication.propose(actor=self.owner, target_type='place', target_id=self.place.pk,
            patch={'description_az': 'Düzəldilmiş təsvir'}, schema_version=1,
            expected_version=self.place.content_version, revision_version=revision.version)
        self.approve(next_revision)
        item.refresh_from_db(); self.place.refresh_from_db()
        self.assertEqual(item.status, 'REJECTED')
        self.assertEqual(item.moderation_note, 'Needs correction')
        self.assertTrue(self.place.is_public)
        self.assertEqual(self.place.description_az, 'Düzəldilmiş təsvir')
        self.assertFalse(PlaceOwnershipRequest.objects.filter(place=self.place, status='PENDING').exists())


    def test_failed_rejection_audit_rolls_back_candidate_request_and_notification(self):
        from catalog.models import WorkflowNotification
        revision = self.propose(); item = self.request()
        before_version = revision.version
        with patch.object(PlaceOwnershipRequestAudit, 'log_event', side_effect=RuntimeError('Audit unavailable')):
            with self.assertRaises(RuntimeError):
                moderate_place_request(actor=self.staff, request_id=item.pk,
                    new_status='REJECTED', note='Not accepted')
        revision.refresh_from_db(); item.refresh_from_db()
        self.assertEqual((revision.status, revision.version), ('pending', before_version))
        self.assertEqual(item.status, 'PENDING')
        self.assertFalse(WorkflowNotification.objects.exists())

    def test_return_does_not_close_request_bound_to_other_owner_version(self):
        revision = self.propose(); item = self.request()
        PlaceOwnershipRequest.objects.filter(pk=item.pk).update(base_ownership_version=999999)
        publication.review(actor=self.staff, revision_id=revision.pk, version=revision.version,
                           approve=False, note='Needs correction')
        item.refresh_from_db()
        self.assertEqual(item.status, 'PENDING')

    def test_publish_after_noop_save_preserves_the_real_pending_edit(self):
        revision = self.propose()
        self.publish_admin_form(action='_save')
        revision.refresh_from_db()
        self.assertEqual(revision.status, 'pending')
        self.publish_admin_form()
        self.place.refresh_from_db(); revision.refresh_from_db()
        self.assertEqual(self.place.description_az, 'Yeni dərslər və yaşa uyğun oyunlar.')
        self.assertEqual(revision.status, 'approved')
