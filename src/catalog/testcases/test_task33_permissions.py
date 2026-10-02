"""Stage07 business permission boundaries, literal grants and actual POST/PG races."""
import importlib.util
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Place, Organization, OwnerTeamMembership, OwnerTeamInvitation, PlaceReview
from catalog.testcases.utils import create_quality_place
from catalog.repositories.django_repositories import DjangoOwnerTeamRepository
from catalog.services.place_access import has_place_permission
from catalog.services.owner_place_use_cases import resolve_owner_permission_scopes

class TeamFixture:
    def setUp(self):
        U=get_user_model()
        self.owner=U.objects.create_user(username='team_owner',email='owner@example.invalid')
        self.member=U.objects.create_user(username='team_member',email='member@example.invalid')
        self.other=U.objects.create_user(username='team_other',email='other@example.invalid')
        self.place=create_quality_place(owner=self.owner,created_by=self.owner,with_subcategory=True)
        self.org=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='Komanda')
        self.repo=DjangoOwnerTeamRepository()
    def membership(self):
        return OwnerTeamMembership.objects.create(place=self.place,owner=self.owner,member=self.member,role='MANAGER')

class LegacyBoundaryTests(TeamFixture,TestCase):
    def test_manager_cannot_delegate_through_real_post(self):
        self.membership();c=Client();c.force_login(self.member)
        c.post(reverse('owner_team_invite'),{'place':self.place.pk,'email':'third@example.invalid','role':'EDITOR'})
        self.assertFalse(OwnerTeamInvitation.objects.exists())
        self.assertFalse(has_place_permission(user=self.member,place=self.place,permission_code='place.team.manage'))
    def test_owner_and_manager_cannot_approve_review_through_post(self):
        self.membership()
        review=PlaceReview.objects.create(place=self.place,user=self.other,rating=4,text='Synthetic review',is_approved=False,status='pending')
        self.assertFalse(review.is_approved)
        for user in (self.owner,self.member):
            c=Client();c.force_login(user);c.post(reverse('owner_review_approve',args=[review.pk]));review.refresh_from_db();self.assertFalse(review.is_approved)
    def test_scope_reloads_live_owner_before_listing_team_places(self):
        self.membership()
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        scopes=resolve_owner_permission_scopes(user=self.member,team_repository=self.repo)
        self.assertFalse(any(s.place_id==self.place.pk and 'place.edit' in s.permissions for s in scopes))
    def test_repository_rejects_stale_invitation_object_after_transfer(self):
        invitation=self.repo.create_invitation(place=self.place,invited_by=self.owner,email=self.member.email,role='EDITOR')
        from catalog.services.organization_ownership import transfer_owner
        transfer_owner(actor=self.owner,target_type='place',target_id=self.place.pk,new_owner_id=self.other.pk,expected_ownership_version=1)
        with self.assertRaises((PermissionDenied,ValidationError)):
            self.repo.accept_invitation(invitation=invitation,user=self.member)
        self.assertFalse(OwnerTeamMembership.objects.filter(is_active=True).exists())
    def test_permission_service_exists(self):
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.business_team'),'Stage07 service missing')

class GrantTests(TeamFixture,TestCase):
    def setUp(self):
        super().setUp()
        self.assertIsNotNone(importlib.util.find_spec('catalog.services.business_team'),'Stage07 service missing')
        from catalog.services import business_team
        self.service=business_team
        from catalog.services.organization_ownership import request_join
        request_join(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.place.refresh_from_db()
    def invite(self,**overrides):
        values=dict(actor=self.owner,target_type='organization',target_id=self.org.pk,email=self.member.email,role='EDITOR',actions=['place.view','place.edit'],scope='selected_places',place_ids=[self.place.pk])
        values.update(overrides)
        return self.service.invite(**values)
    def accept(self,**overrides):
        i=self.invite(**overrides)
        return self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
    def action(self,action,target=None):
        return self.service.has_action(user=self.member,target=target or self.place,action=action)
    def test_selected_all_current_does_not_include_future_branch(self):
        self.accept();p=self.service.create_branch(actor=self.owner,organization_id=self.org.pk,values={'name_az':'Yeni filial','category_id':self.place.category_id})
        self.assertTrue(self.action('place.edit'));self.assertFalse(self.action('place.edit',p))
    def test_all_network_includes_future_branch_but_not_org_or_program_actions(self):
        self.accept(scope='all_network',place_ids=[])
        p=self.service.create_branch(actor=self.owner,organization_id=self.org.pk,values={'name_az':'Yeni filial','category_id':self.place.category_id})
        self.assertTrue(self.action('place.edit',p));self.assertFalse(self.action('organization.edit',self.org));self.assertFalse(self.action('program.manage',self.org));self.assertFalse(self.action('branch.create',self.org))
    def test_delegated_branch_owner_is_org_owner_and_selected_scope_stays_fixed(self):
        g=self.accept(actions=['place.edit','branch.create'])
        p=self.service.create_branch(actor=self.member,organization_id=self.org.pk,values={'name_az':'Əməkdaş filialı','category_id':self.place.category_id})
        self.assertEqual((p.owner_id,p.created_by_id),(self.owner.pk,self.member.pk));self.assertFalse(self.action('place.edit',p));self.assertEqual(list(g.selected_places.values_list('pk',flat=True)),[self.place.pk])
    def test_branch_creation_refuses_network_edit_without_separate_action(self):
        self.accept(scope='all_network',place_ids=[])
        with self.assertRaises(PermissionDenied):self.service.create_branch(actor=self.member,organization_id=self.org.pk,values={'name_az':'No branch','category_id':self.place.category_id})
    def test_forbidden_actions_are_not_grantable(self):
        for action in ['place.team.manage','place.reviews.moderate','place.publish','organization.team.manage','ownership.transfer','unknown']:
            with self.subTest(action=action),self.assertRaises(ValidationError):self.invite(actions=[action])
    def test_foreign_nested_place_and_informational_place_rejected(self):
        foreign=create_quality_place(owner=self.other,created_by=self.other)
        with self.assertRaises(ValidationError):self.invite(place_ids=[foreign.pk])
        Place.objects.filter(pk=self.place.pk).update(organization_relationship_kind='informational')
        with self.assertRaises(ValidationError):self.invite()
    def test_empty_selected_and_all_network_with_ids_rejected(self):
        for values in [dict(place_ids=[]),dict(scope='all_network',place_ids=[self.place.pk]),dict(scope='bad'),dict(place_ids=[True])]:
            with self.subTest(values=values),self.assertRaises(ValidationError):self.invite(**values)
    def test_direct_grant_survives_detach_and_network_grant_stops(self):
        self.accept();self.membership()
        from catalog.services.organization_ownership import detach
        detach(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk,expected_ownership_version=1)
        self.assertTrue(self.action('place.edit'))
        OwnerTeamMembership.objects.filter(member=self.member).update(is_active=False)
        self.assertFalse(self.action('place.edit'))
    def test_revocation_and_leave_immediately_remove_cached_account_access(self):
        g=self.accept();self.assertTrue(self.action('place.edit'))
        self.service.change_grant(actor=self.owner,target_type='organization',grant_id=g.pk,expected_version=g.version,active=False)
        self.assertFalse(self.action('place.edit'))
        self.service.confirm_member(actor=self.owner,target_type='organization',grant_id=g.pk,expected_version=g.version+1)
        self.assertTrue(self.action('place.edit'))
        self.service.leave(actor=self.member,target_type='organization',grant_id=g.pk)
        self.assertFalse(self.action('place.edit'))
    def test_transfer_suspends_team_and_cancels_pending_invites_requires_explicit_confirmation(self):
        g=self.accept();other=self.invite(email=self.other.email)
        from catalog.services.organization_ownership import transfer_owner
        transfer_owner(actor=self.owner,target_type='organization',target_id=self.org.pk,new_owner_id=self.other.pk,expected_ownership_version=1)
        self.assertFalse(self.action('place.edit'));other.refresh_from_db();self.assertEqual(other.status,'CANCELED')
        suspended=self.service.suspended(actor=self.other,target_type='organization',target_id=self.org.pk)
        self.assertEqual([row.pk for row in suspended],[g.pk])
        with self.assertRaises(PermissionDenied):self.service.suspended(actor=self.member,target_type='organization',target_id=self.org.pk)
        # Affiliation is stale after Org transfer; reconfirm relation before network restoration.
        Place.objects.filter(pk=self.place.pk).update(organization_join_org_ownership_version=2)
        g.refresh_from_db();self.service.confirm_member(actor=self.other,target_type='organization',grant_id=g.pk,expected_version=g.version)
        self.assertTrue(self.action('place.edit'));self.assertFalse(self.action('organization.team.manage',self.org))
    def test_model_partial_org_owner_transfer_also_revokes(self):
        g=self.accept();i=self.invite(email=self.other.email)
        self.org.owner=self.other;self.org.save(update_fields=['owner']);g.refresh_from_db();i.refresh_from_db()
        self.assertFalse(g.is_active);self.assertEqual(i.status,'CANCELED')
    def test_expired_canceled_replayed_and_stale_selected_invitation(self):
        from django.utils import timezone
        from datetime import timedelta
        i=self.invite();type(i).objects.filter(pk=i.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(ValidationError):self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        type(i).objects.filter(pk=i.pk).update(expires_at=timezone.now()+timedelta(days=1),status='CANCELED')
        with self.assertRaises(ValidationError):self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        type(i).objects.filter(pk=i.pk).update(status='PENDING');Place.objects.filter(pk=self.place.pk).update(ownership_version=2)
        with self.assertRaises(ValidationError):self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
    def test_wrong_account_and_inactive_actor_refused(self):
        i=self.invite()
        with self.assertRaises(PermissionDenied):self.service.accept(actor=self.other,target_type='organization',invitation_id=i.pk)
        g=self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        get_user_model().objects.filter(pk=self.member.pk).update(is_active=False)
        self.assertFalse(self.action('place.edit'))
        with self.assertRaises(PermissionDenied):self.service.leave(actor=self.member,target_type='organization',grant_id=g.pk)
    def test_no_delegation_even_with_manager_role_or_grant(self):
        self.accept(role='MANAGER')
        with self.assertRaises(PermissionDenied):self.invite(actor=self.member,email=self.other.email)
    def test_scope_list_and_managed_reader_follow_resolver(self):
        self.accept();scopes=resolve_owner_permission_scopes(user=self.member,team_repository=self.repo)
        self.assertIn(self.place.pk,[s.place_id for s in scopes if 'place.edit' in s.permissions])
        from catalog.repositories.django_repositories import DjangoOwnerPlaceRepository
        self.assertIn(self.place.pk,list(DjangoOwnerPlaceRepository().managed_queryset(user=self.member).values_list('pk',flat=True)))
    def test_endpoint_denies_foreign_nested_ids_and_manager_team_post(self):
        self.accept();c=Client();c.force_login(self.member)
        url=reverse('business_team_action',args=['organization',self.org.pk,'invite'])
        self.assertEqual(c.post(url,{'email':self.other.email,'actions':['place.edit'],'scope':'all_network','place_ids':[]},content_type='application/json').status_code,403)
        foreign=create_quality_place(owner=self.other)
        c.force_login(self.owner)
        self.assertEqual(c.post(url,{'email':self.other.email,'actions':['place.edit'],'scope':'selected_places','place_ids':[foreign.pk]},content_type='application/json').status_code,400)
    def test_endpoint_transport_csrf_config_and_conflict(self):
        g=self.accept();c=Client();c.force_login(self.owner)
        url=reverse('business_team_action',args=['organization',self.org.pk,'grant'])
        self.assertEqual(c.get(url).status_code,405)
        payload={'grant_id':g.pk,'expected_version':g.version+1,'active':False}
        self.assertEqual(c.post(url,payload,content_type='application/json').status_code,409)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.owner)
        self.assertEqual(secure.post(url,payload,content_type='application/json').status_code,403)
        config=c.get(reverse('business_permission_config')).json()
        self.assertNotIn('place.reviews.moderate',config['grantable_actions']);self.assertIn('branch.create',config['grantable_actions'])

    def test_legacy_null_place_grant_has_no_network_rights(self):
        OwnerTeamMembership.objects.create(place=None,owner=self.owner,member=self.member,role='MANAGER')
        self.assertFalse(self.action('place.edit'));self.assertFalse(self.action('organization.edit',self.org))
    def test_program_permission_is_explicit_and_target_scoped(self):
        from catalog.models import Program
        program=Program.objects.create(organization=self.org,name_az='Proqram')
        self.accept(actions=['program.manage'],place_ids=[])
        self.assertTrue(self.action('program.manage',program));self.assertFalse(self.action('place.edit'))
        org=Organization.objects.create(owner=self.other,name_az='Digər')
        other=Program.objects.create(organization=org,name_az='Başqa')
        self.assertFalse(self.action('program.manage',other))
    def test_direct_place_individual_actions_and_stale_role_writer(self):
        i=self.service.invite(actor=self.owner,target_type='place',target_id=self.place.pk,email=self.member.email,actions=['place.view','place.stats.view'])
        g=self.service.accept(actor=self.member,target_type='place',invitation_id=i.pk)
        self.assertTrue(self.action('place.stats.view'));self.assertFalse(self.action('place.edit'))
        from catalog.services.organization_ownership import transfer_owner
        transfer_owner(actor=self.owner,target_type='place',target_id=self.place.pk,new_owner_id=self.other.pk,expected_ownership_version=1)
        with self.assertRaises((PermissionDenied,ValidationError)):
            self.repo.update_membership_role(actor=self.owner,membership_id=g.pk,role='MANAGER',expected_version=g.version)
    def test_invitation_grant_version_and_replay_are_checked(self):
        g=self.accept()
        i=self.invite()
        self.service.change_grant(actor=self.owner,target_type='organization',grant_id=g.pk,expected_version=g.version,active=False)
        with self.assertRaises(ValidationError):self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        self.service.decide_invitation(actor=self.owner,target_type='organization',invitation_id=i.pk,cancel=True)
        i=self.invite();self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        with self.assertRaises(ValidationError):self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
    def test_revoked_business_actor_cannot_use_cached_profile(self):
        from django.contrib.auth.models import Group
        from catalog.services.staff_roles import VOLUNTEER_GROUP
        self.accept();self.member.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.assertFalse(self.action('place.edit'))
    def test_api_rechecks_nested_parent_after_precheck(self):
        from unittest.mock import patch
        i=self.invite(actions=['organization.edit'],place_ids=[])
        other_org=Organization.objects.create(owner=self.owner,name_az='Başqa şəbəkə')
        original=self.service.accept
        def moved(**kwargs):
            type(i).objects.filter(pk=i.pk).update(organization=other_org)
            return original(**kwargs)
        c=Client();c.force_login(self.member)
        url=reverse('business_team_action',args=['organization',self.org.pk,'accept'])
        with patch.object(self.service,'accept',side_effect=moved):
            response=c.post(url,{'invitation_id':i.pk},content_type='application/json')
        self.assertEqual(response.status_code,403)
        from catalog.models import OrganizationGrant
        self.assertFalse(OrganizationGrant.objects.exists())

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Barrier
from django.db import close_old_connections, transaction, connection
from django.test import TransactionTestCase

class TeamConcurrencyTests(TeamFixture,TransactionTestCase):
    def setUp(self):
        super().setUp()
        from catalog.services import business_team
        self.service=business_team
        from catalog.services.organization_ownership import request_join
        request_join(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.place.refresh_from_db()
    def work(self, fn, started, finished):
        close_old_connections();started.set()
        try:
            try:return fn()
            except (PermissionDenied,ValidationError) as exc:return type(exc).__name__
        finally:finished.set();close_old_connections()
    def test_transfer_blocks_accept_then_stale_invite_cannot_resurrect(self):
        i=self.service.invite(actor=self.owner,target_type='organization',target_id=self.org.pk,email=self.member.email,scope='all_network',place_ids=[])
        started=Event();finished=Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=self.org.pk)
                future=pool.submit(self.work,lambda:self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk),started,finished)
                self.assertTrue(started.wait(5));self.assertFalse(finished.wait(.2))
                from catalog.services.organization_ownership import transfer_owner
                transfer_owner(actor=self.owner,target_type='organization',target_id=self.org.pk,new_owner_id=self.other.pk,expected_ownership_version=1)
            self.assertIn(future.result(timeout=10),['ValidationError','TeamConflict'])
        from catalog.models import OrganizationGrant
        self.assertFalse(OrganizationGrant.objects.filter(is_active=True).exists())
    def test_revocation_blocks_legacy_place_write_and_preserves_live_description(self):
        i=self.service.invite(actor=self.owner,target_type='organization',target_id=self.org.pk,email=self.member.email,scope='all_network',place_ids=[])
        g=self.service.accept(actor=self.member,target_type='organization',invitation_id=i.pk)
        original=self.place.description_az
        def write():
            p=Place.objects.get(pk=self.place.pk);p.description_az='Revoked mutation';p._authorized_actor_id=self.member.pk;p._required_permission_code='place.edit';p.save(update_fields=['description_az']);return 'saved'
        started=Event();finished=Event()
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                Organization.objects.select_for_update().get(pk=self.org.pk)
                future=pool.submit(self.work,write,started,finished)
                self.assertTrue(started.wait(5));self.assertFalse(finished.wait(.2))
                self.service.change_grant(actor=self.owner,target_type='organization',grant_id=g.pk,expected_version=g.version,active=False)
            self.assertEqual(future.result(timeout=10),'PermissionDenied')
        self.place.refresh_from_db();self.assertEqual(self.place.description_az,original)
    def test_duplicate_accept_creates_one_membership(self):
        i=self.service.invite(actor=self.owner,target_type='place',target_id=self.place.pk,email=self.member.email)
        barrier=Barrier(2)
        def run():
            close_old_connections()
            try:
                barrier.wait(5)
                try:self.service.accept(actor=self.member,target_type='place',invitation_id=i.pk);return 'accepted'
                except ValidationError:return 'stale'
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first=pool.submit(run);second=pool.submit(run)
            self.assertEqual(sorted([first.result(10),second.result(10)]),['accepted','stale'])
        self.assertEqual(OwnerTeamMembership.objects.filter(place=self.place,member=self.member,is_active=True).count(),1)

class AdministrativeBoundaryTests(TeamFixture,TestCase):
    def test_team_admin_cannot_assign_or_reactivate_business_employees(self):
        U=get_user_model();admin=U.objects.create_superuser(username='team_admin',email='admin@example.invalid',password='synthetic')
        grant=self.membership();grant.is_active=False;grant.save(update_fields=['is_active'])
        c=Client();c.force_login(admin)
        data={'place':self.place.pk,'owner':self.owner.pk,'member':self.member.pk,'role':'MANAGER','is_active':'on','version':1}
        response=c.post(reverse('admin:catalog_ownerteammembership_change',args=[grant.pk]),data)
        self.assertEqual(response.status_code,403);grant.refresh_from_db();self.assertFalse(grant.is_active)
        self.assertEqual(c.post(reverse('admin:catalog_ownerteammembership_add'),data).status_code,403)
        self.assertEqual(c.post(reverse('admin:catalog_ownerteammembership_delete',args=[grant.pk]),{'post':'yes'}).status_code,403)
        self.assertTrue(OwnerTeamMembership.objects.filter(pk=grant.pk).exists())
    def test_nested_group_cannot_bypass_archived_activity(self):
        from catalog.models import Activity,OfferingGroup
        from catalog.services.business_team import has_action
        self.membership()
        activity=Activity.objects.create(place=self.place,name_az='Qrup fəaliyyət')
        group=OfferingGroup.objects.create(activity=activity,name_az='Qrup')
        activity.archive()
        self.assertFalse(has_action(user=self.member,target=group,action='place.edit'))
    def test_team_invitation_admin_cannot_bypass_owner_services(self):
        from django.contrib.auth.models import Permission
        staff=get_user_model().objects.create_user(username='team_staff',is_staff=True)
        staff.user_permissions.add(*Permission.objects.filter(codename__in=['add_ownerteaminvitation','change_ownerteaminvitation','delete_ownerteaminvitation']))
        invitation=self.repo.create_invitation(place=self.place,invited_by=self.owner,email=self.member.email,role='EDITOR')
        c=Client();c.force_login(staff)
        url=reverse('admin:catalog_ownerteaminvitation_change',args=[invitation.pk])
        self.assertEqual(c.post(url,{'place':self.place.pk,'owner':self.other.pk,'email':self.member.email,'role':'MANAGER','status':'ACCEPTED'}).status_code,403)
        invitation.refresh_from_db();self.assertEqual(invitation.status,'PENDING');self.assertEqual(invitation.owner_id,self.owner.pk)
        self.assertEqual(c.post(reverse('admin:catalog_ownerteaminvitation_add'),{}).status_code,403)
        self.assertEqual(c.post(reverse('admin:catalog_ownerteaminvitation_delete',args=[invitation.pk]),{'post':'yes'}).status_code,403)
    def test_platform_publish_helper_does_not_grant_ordinary_account_permission(self):
        from django.contrib.auth.models import Permission
        from catalog.services.place_access import staff_has_place_permission
        self.member.user_permissions.add(Permission.objects.get(codename='change_place',content_type__app_label='catalog'))
        self.assertFalse(staff_has_place_permission(user=self.member,permission_code='place.publish'))
