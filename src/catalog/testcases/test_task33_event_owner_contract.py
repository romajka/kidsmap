"""Existing owner form round trips enforce organizer scope and Baku dates."""
from datetime import datetime,timedelta,timezone as dt_timezone
from zoneinfo import ZoneInfo
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from catalog.models import Category,Organization,Specialist,Event,SiteSettings
from catalog.forms import OwnerEventForm


class EventOwnerContractTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user(username='event-form-user')
        self.other=get_user_model().objects.create_user(username='event-form-other')
        self.org=Organization.objects.create(name_az='My Org',owner=self.user)
        self.foreign=Organization.objects.create(name_az='Foreign Org',owner=self.other)
        self.category=Category.objects.create(code='event-form',name_az='Event')
        settings=SiteSettings.get_solo();settings.events_section_enabled=True;settings.save()

    def data(self,**extra):
        data={'name_az':'Online event','category':self.category.code,'organizer_organization':str(self.org.pk),'event_format':'online','event_date':'2035-02-04','start_time_input':'00:00','end_time_input':'01:00','form_action':'save_draft'}
        data.update(extra);return data

    def test_form_limits_organizer_and_requires_explicit_choice_even_draft(self):
        form=OwnerEventForm(user=self.user,data=self.data(organizer_organization=str(self.foreign.pk)),draft_save_only=True)
        self.assertFalse(form.is_valid())
        self.assertIn('organizer_organization',form.errors)
        form=OwnerEventForm(user=self.user,data=self.data(organizer_organization=''),draft_save_only=True)
        self.assertFalse(form.is_valid())

    def test_online_form_uses_baku_even_under_foreign_timezone_override(self):
        with timezone.override(ZoneInfo('America/New_York')):
            form=OwnerEventForm(user=self.user,data=self.data(),draft_save_only=True)
            self.assertTrue(form.is_valid(),form.errors)
            self.assertEqual(form.cleaned_data['start_datetime'],datetime(2035,2,3,20,0,tzinfo=dt_timezone.utc))
            self.assertEqual(form.cleaned_data['address'],'')

    def test_admin_cannot_publish_unverified_person_through_bulk_action(self):
        from unittest.mock import patch
        from django.contrib.admin import AdminSite
        from django.test import RequestFactory
        from catalog.domain_admin.place import EventAdmin
        person=Specialist.objects.create(name='Unverified Person',is_active=True)
        event=Event.objects.create(name='Person event',name_az='Person event',description_az='Description',
            category=self.category,organizer_specialist=person,event_format='online',
            start_datetime=timezone.now()+timedelta(days=2),end_datetime=timezone.now()+timedelta(days=3))
        request=RequestFactory().post('/admin/catalog/event/')
        request.user=get_user_model().objects.create_superuser(username='bulk-event-admin',email='bulk@example.test',password='isolated')
        event_admin=EventAdmin(Event,AdminSite())
        with patch.object(event_admin,'message_user'):
            event_admin.mark_published(request,Event.objects.filter(pk=event.pk))
        event.refresh_from_db()
        self.assertEqual(event.status,'draft')
        self.assertIsNone(event.published_at)

    def test_admin_exposes_organizer_and_format_in_add_and_change(self):
        from django.contrib.admin import AdminSite
        from django.test import RequestFactory
        from catalog.domain_admin.place import EventAdmin
        event_admin=EventAdmin(Event,AdminSite())
        for instance in (None,Event(name='Draft')):
            fields=str(event_admin.get_fieldsets(RequestFactory().get('/admin/catalog/event/'),instance))
            self.assertIn('organizer_organization',fields)
            self.assertIn('organizer_specialist',fields)
            self.assertIn('event_format',fields)

    def test_http_create_persists_resolved_online_and_prevents_forged_owner(self):
        self.client.force_login(self.user)
        response=self.client.post('/ru/account/places/events/create/',self.data(owner=str(self.other.pk),status='published'))
        self.assertEqual(response.status_code,302)
        event=Event.objects.get()
        self.assertEqual(event.status,'draft')
        self.assertEqual(event.owner_id,self.user.pk)
        self.assertEqual(event.organizer_organization_id,self.org.pk)
        self.assertEqual(event.organizer_resolution,'resolved')
        self.assertEqual(event.event_format,'online')

    def test_new_form_shows_real_organizer_and_format_controls(self):
        self.client.force_login(self.user)
        response=self.client.get('/ru/account/places/events/create/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'name="organizer_organization"')
        self.assertContains(response,'name="organizer_specialist"')
        self.assertContains(response,'name="event_format"')

    def test_admin_unpublish_changes_publication_without_cancelling_occurrence(self):
        from unittest.mock import patch
        from django.contrib.admin import AdminSite
        from django.test import RequestFactory
        from catalog.domain_admin.place import EventAdmin
        event=Event.objects.create(name='Approved',name_az='Approved',category=self.category,
            organizer_organization=self.org,event_format='online',status='published',
            start_datetime=timezone.now()+timedelta(days=2),end_datetime=timezone.now()+timedelta(days=3))
        approval=event.published_at
        admin=EventAdmin(Event,AdminSite())
        request=RequestFactory().post('/admin/catalog/event/')
        request.user=get_user_model().objects.create_superuser(username='event-admin',email='event-admin@example.test',password='isolated')
        with patch.object(admin,'message_user'):
            admin._handle_unpublish_event_submit(request,event)
        event.refresh_from_db()
        self.assertEqual(event.status,'draft')
        self.assertEqual(event.occurrence_state,'scheduled')
        self.assertEqual(event.published_at,approval)

    def test_admin_dates_are_baku_and_online_has_no_address_requirement(self):
        from catalog.domain_admin.place import EventAdminForm
        event=Event.objects.create(name='Online',name_az='Online',description_az='Online description',category=self.category,
            organizer_organization=self.org,event_format='online',phone='+994501234567',photo='synthetic.png')
        data={'name':'Online','name_az':'Online','description_az':'Online description','category':self.category.code,
            'organizer_organization':self.org.pk,'event_format':'online','status':'published',
            'start_datetime':'2035-02-04 00:00','end_datetime':'2035-02-04 01:00','phone':'+994501234567'}
        with timezone.override(ZoneInfo('America/New_York')):
            form=EventAdminForm(instance=event,data=data)
            self.assertTrue(form.is_valid(),form.errors)
            self.assertEqual(form.cleaned_data['start_datetime'],datetime(2035,2,3,20,0,tzinfo=dt_timezone.utc))
