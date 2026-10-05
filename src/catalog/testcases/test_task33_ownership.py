"""Stage06 domain/ACL contracts, tested with actual PostgreSQL transactions."""
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest import skipUnless
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection, transaction, IntegrityError
from django.test import TestCase, TransactionTestCase, RequestFactory, Client
from django.urls import reverse
from django.utils import timezone
from catalog.models import Organization, Program, Activity, OfferingGroup, Place, PlaceOwnershipRequest, OrganizationPlaceRequest, OwnerTeamMembership, OwnerTeamInvitation, PlaceReview, PricingPlan
from catalog.testcases.utils import create_quality_place
from catalog.services.staff_roles import VOLUNTEER_GROUP


class ExistingOwnershipBreakTests(TestCase):
    def setUp(self):
        User=get_user_model()
        self.owner=User.objects.create_user(username='break_owner')
        self.other=User.objects.create_user(username='break_other')
        self.admin=User.objects.create_superuser(username='break_admin',email='admin@example.invalid',password='synthetic')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True,is_active=False,status=Place.STATUS_DRAFT)

    def test_management_claim_approval_does_not_publish(self):
        item=PlaceOwnershipRequest.objects.create(place=self.place,applicant=self.other)
        item.apply_moderation(moderator=self.admin,new_status='APPROVED')
        self.place.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.other.pk)
        self.assertFalse(self.place.is_active)
        self.assertEqual(self.place.status,'draft')
        self.assertFalse(self.place.is_verified)

    def test_model_moderation_rejects_nonreviewer(self):
        item=PlaceOwnershipRequest.objects.create(place=self.place,applicant=self.other)
        with self.assertRaises(PermissionDenied): item.apply_moderation(moderator=self.other,new_status='APPROVED')
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.owner.pk)

    def test_eleventh_place_form_is_available(self):
        for index in range(9): Place.objects.create(name=f'Independent draft {index}',name_az=f'Qaralama {index}',category=self.place.category,owner=self.owner,is_active=False,status='draft')
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        request=RequestFactory().get('/');request.user=self.owner
        result=OwnerPlacesController.build_default().build_create_form_context(request=request,draft_save_only=True)
        self.assertTrue(result.ok);self.assertIsNotNone(result.form)


    def test_legacy_create_warns_duplicate_and_allows_explicit_independent_object(self):
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        controller=OwnerPlacesController.build_default()
        request=RequestFactory().post('/');request.user=self.owner
        data={'name_az':self.place.name_az}
        before=Place.objects.count()
        warning=controller.create_place(request=request,data=data,files={},draft_save_only=True)
        self.assertFalse(warning.ok);self.assertEqual(Place.objects.count(),before)
        self.assertIn('name_az',warning.form.errors)
        allowed=controller.create_place(request=request,data={**data,'create_separate':'1'},files={},draft_save_only=True)
        self.assertTrue(allowed.ok);self.assertNotEqual(allowed.place.pk,self.place.pk)
        self.assertEqual(allowed.place.owner_id,self.owner.pk)


class OwnershipFixture:
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.organization_ownership'),'Ownership services missing')
        from catalog.services import organization_ownership
        self.service=organization_ownership
        User=get_user_model()
        self.a=User.objects.create_user(username='rights_a');self.b=User.objects.create_user(username='rights_b');self.c=User.objects.create_user(username='rights_c')
        self.admin=User.objects.create_superuser(username='rights_admin',email='admin@example.invalid',password='synthetic')
        self.volunteer=User.objects.create_user(username='rights_volunteer',is_staff=True)
        self.volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.org=Organization.objects.create(owner=self.b,created_by=self.b,name_az='Şəbəkə',phone='ORG_CONTACT')
        self.place=create_quality_place(owner=self.a,created_by=self.a,name_az='Müstəqil filial',with_subcategory=True)

    def joined(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        self.service.confirm_join(actor=self.b,request_id=item.pk)
        self.place.refresh_from_db();item.refresh_from_db()
        self.assertEqual(item.status,'approved');return item


class OrganizationOwnershipTests(OwnershipFixture,TestCase):
    def test_new_org_has_management_not_business_verification_or_publication(self):
        org=self.service.create_organization(actor=self.a,values={'name_az':'Yeni qurum'})
        self.assertEqual((org.owner_id,org.created_by_id),(self.a.pk,self.a.pk))
        self.assertEqual(org.status,'draft');self.assertIsNone(org.ownership_verified_at)
        self.assertEqual(org.places.count(),0)

    def test_new_place_is_owned_draft_and_eleventh_is_allowed(self):
        for index in range(11):
            place=self.service.create_place(actor=self.a,values={'name_az':f'Yeni məkan {index}','category_id':self.place.category_id})
            self.assertEqual(place.owner_id,self.a.pk);self.assertFalse(place.is_active);self.assertFalse(place.is_verified)
        self.assertEqual(Place.objects.filter(owner=self.a).count(),12)

    def test_volunteer_org_proposal_gives_no_business_ownership(self):
        org=self.service.create_organization(actor=self.volunteer,values={'name_az':'Təklif'})
        self.assertIsNone(org.owner_id);self.assertEqual(org.created_by_id,self.volunteer.pk)
        with self.assertRaises(PermissionDenied):self.service.transfer_owner(actor=self.volunteer,target_type='organization',target_id=org.pk,new_owner_id=self.c.pk,expected_ownership_version=1)

    def test_create_mass_assignment_and_inactive_actor_rejected(self):
        for values in ({'name_az':'Spoof','owner_id':self.c.pk},{'name_az':'Spoof','status':'published'},{'name_az':'Spoof','id':self.place.pk},{'name_az':'Spoof','is_verified':True}):
            with self.assertRaises(ValidationError):self.service.create_place(actor=self.a,values=values)
        self.a.is_active=False;self.a.save(update_fields=['is_active'])
        with self.assertRaises(PermissionDenied):self.service.create_organization(actor=self.a,values={'name_az':'Denied'})

    def test_duplicate_warns_and_explicit_separate_creates_independent_owner(self):
        with self.assertRaises(ValidationError) as caught:self.service.create_place(actor=self.c,values={'name_az':self.place.name_az,'category_id':self.place.category_id})
        self.assertEqual(caught.exception.code,'possible_duplicate')
        second=self.service.create_place(actor=self.c,values={'name_az':self.place.name_az,'category_id':self.place.category_id},allow_separate=True)
        self.assertNotEqual(second.pk,self.place.pk);self.assertEqual(second.owner_id,self.c.pk)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk)

    def test_claim_is_pending_only_then_staff_moves_owner_without_publication(self):
        before=(self.place.status,self.place.is_active,self.place.is_verified,self.place.created_by_id)
        claim=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk)
        with self.assertRaises(PermissionDenied):self.service.moderate_claim(actor=self.c,target_type='place',request_id=claim.pk,approve=True)
        self.service.moderate_claim(actor=self.admin,target_type='place',request_id=claim.pk,approve=True)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.c.pk)
        self.assertEqual((self.place.status,self.place.is_active,self.place.is_verified,self.place.created_by_id),before)

    def test_org_claim_does_not_publish_or_verify(self):
        claim=self.service.submit_claim(actor=self.a,target_type='organization',target_id=self.org.pk)
        self.service.moderate_claim(actor=self.admin,target_type='organization',request_id=claim.pk,approve=True)
        self.org.refresh_from_db();self.assertEqual(self.org.owner_id,self.a.pk);self.assertEqual(self.org.status,'draft');self.assertIsNone(self.org.ownership_verified_at)

    def test_stale_claim_after_owner_away_and_back_fails(self):
        claim=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        self.place.owner=self.b;self.place.save(update_fields=['owner']);self.place.owner=self.a;self.place.save(update_fields=['owner'])
        with self.assertRaises(ValidationError):self.service.moderate_claim(actor=self.admin,target_type='place',request_id=claim.pk,approve=True)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk);self.assertEqual(self.place.ownership_version,3)

    def test_deleted_applicant_and_foreign_request_type_denied(self):
        claim=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        self.c.delete()
        with self.assertRaises(ValidationError):self.service.moderate_claim(actor=self.admin,target_type='place',request_id=claim.pk,approve=True)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk)

    def test_pending_join_does_not_grant_org_or_direct_team_network_rights(self):
        from catalog.services.place_access import has_place_permission
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        OwnerTeamMembership.objects.create(place=self.place,owner=self.a,member=self.c,role='MANAGER')
        with self.assertRaises(PermissionDenied):self.service.confirm_join(actor=self.c,request_id=item.pk)
        other=create_quality_place(owner=self.a,name_az='Separate sibling',with_subcategory=True)
        self.assertFalse(has_place_permission(user=self.c,place=other,permission_code='place.edit'))

    def test_dual_confirmation_and_idempotent_replay_preserve_direct_owner(self):
        item=self.joined();before=self.place.content_version
        self.service.confirm_join(actor=self.b,request_id=item.pk);self.place.refresh_from_db()
        self.assertEqual(self.place.content_version,before);self.assertEqual(self.place.owner_id,self.a.pk)
        from catalog.services.place_access import has_place_permission
        self.assertTrue(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        with self.assertRaises(PermissionDenied):self.service.confirm_join(actor=self.c,request_id=item.pk)

    def test_same_owner_one_request_confirms_both_sides(self):
        self.org.owner=self.a;self.org.save(update_fields=['owner'])
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        item.refresh_from_db();self.place.refresh_from_db()
        self.assertEqual(item.status,'approved');self.assertIsNotNone(item.place_owner_confirmed_at);self.assertIsNotNone(item.organization_owner_confirmed_at)
        self.assertEqual(self.place.organization_id,self.org.pk)

    def test_stale_consent_after_org_owner_away_and_back_rejected(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        self.org.owner=self.c;self.org.save(update_fields=['owner']);self.org.owner=self.b;self.org.save(update_fields=['owner'])
        with self.assertRaises(ValidationError):self.service.confirm_join(actor=self.b,request_id=item.pk)
        self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)

    def test_foreign_ids_and_archived_org_cannot_join(self):
        with self.assertRaises(PermissionDenied):self.service.request_join(actor=self.c,place_id=self.place.pk,organization_id=self.org.pk)
        self.org.archive()
        with self.assertRaises(ValidationError):self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)

    def test_unowned_informational_link_requires_kidsmap_and_grants_nothing(self):
        self.org.owner=None;self.org.save(update_fields=['owner'])
        self.place.owner=None;self.place.created_by=None;self.place.save(update_fields=['owner','created_by'])
        item=self.service.request_join(actor=self.admin,place_id=self.place.pk,organization_id=self.org.pk,relationship_kind='informational')
        self.service.approve_informational_join(actor=self.admin,request_id=item.pk)
        self.place.refresh_from_db();self.assertEqual(self.place.organization_id,self.org.pk)
        from catalog.services.place_access import has_place_permission
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        with self.assertRaises(PermissionDenied):self.service.approve_informational_join(actor=self.a,request_id=item.pk)

    def test_transfer_suspends_old_team_cancels_invites_and_preserves_author(self):
        member=OwnerTeamMembership.objects.create(place=self.place,owner=self.a,member=self.b,role='MANAGER')
        invite=OwnerTeamInvitation.objects.create(place=self.place,owner=self.a,email='synthetic@example.invalid')
        before=(self.place.status,self.place.is_active,self.place.created_by_id)
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        self.place.refresh_from_db();member.refresh_from_db();invite.refresh_from_db()
        self.assertFalse(member.is_active);self.assertEqual(invite.status,'CANCELED');self.assertEqual(self.place.ownership_version,2)
        self.assertEqual((self.place.status,self.place.is_active,self.place.created_by_id),before)
        with self.assertRaises(PermissionDenied):self.service.transfer_owner(actor=self.b,target_type='place',target_id=self.place.pk,new_owner_id=self.b.pk,expected_ownership_version=2)

    def test_org_transfer_invalidates_cached_network_rights_and_proof(self):
        self.joined();self.org.ownership_verified_at=timezone.now();self.org.ownership_verified_by=self.admin;self.org.save()
        stale=self.place
        self.service.transfer_owner(actor=self.b,target_type='organization',target_id=self.org.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        self.org.refresh_from_db();self.assertIsNone(self.org.ownership_verified_at)
        from catalog.services.place_access import has_place_permission
        self.assertFalse(has_place_permission(user=self.b,place=stale,permission_code='place.edit'))
        self.assertFalse(has_place_permission(user=self.c,place=stale,permission_code='place.edit'))

    def test_detach_pending_program_retains_approved_snapshot_ids_and_visibility(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Approved name',description_az='Approved common text',status='published',approved_at=timezone.now())
        activity=Activity.objects.create(place=self.place,program=program,supplement_az='Local supplement')
        group=OfferingGroup.objects.create(activity=activity,age_from=4,age_to=8,schedule_text='Local time')
        plan=PricingPlan.objects.create(place=self.place,product_type='membership',billing_mode='recurring',billing_interval='month',billing_interval_count=1,price_kind='exact',price=77)
        review=PlaceReview.objects.create(place=self.place,rating=5,text='Retained synthetic review')
        program.name_az='Pending name';program.description_az='Pending candidate';program.status='pending';program.save()
        before=(self.place.status,self.place.is_active,self.place.owner_id,self.place.slug,self.place.photo.name)
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.place.refresh_from_db();activity.refresh_from_db();group.refresh_from_db();plan.refresh_from_db()
        self.assertIsNone(self.place.organization_id);self.assertIsNone(activity.program_id)
        self.assertEqual(activity.program_snapshot['description_az'],'Approved common text');self.assertEqual(activity.source_program_id,program.pk)
        self.assertEqual(activity.supplement_az,'Local supplement');self.assertEqual(group.schedule_text,'Local time');self.assertEqual(plan.price,77)
        self.assertTrue(PlaceReview.objects.filter(pk=review.pk).exists());self.assertEqual((self.place.status,self.place.is_active,self.place.owner_id,self.place.slug,self.place.photo.name),before)
        current=self.place.content_version
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.place.refresh_from_db();self.assertEqual(self.place.content_version,current)

    def test_detach_disables_inherited_contacts_without_copy_or_hiding(self):
        self.joined();Place.objects.filter(pk=self.place.pk).update(phone1='',phone2='',phone3='',website='')
        self.assertEqual(self.service.effective_contacts(place_id=self.place.pk)['phone'],'ORG_CONTACT')
        self.service.detach(actor=self.b,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.assertEqual(self.service.effective_contacts(place_id=self.place.pk)['phone'],'')
        self.place.refresh_from_db();self.assertEqual(self.place.phone1,'');self.assertTrue(self.place.is_active)
        from catalog.services.place_access import has_place_permission
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))

    def test_archive_org_still_allows_either_side_detach(self):
        self.joined();self.org.archive()
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.place.refresh_from_db();self.assertIsNone(self.place.organization_id);self.assertTrue(self.place.is_active)

    def test_stale_full_org_and_place_saves_cannot_reverse_transfer(self):
        old_place=self.Place.objects.get(pk=self.place.pk) if hasattr(self,'Place') else Place.objects.get(pk=self.place.pk)
        old_org=Organization.objects.get(pk=self.org.pk)
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        self.service.transfer_owner(actor=self.b,target_type='organization',target_id=self.org.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        old_place.name_en='Content only';old_place.save()
        old_org.description_en='Content only';old_org.save()
        self.place.refresh_from_db();self.org.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.c.pk);self.assertEqual(self.org.owner_id,self.c.pk)
        self.assertEqual(self.place.ownership_version,2);self.assertEqual(self.org.ownership_version,2)

    def test_owner_controller_authorization_is_rechecked_at_locked_save(self):
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        stale=Place.objects.get(pk=self.place.pk)
        self.assertTrue(OwnerPlacesController._has_permission(user=self.a,place=stale,permission_code='place.edit'))
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        stale.name_en='Forbidden stale edit'
        with self.assertRaises(PermissionDenied):stale.save()
        self.place.refresh_from_db();self.assertNotEqual(self.place.name_en,'Forbidden stale edit')

    def test_stale_org_fullsave_cannot_restore_previous_ownership_proof(self):
        self.org.ownership_verified_at=timezone.now();self.org.ownership_verified_by=self.admin
        self.org.save(update_fields=['ownership_verified_at','ownership_verified_by'])
        stale=Organization.objects.get(pk=self.org.pk)
        self.service.transfer_owner(actor=self.b,target_type='organization',target_id=self.org.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
        stale.description_en='Independent content edit';stale.save()
        self.org.refresh_from_db();self.assertIsNone(self.org.ownership_verified_at);self.assertIsNone(self.org.ownership_verified_by_id)

    def test_pending_program_edit_freezes_approved_text_for_preexisting_activity(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='First draft')
        activity=Activity.objects.create(place=self.place,program=program)
        program.name_az='Approved later';program.description_az='Approved later text';program.status='published';program.approved_at=timezone.now();program.save()
        program.name_az='Pending change';program.description_az='Unapproved change';program.status='pending';program.save()
        self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        activity.refresh_from_db();self.assertEqual(activity.program_snapshot['description_az'],'Approved later text')
        self.assertEqual(activity.description_az,'Approved later text')

    def test_partial_activity_save_retains_approved_snapshot_in_database(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Approved',description_az='Retained approved',status='published',approved_at=timezone.now())
        activity=Activity.objects.create(place=self.place)
        activity.program=program;activity.save(update_fields=['program'])
        activity.refresh_from_db();self.assertEqual(activity.program_snapshot['description_az'],'Retained approved')
        self.assertEqual(activity.source_program_id,program.pk)

    def test_detach_wrong_org_and_stale_version_are_rejected(self):
        self.joined()
        other=Organization.objects.create(owner=self.a,name_az='Unrelated')
        for org,version in ((other.pk,1),(self.org.pk,99)):
            with self.assertRaises(ValidationError):self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=org,expected_ownership_version=version)
        with self.assertRaises(PermissionDenied):self.service.detach(actor=self.c,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.place.refresh_from_db();self.assertEqual(self.place.organization_id,self.org.pk)


class OwnershipEndpointTests(OwnershipFixture,TestCase):
    def url(self,action,target='place',pk=None):
        return reverse('organization_ownership_action',kwargs={'action':action,'target_type':target,'target_id':pk or self.place.pk})

    def test_foreign_ids_and_claim_approval_spoof_denied(self):
        self.client.force_login(self.c)
        response=self.client.post(self.url('join'),{'organization_id':self.org.pk},content_type='application/json')
        self.assertEqual(response.status_code,403)
        claim=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        response=self.client.post(self.url('approve-claim',pk=claim.pk),{},content_type='application/json')
        self.assertEqual(response.status_code,403)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk)

    def test_csrf_get_anonymous_and_mass_assignment_boundaries(self):
        self.client.force_login(self.a)
        self.assertEqual(self.client.get(self.url('join')).status_code,405)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.a)
        self.assertEqual(csrf.post(self.url('join'),{'organization_id':self.org.pk},content_type='application/json').status_code,403)
        self.assertEqual(Client().post(self.url('join'),{},content_type='application/json').status_code,403)
        response=self.client.post(self.url('join'),{'organization_id':self.org.pk,'place_owner_confirmed_at':'spoof'},content_type='application/json')
        self.assertEqual(response.status_code,400)

    def test_admin_stale_claim_warns_instead_of_server_error(self):
        claim=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.b.pk,expected_ownership_version=1)
        self.client.force_login(self.admin)
        response=self.client.post(reverse('admin:catalog_placeownershiprequest_approve',args=[claim.pk]))
        self.assertEqual(response.status_code,302)
        self.place.refresh_from_db();claim.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.b.pk);self.assertEqual(claim.status,'PENDING')
        from django.contrib.messages import get_messages
        self.assertTrue(any(message.level==30 for message in get_messages(response.wsgi_request)))

    def test_http_two_owner_confirmation_applies_only_after_second(self):
        self.client.force_login(self.a)
        response=self.client.post(self.url('join'),{'organization_id':self.org.pk},content_type='application/json')
        self.assertEqual(response.status_code,200);request_id=response.json()['request_id']
        self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)
        self.client.force_login(self.b)
        response=self.client.post(self.url('confirm-join',pk=request_id),{},content_type='application/json')
        self.assertEqual(response.status_code,200);self.place.refresh_from_db();self.assertEqual(self.place.organization_id,self.org.pk)


@skipUnless(connection.vendor=='postgresql','Real row locks required')
class OwnershipConcurrencyTests(OwnershipFixture,TransactionTestCase):
    def race(self,operations):
        barrier=Barrier(2)
        def run(operation):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:operation();return True
                except (ValidationError,PermissionDenied,IntegrityError):return False
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2)as pool:return sorted(f.result(timeout=30)for f in [pool.submit(run,op)for op in operations])

    def test_concurrent_final_confirmations_are_idempotent(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        self.assertEqual(self.race([lambda:self.service.confirm_join(actor=self.b,request_id=item.pk)]*2),[True,True])
        self.place.refresh_from_db();self.assertEqual(self.place.content_version,2);self.assertEqual(self.place.organization_id,self.org.pk)

    def test_competing_claims_have_one_versioned_winner(self):
        first=self.service.submit_claim(actor=self.b,target_type='place',target_id=self.place.pk)
        second=self.service.submit_claim(actor=self.c,target_type='place',target_id=self.place.pk)
        self.assertEqual(self.race([lambda:self.service.moderate_claim(actor=self.admin,target_type='place',request_id=first.pk,approve=True),lambda:self.service.moderate_claim(actor=self.admin,target_type='place',request_id=second.pk,approve=True)]),[False,True])
        self.place.refresh_from_db();self.assertIn(self.place.owner_id,[self.b.pk,self.c.pk]);self.assertEqual(self.place.ownership_version,2)

    def test_transfer_racing_confirmation_never_grants_stale_network_right(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        # Either lock order is valid. An anchor conflict must be explicit and
        # caller-owned retry must re-read the now-current parent/version.
        conflict=[]
        def transfer():
            try:self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
            except ValidationError as exc:
                conflict.append(exc.code)
                raise
        self.race([lambda:self.service.confirm_join(actor=self.b,request_id=item.pk),transfer])
        self.place.refresh_from_db()
        if self.place.owner_id!=self.c.pk:
            self.assertEqual(conflict,['structure_changed'])
            self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=self.place.ownership_version)
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.c.pk)
        from catalog.services.place_access import has_place_permission
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))

    def test_detach_racing_pending_edit_keeps_approved_local_snapshot(self):
        self.joined()
        program=Program.objects.create(organization=self.org,name_az='Approved race',description_az='Approved race text',status='published',approved_at=timezone.now())
        activity=Activity.objects.create(place=self.place,program=program)
        def edit():
            current=Program.objects.get(pk=program.pk)
            current.description_az='Pending race text';current.status='pending';current.save()
        self.assertEqual(self.race([edit,lambda:self.service.detach(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)]),[True,True])
        activity.refresh_from_db();self.place.refresh_from_db()
        self.assertIsNone(activity.program_id);self.assertIsNone(self.place.organization_id)
        self.assertEqual(activity.description_az,'Approved race text')
        self.assertEqual(activity.program_snapshot['description_az'],'Approved race text')

    def test_network_edit_waits_for_org_transfer_and_rechecks_permission(self):
        self.joined()
        from catalog.controllers.owner_places_controller import OwnerPlacesController
        stale=Place.objects.get(pk=self.place.pk)
        self.assertTrue(OwnerPlacesController._has_permission(user=self.b,place=stale,permission_code='place.edit'))
        entered=Event();finished=Event()
        def edit():
            close_old_connections();entered.set()
            try:
                stale.description_en='Revoked network edit'
                try:stale.save();return True
                except PermissionDenied:return False
            finally:finished.set();close_old_connections()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=self.org.pk)
                result=pool.submit(edit)
                self.assertTrue(entered.wait(5))
                self.assertFalse(finished.wait(0.5),'Network edit must serialize with Organization transfer')
                self.service.transfer_owner(actor=self.b,target_type='organization',target_id=self.org.pk,new_owner_id=self.c.pk,expected_ownership_version=1)
            self.assertFalse(result.result(timeout=10))
        self.place.refresh_from_db();self.assertNotEqual(self.place.description_en,'Revoked network edit')
