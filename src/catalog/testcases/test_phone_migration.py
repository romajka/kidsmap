"""Exercise the additive transition on historical models and real isolated DB."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class PhoneCompatibilityMigrationTests(TransactionTestCase):
    def test_existing_numbers_and_pending_payload_are_not_rewritten(self):
        before=[('catalog','0144_workflownotification_event_context_db_default')]
        after=[('catalog','0145_place_phone_whatsapp')]
        executor=MigrationExecutor(connection)
        executor.migrate(before)
        apps=executor.loader.project_state(before).apps
        try:
            Category=apps.get_model('catalog','Category')
            Place=apps.get_model('catalog','Place')
            category=Category.objects.create(code='PHONE_MIGRATION',name='Synthetic migration category')
            raw='+994 13 104 56 49'
            place=Place.objects.create(name='Synthetic legacy phones',slug='synthetic-migration-phones',category_id=category.pk,
                phone1=raw,phone2='+1 310 456 4918',phone3='050 427 43 93',schedule='Old schedule',photo='places/old.webp')
            pk=place.pk
            from django.conf import settings
            app_label, model_name = settings.AUTH_USER_MODEL.split('.')
            User = apps.get_model(app_label, model_name)
            author = User.objects.create(username='synthetic_migration_owner')
            Revision = apps.get_model('catalog', 'VolunteerPlaceRevision')
            revision = Revision.objects.create(place=place, author=author, payload={'phone1': '+1 310 456 4918'}, base_snapshot={'phone1': raw}, changed_fields=['phone1'], status='draft')
            revision_pk = revision.pk
            executor=MigrationExecutor(connection)
            executor.migrate(after)
            Updated=executor.loader.project_state(after).apps.get_model('catalog','Place')
            saved=Updated.objects.get(pk=pk)
            self.assertEqual(saved.phone1,raw)
            self.assertEqual(saved.phone2,'+1 310 456 4918')
            self.assertEqual(saved.phone3,'050 427 43 93')
            self.assertEqual(saved.whatsapp_mode,'legacy')
            self.assertEqual(saved.whatsapp_number,'')
            self.assertEqual(saved.phone_country,'AZ')
            self.assertEqual(saved.schedule,'Old schedule')
            self.assertEqual(saved.photo,'places/old.webp')
            # Old workers (or an image rollback) still INSERT only the old columns.
            old_writer = Place.objects.create(
                name='Synthetic old image after migration',
                slug='synthetic-old-image-after-migration', category_id=category.pk,
                phone1='+994504274393')
            compatible = Updated.objects.get(pk=old_writer.pk)
            self.assertEqual(compatible.phone_country, 'AZ')
            self.assertEqual(compatible.whatsapp_mode, 'legacy')
            self.assertEqual(compatible.whatsapp_number, '')
            UpdatedRevision = executor.loader.project_state(after).apps.get_model('catalog', 'VolunteerPlaceRevision')
            pending = UpdatedRevision.objects.get(pk=revision_pk)
            self.assertEqual(pending.payload, {'phone1': '+1 310 456 4918'})
            self.assertEqual(pending.base_snapshot, {'phone1': raw})
            self.assertEqual(pending.status, 'draft')
        finally:
            MigrationExecutor(connection).migrate(after)
