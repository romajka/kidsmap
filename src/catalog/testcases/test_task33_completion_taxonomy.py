"""Real approved taxonomy writers, compatibility and one-group search."""
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.urls import reverse
from catalog.models import Activity, Program
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services import pricing_plans, publication, catalog_search
from catalog.services.filtering import PlaceListFilters
from catalog.testcases.test_task33_ownership import OwnershipFixture
from catalog.testcases.utils import ensure_quality_subcategory

class CompletionTaxonomyTests(OwnershipFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.sub=ensure_quality_subcategory('EDU');self.artsub=ensure_quality_subcategory('ART')

    def payload(self,category='EDU',subcategory=None):
        return {'pricing_schema_version':2,'activities':[{'name_az':'Real writer lesson',
            'category_id':category,'subcategory_id':subcategory or self.sub.pk,
            'groups':[{'name_az':'Age five','age_from':4,'age_to':8,
                'pricing_plans':[{'product_type':'lesson','price':'25'}]}]}]}

    def search(self,**params):
        filters=PlaceListFilters.from_request(RequestFactory().get('/places/',params))
        return list(filters.apply(DjangoPlaceRepository().active_queryset()).values_list('pk',flat=True))

    def test_standalone_real_writer_search_count_and_roundtrip(self):
        pricing_plans.replace_nested_pricing(self.place,self.payload())
        activity=self.place.activities.get()
        self.assertEqual(activity.category_id,'EDU');self.assertEqual(activity.subcategory_id,self.sub.pk)
        self.assertIn(self.place.pk,self.search(category='EDU',subcategory=self.sub.pk,age=5))
        self.assertNotIn(self.place.pk,self.search(category='ART',age=5))
        self.assertNotIn(self.place.pk,self.search(category='EDU',age=12))
        cats,subs=catalog_search.taxonomy_counts(DjangoPlaceRepository().active_queryset())
        self.assertEqual(cats['EDU'],1);self.assertEqual(subs[str(self.sub.pk)],1)
        self.assertEqual(pricing_plans.serialize_nested_pricing(self.place)['activities'][0]['subcategory_id'],self.sub.pk)

    def test_mismatched_nested_taxonomy_rejected_atomically(self):
        with self.assertRaises(ValidationError):pricing_plans.replace_nested_pricing(self.place,self.payload(subcategory=self.artsub.pk))
        self.assertFalse(self.place.activities.exists())

    def test_unknown_legacy_stays_unknown_without_place_inference(self):
        self.assertIn('category',{f.name for f in Activity._meta.fields})
        activity=Activity.objects.create(place=self.place,name_az='Legacy',status='published')
        self.assertIsNone(activity.category_id);self.assertIsNone(activity.subcategory_id)
        self.assertIn(self.place.pk,self.search())
        self.assertNotIn(self.place.pk,self.search(category='EDU',age=5))

    def test_approved_program_snapshot_subcategory_detach_and_pending(self):
        self.assertIn('subcategory',{f.name for f in Program._meta.fields})
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Approved common',category_id='EDU',subcategory=self.sub,status='published',approved_at=timezone.now())
        payload=self.payload();payload['activities'][0]['program_id']=program.pk
        payload['activities'][0]['category_id']='ART';payload['activities'][0]['subcategory_id']=self.artsub.pk
        pricing_plans.replace_nested_pricing(self.place,payload)
        activity=self.place.activities.get()
        self.assertEqual(activity.program_snapshot['subcategory_id'],self.sub.pk)
        self.assertIn(self.place.pk,self.search(category='EDU',subcategory=self.sub.pk,age=5))
        revision=publication.propose(actor=self.b,target_type='program',target_id=program.pk,
            patch={'category':'ART','subcategory':self.artsub.pk},schema_version=1,
            expected_version=program.content_version,revision_version=0,submit=True)
        self.assertIn(self.place.pk,self.search(category='EDU',subcategory=self.sub.pk,age=5))
        publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=False,note='Reject')
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        activity.refresh_from_db();self.assertIsNone(activity.program_id)
        self.assertEqual(activity.category_id,'EDU');self.assertEqual(activity.subcategory_id,self.sub.pk)
        self.assertIn(self.place.pk,self.search(category='EDU',subcategory=self.sub.pk,age=5))

    def test_standalone_publication_pending_rejected_and_stale_preserve_live(self):
        self.assertIn('category',{f.name for f in Activity._meta.fields})
        activity=Activity.objects.create(place=self.place,name_az='Approved',status='published',category_id='EDU',subcategory=self.sub)
        kwargs=dict(actor=self.a,target_type='activity',target_id=activity.pk,schema_version=1,expected_version=1,revision_version=0,submit=True)
        revision=publication.propose(patch={'category':'ART','subcategory':self.artsub.pk},**kwargs)
        activity.refresh_from_db();self.assertEqual(activity.category_id,'EDU')
        publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=False,note='No')
        activity.refresh_from_db();self.assertEqual(activity.category_id,'EDU')
        with self.assertRaises(ValidationError):publication.propose(patch={'category':'EDU','subcategory':self.artsub.pk},**{**kwargs,'revision_version':revision.version+1})

    def test_program_approval_propagates_then_stale_taxonomy_refuses(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Common',category_id='EDU',subcategory=self.sub,status='published',approved_at=timezone.now())
        payload=self.payload();payload['activities'][0]['program_id']=program.pk
        pricing_plans.replace_nested_pricing(self.place,payload)
        revision=publication.propose(actor=self.b,target_type='program',target_id=program.pk,
            patch={'category':'ART','subcategory':self.artsub.pk},schema_version=1,expected_version=1,revision_version=0,submit=True)
        publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        self.assertIn(self.place.pk,self.search(category='ART',subcategory=self.artsub.pk,age=5))
        self.assertNotIn(self.place.pk,self.search(category='EDU',age=5))
        program.refresh_from_db();revision.refresh_from_db()
        revision=publication.propose(actor=self.b,target_type='program',target_id=program.pk,
            patch={'category':'EDU','subcategory':self.sub.pk},schema_version=1,expected_version=program.content_version,revision_version=revision.version,submit=True)
        Program.objects.filter(pk=program.pk).update(subcategory=None)
        with self.assertRaises(ValidationError):publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        self.assertIn(self.place.pk,self.search(category='ART',subcategory=self.artsub.pk,age=5))

    def test_detached_taxonomy_clear_does_not_resurrect_old_snapshot(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Detach',category_id='EDU',subcategory=self.sub,status='published',approved_at=timezone.now())
        activity=Activity.objects.create(place=self.place,program=program,status='published')
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        activity.refresh_from_db()
        revision=publication.propose(actor=self.a,target_type='activity',target_id=activity.pk,
            patch={'category':None,'subcategory':None},schema_version=1,expected_version=activity.content_version,revision_version=0,submit=True)
        publication.review(actor=self.admin,revision_id=revision.pk,version=revision.version,approve=True)
        activity.refresh_from_db()
        self.assertIsNone(activity.category_id)
        self.assertIsNone(activity.program_snapshot.get('category_id'))

    def test_program_http_rejects_mismatch_and_proposes_valid_subcategory(self):
        program=Program.objects.create(organization=self.org,name_az='Workspace',category_id='EDU')
        self.client.force_login(self.b)
        url=reverse('organization_program_save',kwargs={'org_id':self.org.pk,'program_id':program.pk})
        payload={'name_az':'Workspace','category':'EDU','subcategory':self.artsub.pk,'expected_version':1,'revision_version':0,'submit':'1'}
        response=self.client.post(url,payload)
        self.assertEqual(response.status_code,400);self.assertFalse(hasattr(program,'content_revision'))
        response=self.client.post(url,{**payload,'subcategory':self.sub.pk})
        self.assertEqual(response.status_code,302)
        program.refresh_from_db();self.assertEqual(program.content_revision.payload['subcategory'],self.sub.pk)

    def test_public_activity_label_uses_own_category_not_place(self):
        from catalog.services.public_presentation import present
        activity=Activity.objects.create(place=self.place,name_az='Art at education venue',
            status='published',category_id='ART',subcategory=self.artsub)
        self.assertEqual(self.place.category_id,'EDU')
        self.assertTrue(present(activity,'az')['visible'])
        self.assertEqual(present(activity,'az')['category_label'],self.artsub.category.name_i18n('az'))

    def test_public_linked_category_label_is_approved_during_pending_and_detach(self):
        from catalog.services.public_presentation import present
        self.joined()
        self.org.status='published';self.org.approved_at=timezone.now();self.org.save()
        program=Program.objects.create(organization=self.org,name_az='Art program',status='published',
            approved_at=timezone.now(),category_id='ART',subcategory=self.artsub)
        activity=Activity.objects.create(place=self.place,program=program,status='published')
        publication.propose(actor=self.b,target_type='program',target_id=program.pk,
            patch={'category':'EDU','subcategory':self.sub.pk},schema_version=1,
            expected_version=program.content_version,revision_version=0,submit=True)
        self.assertEqual(present(activity,'az')['category_label'],self.artsub.category.name_i18n('az'))
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        activity.refresh_from_db()
        self.assertEqual(present(activity,'az')['category_label'],self.artsub.category.name_i18n('az'))

    def test_editor_unlink_roundtrip_materializes_approved_snapshot(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Approved unlink',status='published',
            approved_at=timezone.now(),category_id='ART',subcategory=self.artsub)
        activity=Activity.objects.create(place=self.place,program=program,status='published')
        from catalog.models import OfferingGroup,PricingPlan
        group=OfferingGroup.objects.create(activity=activity,name_az='Unlink group',age_from=4,age_to=8)
        PricingPlan.objects.create(offering_group=group,product_type='lesson',price='25')
        payload=pricing_plans.serialize_nested_pricing(self.place)
        self.assertEqual(payload['activities'][0]['category_id'],'ART')
        self.assertEqual(payload['activities'][0]['subcategory_id'],self.artsub.pk)
        payload['activities'][0]['program_id']=None
        pricing_plans.replace_nested_pricing(self.place,payload)
        activity.refresh_from_db()
        self.assertIsNone(activity.program_id);self.assertEqual(activity.category_id,'ART')
        self.assertEqual(activity.subcategory_id,self.artsub.pk)
        self.assertEqual(activity.name_az,'Approved unlink')
        self.assertEqual(activity.source_program_id,program.pk)
        self.assertEqual(activity.program_snapshot['category_id'],'ART')
