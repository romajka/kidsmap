"""Stage05 additive schema contract; PostgreSQL is required for SQL invariants."""
from django.apps import apps
from django.test import SimpleTestCase


class CatalogSchemaFoundationTests(SimpleTestCase):
    def test_additive_entities_are_registered_without_replacing_place(self):
        registered = {model.__name__ for model in apps.get_app_config('catalog').get_models()}
        self.assertTrue({'Organization', 'Program', 'Activity', 'OfferingGroup', 'Location',
                         'OrganizationPlaceRequest', 'PlaceVenueRequest'}.issubset(registered),
                        'Additive business/venue schema is missing')

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.models.deletion import ProtectedError
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone, translation


class SchemaFixture:
    def setUp(self):
        names = ('Organization', 'Program', 'Activity', 'OfferingGroup', 'Location',
                 'OrganizationPlaceRequest', 'PlaceVenueRequest')
        registered = {m.__name__ for m in apps.get_app_config('catalog').get_models()}
        self.assertTrue(set(names).issubset(registered), 'Additive schema not yet implemented')
        self.Org, self.Program, self.Activity, self.Group, self.Location, self.Join, self.Venue = [apps.get_model('catalog', n) for n in names]
        from django.contrib.auth import get_user_model
        from catalog.testcases.utils import create_quality_place
        self.owner = get_user_model().objects.create_user(username='schema_owner')
        self.other = get_user_model().objects.create_user(username='schema_other')
        self.org = self.Org.objects.create(name_az='Birinci təşkilat', owner=self.owner)
        self.other_org = self.Org.objects.create(name_az='İkinci təşkilat', owner=self.other)
        self.place = create_quality_place(name_az='Uyğun mərkəz', owner=self.owner, with_subcategory=True)
        self.Place = type(self.place)
        self.location = self.Location.objects.create(address='Synthetic physical hall', confirmed_at=timezone.now())

    def structure(self):
        from catalog.services.catalog_structure import set_place_organization
        set_place_organization(self.place.pk, self.org.pk, expected_content_version=1)
        self.place.refresh_from_db()
        self.program = self.Program.objects.create(organization=self.org, name_az='Elm dərsi')
        self.activity = self.Activity.objects.create(place=self.place, program=self.program)
        return self.Group.objects.create(activity=self.activity, age_from=4, age_to=8)

    def rejects_update(self, queryset, **values):
        with self.assertRaises(IntegrityError), transaction.atomic():
            queryset.update(**values)


class CatalogSchemaInvariantTests(SchemaFixture, TestCase):
    def test_legacy_place_without_org_keeps_public_identity_and_unknown_facts(self):
        before = (self.place.pk, self.place.owner_id, self.place.slug, self.place.photo.name)
        self.place.refresh_from_db()
        self.assertEqual((self.place.pk, self.place.owner_id, self.place.slug, self.place.photo.name), before)
        self.assertIsNone(self.place.organization_id)
        self.assertIsNone(self.place.confirmed_location_id)
        self.assertIsNone(self.place.nature)
        self.assertIsNone(self.place.operating_state)
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 200)

    def test_archive_org_keeps_place_owner_content_and_reviews(self):
        self.structure()
        from catalog.models import PlaceReview
        review = PlaceReview.objects.create(place=self.place, rating=5, text='Synthetic legacy text')
        before = (self.place.owner_id, self.place.is_active, self.place.status, self.place.address)
        self.org.archive(); self.org.archive()
        self.place.refresh_from_db(); self.org.refresh_from_db()
        self.assertEqual((self.place.owner_id, self.place.is_active, self.place.status, self.place.address), before)
        self.assertTrue(PlaceReview.objects.filter(pk=review.pk).exists())
        self.assertEqual(self.org.content_version, 2)
        self.assertIsNotNone(self.org.archived_at)

    def test_business_hard_delete_is_denied_for_instance_and_queryset(self):
        for delete in (self.other_org.delete, self.Org.objects.filter(pk=self.other_org.pk).delete):
            with self.assertRaises(ProtectedError): delete()
        self.assertTrue(self.Org.objects.filter(pk=self.other_org.pk).exists())

    def test_hierarchy_protects_old_place_from_cascade(self):
        group = self.structure()
        with self.assertRaises(ProtectedError): self.place.delete()
        self.assertTrue(self.Group.objects.filter(pk=group.pk).exists())

    def test_negative_and_reversed_group_ages_fail_in_database(self):
        group = self.structure()
        for ages in ({'age_from': -1}, {'age_from': 10, 'age_to': 4}, {'age_to': -1}):
            with self.subTest(ages=ages): self.rejects_update(self.Group.objects.filter(pk=group.pk), **ages)

    def test_unknown_or_open_age_bounds_remain_nullable(self):
        activity = self.Activity.objects.create(place=self.place)
        group = self.Group.objects.create(activity=activity)
        self.assertIsNone(group.age_from); self.assertIsNone(group.age_to)
        self.Group.objects.filter(pk=group.pk).update(age_from=0, age_to=None)
        group.refresh_from_db(); self.assertEqual(group.age_from, 0); self.assertIsNone(group.age_to)

    def test_nonexistent_group_activity_fk_fails_real_database(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.Group.objects.create(activity_id=999999999)
            connection.check_constraints()

    def test_zero_versions_cannot_enter_database(self):
        group = self.structure()
        for model, obj, fields in ((self.Org, self.org, ('content_version', 'ownership_version')),
                                  (self.Place, self.place, ('content_version', 'ownership_version')),
                                  (self.Program, self.program, ('content_version',)),
                                  (self.Activity, self.activity, ('content_version',)),
                                  (self.Group, group, ('content_version',))):
            for field in fields:
                with self.subTest(model=model.__name__, field=field): self.rejects_update(model.objects.filter(pk=obj.pk), **{field: 0})

    def test_nature_and_operating_facts_need_separate_approval(self):
        qs = self.Place.objects.filter(pk=self.place.pk)
        for invalid in ({'nature': 'public_space'}, {'operating_state': 'closed'},
                        {'nature': 'invented', 'nature_approved_at': timezone.now()},
                        {'operating_state': 'invented', 'operating_state_approved_at': timezone.now()},
                        {'nature_approved_at': timezone.now()}, {'operating_state_approved_at': timezone.now()}):
            with self.subTest(fields=tuple(invalid)): self.rejects_update(qs, **invalid)
        qs.update(nature='public_space', nature_approved_at=timezone.now())
        self.place.refresh_from_db(); self.assertIsNone(self.place.operating_state)

    def test_inactive_place_is_not_exposed_by_explicit_closed_state(self):
        self.Place.objects.filter(pk=self.place.pk).update(is_active=False, operating_state='closed', operating_state_approved_at=timezone.now())
        self.place.refresh_from_db()
        self.assertEqual(self.client.get(self.place.get_absolute_url()).status_code, 404)
        self.assertFalse(self.place.is_active)

    def test_location_bounds_pair_and_physical_identity_fail_in_database(self):
        qs = self.Location.objects.filter(pk=self.location.pk)
        for bad in ({'lat': 91, 'lng': 1}, {'lat': 1, 'lng': -181}, {'lat': None, 'lng': 1}, {'address': '', 'lat': None, 'lng': None}):
            with self.subTest(fields=tuple(bad)): self.rejects_update(qs, **bad)
        with self.assertRaises(IntegrityError), transaction.atomic(): self.Location.objects.create(address='Unconfirmed')

    def test_pending_links_do_not_attach_place_or_create_business_rights(self):
        self.Join.objects.create(place=self.place, organization=self.org, requested_by=self.other)
        self.Venue.objects.create(place=self.place, location=self.location, requested_by=self.other)
        self.place.refresh_from_db()
        self.assertIsNone(self.place.organization_id); self.assertIsNone(self.place.confirmed_location_id)
        self.assertEqual(self.place.owner_id, self.owner.pk)

    def test_pending_pair_duplicates_are_rejected_without_deleting_history(self):
        request = self.Join.objects.create(place=self.place, organization=self.org)
        with self.assertRaises(IntegrityError), transaction.atomic(): self.Join.objects.create(place=self.place, organization=self.org)
        self.Join.objects.filter(pk=request.pk).update(status='rejected', decided_at=timezone.now())
        second = self.Join.objects.create(place=self.place, organization=self.org)
        self.assertNotEqual(request.pk, second.pk); self.assertEqual(self.Join.objects.count(), 2)

    def test_pending_venue_duplicate_is_rejected(self):
        self.Venue.objects.create(place=self.place, location=self.location)
        with self.assertRaises(IntegrityError), transaction.atomic(): self.Venue.objects.create(place=self.place, location=self.location)

    def test_request_decisions_and_base_versions_have_local_checks(self):
        item = self.Venue.objects.create(place=self.place, location=self.location)
        for invalid in ({'status': 'approved'}, {'status': 'nonsense', 'decided_at': timezone.now()},
                        {'decided_at': timezone.now()}, {'base_place_content_version': 0}, {'base_location_content_version': 0}):
            with self.subTest(fields=tuple(invalid)): self.rejects_update(self.Venue.objects.filter(pk=item.pk), **invalid)

    def test_confirmed_venue_bind_preserves_independent_place_and_event_address(self):
        from catalog.services.catalog_structure import bind_confirmed_location
        from catalog.models import Event
        from catalog.testcases.utils import create_quality_place
        neighbor = create_quality_place(name_az='Müstəqil biznes', owner=self.other, address=self.place.address, lat=self.place.lat, lng=self.place.lng, with_subcategory=True)
        event = Event.objects.create(name='History event', category=self.place.category, related_place=self.place, address='Original event address')
        before = (self.place.address, self.place.lat, self.place.lng, neighbor.pk, neighbor.owner_id)
        bind_confirmed_location(self.place.pk, self.location.pk, expected_content_version=1)
        self.place.refresh_from_db(); neighbor.refresh_from_db(); event.refresh_from_db()
        self.assertEqual((self.place.address, self.place.lat, self.place.lng, neighbor.pk, neighbor.owner_id), before)
        self.assertEqual(self.place.confirmed_location_id, self.location.pk)
        self.assertIsNone(neighbor.confirmed_location_id); self.assertEqual(event.address, 'Original event address')

    def test_stale_structural_write_rolls_back(self):
        from catalog.services.catalog_structure import bind_confirmed_location
        with self.assertRaises(ValidationError): bind_confirmed_location(self.place.pk, self.location.pk, expected_content_version=2)
        self.place.refresh_from_db(); self.assertIsNone(self.place.confirmed_location_id); self.assertEqual(self.place.content_version, 1)

    def test_mismatched_program_and_place_org_is_rejected_on_normal_save(self):
        program = self.Program.objects.create(organization=self.other_org)
        with self.assertRaises(ValidationError): self.Activity.objects.create(place=self.place, program=program)
        self.assertEqual(self.Activity.objects.count(), 0)

    def test_reparent_place_cannot_invalidate_program_links(self):
        self.structure()
        from catalog.services.catalog_structure import set_place_organization
        with self.assertRaises(ValidationError): set_place_organization(self.place.pk, self.other_org.pk, expected_content_version=self.place.content_version)
        self.place.refresh_from_db(); self.assertEqual(self.place.organization_id, self.org.pk)

    def test_reparent_program_cannot_invalidate_place_links(self):
        self.structure(); self.program.organization = self.other_org
        with self.assertRaises(ValidationError): self.program.save()
        self.program.refresh_from_db(); self.assertEqual(self.program.organization_id, self.org.pk)

    def test_partial_save_cannot_validate_one_pair_and_persist_another(self):
        self.structure()
        from catalog.services.catalog_structure import set_place_organization
        from catalog.testcases.utils import create_quality_place
        second_place = create_quality_place(name_az='Other branch', owner=self.other, with_subcategory=True)
        set_place_organization(second_place.pk, self.other_org.pk, expected_content_version=1)
        second_program = self.Program.objects.create(organization=self.other_org)
        for fields in (['program'], ['place']):
            self.activity.place = second_place
            self.activity.program = second_program
            with self.assertRaises(ValidationError): self.activity.save(update_fields=fields)
            self.activity.refresh_from_db()
            self.assertEqual(self.activity.place_id, self.place.pk)
            self.assertEqual(self.activity.program_id, self.program.pk)

    def test_legacy_full_save_does_not_erase_new_structural_links(self):
        stale = self.Place.objects.get(pk=self.place.pk)
        self.structure()
        stale.name_en = 'Independent legacy edit'
        stale.save()
        stale.refresh_from_db()
        self.assertEqual(stale.organization_id, self.org.pk)
        self.assertEqual(stale.content_version, 2)
        self.assertEqual(stale.name_en, 'Independent legacy edit')
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.program.organization_id, stale.organization_id)

    def test_legacy_partial_save_and_create_cannot_write_structural_fields(self):
        self.place.organization = self.org
        with self.assertRaises(ValidationError): self.place.save(update_fields=['organization'])
        self.place.refresh_from_db()
        self.assertIsNone(self.place.organization_id)
        with self.assertRaises(ValidationError):
            self.Place.objects.create(name='Unchecked branch', organization=self.org)

    def test_archived_location_cannot_accept_new_binding(self):
        from catalog.services.catalog_structure import bind_confirmed_location
        self.location.archive()
        with self.assertRaises(ValidationError): bind_confirmed_location(self.place.pk, self.location.pk, expected_content_version=1)
        self.place.refresh_from_db()
        self.assertIsNone(self.place.confirmed_location_id)
        self.assertEqual(self.place.content_version, 1)

    def test_archived_parent_cannot_accept_new_activity(self):
        self.structure(); self.org.archive()
        with self.assertRaises(ValidationError): self.Activity.objects.create(place=self.place, program=self.program)

    def test_provenance_requires_version_with_source_program(self):
        self.structure()
        qs = self.Activity.objects.filter(pk=self.activity.pk)
        for bad in ({'source_program_id': self.program.pk}, {'source_program_version': 1},
                    {'source_program_id': self.program.pk, 'source_program_version': 0}):
            with self.subTest(fields=tuple(bad)): self.rejects_update(qs, **bad)
        qs.update(source_program_id=self.program.pk, source_program_version=1, program_snapshot={'name_az': 'Approved retained text'})
        self.activity.refresh_from_db(); self.assertEqual(self.activity.program_snapshot['name_az'], 'Approved retained text')


@skipUnless(connection.vendor == 'postgresql', 'Real PostgreSQL row locks are required')
class CatalogSchemaConcurrencyTests(SchemaFixture, TransactionTestCase):
    def race(self, operations):
        barrier = Barrier(2)
        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try: operation(); return True
                except (ValidationError, IntegrityError): return False
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return sorted(f.result(timeout=30) for f in [pool.submit(run, op) for op in operations])

    def test_activity_creation_and_place_reparent_cannot_both_commit(self):
        from catalog.services.catalog_structure import set_place_organization
        set_place_organization(self.place.pk, self.org.pk, expected_content_version=1)
        self.program = self.Program.objects.create(organization=self.org)
        result = self.race([lambda: self.Activity.objects.create(place_id=self.place.pk, program_id=self.program.pk),
                            lambda: set_place_organization(self.place.pk, self.other_org.pk, expected_content_version=2)])
        self.assertEqual(result, [False, True])
        for activity in self.Activity.objects.select_related('place', 'program'):
            self.assertEqual(activity.place.organization_id, activity.program.organization_id)

    def test_activity_creation_and_program_reparent_cannot_both_commit(self):
        from catalog.services.catalog_structure import set_place_organization
        set_place_organization(self.place.pk, self.org.pk, expected_content_version=1)
        self.program = self.Program.objects.create(organization=self.org)
        def move():
            obj = self.Program.objects.get(pk=self.program.pk); obj.organization_id = self.other_org.pk; obj.save()
        self.assertEqual(self.race([lambda: self.Activity.objects.create(place_id=self.place.pk, program_id=self.program.pk), move]), [False, True])
        for activity in self.Activity.objects.select_related('place', 'program'):
            self.assertEqual(activity.place.organization_id, activity.program.organization_id)

    def test_concurrent_pending_request_has_one_database_winner(self):
        make = lambda: self.Venue.objects.create(place_id=self.place.pk, location_id=self.location.pk)
        self.assertEqual(self.race([make, make]), [False, True])
        self.assertEqual(self.Venue.objects.filter(status='pending').count(), 1)


@skipUnless(connection.vendor == 'postgresql', 'Forward schema compatibility requires PostgreSQL')
class CatalogSchemaForwardMigrationTests(TransactionTestCase):
    def test_forward_populated_legacy_preserves_every_original_field_and_url(self):
        leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
        self.assertTrue(all(('catalog', '0117_task33_catalog_structure') in MigrationExecutor(connection).loader.graph.forwards_plan((app, name)) for app, name in leaves if app == 'catalog'), 'Expansion migration is missing from current leaf ancestry')
        executor = MigrationExecutor(connection)
        try:
            executor.migrate([('catalog', '0116_moderation_sla_lifecycle')])
            historical = executor.loader.project_state([('catalog', '0116_moderation_sla_lifecycle')]).apps
            get = lambda name: historical.get_model('catalog', name)
            Category = get('Category'); Place = get('Place'); Plan = get('PricingPlan')
            category, _ = Category.objects.get_or_create(code='EDU')
            user = historical.get_model('auth', 'User').objects.create(username='migration_owner')
            place = Place.objects.create(id=41001, name='Preserved centre', name_az='Saxlanan mərkəz', name_ru='Сохранённый центр', name_en='Preserved centre', slug='preserved-centre', slug_az='saxlanan-merkez', slug_ru='sohranennyj-centr', slug_en='preserved-centre-en', owner_id=user.pk, category=category, status='published', is_active=True, photo='places/synthetic-old.jpg', price_per_month=77, pricing_plans_legacy=[{'name': 'Historical raw JSON', 'price': '77'}])
            inactive = Place.objects.create(id=41002, name='Inactive legacy', slug='inactive-legacy', category=category, is_active=False, status='draft')
            plan = Plan.objects.create(id=42001, place=place, product_type='membership', billing_mode='recurring', billing_interval='month', billing_interval_count=1, price_kind='exact', price=77, age_from=4, age_to=9, currency='AZN')
            review = get('PlaceReview').objects.create(id=43001, place=place, user_id=user.pk, rating=5, text='Synthetic retained old review')
            photo = get('PlacePhoto').objects.create(id=44001, place=place, image='places/gallery/synthetic-old.jpg')
            favorite = get('PlaceLike').objects.create(id=45001, place=place, user_id=user.pk)
            reaction = get('PlaceReviewReaction').objects.create(id=46001, review=review, user_id=user.pk, value=1)
            event = get('Event').objects.create(id=47001, name='Old event', category=category, related_place=place, address='Historical event address')
            records = [('Place', place.pk), ('Place', inactive.pk), ('PricingPlan', plan.pk), ('PlaceReview', review.pk), ('PlacePhoto', photo.pk), ('PlaceLike', favorite.pk), ('PlaceReviewReaction', reaction.pk), ('Event', event.pk)]
            snapshots = {(name, pk): get(name).objects.filter(pk=pk).values().get() for name, pk in records}
            original_fields = {name: [f.attname for f in get(name)._meta.concrete_fields] for name, _ in records}
            executor = MigrationExecutor(connection); executor.migrate(leaves)
            current = executor.loader.project_state(leaves).apps
            for name, pk in records:
                after = current.get_model('catalog', name).objects.filter(pk=pk).values(*original_fields[name]).get()
                self.assertEqual(after, snapshots[(name, pk)], f'Expansion changed legacy {name} values')
            from catalog.models import Place as LivePlace
            old = LivePlace.objects.get(pk=41001); closed = LivePlace.objects.get(pk=41002)
            self.assertIsNone(old.organization_id); self.assertIsNone(old.confirmed_location_id)
            self.assertIsNone(closed.operating_state); self.assertFalse(closed.is_active)
            for lang in ('az', 'ru', 'en'):
                with translation.override(lang):
                    response = self.client.get(old.get_absolute_url(), follow=True)
                    self.assertEqual(response.status_code, 200, f'Legacy {lang} URL lost')
        finally:
            MigrationExecutor(connection).migrate(leaves)
