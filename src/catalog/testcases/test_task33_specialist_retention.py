"""Existing deletion policy unlinks identity without deleting historical contributions."""
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from catalog.models import (AccountDeletionRequest, Specialist, SpecialistDocument, SpecialistClaim,
    SpecialistEmployment, SpecialistEmploymentEvent, Organization, SpecialistPracticeLocation)
from catalog.services.account_deletion import finalize_account_deletion
from catalog.testcases.test_account_deletion import TEST_POLICY


class SpecialistRetentionTests(TestCase):
    def test_account_deletion_revokes_consent_and_anonymizes_claim_keeps_history(self):
        person = get_user_model().objects.create_user('delete-specialist-person')
        organization_user = get_user_model().objects.create_user('retained-organization')
        specialist = Specialist.objects.create(name='Retained person', owner=person,
            created_by=person, verified_person_user=person, person_verified_at=timezone.now())
        organization = Organization.objects.create(name_az='Synthetic retained organization', owner=organization_user)
        location = SpecialistPracticeLocation.objects.create(specialist=specialist, address='Synthetic old address')
        claim = SpecialistClaim.objects.create(specialist=specialist, applicant=person, reason='Synthetic private note')
        link = SpecialistEmployment.objects.create(specialist=specialist, organization=organization,
            person_user=person, organization_owner=organization_user, role='Teacher', start_date=date(2020, 1, 1),
            person_confirmed_by=person, person_confirmed_at=timezone.now(),
            organization_confirmed_by=organization_user, organization_confirmed_at=timezone.now(), status='active')
        event = SpecialistEmploymentEvent.objects.create(employment=link, actor=person, action='confirmed',
                    version=1, role='Teacher', start_date=link.start_date)
        document = SpecialistDocument.objects.create(specialist=specialist, document_type='certificate',
            name='Synthetic qualification', file='specialist-documents/synthetic.bin',
            status='approved', is_published=True, opted_in_by=person, opted_in_at=timezone.now())
        request = AccountDeletionRequest.objects.create(user=person, status='SCHEDULED',
            scheduled_for=timezone.now()-timedelta(seconds=1), policy_version=TEST_POLICY['version'],
            policy_snapshot=TEST_POLICY)
        result = finalize_account_deletion(request.pk)
        self.assertEqual(result.outcome, 'completed')
        specialist.refresh_from_db(); document.refresh_from_db(); claim.refresh_from_db(); link.refresh_from_db()
        self.assertIsNone(specialist.owner_id)
        self.assertIsNone(specialist.verified_person_user_id)
        self.assertIsNone(specialist.person_verified_at)
        self.assertFalse(document.is_published)
        self.assertIsNone(document.opted_in_at)
        self.assertIsNone(document.opted_in_by_id)
        self.assertEqual(claim.reason, '')
        self.assertEqual(claim.status, 'withdrawn')
        self.assertEqual(link.status, 'cancelled')
        self.assertTrue(SpecialistPracticeLocation.objects.filter(pk=location.pk).exists())
        self.assertTrue(SpecialistEmploymentEvent.objects.filter(pk=event.pk).exists())
        event.refresh_from_db()
        self.assertIsNone(event.actor_id)
        self.assertEqual(event.role, 'Teacher')
