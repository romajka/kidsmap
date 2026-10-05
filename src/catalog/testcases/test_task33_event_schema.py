"""Stage26 real PostgreSQL Event invariants and conservative legacy transition."""
import importlib
import uuid
from datetime import timedelta
from types import SimpleNamespace

from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.forms import modelform_factory
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from catalog.models import Category, Event, Organization, Specialist
from catalog.testcases.test_task33_specialist_db_review import require_disposable_postgres


class EventSchemaTests(TestCase):
    def setUp(self):
        require_disposable_postgres(self)
        self.actor = get_user_model().objects.create_user(username='event-schema-owner')
        self.category = Category.objects.first() or Category.objects.create(code='EV26', name_az='Synthetic')
        self.organization = Organization.objects.create(owner=self.actor, name_az='Synthetic organizer')
        self.person = Specialist.objects.create(name='Synthetic person', verified_person_user=self.actor)

    def event(self, **overrides):
        values = dict(name='Synthetic Event', category=self.category,
                      organizer_organization=self.organization,
                      start_datetime=timezone.now() + timedelta(days=2),
                      end_datetime=timezone.now() + timedelta(days=2, hours=1))
        values.update(overrides)
        return Event.objects.create(**values)

    def test_postgres_organizer_xor_blocks_two_or_zero_resolved_and_resolved_legacy_mismatch(self):
        event = self.event()
        self.assertEqual(event.organizer_resolution, 'resolved')
        for patch in ({'organizer_specialist_id': self.person.pk},
                      {'organizer_organization_id': None},
                      {'organizer_resolution': 'legacy_unresolved'}):
            with self.subTest(patch=patch), self.assertRaises(IntegrityError), transaction.atomic():
                Event.objects.filter(pk=event.pk).update(**patch)
        Event.objects.filter(pk=event.pk).update(organizer_organization=None, organizer_specialist=self.person)
        event.refresh_from_db()
        self.assertEqual(event.organizer_specialist_id, self.person.pk)

    def test_online_has_no_fabricated_place_or_geography_and_raw_updates_rejected(self):
        event = self.event(event_format='online', address='Must be cleared', district='Synthetic district', lat='40', lng='49')
        self.assertEqual(event.address, '')
        self.assertIsNone(event.lat)
        self.assertIsNone(event.lng)
        self.assertEqual(event.venue_snapshot, {})
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.filter(pk=event.pk).update(address='Forbidden online address')

    def test_aware_positive_interval_validated_in_save_and_postgres(self):
        event = self.event()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Event.objects.filter(pk=event.pk).update(end_datetime=event.start_datetime)
        event.start_datetime = event.start_datetime.replace(tzinfo=None)
        with self.assertRaises(ValidationError):
            event.save()

    def test_approved_snapshot_is_immutable_and_completed_dates_cannot_reuse_id(self):
        event = self.event(status='published', address='Approved historical address',
                           venue_snapshot={'label': 'Synthetic venue', 'address': 'Approved historical address',
                                           'district': 'Old district', 'metro': '', 'lat': None, 'lng': None})
        event.venue_snapshot['address'] = 'Forged history'
        with self.assertRaises(ValidationError):
            event.save()
        event.refresh_from_db()
        Event.objects.filter(pk=event.pk).update(start_datetime=timezone.now()-timedelta(days=2),
                                                end_datetime=timezone.now()-timedelta(days=1))
        event.refresh_from_db()
        event.start_datetime = timezone.now()+timedelta(days=2)
        event.end_datetime = timezone.now()+timedelta(days=3)
        event._allow_occurrence_change = True
        with self.assertRaises(ValidationError):
            event.save()

    def test_approved_past_and_cancelled_visibility_separate_from_publication(self):
        event = self.event(status='published', occurrence_state='cancelled',
                           start_datetime=timezone.now()-timedelta(days=2),
                           end_datetime=timezone.now()-timedelta(days=1),
                           venue_snapshot={'label': '', 'address': '', 'district': '', 'metro': '', 'lat': None, 'lng': None})
        self.assertTrue(event.is_public)
        # Unknown approval time on a legacy row is not today's content-edit time.
        Event.objects.filter(pk=event.pk).update(published_at=None)
        event.refresh_from_db()
        event.name = 'Edited approved historical title'
        event.save()
        self.assertIsNone(event.published_at)
        event.status = 'draft'
        event.save()
        self.assertFalse(event.is_public)

    def test_occurrence_history_append_only_and_unique_event_version(self):
        model = apps.get_model('catalog', 'EventOccurrenceChange')
        event = self.event()
        log = model.objects.create(event=event, actor=self.actor, kind='cancel', reason='Synthetic reason',
                                   version=1, before={'state': 'scheduled'}, after={'state': 'cancelled'})
        log.reason = 'Overwrite'
        with self.assertRaises(ValidationError):
            log.save()
        with self.assertRaises(ValidationError):
            log.delete()
        with self.assertRaises(ValidationError):
            model.objects.filter(pk=log.pk).update(reason='Queryset overwrite')
        with self.assertRaises(ValidationError):
            model.objects.filter(pk=log.pk).delete()
        with self.subTest(overwrite='constructed'), self.assertRaises(ValidationError):
            model(pk=log.pk, event=event, kind='cancel', version=1, reason='Constructed overwrite').save()
        with self.subTest(overwrite='bulk_conflict'), self.assertRaises(ValidationError):
            model.objects.bulk_create([model(event=event, kind='cancel', version=1, reason='Conflict overwrite')],
                update_conflicts=True, update_fields=['reason'], unique_fields=['event', 'version'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            model.objects.bulk_create([model(event=event, kind='reschedule', version=1)])

    def test_first_approved_format_survives_unpublication_and_blocks_both_content_switches(self):
        for original_format, changed_format in (('physical', 'online'), ('online', 'physical')):
            with self.subTest(original_format=original_format):
                event = self.event(event_format=original_format, status='published', address='Approved address')
                snapshot = event.venue_snapshot.copy()
                if original_format == 'physical':
                    Event.objects.filter(pk=event.pk).update(published_at=None)
                    event.refresh_from_db()
                event.status = 'draft'
                event.save()
                event.event_format = changed_format
                with self.assertRaises(ValidationError) as error:
                    event.save()
                self.assertIn('event_format', error.exception.message_dict)
                event.refresh_from_db()
                self.assertEqual(event.event_format, original_format)
                self.assertEqual(event.venue_snapshot, snapshot)

    def test_modelform_post_clean_reports_approved_format_change_before_admin_save(self):
        form_class = modelform_factory(Event, fields=('event_format', 'status'))
        for original_format, changed_format in (('physical', 'online'), ('online', 'physical')):
            with self.subTest(original_format=original_format):
                event = self.event(event_format=original_format, status='published', address='Approved address')
                form = form_class(data={'event_format': changed_format, 'status': 'draft'}, instance=event)
                self.assertFalse(form.is_valid())
                self.assertIn('event_format', form.errors)
                event.refresh_from_db()
                self.assertEqual(event.event_format, original_format)
                self.assertEqual(event.status, 'published')


class EventMigrationTests(TransactionTestCase):
    databases = {'default'}

    def test_0132_0133_preserves_ids_reviews_unknown_organizers_and_own_snapshot_only(self):
        require_disposable_postgres(self)
        schema = 'task33_event_migration_' + uuid.uuid4().hex
        quoted = connection.ops.quote_name(schema)
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_setting('search_path')")
            previous = cursor.fetchone()[0]
            cursor.execute('CREATE SCHEMA ' + quoted)
            cursor.execute('SET search_path TO ' + quoted)
        old_target = [('catalog', '0132_task33_specialist_foundation')]
        target = [('catalog', '0133_task33_event_foundation')]
        try:
            executor = MigrationExecutor(connection)
            executor.migrate(old_target)
            old = executor.loader.project_state(old_target).apps
            category = old.get_model('catalog', 'Category').objects.first()
            place = old.get_model('catalog', 'Place').objects.create(name='Moved current venue', category_id=category.pk,
                address='Current address must never be backfilled', district='Current district')
            model = old.get_model('catalog', 'Event')
            now = timezone.now()
            own = model.objects.create(name='Known legacy', category_id=category.pk, related_place=place,
                address='Event original address', district='Original district', lat='40.2', lng='49.2',
                status='expired', published_at=now-timedelta(days=10), start_datetime=now-timedelta(days=5),
                end_datetime=now-timedelta(days=4), slug='stable-known')
            unknown = model.objects.create(name='Unknown legacy', category_id=category.pk, related_place=place,
                status='published', slug='stable-unknown')
            unapproved = model.objects.create(name='Unproven cancellation', category_id=category.pk,
                status='cancelled', slug='stable-unapproved')
            proven = model.objects.create(name='Approved cancellation', category_id=category.pk,
                status='cancelled', published_at=now-timedelta(days=10), slug='stable-cancelled')
            review = old.get_model('catalog', 'EventReview').objects.create(event=own, text='Synthetic review', rating=4)
            before = list(model.objects.order_by('pk').values('pk', 'slug', 'address', 'district', 'related_place_id'))
            original_rows = list(model.objects.order_by('pk').values())
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            new = executor.loader.project_state(target).apps
            records = new.get_model('catalog', 'Event').objects
            self.assertEqual(list(records.order_by('pk').values('pk', 'slug', 'address', 'district', 'related_place_id')), before)
            stable_fields = [field for field in original_rows[0] if field != 'status']
            self.assertEqual(list(records.order_by('pk').values(*stable_fields)),
                             [{field: row[field] for field in stable_fields} for row in original_rows])
            self.assertEqual(records.get(pk=own.pk).venue_snapshot['address'], 'Event original address')
            self.assertEqual(records.get(pk=own.pk).venue_snapshot['district'], 'Original district')
            self.assertEqual(records.get(pk=own.pk).venue_snapshot['label'], '')
            self.assertEqual(records.get(pk=unknown.pk).venue_snapshot['address'], '')
            self.assertEqual(records.get(pk=unapproved.pk).status, 'draft')
            self.assertEqual(records.get(pk=proven.pk).status, 'published')
            self.assertEqual(records.get(pk=proven.pk).occurrence_state, 'cancelled')
            self.assertFalse(records.exclude(organizer_resolution='legacy_unresolved').exists())
            self.assertFalse(records.exclude(organizer_organization=None, organizer_specialist=None).exists())
            self.assertEqual(new.get_model('catalog', 'EventReview').objects.get(pk=review.pk).event_id, own.pk)
            reconciled = list(records.order_by('pk').values())
            importlib.import_module('catalog.migrations.0133_task33_event_foundation').reconcile_legacy_events(
                new, SimpleNamespace(connection=connection))
            self.assertEqual(list(records.order_by('pk').values()), reconciled)
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            self.assertEqual(records.count(), 4)
            executor.migrate(old_target)
            self.assertEqual(old.get_model('catalog', 'Event').objects.count(), 4)
            self.assertEqual(list(old.get_model('catalog', 'Event').objects.order_by('pk').values()), original_rows)
            self.assertEqual(old.get_model('catalog', 'Event').objects.get(pk=own.pk).status, 'expired')
            self.assertEqual(old.get_model('catalog', 'Event').objects.get(pk=unapproved.pk).status, 'cancelled')
            executor = MigrationExecutor(connection)
            executor.migrate(target)
            self.assertEqual(new.get_model('catalog', 'Event').objects.get(pk=own.pk).venue_snapshot['address'], 'Event original address')
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('search_path', %s, false)", [previous])
                cursor.execute('DROP SCHEMA ' + quoted + ' CASCADE')
