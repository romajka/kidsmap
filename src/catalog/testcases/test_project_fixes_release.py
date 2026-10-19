"""Private bytes must survive deployment and mixed-version notification writes."""
from pathlib import Path
import re
from tempfile import TemporaryDirectory

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db import connection, IntegrityError, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from catalog.models import WorkflowNotification
from catalog.private_storage import specialist_private_storage
from catalog.services.server_drafts import private_storage


class PrivateStorageReleaseTests(TestCase):
    def test_every_deployed_private_root_is_covered_by_a_persistent_mount(self):
        compose=(Path(__file__).resolve().parents[3]/'docker-compose.yml').read_text()
        targets=re.findall(r'^\s+-\s+[^\s:]+:(/[^\s:]+)',compose,re.M)
        with override_settings(MEDIA_ROOT='/app/media',PRIVATE_MEDIA_ROOT='/kidsmap-private-media',PRIVATE_DRAFT_MEDIA_ROOT=None):
            roots=[Path(specialist_private_storage.location),Path(private_storage().location)]
        for root in roots:
            with self.subTest(root=str(root)):
                self.assertTrue(any(root.is_relative_to(Path(target)) for target in targets),f'No persistent mount protects {root}')

    def test_draft_bytes_use_the_explicit_private_root(self):
        with TemporaryDirectory() as directory:
            public=Path(directory)/'public'
            private=Path(directory)/'persistent-private-drafts'
            with override_settings(MEDIA_ROOT=public,PRIVATE_DRAFT_MEDIA_ROOT=private):
                storage=private_storage()
                name=storage.save('synthetic.bin',ContentFile(b'fictional private data'))
                self.assertTrue((private/name).exists(),'Draft storage must use its configured persistent root')
                self.assertEqual((private/name).read_bytes(),b'fictional private data')
                self.assertFalse((public/name).exists())
                with self.assertRaises(ValueError):
                    storage.url(name)

    def test_draft_root_cannot_be_public_media_or_its_child(self):
        with TemporaryDirectory() as directory:
            public=Path(directory)/'public'
            for root in (public,public/'private'):
                with self.subTest(root=str(root)),override_settings(MEDIA_ROOT=public,PRIVATE_DRAFT_MEDIA_ROOT=root):
                    with self.assertRaises(ImproperlyConfigured):
                        private_storage()


class WorkflowContextCompatibilityTests(TestCase):
    def test_old_worker_insert_gets_an_empty_context_from_the_database(self):
        table=WorkflowNotification._meta.db_table
        try:
            with transaction.atomic(),connection.cursor() as cursor:
                cursor.execute(f'INSERT INTO "{table}" (event_kind,entity_type,entity_id,entity_version,recipient_key,recipient_email,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                    ['synthetic','place',1,1,'fictional-old-worker','',timezone.now()])
                row_id=cursor.fetchone()[0]
        except IntegrityError:
            self.fail('Old application notification INSERT must remain compatible with the new schema')
        self.assertEqual(WorkflowNotification.objects.get(pk=row_id).event_context,{})


class WorkflowMigrationRehearsalTests(TransactionTestCase):
    latest = ('catalog','0144_workflownotification_event_context_db_default')

    def migrate(self, name):
        executor = MigrationExecutor(connection)
        executor.migrate([('catalog',name)])
        return executor.loader.project_state([('catalog',name)]).apps

    def tearDown(self):
        self.migrate(self.latest[1])
        super().tearDown()

    def test_populated_0141_forward_and_additive_rollback_preserve_notifications(self):
        old = self.migrate('0141_catalog_admin_names')
        model = old.get_model('catalog','WorkflowNotification')
        original = model.objects.create(event_kind='synthetic', entity_type='place',
            entity_id=1,entity_version=1,recipient_key='fictional-existing')
        middle = self.migrate('0142_workflownotification_event_context')
        self.assertEqual(middle.get_model('catalog','WorkflowNotification').objects.get(pk=original.pk).event_context,{})
        self.migrate(self.latest[1])
        WorkflowNotification.objects.filter(pk=original.pk).update(event_context={'name':'Synthetic approved history'})
        # Old code ignores additive columns. Reversing only0144 must not remove
        # persisted history, and reapplying must restore old INSERT compatibility.
        before_default = self.migrate('0143_pending_email_change')
        self.assertEqual(before_default.get_model('catalog','WorkflowNotification').objects.get(pk=original.pk).event_context,
            {'name':'Synthetic approved history'})
        self.migrate(self.latest[1])
        with connection.cursor() as cursor:
            cursor.execute('INSERT INTO catalog_workflownotification (event_kind,entity_type,entity_id,entity_version,recipient_key,recipient_email,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id',
                ['synthetic','place',1,1,'fictional-old-image','',timezone.now()])
            row_id=cursor.fetchone()[0]
        self.assertEqual(WorkflowNotification.objects.get(pk=row_id).event_context,{})
        self.assertEqual(WorkflowNotification.objects.get(pk=original.pk).event_context,{'name':'Synthetic approved history'})
