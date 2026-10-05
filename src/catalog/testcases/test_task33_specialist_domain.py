"""D08 person ownership is independent from proposals, grants and locations."""
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from catalog.forms import OwnerSpecialistForm
from catalog.models import Organization, Region, Specialist, SpecialistPracticeLocation
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile


def domain():
    from catalog.services import specialist_domain
    return specialist_domain


class SpecialistDomainTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user('domain-person')
        self.proposer = users.objects.create_user('domain-proposer')
        self.other = users.objects.create_user('domain-other')
        self.org_owner = users.objects.create_user('domain-organization')
        self.reviewer = users.objects.create_user('domain-reviewer', is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename='review_specialist_claim'))
        self.organization = Organization.objects.create(name_az='Synthetic organization', owner=self.org_owner)
        self.region, _ = Region.objects.get_or_create(key='domain-region', defaults={
            'name_az': 'Synthetic region', 'name_ru': 'Synthetic region', 'name_en': 'Synthetic region'})

    def profile(self, **values):
        return Specialist.objects.create(name='Synthetic person', **values)

    def verified(self):
        return self.profile(owner=self.person, verified_person_user=self.person, person_verified_at=timezone.now())

    def form(self, *, instance=None, consultation_format='online', address=''):
        return OwnerSpecialistForm(data={'name': 'Synthetic person',
            'consultation_format': consultation_format, 'location_address': address,
            'location_region': self.region.pk}, instance=instance, draft_save_only=True)

    def claim(self, specialist, applicant=None):
        return domain().request_claim(actor=applicant or self.person, specialist_id=specialist.pk)

    def employment(self, *, actor=None):
        return domain().propose_employment(actor=actor or self.org_owner,
            specialist_id=self.verified().pk, organization_id=self.organization.pk,
            role='Teacher', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))

    def test_form_proposal_records_author_without_person_ownership(self):
        result = save_owner_specialist_profile(user=self.proposer, form=self.form(), draft_save_only=True)
        self.assertTrue(result.ok)
        result.specialist.refresh_from_db()
        self.assertIsNone(result.specialist.owner_id)
        self.assertIsNone(result.specialist.verified_person_user_id)
        self.assertEqual(result.specialist.created_by_id, self.proposer.pk)

    def test_new_form_instance_cannot_supply_verified_identity(self):
        forged = Specialist(owner=self.proposer, verified_person_user=self.proposer,
                            person_verified_at=timezone.now())
        result = save_owner_specialist_profile(user=self.proposer,
            form=self.form(instance=forged), draft_save_only=True)
        self.assertTrue(result.ok)
        result.specialist.refresh_from_db()
        self.assertIsNone(result.specialist.verified_person_user_id)
        self.assertIsNone(result.specialist.person_verified_at)

    def test_prevalidated_form_is_rebound_to_fresh_locked_person(self):
        specialist = self.verified()
        form = self.form(instance=specialist)
        form.data = {**form.data, 'name': 'Updated synthetic name'}
        self.assertTrue(form.is_valid())
        result = save_owner_specialist_profile(user=self.person, form=form, draft_save_only=True)
        self.assertTrue(result.ok)
        result.specialist.refresh_from_db()
        self.assertEqual(result.specialist.name, 'Updated synthetic name')
        self.assertEqual(result.specialist.verified_person_user_id, self.person.pk)

    def test_exact_employment_duplicate_is_refused_but_cancelled_history_allows_new(self):
        item = self.employment()
        values = dict(actor=self.person, specialist_id=item.specialist_id,
            organization_id=self.organization.pk, role=' Teacher ',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        with self.assertRaises(ValidationError):
            domain().propose_employment(**values)
        domain().confirm_employment(actor=self.person, employment_id=item.pk, side='person', expected_version=1)
        domain().confirm_employment(actor=self.org_owner, employment_id=item.pk, side='organization', expected_version=2)
        with self.assertRaises(ValidationError):
            domain().propose_employment(**values)
        domain().cancel_employment(actor=self.person, employment_id=item.pk, expected_version=3)
        replacement = domain().propose_employment(**values)
        self.assertNotEqual(replacement.pk, item.pk)
        self.assertEqual(replacement.role, 'Teacher')
        self.assertEqual(item.history.count(), 4)

    def test_overlapping_employments_with_distinct_role_or_period_are_allowed(self):
        item = self.employment()
        other_role = domain().propose_employment(actor=self.person, specialist_id=item.specialist_id,
            organization_id=self.organization.pk, role='Assistant',
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        other_period = domain().propose_employment(actor=self.person, specialist_id=item.specialist_id,
            organization_id=self.organization.pk, role='Teacher',
            start_date=date(2026, 2, 1), end_date=date(2026, 12, 31))
        self.assertNotEqual(other_role.pk, item.pk)
        self.assertNotEqual(other_period.pk, item.pk)

    def test_open_ended_exact_employment_duplicate_is_refused(self):
        specialist = self.verified()
        values = dict(actor=self.person, specialist_id=specialist.pk,
            organization_id=self.organization.pk, role='Teacher', start_date=date(2026, 1, 1))
        domain().propose_employment(**values)
        with self.assertRaises(ValidationError):
            domain().propose_employment(**values)

    def test_unverified_legacy_manager_cannot_edit_person(self):
        specialist = self.profile(owner=self.proposer)
        with self.assertRaises(PermissionDenied):
            save_owner_specialist_profile(user=self.proposer, form=self.form(instance=specialist), draft_save_only=True)

    def test_foreign_form_edit_rechecks_verified_person(self):
        specialist = self.verified()
        with self.assertRaises(PermissionDenied):
            save_owner_specialist_profile(user=self.other, form=self.form(instance=specialist), draft_save_only=True)

    def test_online_switch_preserves_historical_location_and_primary(self):
        specialist = self.verified()
        location = SpecialistPracticeLocation.objects.create(specialist=specialist,
            address='Historical office', region=self.region, is_primary=True)
        result = save_owner_specialist_profile(user=self.person,
            form=self.form(instance=specialist), draft_save_only=True)
        self.assertTrue(result.ok)
        location.refresh_from_db()
        self.assertEqual(location.address, 'Historical office')
        self.assertTrue(location.is_primary)
        self.assertFalse(location.is_active)

    def test_changed_location_retires_old_row_without_overwriting_history(self):
        specialist = self.verified()
        location = SpecialistPracticeLocation.objects.create(specialist=specialist,
            address='Historical office', region=self.region, is_primary=True)
        result = save_owner_specialist_profile(user=self.person,
            form=self.form(instance=specialist, consultation_format='offline', address='New office'), draft_save_only=True)
        self.assertTrue(result.ok)
        location.refresh_from_db()
        self.assertEqual(location.address, 'Historical office')
        self.assertFalse(location.is_active)
        self.assertFalse(location.is_primary)
        self.assertEqual(specialist.practice_locations.get(is_primary=True).address, 'New office')

    def test_back_to_offline_reactivates_same_unchanged_location(self):
        specialist = self.verified()
        location = SpecialistPracticeLocation.objects.create(specialist=specialist,
            address='Historical office', region=self.region, is_primary=True, is_active=False)
        result = save_owner_specialist_profile(user=self.person,
            form=self.form(instance=specialist, consultation_format='offline', address='Historical office'), draft_save_only=True)
        self.assertTrue(result.ok)
        location.refresh_from_db()
        self.assertTrue(location.is_active)
        self.assertEqual(specialist.practice_locations.count(), 1)

    def test_claim_requires_dedicated_active_nonvolunteer_reviewer(self):
        specialist = self.profile()
        claim = self.claim(specialist)
        staff = get_user_model().objects.create_user('ordinary-staff', is_staff=True)
        volunteer = get_user_model().objects.create_user('domain-volunteer', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        volunteer.user_permissions.add(Permission.objects.get(codename='review_specialist_claim'))
        for actor in [self.person, staff, volunteer, self.org_owner]:
            with self.subTest(actor=actor.pk), self.assertRaises(PermissionDenied):
                domain().review_claim(actor=actor, claim_id=claim.pk, expected_version=1, approve=True)
        self.reviewer.is_active = False
        self.reviewer.save(update_fields=['is_active'])
        with self.assertRaises(PermissionDenied):
            domain().review_claim(actor=self.reviewer, claim_id=claim.pk, expected_version=1, approve=True)
        specialist.refresh_from_db()
        self.assertIsNone(specialist.verified_person_user_id)

    def test_claim_assigns_verified_person_and_records_legacy_manager(self):
        specialist = self.profile(owner=self.proposer, created_by=self.proposer)
        claim = self.claim(specialist)
        decided = domain().review_claim(actor=self.reviewer, claim_id=claim.pk, expected_version=1, approve=True)
        specialist.refresh_from_db()
        self.assertEqual(specialist.verified_person_user_id, self.person.pk)
        self.assertEqual(specialist.owner_id, self.person.pk)
        self.assertIsNotNone(specialist.person_verified_at)
        self.assertEqual(decided.previous_legacy_owner_id, self.proposer.pk)
        self.assertEqual(decided.reviewed_by_id, self.reviewer.pk)
        self.assertEqual(decided.status, 'approved')
        with self.assertRaises(ValidationError):
            domain().review_claim(actor=self.reviewer, claim_id=claim.pk, expected_version=1, approve=True)

    def test_two_applicants_cannot_replace_first_verified_person(self):
        specialist = self.profile()
        first = self.claim(specialist)
        second = self.claim(specialist, self.other)
        domain().review_claim(actor=self.reviewer, claim_id=first.pk, expected_version=1, approve=True)
        with self.assertRaises(ValidationError):
            domain().review_claim(actor=self.reviewer, claim_id=second.pk, expected_version=1, approve=True)
        specialist.refresh_from_db()
        self.assertEqual(specialist.verified_person_user_id, self.person.pk)
        second.refresh_from_db()
        self.assertEqual(second.status, 'pending')

    def test_account_cannot_claim_two_person_profiles(self):
        first = self.claim(self.profile())
        second_specialist = self.profile()
        second = self.claim(second_specialist)
        domain().review_claim(actor=self.reviewer, claim_id=first.pk, expected_version=1, approve=True)
        with self.assertRaises(ValidationError):
            domain().review_claim(actor=self.reviewer, claim_id=second.pk, expected_version=1, approve=True)
        second_specialist.refresh_from_db()
        self.assertIsNone(second_specialist.verified_person_user_id)

    def test_claim_withdrawal_keeps_record_and_blocks_reviewer_replay(self):
        claim = self.claim(self.profile())
        with self.assertRaises(PermissionDenied):
            domain().withdraw_claim(actor=self.other, claim_id=claim.pk, expected_version=1)
        domain().withdraw_claim(actor=self.person, claim_id=claim.pk, expected_version=1)
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'withdrawn')
        with self.assertRaises(ValidationError):
            domain().review_claim(actor=self.reviewer, claim_id=claim.pk, expected_version=2, approve=True)

    def test_organization_invitation_or_proposal_is_not_person_confirmation(self):
        item = self.employment()
        self.assertEqual(item.status, 'pending')
        self.assertIsNone(item.person_confirmed_at)
        self.assertIsNone(item.organization_confirmed_at)
        item = domain().confirm_employment(actor=self.org_owner, employment_id=item.pk,
            side='organization', expected_version=1)
        self.assertEqual(item.status, 'pending')
        self.assertIsNone(item.person_confirmed_at)
        with self.assertRaises(PermissionDenied):
            domain().confirm_employment(actor=self.org_owner, employment_id=item.pk,
                side='person', expected_version=2)
        item = domain().confirm_employment(actor=self.person, employment_id=item.pk,
            side='person', expected_version=2)
        self.assertEqual(item.status, 'active')
        self.assertEqual(item.person_confirmed_by_id, self.person.pk)
        self.assertEqual(item.organization_confirmed_by_id, self.org_owner.pk)
        self.assertEqual(list(item.history.values_list('action', flat=True)),
                         ['proposed', 'organization_confirmed', 'person_confirmed'])

    def test_consent_rechecks_changed_organization_owner(self):
        item = self.employment()
        domain().confirm_employment(actor=self.person, employment_id=item.pk,
            side='person', expected_version=1)
        self.organization.owner = self.other
        self.organization.save(update_fields=['owner'])
        with self.assertRaises(ValidationError):
            domain().confirm_employment(actor=self.other, employment_id=item.pk,
                side='organization', expected_version=2)
        item.refresh_from_db()
        self.assertIsNone(item.organization_confirmed_at)

    def test_organization_handover_away_and_back_invalidates_pending_consent(self):
        item = self.employment()
        domain().confirm_employment(actor=self.person, employment_id=item.pk,
            side='person', expected_version=1)
        from catalog.services.organization_ownership import transfer_owner
        transfer_owner(actor=self.org_owner, target_type='organization', target_id=self.organization.pk,
                       new_owner_id=self.other.pk, expected_ownership_version=1)
        transfer_owner(actor=self.other, target_type='organization', target_id=self.organization.pk,
                       new_owner_id=self.org_owner.pk, expected_ownership_version=2)
        with self.assertRaises(ValidationError):
            domain().confirm_employment(actor=self.org_owner, employment_id=item.pk,
                side='organization', expected_version=2)
        item.refresh_from_db()
        self.assertEqual(item.status, 'pending')
        self.assertIsNone(item.organization_confirmed_at)

    def test_foreign_actor_and_stale_version_cannot_confirm_or_cancel(self):
        item = self.employment()
        with self.assertRaises(PermissionDenied):
            domain().confirm_employment(actor=self.other, employment_id=item.pk, side='person', expected_version=1)
        domain().confirm_employment(actor=self.person, employment_id=item.pk, side='person', expected_version=1)
        with self.assertRaises(ValidationError):
            domain().confirm_employment(actor=self.org_owner, employment_id=item.pk, side='organization', expected_version=1)
        with self.assertRaises(PermissionDenied):
            domain().cancel_employment(actor=self.other, employment_id=item.pk, expected_version=2)

    def test_cancel_keeps_employment_period_location_and_review_history(self):
        item = self.employment()
        specialist = item.specialist
        location = SpecialistPracticeLocation.objects.create(specialist=specialist, address='Historical office', region=self.region)
        from catalog.services.review_versions import submit_review
        review, revision = submit_review(target=specialist, user=self.other, rating=5,
                                         text='Synthetic review', author_name='Synthetic parent')
        domain().confirm_employment(actor=self.person, employment_id=item.pk, side='person', expected_version=1)
        domain().confirm_employment(actor=self.org_owner, employment_id=item.pk, side='organization', expected_version=2)
        item = domain().cancel_employment(actor=self.person, employment_id=item.pk, expected_version=3)
        self.assertEqual(item.status, 'cancelled')
        self.assertEqual(item.role, 'Teacher')
        self.assertEqual(item.start_date, date(2026, 1, 1))
        self.assertEqual(item.end_date, date(2026, 12, 31))
        self.assertIsNotNone(item.person_confirmed_at)
        self.assertIsNotNone(item.organization_confirmed_at)
        self.assertEqual(item.history.count(), 4)
        location.refresh_from_db()
        self.assertEqual(location.address, 'Historical office')
        review.refresh_from_db()
        self.assertEqual(review.candidate_revision_id, revision.pk)

    def test_employment_rejects_invalid_period_blank_role_and_unverified_person(self):
        specialist = self.verified()
        for role, start, end in [('', date(2026, 1, 1), None), ('Teacher', date(2026, 2, 1), date(2026, 1, 1))]:
            with self.assertRaises(ValidationError):
                domain().propose_employment(actor=self.org_owner, specialist_id=specialist.pk,
                    organization_id=self.organization.pk, role=role, start_date=start, end_date=end)
        unverified = self.profile()
        with self.assertRaises(ValidationError):
            domain().propose_employment(actor=self.org_owner, specialist_id=unverified.pk,
                organization_id=self.organization.pk, role='Teacher', start_date=date(2026, 1, 1))

    def test_same_account_two_roles_still_need_two_explicit_confirmations(self):
        self.organization.owner = self.person
        self.organization.save(update_fields=['owner'])
        item = domain().propose_employment(actor=self.person, specialist_id=self.verified().pk,
            organization_id=self.organization.pk, role='Teacher', start_date=date(2026, 1, 1))
        item = domain().confirm_employment(actor=self.person, employment_id=item.pk,
            side='person', expected_version=1)
        self.assertEqual(item.status, 'pending')
        self.assertIsNone(item.organization_confirmed_at)
        item = domain().confirm_employment(actor=self.person, employment_id=item.pk,
            side='organization', expected_version=2)
        self.assertEqual(item.status, 'active')


class SpecialistDomainConcurrencyTests(TransactionTestCase):
    def setUp(self):
        users = get_user_model()
        self.person = users.objects.create_user('race-person')
        self.other = users.objects.create_user('race-other')
        self.organization_owner = users.objects.create_user('race-organization')
        self.reviewer = users.objects.create_user('race-reviewer', is_staff=True)
        self.reviewer.user_permissions.add(Permission.objects.get(codename='review_specialist_claim'))

    def parallel(self, operations):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections, connections
        barrier = Barrier(len(operations))
        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                operation()
                return 'accepted'
            except ValidationError:
                return 'conflict'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_concurrent_claimants_cannot_both_own_one_person(self):
        specialist = Specialist.objects.create(name='Synthetic person')
        first = domain().request_claim(actor=self.person, specialist_id=specialist.pk)
        second = domain().request_claim(actor=self.other, specialist_id=specialist.pk)
        def review(item):
            return lambda: domain().review_claim(actor=self.reviewer, claim_id=item.pk,
                                                 expected_version=1, approve=True)
        self.assertCountEqual(self.parallel([review(first), review(second)]), ['accepted', 'conflict'])
        specialist.refresh_from_db()
        self.assertIn(specialist.verified_person_user_id, [self.person.pk, self.other.pk])
        self.assertEqual(specialist.person_claims.filter(status='approved').count(), 1)
        self.assertEqual(specialist.person_claims.filter(status='pending').count(), 1)

    def test_concurrent_profiles_cannot_both_claim_one_account(self):
        first = domain().request_claim(actor=self.person,
            specialist_id=Specialist.objects.create(name='First synthetic person').pk)
        second = domain().request_claim(actor=self.person,
            specialist_id=Specialist.objects.create(name='Second synthetic person').pk)
        def review(item):
            return lambda: domain().review_claim(actor=self.reviewer, claim_id=item.pk,
                                                 expected_version=1, approve=True)
        self.assertCountEqual(self.parallel([review(first), review(second)]), ['accepted', 'conflict'])
        self.assertEqual(Specialist.objects.filter(verified_person_user=self.person).count(), 1)

    def test_simultaneous_consents_require_fresh_version_retry(self):
        specialist = Specialist.objects.create(name='Synthetic person',
            owner=self.person, verified_person_user=self.person, person_verified_at=timezone.now())
        organization = Organization.objects.create(name_az='Synthetic organization', owner=self.organization_owner)
        item = domain().propose_employment(actor=self.person, specialist_id=specialist.pk,
            organization_id=organization.pk, role='Teacher', start_date=date(2026, 1, 1))
        operations = [lambda: domain().confirm_employment(actor=self.person,
            employment_id=item.pk, side='person', expected_version=1),
            lambda: domain().confirm_employment(actor=self.organization_owner,
            employment_id=item.pk, side='organization', expected_version=1)]
        self.assertCountEqual(self.parallel(operations), ['accepted', 'conflict'])
        item.refresh_from_db()
        self.assertEqual(item.status, 'pending')
        side = 'organization' if item.person_confirmed_at else 'person'
        actor = self.organization_owner if side == 'organization' else self.person
        item = domain().confirm_employment(actor=actor, employment_id=item.pk, side=side, expected_version=2)
        self.assertEqual(item.status, 'active')
        self.assertEqual(item.history.count(), 3)

    def test_concurrent_exact_open_ended_employment_proposals_cannot_duplicate(self):
        specialist = Specialist.objects.create(name='Synthetic person',
            owner=self.person, verified_person_user=self.person, person_verified_at=timezone.now())
        organization = Organization.objects.create(name_az='Synthetic organization', owner=self.organization_owner)
        values = dict(specialist_id=specialist.pk, organization_id=organization.pk,
                      role='Teacher', start_date=date(2026, 1, 1))
        operations = [lambda: domain().propose_employment(actor=self.person, **values),
                      lambda: domain().propose_employment(actor=self.organization_owner, **values)]
        self.assertCountEqual(self.parallel(operations), ['accepted', 'conflict'])
        self.assertEqual(specialist.employment_links.count(), 1)
        self.assertEqual(specialist.employment_links.get().history.count(), 1)

    def test_account_deletion_racing_consent_revokes_authority_without_deadlock(self):
        from concurrent.futures import ThreadPoolExecutor
        from datetime import timedelta
        from threading import Barrier
        from django.db import close_old_connections, connections
        from catalog.models import AccountDeletionRequest
        from catalog.services.account_deletion import finalize_account_deletion
        from catalog.testcases.test_account_deletion import TEST_POLICY
        specialist = Specialist.objects.create(name='Synthetic retained person',
            owner=self.person, created_by=self.person, verified_person_user=self.person,
            person_verified_at=timezone.now())
        organization = Organization.objects.create(name_az='Synthetic organization', owner=self.organization_owner)
        item = domain().propose_employment(actor=self.organization_owner, specialist_id=specialist.pk,
            organization_id=organization.pk, role='Teacher', start_date=date(2026, 1, 1))
        deletion = AccountDeletionRequest.objects.create(user=self.person, status='SCHEDULED',
            scheduled_for=timezone.now()-timedelta(seconds=1),
            policy_version=TEST_POLICY['version'], policy_snapshot=TEST_POLICY)
        barrier = Barrier(2)
        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return operation()
            finally:
                connections.close_all()
        def consent():
            try:
                domain().confirm_employment(actor=self.person, employment_id=item.pk,
                    side='person', expected_version=1)
                return 'confirmed'
            except (PermissionDenied, ValidationError):
                return 'authority_revoked'
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(run, [lambda: finalize_account_deletion(deletion.pk).outcome, consent]))
        self.assertEqual(outcomes[0], 'completed')
        self.assertIn(outcomes[1], ['confirmed', 'authority_revoked'])
        item.refresh_from_db()
        specialist.refresh_from_db()
        self.assertEqual(item.status, 'cancelled')
        self.assertIsNone(specialist.verified_person_user_id)
        self.assertTrue(item.history.exists())
        self.assertEqual(item.role, 'Teacher')
