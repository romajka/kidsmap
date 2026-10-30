"""Private working-copy visibility and authoritative editor progress."""
from django.test import TestCase, RequestFactory
from django.urls import reverse
from catalog.models import ServerDraft
from catalog.controllers.owner_places_controller import OwnerPlacesController
from catalog.services import publication
from catalog.testcases.test_content_entry_final import CandidateMediaFixture


class PlaceWorkflowReadinessTests(CandidateMediaFixture, TestCase):
    def test_new_owner_schedule_starts_with_localized_empty_choice(self):
        from catalog.forms import OwnerPlaceCreateForm
        from django.utils.translation import override
        for language, label in [('ru', 'Выберите тип расписания'), ('az', 'Cədvəl növünü seçin'), ('en', 'Choose a schedule type')]:
            with self.subTest(language=language), override(language):
                form = OwnerPlaceCreateForm()
                self.assertEqual(form['schedule_mode'].value(), '')
                self.assertEqual(list(form.fields['schedule_mode'].choices)[0], ('', label))

    def test_saved_and_explicit_owner_schedule_choices_are_preserved(self):
        from catalog.forms import OwnerPlaceCreateForm, OwnerPlaceEditForm
        self.assertEqual(OwnerPlaceEditForm(instance=self.place)['schedule_mode'].value(), self.place.schedule_mode)
        for mode in ['regular', 'always_open', 'by_appointment', 'variable', 'events']:
            with self.subTest(mode=mode):
                self.assertEqual(OwnerPlaceCreateForm(initial={'schedule_mode': mode})['schedule_mode'].value(), mode)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def draft(self, **kwargs):
        return ServerDraft.objects.create(actor=self.owner, target_type='place',
            schema_version=publication.SCHEMA_VERSION, fields={'name_az':'Unfinished saved place'}, **kwargs)

    def dashboard(self):
        request=RequestFactory().get('/ru/account/places/')
        request.user=self.owner
        return OwnerPlacesController.build_default().build_dashboard_context(request=request)[0]

    def test_incomplete_working_copy_is_in_dashboard_without_materializing_a_place(self):
        from catalog.models import Place
        before=Place.objects.count()
        draft=self.draft()
        context=self.dashboard()
        self.assertEqual([row['id'] for row in context['working_drafts']], [str(draft.pk)])
        self.assertIn('draft_id='+str(draft.pk), context['working_drafts'][0]['url'])
        self.assertEqual(Place.objects.count(), before)

    def test_consumed_and_foreign_drafts_are_not_exposed_and_edit_copy_merges_with_place(self):
        self.draft(materialized_place=self.place)
        foreign=self.draft(); foreign.actor=self.other; foreign.save()
        editing=self.draft(target_id=self.place.pk, source_version=self.place.content_version)
        context=self.dashboard()
        self.assertEqual(context['working_drafts'], [])
        row=next(p for p in context['managed_places'] if p.pk==self.place.pk)
        self.assertEqual(row.working_draft['id'], str(editing.pk))

    def test_check_returns_grouped_server_readiness_even_when_invalid_and_never_writes(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        for actor,suffix in ((self.owner,''),(self.staff,'?surface=admin')):
            self.client.force_login(actor)
            with CaptureQueriesContext(connection) as queries:
                response=self.client.post(reverse('place_editor_preview_new')+suffix,{'_km_check_required':'1'})
            self.assertEqual(response.status_code,422)
            result=response.json()['readiness']
            self.assertFalse(result['is_ready'])
            self.assertEqual([s['id'] for s in result['sections']], [1,2,3,4])
            self.assertEqual(sum(s['required_count'] for s in result['sections']), result['required_count'])
            self.assertEqual(sum(s['completed_count'] for s in result['sections']), result['completed_count'])
            self.assertEqual(result['error_count'],0)
            self.assertFalse(any(q['sql'].lstrip().upper().startswith(('INSERT','UPDATE','DELETE')) for q in queries))

    def test_main_photo_is_a_required_media_field(self):
        response=self.client.post(reverse('place_editor_preview_new'),{'_km_check_required':'1','name_az':'A valid name','description_az':'Description','price_mode':'free','schedule_mode':'always_open'})
        ready=response.json()['readiness']
        self.assertEqual(ready['sections'][3]['required_count'],1)
        photo = next(item for item in ready['items'] if item['field'] == 'photo')
        self.assertFalse(photo['complete'])

    def test_volunteer_current_preview_is_private_and_foreign_target_is_denied(self):
        from django.contrib.auth.models import Group
        self.other.is_staff=True; self.other.save(update_fields=['is_staff'])
        self.other.groups.add(Group.objects.get_or_create(name='KidsMap Volunteers')[0])
        self.client.force_login(self.other)
        response=self.client.post(reverse('place_editor_preview_new')+'?surface=volunteer', {'name_az':'Volunteer unsaved place','description_az':'Read only preview','revision_version':'0','base_token':'','action':'draft'})
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Volunteer unsaved place')
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertEqual(self.client.post(reverse('place_editor_preview',args=[self.place.pk])+'?surface=volunteer',{}).status_code,404)

    def test_dashboard_renders_saved_copy_and_merge_link(self):
        draft=self.draft()
        response=self.client.get(reverse('owner_places_dashboard'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'data-working-draft-id="'+str(draft.pk)+'"')
        self.assertContains(response,'Unfinished saved place')

    def test_account_overview_lists_new_working_drafts_for_owner_and_admin(self):
        from catalog.models import Place
        for actor in (self.owner, self.staff):
            with self.subTest(actor=actor.username):
                draft = ServerDraft.objects.create(actor=actor, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={'name_az': 'Saved for later '+actor.username})
                before = Place.objects.count()
                self.client.force_login(actor)
                response = self.client.get(reverse('account_dashboard'))
                self.assertContains(response, draft.fields['name_az'])
                self.assertContains(response, 'draft_id='+str(draft.pk))
                self.assertEqual(Place.objects.count(), before)

    def test_working_drafts_section_precedes_published_places(self):
        draft = self.draft()
        response = self.client.get(reverse('owner_places_dashboard'))
        html = response.content.decode()
        self.assertIn('id="owner-working-drafts-panel"', html)
        self.assertLess(html.index('data-working-draft-id="'+str(draft.pk)+'"'), html.index('id="owner-places-list"'))

    def test_overview_lists_latest_four_working_drafts_and_total_without_foreign_or_consumed(self):
        drafts = [ServerDraft.objects.create(actor=self.owner, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={'name_az': 'Saved draft '+str(i)}) for i in range(13)]
        foreign = ServerDraft.objects.create(actor=self.other, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={'name_az': 'Private foreign draft'})
        consumed = self.draft(materialized_place=self.place)
        response = self.client.get(reverse('account_dashboard'))
        self.assertEqual(response.context['working_drafts_overview_count'], 13)
        self.assertEqual([row['id'] for row in response.context['working_drafts_overview']], [str(d.pk) for d in reversed(drafts[-4:])])
        self.assertNotContains(response, str(foreign.pk))
        self.assertNotContains(response, str(consumed.pk))

    def test_overview_keeps_a_draft_when_it_has_no_title(self):
        draft = ServerDraft.objects.create(actor=self.owner, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={})
        response = self.client.get(reverse('account_dashboard'))
        self.assertContains(response, 'data-working-draft-id="'+str(draft.pk)+'"')

    def test_profile_entry_shows_saved_working_drafts_for_owner_and_admin(self):
        for actor in (self.owner, self.staff):
            with self.subTest(actor=actor.username):
                draft = ServerDraft.objects.create(actor=actor, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={'name_az': 'Saved profile entry '+actor.username})
                self.client.force_login(actor)
                response = self.client.get(reverse('account_profile'))
                self.assertContains(response, 'data-working-draft-id="'+str(draft.pk)+'"')
                self.assertContains(response, draft.fields['name_az'])
                html = response.content.decode()
                self.assertLess(html.index('id="account-working-drafts"'), html.index('id="my-places"'))

    def test_profile_entry_excludes_foreign_and_consumed_working_drafts(self):
        own = self.draft()
        foreign = ServerDraft.objects.create(actor=self.other, target_type='place', schema_version=publication.SCHEMA_VERSION, fields={'name_az': 'Private foreign profile draft'})
        consumed = self.draft(materialized_place=self.place)
        response = self.client.get(reverse('account_profile'))
        self.assertContains(response, str(own.pk))
        self.assertNotContains(response, str(foreign.pk))
        self.assertNotContains(response, str(consumed.pk))

    def test_missing_defaults_are_incomplete_but_invalid_optional_field_is_an_error(self):
        url=reverse('place_editor_preview_new')
        response=self.client.post(url,{'_km_check_required':'1','pricing_plans':'[]','structured_schedule':'[]','name_az':'   '})
        self.assertEqual(response.json()['readiness']['error_count'],0)
        response=self.client.post(url,{'_km_check_required':'1','website':'javascript:bad'})
        self.assertGreater(response.json()['readiness']['sections'][1]['error_count'],0)

    def test_working_drafts_are_paginated_and_stale_edit_copy_stays_visible_for_review(self):
        drafts=[self.draft() for _ in range(13)]
        request=RequestFactory().get('/ru/account/places/?draft_page=2');request.user=self.owner
        context=OwnerPlacesController.build_default().build_dashboard_context(request=request)[0]
        self.assertEqual(context['working_drafts_count'],13)
        self.assertEqual(len(context['working_drafts']),1)
        self.assertEqual(context['working_drafts'][0]['id'],str(drafts[0].pk))
        from catalog.services.server_drafts import editor_base_signature
        old=self.draft(target_id=self.place.pk,source_version=self.place.content_version)
        old.fields['_editor_base_signature']=editor_base_signature(self.place);old.save()
        self.propose({'description_az':'A newer candidate'})
        context=self.dashboard()
        row=next(p for p in context['managed_places'] if p.pk==self.place.pk)
        self.assertTrue(row.working_draft['needs_review'])

    def test_closed_default_schedule_is_missing_not_invalid(self):
        import json
        from catalog.services.place_schedule import build_default_schedule_payload
        schedule=build_default_schedule_payload()
        response=self.client.post(reverse('place_editor_preview_new'),{'_km_check_required':'1','structured_schedule':json.dumps(schedule),'schedule_mode':'regular','name_az':'Started'})
        self.assertEqual(response.json()['readiness']['sections'][1]['error_count'],0)
        self.assertFalse(response.json()['readiness']['is_ready'])

    def test_owner_native_saves_do_not_retire_a_newer_same_uuid_copy(self):
        from uuid import uuid4
        from catalog.services.publication_forms import version_token
        for ajax, editing in ((True,False),(False,False),(True,True),(False,True)):
            with self.subTest(ajax=ajax,editing=editing):
                self.place.refresh_from_db()
                draft=self.draft(version=2,target_id=self.place.pk if editing else None,source_version=self.place.content_version if editing else 0)
                data={'form_action':'save_draft','name_az':f'Private native save {int(ajax)} {int(editing)}','category':self.place.category_id,
                    'server_draft_id':str(draft.pk),'server_draft_version':'1','photo_request_id':str(uuid4())}
                if editing:data['publication_token']=version_token(self.place)
                url=reverse(('owner_photo_edit_save' if editing else 'owner_photo_create_save') if ajax else ('owner_place_edit' if editing else 'owner_place_create'),args=[self.place.pk] if editing else [])
                response=self.client.post(url,data)
                self.assertEqual(response.status_code,200 if ajax else 302,response.content[:300])
                draft.refresh_from_db();self.assertIsNone(draft.materialized_place_id)

    def test_matching_owner_native_save_retires_the_used_copy(self):
        from uuid import uuid4
        draft=self.draft()
        response=self.client.post(reverse('owner_photo_create_save'),{'form_action':'save_draft','name_az':'Private native save','category':self.place.category_id,
            'server_draft_id':str(draft.pk),'server_draft_version':str(draft.version),'photo_request_id':str(uuid4())})
        self.assertEqual(response.status_code,200,response.content[:300])
        draft.refresh_from_db();self.assertIsNotNone(draft.materialized_place_id)
