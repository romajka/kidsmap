"""Stage25 isolated legacy transfer rehearsal: IDs, explicit ambiguity, no inference."""
import uuid
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from catalog.testcases.test_task33_specialist_db_review import require_disposable_postgres


class SpecialistTransferReconciliationTests(TransactionTestCase):
    databases = {'default'}

    def test_duplicate_names_legacy_business_link_and_private_online_offices_survive(self):
        require_disposable_postgres(self)
        schema = 'task33_specialist_transfer_' + uuid.uuid4().hex
        quoted = connection.ops.quote_name(schema)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('search_path')")
            previous = cursor.fetchone()[0]
            cursor.execute('CREATE SCHEMA ' + quoted)
            cursor.execute('SET search_path TO ' + quoted)
        try:
            old_target = [('catalog', '0130_task33_review_versions')]
            executor = MigrationExecutor(connection)
            executor.migrate(old_target)
            apps = executor.loader.project_state(old_target).apps
            User = apps.get_model('auth', 'User')
            manager = User.objects.create(username='synthetic-legacy-manager')
            Category = apps.get_model('catalog', 'Category')
            category = Category.objects.first()
            if category is None:
                category = Category.objects.create(code='TR25', name_az='Synthetic category')
            place = apps.get_model('catalog', 'Place').objects.create(name='Synthetic legacy business',
                category_id=category.pk, owner_id=manager.pk)
            Profile = apps.get_model('catalog', 'Specialist')
            Location = apps.get_model('catalog', 'SpecialistPracticeLocation')
            Document = apps.get_model('catalog', 'SpecialistDocument')
            Review = apps.get_model('catalog', 'SpecialistReview')
            first = Profile.objects.create(name='Same synthetic name', slug='transfer-person-one',
                owner_id=manager.pk, status='published', consultation_format='both')
            second = Profile.objects.create(name=first.name, slug='transfer-person-two',
                owner_id=manager.pk, status='published', consultation_format='online')
            Location.objects.create(specialist_id=first.pk, place_id=place.pk,
                is_primary=True, is_active=True)
            Location.objects.create(specialist_id=first.pk, address='Synthetic independent office',
                is_primary=False, is_active=True)
            Location.objects.create(specialist_id=second.pk, address='Synthetic retired online office',
                is_primary=False, is_active=False)
            Document.objects.create(specialist_id=first.pk, document_type='certificate',
                name='Legacy synthetic certificate', file='protected_docs/specialists/synthetic.pdf',
                status='approved', is_published=True)
            Review.objects.create(specialist_id=first.pk, user_id=manager.pk,
                text='Synthetic legacy review', rating=4, status='approved', is_approved=True)
            models = ('Specialist', 'SpecialistPracticeLocation', 'SpecialistDocument', 'SpecialistReview')
            before = {name: list(apps.get_model('catalog', name).objects.order_by('pk').values()) for name in models}
            target = [('catalog', '0132_task33_specialist_foundation')]
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            new = executor.loader.project_state(target).apps
            for name, rows in before.items():
                model = new.get_model('catalog', name)
                actual = list(model.objects.order_by('pk').values(*rows[0].keys()))
                self.assertEqual(actual, rows, name)
            profiles = new.get_model('catalog', 'Specialist').objects.order_by('pk')
            self.assertEqual(list(profiles.values_list('slug', flat=True)),
                ['transfer-person-one', 'transfer-person-two'])
            self.assertFalse(profiles.exclude(verified_person_user_id=None).exists())
            self.assertFalse(new.get_model('catalog', 'SpecialistClaim').objects.exists())
            self.assertFalse(new.get_model('catalog', 'SpecialistEmployment').objects.exists())
            self.assertFalse(new.get_model('catalog', 'SpecialistDocument').objects.exclude(opted_in_by_id=None).exists())
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            self.assertEqual(new.get_model('catalog', 'SpecialistPracticeLocation').objects.count(), 3)
            self.assertEqual(profiles.count(), 2)
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('search_path', %s, false)", [previous])
                cursor.execute('DROP SCHEMA ' + quoted + ' CASCADE')
