"""Stage08 approved content, candidate patches, readiness and propagation."""
import importlib.util
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.test import TestCase
from catalog.models import Place, Organization, Program, Activity, VolunteerPlaceRevision
from catalog.testcases.utils import create_quality_place

class PublicationFixture:
    def setUp(self):
        U=get_user_model();self.owner=U.objects.create_user(username='pub_owner');self.other=U.objects.create_user(username='pub_other');self.staff=U.objects.create_superuser(username='pub_staff',email='staff@example.invalid',password='synthetic')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True,with_pricing_plan=True,with_schedule_days=True)
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.publication'),'Unified publication service missing')
        from catalog.services import publication
        self.s=publication
    def propose(self,patch,**kw):
        self.place.refresh_from_db();values=dict(actor=self.owner,target_type='place',target_id=self.place.pk,patch=patch,schema_version=1,expected_version=self.place.content_version,revision_version=0,submit=True,explicit_save=True);values.update(kw);return self.s.propose(**values)
    def approve(self,r,**kw):return self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=True,**kw)
class PublicationTests(PublicationFixture,TestCase):
    def test_pending_and_rejected_keep_approved_live(self):
        old=self.place.description_az;r=self.propose({'description_az':'Yeni təsvir'});self.place.refresh_from_db();self.assertEqual(self.place.description_az,old);self.assertTrue(self.place.is_public)
        self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=False,note='Düzəliş');self.place.refresh_from_db();self.assertEqual(self.place.description_az,old);self.assertTrue(self.place.is_public)
    def test_price_change_does_not_conflict_with_description_approval(self):
        r=self.propose({'description_az':'Yeni təsvir'});v=self.place.content_version
        self.s.propose(actor=self.owner,target_type='place',target_id=self.place.pk,patch={'price_from':'44.00'},schema_version=1,expected_version=v,revision_version=r.version,submit=True,explicit_save=True)
        r.refresh_from_db();self.approve(r);self.place.refresh_from_db();self.assertEqual(str(self.place.price_from),'44.00');self.assertEqual(self.place.description_az,'Yeni təsvir')
    def test_overlapping_live_change_refuses_stale_approval(self):
        r=self.propose({'description_az':'Candidate'});Place.objects.filter(pk=self.place.pk).update(description_az='Fresh')
        with self.assertRaises(ValidationError):self.approve(r)
        self.place.refresh_from_db();self.assertEqual(self.place.description_az,'Fresh')
    def test_schema_and_source_conflicts_do_not_write(self):
        for kw in ({'schema_version':2},{'expected_version':999}):
            with self.assertRaises(ValidationError):self.propose({'description_az':'Bad'},**kw)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
    def test_dependent_price_conditions_bundle_wholly_gated(self):
        old=self.place.price_from;r=self.propose({'price_from':'65.00','extra_conditions_az':'Aylıq şərtlər'});self.place.refresh_from_db();self.assertEqual(self.place.price_from,old)
        self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=False,note='No');self.place.refresh_from_db();self.assertEqual(self.place.price_from,old)
    def test_nonexplicit_save_never_applies_price_or_nature(self):
        old=self.place.price_from;r=self.propose({'price_from':'91.00','nature':'public_space'},explicit_save=False);self.place.refresh_from_db();self.assertEqual(self.place.price_from,old);self.assertIsNone(self.place.nature)
    def test_foreign_actor_and_owner_publish_denied(self):
        with self.assertRaises(PermissionDenied):self.propose({'description_az':'No'},actor=self.other)
        r=self.propose({'description_az':'No'})
        with self.assertRaises(PermissionDenied):self.s.review(actor=self.owner,revision_id=r.pk,version=r.version,approve=True)
    def test_handover_refuses_approval(self):
        r=self.propose({'description_az':'Candidate'});Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        with self.assertRaises((PermissionDenied,ValidationError)):self.approve(r)
    def test_approval_changes_only_patch_and_uses_new_version(self):
        old=self.place.phone1;r=self.propose({'description_az':'Yeni təsvir'});Place.objects.filter(pk=self.place.pk).update(phone1='0501112223');self.approve(r);self.place.refresh_from_db();self.assertEqual(self.place.phone1,'0501112223');self.assertEqual(self.place.description_az,'Yeni təsvir');self.assertGreater(self.place.content_version,1)
    def test_replay_approval_rejected(self):
        r=self.propose({'description_az':'Yeni təsvir'});self.approve(r)
        with self.assertRaises(ValidationError):self.approve(r)
    def test_optional_photos_coordinates_and_business_website(self):
        from catalog.services.place_readiness import evaluate_place_readiness
        self.place.photo='';self.place.cover_photo='';self.place.lat=None;self.place.lng=None;self.place.phone1='';self.place.website='https://example.invalid';self.assertTrue(evaluate_place_readiness(self.place).is_ready)
    def test_public_space_without_contacts_is_ready(self):
        from catalog.services.place_readiness import evaluate_place_readiness
        self.place.nature='public_space';self.place.phone1='';self.place.phone2='';self.place.phone3='';self.place.website='';self.assertTrue(evaluate_place_readiness(self.place).is_ready)
    def test_confirmed_closure_keeps_detail_and_excludes_catalog(self):
        from catalog.services.content_quality import public_place_queryset,published_place_queryset
        r=self.propose({'operating_state':'closed'});self.approve(r);self.assertFalse(public_place_queryset(Place.objects.filter(pk=self.place.pk)).exists());self.assertTrue(published_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())
    def test_old_inactive_is_not_exposed_by_closure(self):
        Place.objects.filter(pk=self.place.pk).update(is_active=False,status='draft');from catalog.services.content_quality import published_place_queryset
        self.assertFalse(published_place_queryset(Place.objects.filter(pk=self.place.pk)).exists())
    def test_program_propagates_only_common_active_links(self):
        org=Organization.objects.create(owner=self.owner,name_az='Təşkilat');Place.objects.filter(pk=self.place.pk).update(organization=org);p=Program.objects.create(organization=org,name_az='Köhnə',description_az='Təsvir',status='published')
        from django.utils import timezone
        Program.objects.filter(pk=p.pk).update(approved_at=timezone.now());p.refresh_from_db();a=Activity.objects.create(place=self.place,program=p,name_az='Local',supplement_az='Only local');d=Activity.objects.create(place=self.place,name_az='Detached');r=self.s.propose(actor=self.owner,target_type='program',target_id=p.pk,patch={'name_az':'Yeni'},schema_version=1,expected_version=p.content_version,revision_version=0,submit=True,explicit_save=True);self.approve(r);a.refresh_from_db();d.refresh_from_db();p.refresh_from_db();self.assertEqual(a.program_snapshot['name_az'],'Yeni');self.assertEqual(a.source_program_version,p.content_version);self.assertEqual(a.name_az,'Local');self.assertEqual(a.supplement_az,'Only local');self.assertEqual(d.name_az,'Detached');self.assertFalse(d.program_snapshot)
    def test_revoked_candidate_author_cannot_be_approved(self):
        from catalog.models import OwnerTeamMembership
        grant=OwnerTeamMembership.objects.create(place=self.place,owner=self.owner,member=self.other,role='EDITOR')
        r=self.propose({'description_az':'Employee proposal'},actor=self.other);grant.is_active=False;grant.save()
        with self.assertRaises((PermissionDenied,ValidationError)):self.approve(r)
        self.place.refresh_from_db();self.assertNotEqual(self.place.description_az,'Employee proposal')
    def test_revert_candidate_field_to_live_removes_pending_change(self):
        original=self.place.description_az;r=self.propose({'description_az':'Candidate'})
        r=self.propose({'description_az':original},revision_version=r.version)
        self.assertNotIn('description_az',r.payload)
    def test_plan_conditions_candidate_keeps_amount_gated(self):
        import copy
        old=copy.deepcopy(self.place.pricing_plans);proposal=copy.deepcopy(old);proposal[0]['title_az']='Aylıq paket';proposal[0]['price']='88.00';r=self.propose({'pricing_plans':proposal})
        amounts=copy.deepcopy(old);amounts[0]['price']='92.00';r=self.propose({'pricing_plans':amounts},revision_version=r.version)
        self.place.refresh_from_db();self.assertEqual(self.place.pricing_plans[0]['price'],old[0]['price']);self.assertEqual(r.payload['pricing_plans'][0]['title_az'],'Aylıq paket')
    def test_gallery_delete_is_pending_until_approval(self):
        from catalog.models import PlacePhoto
        from django.test import RequestFactory
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        photo=PlacePhoto.objects.create(place=self.place,image='places/gallery/approved.jpg')
        request=RequestFactory().post('/synthetic');request.user=self.owner
        result=OwnerPlacesController.build_default().delete_gallery_photo(request=request,place_id=self.place.pk,photo_id=photo.pk)
        self.assertTrue(result.ok);self.assertTrue(PlacePhoto.objects.filter(pk=photo.pk).exists(),'Approved gallery was deleted before moderation')
        r=VolunteerPlaceRevision.objects.get(place=self.place);self.approve(r);self.assertFalse(PlacePhoto.objects.filter(pk=photo.pk).exists())
    def test_owner_form_posts_candidate_and_refuses_stale_token(self):
        import json
        from django.test import RequestFactory
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        from catalog.forms import OwnerPlaceEditForm
        from catalog.services.publication_forms import version_token
        from catalog.services.place_schedule import serialize_place_schedule
        old=self.place.description_az;token=version_token(self.place)
        data={'description_az':'Owner pending description','publication_token':token,'pricing_plans':json.dumps(self.place.pricing_plans),'structured_schedule':json.dumps(serialize_place_schedule(self.place))}
        request=RequestFactory().post('/synthetic',data);request.user=self.owner
        result=OwnerPlacesController.build_default().save_edit_form(request=request,place_id=self.place.pk,data=data,files={},draft_save_only=True)
        self.assertTrue(result.ok, str(result.form.errors));self.place.refresh_from_db();self.assertEqual(self.place.description_az,old);self.assertTrue(self.place.is_public)
        result=OwnerPlacesController.build_default().save_edit_form(request=request,place_id=self.place.pk,data=data,files={},draft_save_only=True)
        self.assertFalse(result.ok)
    def test_csv_stale_source_cannot_modify_live(self):
        from io import StringIO
        import csv,tempfile,os
        from django.core.management import call_command,CommandError
        keys=['category','district','metro','address','age_from','age_to','price_from','price_to','phone1','instagram','website','name_ru','name_en','name_az','description_ru','description_en','description_az','place_id','base_content_version','revision_version']
        row={k:str(getattr(self.place,k,'')) for k in keys};row.update(category=self.place.category_id,place_id=self.place.pk,base_content_version=999,revision_version=0,description_az='Stale import')
        with tempfile.TemporaryDirectory() as directory:
            path=os.path.join(directory,'synthetic.csv')
            with open(path,'w') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerow(row)
            with self.assertRaises(CommandError):call_command('import_places',path,actor_id=self.staff.pk,schema_version=1,stdout=StringIO())
        self.place.refresh_from_db();self.assertNotEqual(self.place.description_az,'Stale import')
    def admin_form(self,**overrides):
        import json
        from catalog.domain_admin.place import PlaceAdminForm
        from catalog.services.place_schedule import serialize_place_schedule
        initial=PlaceAdminForm(instance=self.place)
        data=dict(initial.initial);data.update(pricing_plans=json.dumps(self.place.pricing_plans),structured_schedule=json.dumps(serialize_place_schedule(self.place)),_save_draft='1');data.update(overrides)
        form=PlaceAdminForm(data=data,instance=Place.objects.get(pk=self.place.pk));self.assertTrue(form.is_valid(),str(form.errors));return form
    def test_admin_draft_preserves_live_and_metadata(self):
        from django.test import RequestFactory
        from django.contrib import admin
        from catalog.domain_admin.place import PlaceAdmin
        old=self.place.description_az;form=self.admin_form(description_az='Admin candidate',is_home_recommended=True)
        request=RequestFactory().post('/synthetic',{'_save_draft':'1'});request.user=self.staff
        PlaceAdmin(Place,admin.site).save_model(request,form.instance,form,True)
        self.place.refresh_from_db();self.assertEqual(self.place.description_az,old);self.assertTrue(self.place.is_public);self.assertTrue(self.place.is_home_recommended)
    def test_admin_wrong_import_schema_refused(self):
        import json
        from django.test import RequestFactory
        from django.contrib import admin
        from catalog.domain_admin.place import PlaceAdmin
        request=RequestFactory().post('/synthetic',data=json.dumps({'schema_version':2}),content_type='application/json');request.user=self.staff
        response=PlaceAdmin(Place,admin.site).validate_pricing_import_view(request);self.assertEqual(response.status_code,409)
    def test_amount_only_plan_explicit_save_keeps_id_and_live(self):
        import copy
        plans=copy.deepcopy(self.place.pricing_plans);pk=plans[0]['id'];plans[0]['price']='99.00';self.propose({'pricing_plans':plans});self.place.refresh_from_db();self.assertEqual(self.place.pricing_plans[0]['id'],pk);self.assertEqual(self.place.pricing_plans[0]['price'],'99.00')
    def test_schedule_explicit_save_is_immediate(self):
        from catalog.services.place_schedule import serialize_place_schedule
        days=serialize_place_schedule(self.place)
        day=next(d for d in days if not d['is_closed']);day['intervals']=[{'start':'09:00','end':'11:00'}]
        self.propose({'structured_schedule':days});self.place.refresh_from_db();stored=serialize_place_schedule(self.place);self.assertEqual(next(d for d in stored if not d['is_closed'])['intervals'][0]['start'],'09:00')
    def test_foreign_tariff_id_rejected_before_candidate_write(self):
        foreign=create_quality_place(with_pricing_plan=True);plans=foreign.pricing_plans
        with self.assertRaises(ValidationError):self.propose({'pricing_plans':plans})
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
    def test_inactive_author_refuses_approval(self):
        r=self.propose({'description_az':'Pending inactive author'});self.owner.is_active=False;self.owner.save(update_fields=['is_active'])
        with self.assertRaises(PermissionDenied):self.approve(r)
    def test_pending_schema_mutation_refuses_approval(self):
        r=self.propose({'description_az':'Candidate'});VolunteerPlaceRevision.objects.filter(pk=r.pk).update(schema_version=2)
        with self.assertRaises(ValidationError):self.approve(r)
    def test_program_archived_activity_snapshot_is_preserved(self):
        from django.utils import timezone
        org=Organization.objects.create(owner=self.owner,name_az='Təşkilat');Place.objects.filter(pk=self.place.pk).update(organization=org);p=Program.objects.create(organization=org,name_az='Old',description_az='Description',status='published',approved_at=timezone.now());a=Activity.objects.create(place=self.place,program=p,name_az='Local');before=a.program_snapshot;a.archive()
        r=self.s.propose(actor=self.owner,target_type='program',target_id=p.pk,patch={'name_az':'Yeni'},schema_version=1,expected_version=p.content_version,revision_version=0,submit=True,explicit_save=True);self.approve(r);a.refresh_from_db();self.assertEqual(a.program_snapshot,before)

from django.test import TransactionTestCase
from django.db import close_old_connections,transaction
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier,Event

class PublicationConcurrencyTests(TransactionTestCase):
    def setUp(self):
        U=get_user_model();self.owner=U.objects.create_user(username='race_pub_owner');self.staff=U.objects.create_superuser(username='race_pub_staff',email='staff@example.invalid',password='synthetic');self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True,with_pricing_plan=True,with_schedule_days=True)
        from catalog.services import publication
        self.s=publication
    def propose(self,kind,pk,patch,source=1,version=0):return self.s.propose(actor=self.owner,target_type=kind,target_id=pk,patch=patch,schema_version=1,expected_version=source,revision_version=version,submit=True,explicit_save=True)
    def race(self,functions):
        barrier=Barrier(len(functions))
        def run(fn):
            close_old_connections();barrier.wait(timeout=5)
            try:
                try:fn();return True
                except (ValidationError,PermissionDenied):return False
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=len(functions)) as pool:return sorted(list(pool.map(run,functions)))
    def test_two_approvals_apply_candidate_once(self):
        r=self.propose('place',self.place.pk,{'description_az':'Concurrent approved'})
        fn=lambda:self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=True)
        self.assertEqual(self.race([fn,fn]),[False,True]);self.place.refresh_from_db();self.assertEqual(self.place.content_version,2);self.assertEqual(self.place.description_az,'Concurrent approved')
    def test_price_description_race_conflict_retry_preserves_both(self):
        r=self.propose('place',self.place.pk,{'description_az':'Concurrent description'})
        result=self.race([lambda:self.propose('place',self.place.pk,{'price_from':'73.00'},version=r.version),lambda:self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=True)])
        self.assertEqual(result,[False,True]);self.place.refresh_from_db();r.refresh_from_db()
        if r.status=='pending':self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=True)
        else:self.propose('place',self.place.pk,{'price_from':'73.00'},source=self.place.content_version,version=r.version)
        self.place.refresh_from_db();self.assertEqual(self.place.description_az,'Concurrent description');self.assertEqual(self.place.price_from,73)
    def test_program_approval_and_new_activity_serialize_common_pointer(self):
        from django.utils import timezone
        org=Organization.objects.create(owner=self.owner,name_az='Org');Place.objects.filter(pk=self.place.pk).update(organization=org);p=Program.objects.create(organization=org,name_az='Old',description_az='Description',status='published',approved_at=timezone.now());r=self.propose('program',p.pk,{'name_az':'Yeni'})
        self.assertEqual(self.race([lambda:self.s.review(actor=self.staff,revision_id=r.pk,version=r.version,approve=True),lambda:Activity.objects.create(place=self.place,program=p,name_az='Local')]),[True,True])
        p.refresh_from_db();a=Activity.objects.get(program=p);self.assertEqual(a.program_snapshot['name_az'],'Yeni');self.assertEqual(a.source_program_version,p.content_version);self.assertEqual(a.name_az,'Local')
    def test_group_proposal_rejects_relocated_ancestor_after_wait(self):
        from catalog.models import OfferingGroup
        org=Organization.objects.create(owner=self.owner,name_az='Org');other=create_quality_place(owner=self.owner,created_by=self.owner);Place.objects.filter(pk__in=[self.place.pk,other.pk]).update(organization=org);self.place.refresh_from_db();other.refresh_from_db();a=Activity.objects.create(place=self.place);g=OfferingGroup.objects.create(activity=a,name_az='Group');entered=Event();finished=Event()
        def edit():
            close_old_connections();entered.set()
            try:
                try:self.propose('offering_group',g.pk,{'teachers_text':'Stale parent'});return True
                except ValidationError:return False
            finally:finished.set();close_old_connections()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=org.pk);future=pool.submit(edit);self.assertTrue(entered.wait(5));self.assertFalse(finished.wait(.5));a.place=other;a.save()
            self.assertFalse(future.result(timeout=10))
        self.assertFalse(VolunteerPlaceRevision.objects.filter(offering_group=g).exists())

class PublicationIngressTests(PublicationFixture,TestCase):
    def test_owner_form_can_revert_existing_pending_field(self):
        import json
        from django.test import RequestFactory
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        from catalog.services.publication_forms import version_token
        from catalog.services.place_schedule import serialize_place_schedule
        old=self.place.description_az;r=self.propose({'description_az':'Pending description'})
        data={'description_az':old,'publication_token':version_token(self.place),'pricing_plans':json.dumps(self.place.pricing_plans),'structured_schedule':json.dumps(serialize_place_schedule(self.place))}
        request=RequestFactory().post('/synthetic',data);request.user=self.owner
        result=OwnerPlacesController.build_default().save_edit_form(request=request,place_id=self.place.pk,data=data,files={},draft_save_only=True)
        self.assertTrue(result.ok,str(result.form.errors));r.refresh_from_db();self.assertNotIn('description_az',r.payload)
    def test_legacy_publication_approval_cannot_ignore_candidate(self):
        from catalog.models import PlaceOwnershipRequest
        from catalog.services.organization_ownership import moderate_place_request
        r=self.propose({'description_az':'Candidate via old request'})
        request=PlaceOwnershipRequest.objects.create(place=self.place,applicant=self.owner,request_kind='PUBLICATION')
        moderate_place_request(actor=self.staff,request_id=request.pk,new_status='APPROVED');self.place.refresh_from_db();self.assertEqual(self.place.description_az,'Candidate via old request')
    def test_owner_create_readiness_without_photos_coordinates_phone(self):
        import json
        from catalog.forms import OwnerPlaceCreateForm
        from catalog.services.place_schedule import serialize_place_schedule
        plans=self.place.pricing_plans
        for p in plans:p.pop('id',None)
        data={'name_az':'Yeni məkan','description_az':'Uşaqlar üçün dərnək','category':self.place.category_id,'subcategory':self.place.subcategory_id,'age_from':5,'age_to':12,'region':'sumgait','district':'','address':'Sumqayıt şəhəri, Sülh küçəsi 10','website':'https://example.invalid','phone1':'','pricing_plans':json.dumps(plans),'structured_schedule':json.dumps(serialize_place_schedule(self.place)),'schedule_mode':'regular','price_mode':'tariffs'}
        form=OwnerPlaceCreateForm(data=data);self.assertTrue(form.is_valid(),str(form.errors))
    def test_group_invalid_age_refused_before_candidate_write(self):
        from catalog.models import OfferingGroup
        a=Activity.objects.create(place=self.place);g=OfferingGroup.objects.create(activity=a,name_az='Group')
        with self.assertRaises(ValidationError):self.s.propose(actor=self.owner,target_type='offering_group',target_id=g.pk,patch={'age_from':12,'age_to':3},schema_version=1,expected_version=1,revision_version=0,submit=True,explicit_save=True)
        self.assertFalse(VolunteerPlaceRevision.objects.filter(offering_group=g).exists())
