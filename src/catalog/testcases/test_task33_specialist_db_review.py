"""Independent stage-24 PostgreSQL schema and additive-migration checks."""
import os
import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from catalog.models import Organization, Specialist, SpecialistClaim, SpecialistEmployment


def require_disposable_postgres(test):
    test.assertEqual(connection.vendor, 'postgresql')
    test.assertEqual(os.environ.get('DJANGO_TESTING'), '1')
    test.assertTrue(os.environ.get('TASK33_QA_ROOT', '').startswith('/tmp/kidsmap-task33-qa04-'))
    test.assertEqual(connection.settings_dict['NAME'], 'test_qa_stage04')
    test.assertIn('kidsmap-task33-qa04-socket-', connection.settings_dict['HOST'])


class SpecialistAdditiveMigrationReview(TransactionTestCase):
    databases = {'default'}

    def test_0130_to_latest_leaf_keeps_legacy_identity_locations_documents_reviews(self):
        require_disposable_postgres(self)
        schema = 'task33_specialist_migration_' + uuid.uuid4().hex
        quoted = connection.ops.quote_name(schema)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('search_path')")
            old_search_path = cursor.fetchone()[0]
            cursor.execute('CREATE SCHEMA ' + quoted)
            cursor.execute('SET search_path TO ' + quoted)
        try:
            before_target = [('catalog', '0130_task33_review_versions')]
            executor = MigrationExecutor(connection)
            executor.migrate(before_target)
            before = executor.loader.project_state(before_target).apps
            User = before.get_model('auth', 'User')
            OldSpecialist = before.get_model('catalog', 'Specialist')
            OldDocument = before.get_model('catalog', 'SpecialistDocument')
            OldLocation = before.get_model('catalog', 'SpecialistPracticeLocation')
            OldDay = before.get_model('catalog', 'SpecialistScheduleDay')
            OldReview = before.get_model('catalog', 'SpecialistReview')
            owner = User.objects.create(username='legacy-manager')
            reviewer = User.objects.create(username='legacy-reviewer')
            specialist = OldSpecialist.objects.create(owner_id=owner.pk, name='Legacy person',
                slug='legacy-person', status='published', is_verified=True)
            doc = OldDocument.objects.create(specialist_id=specialist.pk, document_type='certificate',
                name='Legacy certificate', file='protected_docs/specialists/legacy.bin',
                status='approved', is_published=True)
            location = OldLocation.objects.create(specialist_id=specialist.pk, address='Legacy room',
                is_primary=True, is_active=True)
            day = OldDay.objects.create(practice_location_id=location.pk, weekday='mon')
            review = OldReview.objects.create(specialist_id=specialist.pk, user_id=reviewer.pk,
                text='Legacy approved review', rating=4, status='approved', is_approved=True)
            old_pk = (specialist.pk, doc.pk, location.pk, day.pk, review.pk)

            after_target = [('catalog', '0132_task33_specialist_foundation')]
            executor = MigrationExecutor(connection)
            executor.migrate(after_target)
            after = executor.loader.project_state(after_target).apps
            NewSpecialist = after.get_model('catalog', 'Specialist')
            NewDocument = after.get_model('catalog', 'SpecialistDocument')
            NewLocation = after.get_model('catalog', 'SpecialistPracticeLocation')
            NewDay = after.get_model('catalog', 'SpecialistScheduleDay')
            NewReview = after.get_model('catalog', 'SpecialistReview')
            actual = NewSpecialist.objects.get(pk=specialist.pk)
            self.assertEqual((actual.pk, actual.owner_id, actual.slug, actual.status, actual.is_verified),
                             (old_pk[0], owner.pk, 'legacy-person', 'published', True))
            self.assertIsNone(actual.verified_person_user_id)
            self.assertIsNone(actual.person_verified_at)
            self.assertIsNone(actual.created_by_id)
            stored = NewDocument.objects.get(pk=doc.pk)
            self.assertEqual((stored.pk, stored.specialist_id, stored.file.name, stored.status, stored.is_published),
                             (old_pk[1], specialist.pk, 'protected_docs/specialists/legacy.bin', 'approved', True))
            self.assertIsNone(stored.opted_in_by_id)
            self.assertIsNone(stored.opted_in_at)
            self.assertEqual((NewLocation.objects.get(pk=location.pk).specialist_id,
                              NewDay.objects.get(pk=day.pk).practice_location_id),
                             (specialist.pk, location.pk))
            self.assertEqual(NewReview.objects.get(pk=review.pk).specialist_id, specialist.pk)
            self.assertEqual(after.get_model('catalog', 'SpecialistClaim').objects.count(), 0)
            self.assertEqual(after.get_model('catalog', 'SpecialistEmployment').objects.count(), 0)
            executor = MigrationExecutor(connection)
            executor.migrate(after_target)
            self.assertEqual(NewDocument.objects.get(pk=doc.pk).file.name,
                             'protected_docs/specialists/legacy.bin')
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('search_path', %s, false)", [old_search_path])
                cursor.execute('DROP SCHEMA ' + quoted + ' CASCADE')


class SpecialistDatabaseConstraintReview(TestCase):
    databases = {'default'}

    def setUp(self):
        require_disposable_postgres(self)
        User = get_user_model()
        self.person = User.objects.create_user(username='specialist-db-person')
        self.owner = User.objects.create_user(username='specialist-db-owner')
        self.specialist = Specialist.objects.create(name='One person')
        self.other = Specialist.objects.create(name='Second person')
        self.org = Organization.objects.create(name_az='Synthetic employer', owner=self.owner)

    def rejects(self, callback):
        with self.assertRaises(IntegrityError), transaction.atomic():
            callback()

    def test_one_verified_account_cannot_claim_two_person_rows_by_direct_sql_write(self):
        Specialist.objects.filter(pk=self.specialist.pk).update(verified_person_user=self.person)
        self.rejects(lambda: Specialist.objects.filter(pk=self.other.pk).update(verified_person_user=self.person))
        self.assertIsNone(Specialist.objects.get(pk=self.other.pk).verified_person_user_id)

    def test_claim_pending_pair_and_status_version_are_enforced_in_database(self):
        SpecialistClaim.objects.create(specialist=self.specialist, applicant=self.person)
        self.rejects(lambda: SpecialistClaim.objects.create(specialist=self.specialist, applicant=self.person))
        self.rejects(lambda: SpecialistClaim.objects.create(specialist=self.other, applicant=self.person,
                                                             status='unknown'))
        self.rejects(lambda: SpecialistClaim.objects.create(specialist=self.other, applicant=self.person,
                                                             version=0))

    def test_employment_period_role_status_version_and_two_confirmations_are_database_checks(self):
        valid = dict(specialist=self.specialist, organization=self.org, role='Teacher',
                     start_date=date(2026, 1, 1), person_user=self.person, organization_owner=self.owner)
        self.rejects(lambda: SpecialistEmployment.objects.create(**valid, end_date=date(2025, 12, 31)))
        self.rejects(lambda: SpecialistEmployment.objects.create(**{**valid, 'role': ''}))
        self.rejects(lambda: SpecialistEmployment.objects.create(**valid, status='unknown'))
        self.rejects(lambda: SpecialistEmployment.objects.create(**valid, version=0))
        self.rejects(lambda: SpecialistEmployment.objects.create(**valid, status='active',
                              person_confirmed_at=timezone.now()))
        confirmed = SpecialistEmployment.objects.create(**valid, status='active',
            person_confirmed_at=timezone.now(), organization_confirmed_at=timezone.now())
        self.assertEqual(confirmed.status, 'active')

    def test_exact_open_ended_duplicate_is_rejected_but_distinct_history_allowed(self):
        values = dict(specialist=self.specialist, organization=self.org, role='Teacher',
                      start_date=date(2026, 1, 1), end_date=None,
                      person_user=self.person, organization_owner=self.owner)
        first = SpecialistEmployment.objects.create(**values)
        self.rejects(lambda: SpecialistEmployment.objects.create(**values))
        # A distinct period is not the same appointment; the schema deliberately
        # does not ban all overlap or different roles without a product rule.
        later = SpecialistEmployment.objects.create(**{**values, 'start_date': date(2026, 2, 1)})
        self.assertNotEqual(first.pk, later.pk)
        SpecialistEmployment.objects.filter(pk=first.pk).update(status='cancelled')
        replacement = SpecialistEmployment.objects.create(**values)
        self.assertNotEqual(replacement.pk, first.pk)
