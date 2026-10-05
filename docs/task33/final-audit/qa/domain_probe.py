"""New external audit probes; existing assertions/application remain unchanged."""
import json
from pathlib import Path
import os
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from catalog.models import Activity, OfferingGroup, Organization, Place, Program
from catalog.services import organization_ownership, publication
from catalog.services.filtering import PlaceListFilters
from catalog.services.pricing_plans import replace_nested_pricing
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory

def record(key,value):
    path=Path(os.environ['TASK33_QA_OUTPUT'])/'domain-observations.json'
    data=json.loads(path.read_text()) if path.exists() else {}
    data[key]=value;path.write_text(json.dumps(data,indent=2)+'\n')

class DomainCrossStageTests(TestCase):
    def test_legacy_audience_failures_retain_age_and_adult_facts(self):
        from catalog.testcases.adult_classes import PlaceAdultClassesPublicTests
        from django.utils.translation import override
        from django.utils.html import strip_tags
        from html import unescape
        case=PlaceAdultClassesPublicTests(methodName='test_catalog_has_no_adult_filter_and_renders_compact_audience')
        case.client=Client();case.setUp()
        failures=[]
        with override('ru'):
            for name in ('test_catalog_has_no_adult_filter_and_renders_compact_audience',
                         'test_place_detail_renders_children_only_and_mixed_audience'):
                try:getattr(case,name)()
                except AssertionError:failures.append(name)
            catalog=case.client.get(reverse('place_list'))
            detail=case.client.get(case.family_place.get_absolute_url())
        text=lambda response:' '.join(strip_tags(unescape(response.content.decode())).split())
        catalog_text=text(catalog);detail_text=text(detail)
        self.assertEqual(len(failures),2);self.assertEqual(detail.status_code,200)
        self.assertIn('6–17',detail_text);self.assertIn('Взрослые группы',detail_text)
        self.assertIn('Взрослые',catalog_text)
        record('legacy_audience',{'unchanged_failures':failures,'detail_http':200,
            'detail_age_value_retained':True,'detail_adult_label_retained':True,
            'catalog_short_adult_label_retained':True,'catalog_exact_old_long_label':'Взрослые группы' in catalog_text,
            'detail_exact_old_age_suffix':'6–17 лет' in detail_text,
            'classification':'SOURCE_AND_RUNTIME_PRESENTATION_EXPECTATION_FACTS_RETAINED'})

    def search_ids(self,**params):
        from catalog.repositories.django_repositories import DjangoPlaceRepository
        filters=PlaceListFilters.from_request(RequestFactory().get('/places/',params))
        return set(filters.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))

    def test_new_standalone_writer_offer_disappears_on_category_age(self):
        place=create_quality_place(name_az='Standalone new audit lesson',category='EDU',age_from=4,age_to=8)
        payload={'pricing_schema_version':2,'activities':[{'id':None,'name_az':'Standalone lesson','groups':[
            {'id':None,'name_az':'Known age group','age_from':4,'age_to':8,'pricing_plans':[{'product_type':'lesson','price':'25'}]}]}]}
        replace_nested_pricing(place,payload)
        activity=Activity.objects.get(place=place)
        general=place.pk in self.search_ids();age=place.pk in self.search_ids(age='5')
        combined=place.pk in self.search_ids(category='EDU',age='5')
        self.assertTrue(general);self.assertTrue(age);self.assertFalse(combined)
        self.assertEqual(activity.program_snapshot,{})
        record('standalone_search',{'real_nested_writer':True,'general_found':general,'age_only_found':age,
            'category_age_found':combined,'snapshot_empty':not activity.program_snapshot,
            'classification':'CONFIRMED_P2_PRODUCT_GAP_NOT_EXPECTED_PASS_OF_ORIGINAL_IDEA'})

    def test_program_category_writer_works_but_subcategory_has_no_writer(self):
        User=get_user_model();owner=User.objects.create_user('domain_org_owner');staff=User.objects.create_superuser('domain_staff','audit@example.invalid','synthetic')
        org=organization_ownership.create_organization(actor=owner,values={'name_az':'Audit organization'})
        place=create_quality_place(owner=owner,created_by=owner,name_az='Shared audit branch')
        organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk)
        place.refresh_from_db()
        program=Program.objects.create(organization=org,created_by=owner,name_az='Approved program')
        revision=publication.propose(actor=owner,target_type='program',target_id=program.pk,
            patch={'name_az':'Approved program','category':'EDU'},schema_version=publication.SCHEMA_VERSION,expected_version=program.content_version)
        publication.review(actor=staff,revision_id=revision.pk,version=revision.version,approve=True)
        program.refresh_from_db()
        replace_nested_pricing(place,{'pricing_schema_version':2,'activities':[{'id':None,'program_id':program.pk,'groups':[
            {'id':None,'name_az':'Program age group','age_from':4,'age_to':8,'pricing_plans':[{'product_type':'lesson','price':'25'}]}]}]})
        category_found=place.pk in self.search_ids(category='EDU',age='5')
        sub=ensure_quality_subcategory('EDU')
        Place.objects.filter(pk=place.pk).update(subcategory=sub)
        sub_found=place.pk in self.search_ids(subcategory=str(sub.pk),age='5')
        self.assertTrue(category_found);self.assertFalse(sub_found)
        self.assertNotIn('subcategory',publication.fields_for('program'));self.assertNotIn('category',publication.fields_for('activity'))
        record('program_search',{'actual_propose_review_used':True,'category_age_found':category_found,
            'place_subcategory_known_but_offer_subcategory_age_found':sub_found,'program_subcategory_writer':False,
            'classification':'CATEGORY_PROVEN_SUBCATEGORY_PRODUCT_GAP'})

    def legacy_context(self,name):
        from catalog.testcases.admin import TestAdminOwnershipModerationUX
        case=TestAdminOwnershipModerationUX(methodName=name);case.client=Client();case.setUp();return case

    def test_legacy_claim_failure_is_publication_expectation(self):
        case=self.legacy_context('test_admin_can_approve_request_with_direct_button_url')
        failed=False
        try:case.test_admin_can_approve_request_with_direct_button_url()
        except AssertionError:failed=True
        case.request_item.refresh_from_db();case.place.refresh_from_db()
        self.assertTrue(failed);self.assertEqual(case.request_item.status,'APPROVED')
        self.assertEqual(case.place.owner_id,case.owner_user.pk);self.assertFalse(case.place.is_active)
        record('legacy_claim',{'unchanged_assertion_failed':failed,'claim_approved':True,'owner_changed':True,
            'inactive_retained':True,'classification':'ACCEPTED_MANAGEMENT_IS_NOT_PUBLICATION_CONTRACT'})

    def test_legacy_unpublish_missing_version_then_current_version_works(self):
        case=self.legacy_context('test_place_admin_can_unpublish_place_from_change_form')
        failed=False
        try:case.test_place_admin_can_unpublish_place_from_change_form()
        except AssertionError:failed=True
        case.place.refresh_from_db();self.assertTrue(case.place.is_active)
        response=case.client.post(reverse('admin:catalog_place_change',args=[case.place.pk]),
            {'_unpublish_place':'1','unpublish_version':case.place.content_version})
        case.place.refresh_from_db()
        self.assertTrue(failed);self.assertEqual(response.status_code,302);self.assertFalse(case.place.is_active)
        self.assertEqual(case.place.status,'draft')
        record('legacy_unpublish',{'unchanged_assertion_failed':failed,'only_missing_version_replay':True,
            'current_version_http':response.status_code,'draft_inactive':True,'classification':'LEGACY_FORM_VERSION_FIXTURE'})

    def test_legacy_ratings_pagination_reason_is_recorded_without_blanket_attribution(self):
        from catalog.testcases.admin import TestPlaceRatingsAdmin
        TestPlaceRatingsAdmin.setUpTestData()
        case=TestPlaceRatingsAdmin(methodName='test_changelist_pagination_preserves_filters_search_and_sorting');case.client=Client();case.setUp()
        failure=''
        try:case.test_changelist_pagination_preserves_filters_search_and_sorting()
        except AssertionError as exc:failure=str(exc).splitlines()[0][:220]
        finally:case.doCleanups()
        rows=Place.objects.filter(name__startswith='Ratings page ')
        self.assertTrue(failure);self.assertEqual(rows.count(),5)
        from django.contrib import admin
        from catalog.models import PlaceReviewsByClub
        pagination_admin=admin.site._registry[PlaceReviewsByClub]
        previous=pagination_admin.list_per_page
        district=rows.values_list('district',flat=True).first()
        query={'category__code__exact':'EDU','district':district,'is_active__exact':'1',
               'is_verified__exact':'1','q':'Пагинация','o':'-1'}
        try:
            pagination_admin.list_per_page=2
            url=reverse('admin:catalog_placereviewsbyclub_changelist')
            for page in (1,2,3):
                response=case.client.get(url,{**query,'p':page})
                self.assertContains(response,'km-changelist-pagination__nav')
                self.assertContains(response,f'aria-current="page">{page}')
                self.assertContains(response,'district='+district)
        finally:pagination_admin.list_per_page=previous
        record('legacy_pagination',{'unchanged_assertion_failure':failure,'fixture_count':rows.count(),
            'stored_districts':sorted(set(rows.values_list('district',flat=True))),
            'query_district':'baku','matching_district_count':rows.filter(district='baku').count(),
            'same_query_actual_district_three_pages_passed':True,
            'classification':'CONFIRMED_FIXTURE_QUERY_DISTRICT_MISMATCH_NOT_PAGINATION_DEFECT'})
