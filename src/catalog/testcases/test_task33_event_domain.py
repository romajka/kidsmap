"""D09: organizer ACL, aware occurrence history and versioned publication."""
from datetime import timedelta
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from catalog.models import Category, Organization, Place, Specialist, Event


class EventDomainTests(TestCase):
    def setUp(self):
        users=get_user_model()
        self.person=users.objects.create_user(username='evt-person')
        self.other=users.objects.create_user(username='evt-other')
        self.reviewer=users.objects.create_superuser(username='evt-reviewer',email='reviewer@example.test',password='isolated')
        self.category=Category.objects.create(code='evt-test',name_az='Test')
        self.org=Organization.objects.create(name_az='Organizer',owner=self.person)
        self.venue=Place.objects.create(name='Venue',name_az='Venue',category=self.category,owner=self.other,status='published',address='Original address',district='baku_narimanov',lat='40.400000',lng='49.900000')
        # Stable synthetic location after normal Place location/coordinate reconciliation.
        Place.objects.filter(pk=self.venue.pk).update(district='baku_narimanov')
        self.venue.refresh_from_db()

    def api(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.event_domain'),'Event organizer service is required')
        from catalog.services import event_domain
        return event_domain

    def values(self,**extra):
        values=dict(name_az='Event',category_id=self.category.code,start_datetime=timezone.now()+timedelta(days=3),end_datetime=timezone.now()+timedelta(days=3,hours=2),organizer_organization_id=self.org.pk,event_format='physical',related_place_id=self.venue.pk,address='Original address',age_from=3,age_to=12,price_text='Free',phone='+994501234567',description_az='Event details')
        values.update(extra)
        return values

    def create(self,**extra):
        return self.api().create_event(actor=self.person,values=self.values(**extra))

    def test_service_available_for_authorized_organizer(self):
        event=self.create()
        self.assertEqual(event.organizer_organization_id,self.org.pk)
        self.assertEqual(event.organizer_resolution,'resolved')
        self.assertEqual(event.status,'draft')

    def test_venue_owner_cannot_edit_organizers_event(self):
        event=self.create()
        with self.assertRaises(PermissionDenied):
            self.api().save_event(actor=self.other,event_id=event.pk,values={'name_az':'Hijacked'},expected_updated_at=event.updated_at.isoformat())
        event.refresh_from_db();self.assertEqual(event.name_az,'Event')

    def test_transfer_revokes_old_actor_even_if_stale_event_owner_matches(self):
        event=self.create()
        Organization.objects.filter(pk=self.org.pk).update(owner=self.other)
        self.assertFalse(self.api().can_manage_event(self.person,event))
        with self.assertRaises(PermissionDenied):
            self.api().cancel_event(actor=self.person,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),reason='Changed')

    def test_unverified_person_cannot_organize(self):
        person=Specialist.objects.create(name='Unverified',owner=self.person,created_by=self.person)
        with self.assertRaises(PermissionDenied):
            self.api().create_event(actor=self.person,values=self.values(organizer_organization_id=None,organizer_specialist_id=person.pk,event_format='online',related_place_id=None,address=''))
        self.assertEqual(Event.objects.count(),0)

    def test_confirmed_online_person_needs_no_geography(self):
        person=Specialist.objects.create(name='Verified',verified_person_user=self.person,person_verified_at=timezone.now(),owner=self.person)
        event=self.api().create_event(actor=self.person,values=self.values(organizer_organization_id=None,organizer_specialist_id=person.pk,event_format='online',related_place_id=None,address=''))
        self.assertIsNone(event.related_place_id)
        self.assertIsNone(event.lat)
        self.assertEqual(event.address,'')

    def test_new_service_does_not_accept_legacy_marker_or_owner_override(self):
        for payload in ({'organizer_resolution':'legacy_unresolved'},{'owner_id':self.other.pk},{'status':'published'},{'venue_snapshot':{'address':'Forged'}}):
            with self.subTest(payload=payload),self.assertRaises(ValidationError):
                self.api().create_event(actor=self.person,values=self.values(**payload))
        self.assertEqual(Event.objects.count(),0)

    def test_stale_save_preserves_newer_content(self):
        event=self.create();token=event.updated_at.isoformat()
        fresh=self.api().save_event(actor=self.person,event_id=event.pk,values={'name_az':'Newer'},expected_updated_at=token)
        with self.assertRaises(ValidationError):
            self.api().save_event(actor=self.person,event_id=event.pk,values={'name_az':'Stale'},expected_updated_at=token)
        fresh.refresh_from_db();self.assertEqual(fresh.name_az,'Newer')

    def test_publication_snapshot_stays_at_original_venue_after_move(self):
        event=self.create()
        event=self.api().publish_event(actor=self.reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat())
        self.assertEqual(event.venue_snapshot['address'],'Original address')
        Place.objects.filter(pk=self.venue.pk).update(address='Moved address',district='baku_yasamal')
        event.refresh_from_db()
        self.assertEqual(event.venue_snapshot['address'],'Original address')
        self.assertEqual(event.venue_snapshot['district'],'baku_narimanov')

    def test_cancel_keeps_approved_publication_and_append_only_period(self):
        event=self.create()
        event=self.api().publish_event(actor=self.reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat())
        old=(event.start_datetime,event.end_datetime)
        event=self.api().cancel_event(actor=self.person,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),reason='Cancelled by organizer')
        self.assertEqual(event.status,'published');self.assertEqual(event.occurrence_state,'cancelled')
        self.assertEqual((event.start_datetime,event.end_datetime),old)
        self.assertEqual(event.occurrence_changes.count(),1)
        log=event.occurrence_changes.get();self.assertEqual(log.kind,'cancel')
        self.assertEqual(log.before['start_datetime'],old[0].isoformat())

    def test_future_reschedule_retains_original_period_and_stale_retry_fails(self):
        event=self.create();token=event.updated_at.isoformat();start=event.start_datetime
        event=self.api().reschedule_event(actor=self.person,event_id=event.pk,start_datetime=start+timedelta(days=1),end_datetime=event.end_datetime+timedelta(days=1),expected_updated_at=token,reason='New time')
        self.assertEqual(event.occurrence_state,'rescheduled')
        self.assertEqual(event.occurrence_changes.get().before['start_datetime'],start.isoformat())
        with self.assertRaises(ValidationError):
            self.api().cancel_event(actor=self.person,event_id=event.pk,expected_updated_at=token,reason='Stale')
        self.assertEqual(event.occurrence_changes.count(),1)

    def test_past_occurrence_cannot_be_reused_under_same_id(self):
        event=self.create(start_datetime=timezone.now()-timedelta(days=4),end_datetime=timezone.now()-timedelta(days=3))
        with self.assertRaises(ValidationError):
            self.api().reschedule_event(actor=self.person,event_id=event.pk,start_datetime=timezone.now()+timedelta(days=2),end_datetime=timezone.now()+timedelta(days=3),expected_updated_at=event.updated_at.isoformat(),reason='Reuse')
        event.refresh_from_db();self.assertLess(event.end_datetime,timezone.now())
