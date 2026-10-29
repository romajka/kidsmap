import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from catalog.models import Category, Place, VolunteerPlaceRevision, ServerDraft


class PlaceIdentityAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor=get_user_model().objects.create_superuser('registry-editor','','fictional')
        cls.viewer=get_user_model().objects.create_user('registry-viewer',is_staff=True)
        cls.viewer.user_permissions.add(Permission.objects.get(codename='view_place'))
        cls.category=Category.objects.create(code='QA_REGISTRY',name_az='Registry category')
        cls.place=Place(slug='registry-fixture',name='Stored Club',name_az='Stored Club',category=cls.category,
            address='Original Street 10',phone1='+994501234567',status='draft',is_active=False)
        Place.objects.bulk_create([cls.place])
        cls.revision=VolunteerPlaceRevision.objects.create(place=cls.place,author=cls.editor,
            status='draft',payload={'name_az':'Saved Club','address':'Saved Street 20','phone1':'+994502345678','review_note':'InternalMarker'})

    def setUp(self):self.client.force_login(self.editor)

    def url(self,name,**kwargs):return reverse('admin:catalog_place_'+name,**kwargs)

    def test_comparison_html_and_json_keep_both_versions(self):
        url=self.url('identity_compare',args=[self.place.pk])
        response=self.client.get(url)
        self.assertEqual(response.status_code,200)
        for value in ('Original Street 10','Saved Street 20','Stored Club','Saved Club'):
            self.assertContains(response,value)
        data=self.client.get(url,{'format':'json'}).json()
        self.assertEqual(data['export_scope'],'identity_comparison')
        self.assertEqual([v['source'] for v in data['records'][0]['versions']],['stored','candidate'])
        self.assertNotIn('InternalMarker',json.dumps(data))

    def test_registry_export_is_full_and_explicit_about_access(self):
        response=self.client.get(self.url('identity_registry'),{'format':'json'})
        self.assertEqual(response.status_code,200)
        self.assertIn('attachment',response['Content-Disposition'])
        self.assertIn('no-store',response['Cache-Control'])
        data=response.json();self.assertEqual(data['export_scope'],'duplicate_registry')
        self.assertTrue(data['coverage']['complete_within_access'])
        self.assertFalse(data['coverage']['global_absence_proven'])
        self.assertEqual(len(data['records']),1)

    def test_viewer_export_has_no_candidate_and_anonymous_has_no_access(self):
        self.client.force_login(self.viewer)
        url=self.url('identity_compare',args=[self.place.pk])
        data=self.client.get(url,{'format':'json'}).json()
        self.assertEqual(len(data['records'][0]['versions']),1)
        self.assertNotIn('Saved Street 20',json.dumps(data))
        self.client.logout();self.assertEqual(self.client.get(url).status_code,302)

    def test_registry_and_comparison_are_get_only(self):
        for url in (self.url('identity_registry'),self.url('identity_compare',args=[self.place.pk])):
            self.assertEqual(self.client.post(url).status_code,405)

    def test_duplicate_endpoint_paginates_instead_of_silently_cutting_after_eight(self):
        Place.objects.bulk_create([Place(slug=f'registry-club-{i}',name=f'Club {i}',name_az=f'Club {i}',category=self.category,
            phone1='+994509999999',status='draft',is_active=False) for i in range(13)])
        url=self.url('duplicate_candidates')
        page1=self.client.get(url,{'phone':'+994509999999','page_size':8}).json()
        page2=self.client.get(url,{'phone':'+994509999999','page_size':8,'page':2}).json()
        self.assertEqual(page1['total'],13)
        self.assertTrue(page1['has_next']);self.assertEqual(len(page1['results']),8)
        self.assertEqual(len(page2['results']),5)
        self.assertFalse({r['id'] for r in page1['results']}&{r['id'] for r in page2['results']})
        self.assertIn('coverage',page1)
        self.assertIn('evidence',page1['results'][0])

    def test_matching_name_and_secondary_phone_is_supported(self):
        Place.objects.filter(pk=self.place.pk).update(phone2='+994507654321')
        url=self.url('duplicate_candidates')
        for params in ({'name':'Saved Club'},{'phone':'+994507654321'}):
            data=self.client.get(url,params).json()
            self.assertEqual(data['results'][0]['id'],self.place.pk)

    def test_no_match_still_returns_timestamp_and_scope(self):
        data=self.client.get(self.url('duplicate_candidates'),{'name':'No identity fixture'}).json()
        self.assertEqual(data['results'],[])
        self.assertIn('generated_at',data)
        self.assertEqual(data['decision'],'not_found_within_access')

    def test_list_and_editor_link_to_registry_and_comparison(self):
        response=self.client.get(reverse('admin:catalog_place_changelist'))
        self.assertContains(response,self.url('identity_registry'))
        response=self.client.get(reverse('admin:catalog_place_change',args=[self.place.pk]))
        self.assertContains(response,self.url('identity_compare',args=[self.place.pk]))

    def test_dedup_export_cannot_be_used_as_an_edit_import(self):
        data=self.client.get(self.url('identity_registry'),{'format':'json'}).json()
        response=self.client.post(self.url('pricing_import_validate'),data=json.dumps(data),content_type='application/json')
        self.assertEqual(response.status_code,400)

    def test_normal_export_remains_candidate_for_editor_and_stored_for_viewer(self):
        url=self.url('export_json',args=[self.place.pk])
        self.assertEqual(self.client.get(url).json()['export_scope'],'candidate')
        self.client.force_login(self.viewer)
        data=self.client.get(url).json()
        self.assertEqual((data['export_scope'],data['address']),('stored','Original Street 10'))

    def test_pagination_rejects_a_changed_snapshot_instead_of_silent_partial_result(self):
        url=self.url('duplicate_candidates')
        first=self.client.get(url,{'phone':'+994501234567'}).json()
        Place.objects.filter(pk=self.place.pk).update(address='Updated Street')
        response=self.client.get(url,{'phone':'+994501234567','snapshot':first['snapshot_id']})
        self.assertEqual(response.status_code,409)

    def test_invalid_pagination_is_not_reported_as_no_matches(self):
        for params in ({'page':-1},{'page_size':101},{'page':'bad'}):
            response=self.client.get(self.url('duplicate_candidates'),{'name':'Saved Club',**params})
            self.assertEqual(response.status_code,400)

    def test_current_own_private_draft_can_be_excluded_from_hints(self):
        draft=ServerDraft.objects.create(actor=self.editor,target_type='place',
            fields={'name_az':'Own private club','address':'Own Street'})
        url=self.url('duplicate_candidates')
        first=self.client.get(url,{'name':'Own private club'}).json()
        self.assertEqual(first['results'][0]['draft_id'],str(draft.pk))
        result=self.client.get(url,{'name':'Own private club','exclude_draft_id':str(draft.pk)}).json()
        self.assertEqual(result['results'],[])
