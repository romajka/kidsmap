"""Populated historical schema proves additive upgrade without taxonomy inference."""
from django.conf import settings
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone
from catalog.models import Activity,Program


class CompletionTaxonomyMigrationTests(TransactionTestCase):
    def test_populated_0133_upgrade_keeps_ids_links_prices_and_unknown_taxonomy(self):
        self.assertTrue(settings.TESTING)
        self.assertFalse(Activity.objects.exists());self.assertFalse(Program.objects.exists())
        executor=MigrationExecutor(connection)
        latest=executor.loader.graph.leaf_nodes()
        try:
            # Rewind only an empty owned test schema; no modern taxonomy is discarded.
            executor.migrate([('catalog','0133_task33_event_foundation')])
            old=executor.loader.project_state([('catalog','0133_task33_event_foundation')]).apps
            User=old.get_model(*settings.AUTH_USER_MODEL.split('.'))
            owner=User.objects.create(username='completion_migration_synthetic')
            category=old.get_model('catalog','Category').objects.create(code='MIG',name_az='Migration category')
            org=old.get_model('catalog','Organization').objects.create(owner_id=owner.pk,name_az='Historical organization')
            place=old.get_model('catalog','Place').objects.create(name='Historical place',name_az='Historical place',
                category_id=category.pk,owner_id=owner.pk,organization_id=org.pk,
                organization_relationship_kind='business',organization_join_place_ownership_version=1,
                organization_join_org_ownership_version=1)
            program=old.get_model('catalog','Program').objects.create(organization_id=org.pk,name_az='Historical program',
                category_id=category.pk,status='published',approved_at=timezone.now())
            activity=old.get_model('catalog','Activity').objects.create(place_id=place.pk,program_id=program.pk,
                source_program_id=program.pk,source_program_version=1,
                program_snapshot={'category_id':category.pk,'name_az':'Historical approved copy'},status='published')
            group=old.get_model('catalog','OfferingGroup').objects.create(activity_id=activity.pk,name_az='Historical group',age_from=4,age_to=8)
            plan=old.get_model('catalog','PricingPlan').objects.create(offering_group_id=group.pk,price='25',product_type='lesson')
            ids=(org.pk,place.pk,program.pk,activity.pk,group.pk,plan.pk)
            preserved_snapshot=dict(activity.program_snapshot)
            executor=MigrationExecutor(connection)
            executor.migrate([('catalog','0134_completion_taxonomy')])
            new=executor.loader.project_state([('catalog','0134_completion_taxonomy')]).apps
            actual=new.get_model('catalog','Activity').objects.get(pk=activity.pk)
            common=new.get_model('catalog','Program').objects.get(pk=program.pk)
            self.assertEqual((actual.place_id,actual.program_id,actual.source_program_id,actual.source_program_version),
                (place.pk,program.pk,program.pk,1))
            self.assertEqual(actual.program_snapshot,preserved_snapshot)
            self.assertIsNone(actual.category_id);self.assertIsNone(actual.subcategory_id)
            self.assertEqual(common.category_id,category.pk);self.assertIsNone(common.subcategory_id)
            price=new.get_model('catalog','PricingPlan').objects.get(pk=plan.pk)
            self.assertEqual(price.offering_group_id,group.pk);self.assertEqual(str(price.price),'25.00')
            self.assertEqual(tuple(new.get_model('catalog',name).objects.get(pk=pk).pk for name,pk in zip(
                ('Organization','Place','Program','Activity','OfferingGroup','PricingPlan'),ids)),ids)
        finally:
            MigrationExecutor(connection).migrate(latest)
