"""Identity extraction, access and duplicate evidence share one contract."""
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from catalog.models import Category, Place, ServerDraft, VolunteerPlaceRevision


class PlaceIdentityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor=get_user_model().objects.create_superuser('identity-editor','','fictional')
        cls.other=get_user_model().objects.create_superuser('identity-other','','fictional')
        cls.viewer=get_user_model().objects.create_user('identity-viewer',is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename='view_place'))
        cls.category=Category.objects.create(code='QA_IDENTITY',name_az='Identity category')
        cls.place=Place(slug='identity-fixture',name='Məktəb Club',name_az='Məktəb Club',name_ru='Старый клуб',
            category=cls.category,address='Stored Avenue 10',phone1='+994501111111',
            created_by=cls.editor,status='draft',is_active=False)
        Place.objects.bulk_create([cls.place])
        cls.revision=VolunteerPlaceRevision.objects.create(place=cls.place,author=cls.editor,
            status='pending',version=3,payload={'name_az':'Yeni Club','address':'Saved Avenue 20',
            'phone1':'+994502222222','review_note':'NeverExportThisMarker',
            'pricing_plans':{'invalid':'irrelevant'}})

    def registry(self,actor=None,**kwargs):
        from catalog.services.place_identity import identity_registry
        return identity_registry(actor or self.editor,**kwargs)

    def check(self,values,actor=None,**kwargs):
        from catalog.services.place_identity import check_duplicates
        return check_duplicates(actor or self.editor,values,**kwargs)

    def test_registry_keeps_both_versions_and_versions_are_explicit(self):
        row=self.registry()['records'][0]
        self.assertEqual(row['id'],self.place.pk)
        stored,candidate=row['versions']
        self.assertEqual((stored['source'],candidate['source']),('stored','candidate'))
        self.assertEqual(stored['fields']['address'],'Stored Avenue 10')
        self.assertEqual(candidate['fields']['address'],'Saved Avenue 20')
        self.assertEqual((candidate['version'],candidate['status']),(3,'pending'))
        self.assertEqual(row['base_content_version'],self.place.content_version)

    def test_allowlist_does_not_export_notes_owner_or_unrelated_payload(self):
        raw=json.dumps(self.registry())
        for forbidden in ('NeverExportThisMarker','review_note','pricing_plans','owner_id','author_id','password'):
            self.assertNotIn(forbidden,raw)

    def test_explicit_clear_overrides_live_value_in_candidate_only(self):
        VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(payload={'address':'','phone1':None})
        row=self.registry()['records'][0]
        self.assertEqual(row['versions'][1]['fields']['address'],'')
        self.assertEqual(row['versions'][1]['fields']['phone1'],'')
        self.assertEqual(row['versions'][0]['fields']['phone1'],'+994501111111')

    def test_approved_declined_revisions_do_not_appear_as_current_candidates(self):
        for status in ('approved','declined'):
            VolunteerPlaceRevision.objects.filter(pk=self.revision.pk).update(status=status)
            self.assertEqual(len(self.registry()['records'][0]['versions']),1)

    def test_viewer_can_only_read_stored_identity(self):
        rows=self.registry(self.viewer)['records']
        self.assertEqual([v['source'] for v in rows[0]['versions']],['stored'])
        self.assertEqual(self.check({'phone':'+994502222222'},self.viewer)['results'],[])

    def test_object_permission_callbacks_restrict_versions_and_records(self):
        self.assertEqual(self.registry(can_view=lambda obj:False)['records'],[])
        row=self.registry(can_edit=lambda obj:False)['records'][0]
        self.assertEqual(len(row['versions']),1)

    def test_revoked_actor_cannot_read_even_with_stale_superuser_object(self):
        get_user_model().objects.filter(pk=self.editor.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):self.registry()

    def test_other_actors_private_drafts_are_not_visible_to_superuser(self):
        ServerDraft.objects.create(actor=self.other,target_type='place',fields={
            'name_az':'OtherPrivateDraft','phone1':'+994503333333'})
        self.assertNotIn('OtherPrivateDraft',json.dumps(self.registry()))
        self.assertEqual(self.check({'phone':'+994503333333'})['results'],[])

    def test_own_private_draft_is_separate_and_can_be_excluded(self):
        draft=ServerDraft.objects.create(actor=self.editor,target_type='place',
            fields={'name_az':'Own pending club','address':'Own Avenue 30'})
        rows=self.registry()['records']
        own=next(r for r in rows if r['draft_id']==str(draft.pk))
        self.assertEqual(own['versions'][0]['source'],'own_draft')
        self.assertNotIn(str(draft.pk),[r['draft_id'] for r in self.registry(exclude_draft_id=str(draft.pk))['records']])

    def test_target_private_draft_is_a_version_of_its_place(self):
        ServerDraft.objects.create(actor=self.editor,target_type='place',target_id=self.place.pk,
            source_version=self.place.content_version,fields={'address':'Private Avenue 40'})
        rows=self.registry()['records']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['versions'][2]['fields']['address'],'Private Avenue 40')
        self.assertEqual(rows[0]['versions'][2]['fields']['phone1'],'+994502222222')

    def test_exact_name_and_address_match_is_confirmed_and_attributed(self):
        row=self.check({'name_az':'Yeni Club','address':'Saved Avenue 20'})['results'][0]
        self.assertEqual(row['classification'],'confirmed')
        evidence=next(e for e in row['evidence'] if e['source']=='candidate')
        self.assertEqual(set(evidence['signals']),{'name','address'})
        self.assertEqual(evidence['version'],3)

    def test_all_phones_and_multilingual_transliteration_are_searchable(self):
        Place.objects.filter(pk=self.place.pk).update(phone2='+994504444444',phone3='+994505555555')
        for values in ({'phone':'+994 (50) 444-44-44'},{'phone':'+994505555555'},
                       {'name':'Mekteb Club'},{'name_ru':'старый клуб'}):
            self.assertEqual(self.check(values)['results'][0]['id'],self.place.pk)

    def test_different_version_signals_cannot_be_stitched_into_confirmation(self):
        row=self.check({'name_az':'Məktəb Club','address':'Saved Avenue 20'})['results'][0]
        self.assertNotEqual(row['classification'],'confirmed')
        self.assertFalse(any({'name','address'}<=set(e['signals']) for e in row['evidence']))

    def test_shared_network_contact_at_another_address_is_not_a_confirmed_duplicate(self):
        row=self.check({'name_az':'Independent Club','phone':'+994502222222',
                        'address':'Different Avenue 90'})['results'][0]
        self.assertEqual(row['classification'],'network_contact')

    def test_named_branch_with_a_different_address_requires_confirmation(self):
        row=self.check({'name_az':'Yeni Club','address':'Branch Avenue 50'})['results'][0]
        self.assertEqual(row['classification'],'possible_branch')
        self.assertTrue(row['branch_override_allowed'])

    def test_coverage_never_claims_global_absence(self):
        result=self.check({'name':'No Such Fixture'})
        self.assertEqual(result['results'],[])
        self.assertEqual(result['decision'],'not_found_within_access')
        self.assertFalse(result['coverage']['global_absence_proven'])
        self.assertTrue(result['coverage']['complete_within_access'])
        self.assertIn('generated_at',result)

    def test_stale_candidate_is_labelled_and_does_not_become_confirmed(self):
        Place.objects.filter(pk=self.place.pk).update(content_version=2)
        row=self.registry()['records'][0]
        self.assertTrue(row['versions'][1]['stale'])
        result=self.check({'name_az':'Yeni Club','address':'Saved Avenue 20'})['results'][0]
        self.assertEqual(result['classification'],'probable')

    def test_deleted_places_still_appear_with_explicit_deleted_flag(self):
        from django.utils import timezone
        Place.objects.filter(pk=self.place.pk).update(deleted_at=timezone.now())
        self.assertTrue(self.registry()['records'][0]['deleted'])

    def test_registry_does_not_modify_any_saved_values(self):
        before=VolunteerPlaceRevision.objects.values().get(pk=self.revision.pk)
        self.registry();self.check({'name_az':'Yeni Club'})
        self.assertEqual(VolunteerPlaceRevision.objects.values().get(pk=self.revision.pk),before)
        self.place.refresh_from_db();self.assertEqual(self.place.address,'Stored Avenue 10')

    def test_guard_blocks_confirmed_duplicate_before_any_creation(self):
        from catalog.services.place_identity import guard_new_place
        from django.db import transaction
        with transaction.atomic(),self.assertRaises(ValidationError):
            guard_new_place(self.editor,{'name_az':'Yeni Club','address':'Saved Avenue 20'})
        self.assertEqual(Place.objects.count(),1)

    def test_guard_preserves_explicit_branch_confirmation(self):
        from catalog.services.place_identity import guard_new_place
        from django.db import transaction
        values={'name_az':'Yeni Club','address':'Branch Avenue 50'}
        with transaction.atomic(),self.assertRaises(ValidationError):guard_new_place(self.editor,values)
        with transaction.atomic():guard_new_place(self.editor,values,distinct_branch=True)
        with transaction.atomic(),self.assertRaises(ValidationError):
            guard_new_place(self.editor,{'name_az':'Yeni Club','address':'Saved Avenue 20'},distinct_branch=True)

    def test_confirmed_new_branch_can_ignore_empty_placeholder_base(self):
        from catalog.services.place_identity import guard_new_place
        Place.objects.filter(pk=self.place.pk).update(name='Yeni Club',name_az='',name_ru='',address='')
        guard_new_place(self.editor,{'name_az':'Yeni Club','address':'Another Avenue 60'},distinct_branch=True)
