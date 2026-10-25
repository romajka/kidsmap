"""Pre-release workers must keep writing after the additive schema release."""
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase


class PlaceReleaseSchemaCompatibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.old_apps = MigrationExecutor(connection).loader.project_state(
            [('catalog', '0145_place_phone_whatsapp')]
        ).apps

    def test_previous_place_model_can_insert_without_public_links(self):
        old_place = self.old_apps.get_model('catalog', 'Place')
        old_category = self.old_apps.get_model('catalog', 'Category')
        category = old_category.objects.create(code='schema_compatibility', name='Schema compatibility')
        created = old_place.objects.create(name_az='Schema compatibility probe', category=category)
        from catalog.models import Place
        self.assertEqual(Place.objects.get(pk=created.pk).public_links, [])

    def test_previous_draft_model_can_insert_without_media_manifest(self):
        old_user = self.old_apps.get_model('auth', 'User')
        actor = old_user.objects.create(username='schema_compatibility_probe')
        old_draft = self.old_apps.get_model('catalog', 'ServerDraft')
        created = old_draft.objects.create(actor_id=actor.pk, target_type='place', fields={})
        from catalog.models import ServerDraft
        self.assertEqual(ServerDraft.objects.get(pk=created.pk).media_manifest, [])
