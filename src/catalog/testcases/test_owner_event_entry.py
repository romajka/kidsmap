"""Synthetic owner Event entry regressions; no changes to domain policy."""
from datetime import datetime,timedelta,timezone as dt_timezone
from zoneinfo import ZoneInfo
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.forms import OwnerEventForm
from catalog.models import Category,Event,Organization,Specialist,SiteSettings,EventOccurrenceChange
from catalog.services import event_domain

class OwnerEventEntryTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user('entry-event-owner')
        self.other=get_user_model().objects.create_user('entry-event-other')
        self.org=Organization.objects.create(name_az='Synthetic organizer',owner=self.user)
        self.category=Category.objects.create(code='entry-event',name_az='Synthetic event')
        site=SiteSettings.get_solo();site.events_section_enabled=True;site.save()
        self.client.force_login(self.user)

    def data(self,**extra):
        data={'category':self.category.code,'organizer_organization':str(self.org.pk),'event_format':'online','form_action':'save_draft'}
        data.update(extra);return data

    def event(self,**extra):
        values={'category':self.category,'organizer_organization':self.org,'event_format':'online','name_az':'Synthetic event','description_az':'Synthetic description','start_datetime':timezone.now()+timedelta(days=3),'end_datetime':timezone.now()+timedelta(days=3,hours=1)}
        values.update(extra);return event_domain.create_event(actor=self.user,values={k+'_id' if k in ('category','organizer_organization') else k:v.pk if k in ('category','organizer_organization') else v for k,v in values.items()})

    def test_draft_without_category_is_addressable_form_error(self):
        form=OwnerEventForm(user=self.user,data=self.data(category=''),draft_save_only=True)
        self.assertFalse(form.is_valid())
        self.assertIn('category',form.errors)
        response=self.client.post(reverse('owner_event_create'),self.data(category=''))
        self.assertEqual(response.status_code,200)
        self.assertEqual(Event.objects.count(),0)
        self.assertContains(response,'data-error-field-ref="category"')

    def test_partial_date_pair_draft_links_to_missing_control(self):
        for extra,field in [({'event_date':'2035-02-04','start_time_input':'23:30'},'end_time_input'),({'event_date':'2035-02-04','end_time_input':'23:30'},'start_time_input')]:
            with self.subTest(field=field):
                form=OwnerEventForm(user=self.user,data=self.data(**extra),draft_save_only=True)
                self.assertFalse(form.is_valid());self.assertIn(field,form.errors)

    def test_draft_can_be_empty_except_organizer_and_category_and_resume(self):
        response=self.client.post(reverse('owner_event_create'),self.data())
        self.assertEqual(response.status_code,302)
        event=Event.objects.get();self.assertEqual(event.status,'draft');self.assertIsNone(event.start_datetime)
        self.assertEqual(response.url,reverse('owner_event_edit',kwargs={'pk':event.pk}))
        response=self.client.get(response.url)
        self.assertContains(response,'data-explicit-save="1"')
        self.assertContains(response,'data-recovery-clear-key=')
        response=self.client.get(reverse('owner_event_edit',kwargs={'pk':event.pk}))
        self.assertContains(response,'data-explicit-save="0"')

    def test_stale_error_structured_and_token_retained(self):
        event=self.event();old=event.updated_at.isoformat()
        event_domain.save_event(actor=self.user,event_id=event.pk,values={'name_az':'New'},expected_updated_at=old)
        response=self.client.post(reverse('owner_event_edit',kwargs={'pk':event.pk}),self.data(expected_updated_at=old,name_az='Stale'))
        self.assertContains(response,'data-error-code="stale_version"')
        self.assertEqual(response.context['form'].data['expected_updated_at'],old)
        event.refresh_from_db();self.assertEqual(event.name_az,'New')

    def test_ui_native_format_and_actor_scoped_recovery(self):
        response=self.client.get(reverse('owner_event_create'))
        self.assertContains(response,'type="radio" name="event_format"')
        self.assertContains(response,'data-recovery-actor="'+str(self.user.pk)+'"')
        self.assertContains(response,'data-event-requirements')
        self.client.force_login(self.other)
        empty = self.client.get(reverse('owner_event_create'))
        self.assertContains(empty,reverse('organization_workspace_create'))
        self.assertContains(response,'data-photo-source-bytes="15728640"')

    def test_edit_organizer_locked_without_new_authority(self):
        event=self.event();response=self.client.get(reverse('owner_event_edit',kwargs={'pk':event.pk}))
        self.assertContains(response,'data-organizer-locked')
        self.assertNotContains(response,'name="organizer_role_switch"')
        foreign=Organization.objects.create(owner=self.user,name_az='Another own org')
        response=self.client.post(reverse('owner_event_edit',kwargs={'pk':event.pk}),self.data(organizer_organization=foreign.pk,expected_updated_at=event.updated_at.isoformat()))
        event.refresh_from_db();self.assertEqual(event.organizer_organization_id,self.org.pk)
        self.assertEqual(response.status_code,200)

    def test_management_reschedule_cancel_keeps_identity_snapshot_and_history(self):
        event=self.event()
        event.status='published';event.save();original_id=event.pk
        url=reverse('owner_event_manage',kwargs={'pk':event.pk})
        self.assertContains(self.client.get(url),'name="reason"')
        response=self.client.post(reverse('owner_event_reschedule',kwargs={'pk':event.pk}),{'expected_updated_at':event.updated_at.isoformat(),'reason':'Synthetic move','start_datetime':'2035-02-04T23:30','end_datetime':'2035-02-05T00:30'})
        self.assertEqual(response.status_code,302);event.refresh_from_db()
        self.assertEqual(event.pk,original_id);self.assertEqual(event.status,'published');self.assertEqual(event.occurrence_state,'rescheduled')
        self.assertEqual(event.start_datetime,datetime(2035,2,4,19,30,tzinfo=dt_timezone.utc))
        self.assertEqual(EventOccurrenceChange.objects.filter(event=event).count(),1)
        old=event.updated_at.isoformat()
        response=self.client.post(reverse('owner_event_cancel',kwargs={'pk':event.pk}),{'expected_updated_at':old,'reason':'Synthetic cancellation'})
        self.assertEqual(response.status_code,302);event.refresh_from_db();self.assertEqual(event.occurrence_state,'cancelled')
        self.client.post(reverse('owner_event_cancel',kwargs={'pk':event.pk}),{'expected_updated_at':old,'reason':'Repeat'})
        self.assertEqual(EventOccurrenceChange.objects.filter(event=event).count(),2)
        self.assertIsNone(event.deleted_at)

    def test_management_rejects_foreign_role_get_and_post(self):
        event=self.event();self.client.force_login(self.other)
        for route in ['owner_event_manage','owner_event_cancel','owner_event_reschedule']:
            with self.subTest(route=route):
                url=reverse(route,kwargs={'pk':event.pk})
                response=self.client.get(url) if route.endswith('manage') else self.client.post(url,{'expected_updated_at':event.updated_at.isoformat(),'reason':'Forged'})
                self.assertEqual(response.status_code,403)
        self.assertEqual(EventOccurrenceChange.objects.count(),0)

    def test_management_stale_and_started_errors_keep_input(self):
        event=self.event(start_datetime=timezone.now()-timedelta(hours=1),end_datetime=timezone.now()+timedelta(hours=1))
        response=self.client.post(reverse('owner_event_reschedule',kwargs={'pk':event.pk}),{'expected_updated_at':event.updated_at.isoformat(),'reason':'Retain me','start_datetime':'2035-02-04T23:30','end_datetime':'2035-02-05T00:30'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'Retain me');self.assertEqual(EventOccurrenceChange.objects.count(),0)
        old=event.updated_at.isoformat();event_domain.save_event(actor=self.user,event_id=event.pk,values={'name_az':'Changed'},expected_updated_at=old)
        response=self.client.post(reverse('owner_event_cancel',kwargs={'pk':event.pk}),{'expected_updated_at':old,'reason':'Keep conflict'})
        self.assertContains(response,'data-error-code="stale_version"');self.assertContains(response,'Keep conflict')

    def test_management_feature_gate_and_post_only(self):
        event=self.event()
        self.assertEqual(self.client.get(reverse('owner_event_cancel',kwargs={'pk':event.pk})).status_code,405)
        site=SiteSettings.get_solo();site.events_section_enabled=False;site.save()
        for route in ['owner_event_manage','owner_event_cancel','owner_event_reschedule']:
            response=self.client.get(reverse(route,kwargs={'pk':event.pk})) if route.endswith('manage') else self.client.post(reverse(route,kwargs={'pk':event.pk}),{})
            self.assertEqual(response.status_code,404)

    def test_baku_overnight_and_exact_seconds_round_trip(self):
        with timezone.override(ZoneInfo('America/New_York')):
            form=OwnerEventForm(user=self.user,data=self.data(event_date='2035-02-04',end_date='2035-02-05',start_time_input='23:30',end_time_input='00:30'),draft_save_only=True)
            self.assertTrue(form.is_valid(),form.errors)
            self.assertEqual(form.cleaned_data['end_datetime']-form.cleaned_data['start_datetime'],timedelta(hours=1))
        event=self.event(start_datetime=datetime(2035,2,4,19,30,17,42,tzinfo=dt_timezone.utc),end_datetime=datetime(2035,2,4,20,30,18,43,tzinfo=dt_timezone.utc))
        form=OwnerEventForm(instance=event,user=self.user,data=self.data(event_date='2035-02-04',end_date='2035-02-05',start_time_input='23:30',end_time_input='00:30'),draft_save_only=True)
        self.assertTrue(form.is_valid(),form.errors);self.assertEqual(form.cleaned_data['start_datetime'].microsecond,42);self.assertEqual(form.cleaned_data['end_datetime'].second,18)

    def test_organizer_specialist_requires_confirmed_person_and_venue_does_not_grant_rights(self):
        from catalog.models import Place
        person=Specialist.objects.create(name='Synthetic person',verified_person_user=self.user,person_verified_at=timezone.now(),is_active=True,consultation_format='online')
        venue=Place.objects.create(name='Synthetic venue',category=self.category,owner=self.other,status='published',address='Venue address',is_active=True)
        response=self.client.post(reverse('owner_event_create'),self.data(organizer_organization='',organizer_specialist=person.pk,event_format='physical',related_place=venue.pk))
        self.assertEqual(response.status_code,302);event=Event.objects.get();self.assertEqual(event.organizer_specialist_id,person.pk);self.assertEqual(event.related_place_id,venue.pk)
        self.assertEqual(event.address,'Venue address');self.assertEqual(event.phone,'')
        self.client.force_login(self.other);self.assertEqual(self.client.get(reverse('owner_event_edit',kwargs={'pk':event.pk})).status_code,403)
        self.client.force_login(self.user);Specialist.objects.filter(pk=person.pk).update(person_verified_at=None)
        self.assertEqual(self.client.get(reverse('owner_event_edit',kwargs={'pk':event.pk})).status_code,403)

    def test_photo_source_above_two_mb_normalizes_and_bad_file_retains_text(self):
        from io import BytesIO
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        output=BytesIO();Image.new('RGB',(48,32),'green').save(output,format='PNG')
        raw=output.getvalue()+b'\0'*(3*1024*1024)
        form=OwnerEventForm(user=self.user,data=self.data(name_az='Photo draft'),files={'photo':SimpleUploadedFile('synthetic.png',raw,content_type='image/png')},draft_save_only=True)
        self.assertTrue(form.is_valid(),form.errors);self.assertLessEqual(form.cleaned_data['photo'].size,2*1024*1024)
        response=self.client.post(reverse('owner_event_create'),self.data(name_az='Retained bad file',photo=SimpleUploadedFile('broken.png',b'not a photo',content_type='image/png')))
        self.assertEqual(response.status_code,200);self.assertContains(response,'Retained bad file');self.assertContains(response,'data-error-field-ref="photo"');self.assertEqual(Event.objects.count(),0)
        over=OwnerEventForm(user=self.user,data=self.data(),files={'photo':SimpleUploadedFile('synthetic.png',output.getvalue()+b'\0'*(16*1024*1024),content_type='image/png')},draft_save_only=True)
        self.assertFalse(over.is_valid());self.assertIn('photo',over.errors)

    def test_unavailable_venue_is_not_silently_replaced(self):
        from catalog.models import Place
        venue=Place.objects.create(name='Hidden unrelated venue',category=self.category,owner=self.other,status='draft',address='Private address',is_active=True)
        response=self.client.post(reverse('owner_event_create'),self.data(event_format='physical',related_place=venue.pk,name_az='Keep venue input'))
        self.assertEqual(response.status_code,200);self.assertContains(response,'data-error-field-ref="related_place"');self.assertNotContains(response,'Private address');self.assertContains(response,'Keep venue input');self.assertEqual(Event.objects.count(),0)

    def test_owner_submission_requirements_and_pending_lock_unchanged(self):
        event=self.event();data=self.data(expected_updated_at=event.updated_at.isoformat(),form_action='submit',name_az='Ready name',event_date='2035-02-04',start_time_input='23:30',end_date='2035-02-05',end_time_input='00:30',age_from='0',age_to='10',price_text='Free',description_az='AZ description',phone='')
        response=self.client.post(reverse('owner_event_edit',kwargs={'pk':event.pk}),data);self.assertEqual(response.status_code,200);event.refresh_from_db();self.assertEqual(event.status,'draft')
        event.status='pending';event.save();response=self.client.post(reverse('owner_event_edit',kwargs={'pk':event.pk}),self.data(expected_updated_at=event.updated_at.isoformat(),name_az='FORGED'))
        self.assertEqual(response.status_code,302);event.refresh_from_db();self.assertEqual(event.name_az,'Synthetic event')

    def test_occurrence_bad_datetime_is_form_error_not_server_error(self):
        event=self.event()
        response=self.client.post(reverse('owner_event_reschedule',kwargs={'pk':event.pk}),{'expected_updated_at':event.updated_at.isoformat(),'reason':'Retain invalid date','start_datetime':'2035-99-99T23:30','end_datetime':'2035-02-05T00:30'})
        self.assertEqual(response.status_code,200);self.assertContains(response,'Retain invalid date');self.assertEqual(EventOccurrenceChange.objects.count(),0)

    def test_approved_history_date_edit_is_addressable_error_not_500(self):
        reviewer=get_user_model().objects.create_superuser('entry-event-reviewer','reviewer@example.test','synthetic')
        event=self.event();event=event_domain.publish_event(actor=reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat());event.status='draft';event.save()
        old=event.start_datetime
        response=self.client.post(reverse('owner_event_edit',kwargs={'pk':event.pk}),self.data(expected_updated_at=event.updated_at.isoformat(),event_date='2035-02-04',start_time_input='23:30',end_date='2035-02-05',end_time_input='00:30'))
        self.assertEqual(response.status_code,200);event.refresh_from_db();self.assertEqual(event.start_datetime,old);self.assertEqual(event.occurrence_changes.count(),0)
