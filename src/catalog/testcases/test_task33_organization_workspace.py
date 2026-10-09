"""Stage 12 route and form contracts on isolated PostgreSQL."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from catalog.models import Organization, Place, OrganizationGrant, OrganizationPlaceRequest
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory
from catalog.services import organization_ownership


class OrganizationWorkspaceTests(TestCase):
    def setUp(self):
        ensure_quality_subcategory('EDU')
        User = get_user_model()
        self.owner = User.objects.create_user(username='workspace_owner')
        self.manager = User.objects.create_user(username='workspace_manager')
        self.stranger = User.objects.create_user(username='workspace_stranger')
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner, name_az='Şəbəkə')
        self.first = create_quality_place(owner=self.owner, created_by=self.owner, name_az='Birinci')
        self.second = create_quality_place(owner=self.owner, created_by=self.owner, name_az='İkinci')
        for place in (self.first, self.second):
            organization_ownership.request_join(actor=self.owner, place_id=place.pk, organization_id=self.org.pk)
        self.grant = OrganizationGrant.objects.create(
            organization=self.org, owner=self.owner, member=self.manager,
            base_ownership_version=self.org.ownership_version, actions=['organization.view', 'place.view'],
            scope='selected_places', role='EDITOR',
        )
        self.grant.selected_places.add(self.first)

    def test_empty_account_creates_organization_without_address_or_branch(self):
        self.client.force_login(self.stranger)
        index = self.client.get(reverse('organization_workspace_index'))
        self.assertEqual(index.status_code, 200)
        self.assertContains(index, 'data-empty-organizations')
        response = self.client.post(reverse('organization_workspace_create'), {'name_az': 'Yeni qurum'})
        self.assertEqual(response.status_code, 302)
        created = Organization.objects.get(name_az='Yeni qurum')
        self.assertEqual(created.owner_id, self.stranger.pk)
        self.assertFalse(created.places.exists())
        self.assertEqual(self.client.get(reverse('organization_workspace_detail', args=[created.pk])).status_code, 200)

    def test_manager_sees_selected_branch_only_and_direct_url_does_not_expand_scope(self):
        self.client.force_login(self.manager)
        detail = self.client.get(reverse('organization_workspace_detail', args=[self.org.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, self.first.name_az)
        self.assertNotContains(detail, self.second.name_az)
        self.assertEqual(self.client.get(reverse('organization_workspace_branch', args=[self.org.pk, self.second.pk])).status_code, 404)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('organization_workspace_detail', args=[self.org.pk])).status_code, 404)

    def test_join_pending_confirmation_and_stale_detach_are_server_checked(self):
        external = create_quality_place(owner=self.manager, created_by=self.manager, name_az='Müstəqil')
        self.client.force_login(self.owner)
        join = self.client.post(reverse('organization_workspace_join', args=[self.org.pk]), {'place_id': external.pk})
        self.assertEqual(join.status_code, 302)
        req = OrganizationPlaceRequest.objects.get(place=external, organization=self.org, status='pending')
        self.client.force_login(self.manager)
        self.assertEqual(self.client.post(reverse('organization_workspace_confirm', args=[self.org.pk, req.pk])).status_code, 302)
        external.refresh_from_db()
        self.assertEqual(external.organization_id, self.org.pk)
        self.client.force_login(self.owner)
        stale = self.client.post(reverse('organization_workspace_detach', args=[self.org.pk, external.pk]), {'expected_ownership_version': external.ownership_version + 1})
        self.assertEqual(stale.status_code, 409)
        external.refresh_from_db()
        self.assertEqual(external.organization_id, self.org.pk)

    def test_organization_edit_candidate_preserves_live_content_and_rejects_stale_version(self):
        self.client.force_login(self.owner)
        action = reverse('organization_workspace_save', args=[self.org.pk])
        first = self.client.post(action, {'name_az': 'Yeni ad', 'expected_version': self.org.content_version, 'revision_version': 0, 'submit': '1'})
        self.assertEqual(first.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az, 'Şəbəkə')
        self.assertEqual(self.org.content_revision.status, 'pending')
        stale = self.client.post(action, {'name_az': 'Wrong', 'expected_version': 0, 'revision_version': 0, 'submit': '1'})
        self.assertEqual(stale.status_code, 409)
        self.org.refresh_from_db()
        self.assertEqual(self.org.content_revision.payload['name_az'], 'Yeni ad')

    def test_place_owner_can_confirm_request_without_organization_workspace_access(self):
        external = create_quality_place(owner=self.manager, created_by=self.manager, name_az='Müstəqil')
        pending = organization_ownership.request_join(actor=self.owner, place_id=external.pk, organization_id=self.org.pk)
        self.grant.actions = ['place.view']
        self.grant.save(update_fields=['actions'])
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,404)
        response = self.client.post(reverse('organization_workspace_confirm', args=[self.org.pk, pending.pk]))
        self.assertEqual(response.status_code, 302)
        external.refresh_from_db()
        self.assertEqual(external.organization_id, self.org.pk)
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,404)

    def test_branch_creation_keeps_org_owner_and_limits_selected_manager(self):
        self.grant.actions = ['organization.view', 'branch.create', 'place.view']
        self.grant.save(update_fields=['actions'])
        self.client.force_login(self.manager)
        response = self.client.post(reverse('organization_workspace_branch_create', args=[self.org.pk]), {'name_az': 'Yeni filial', 'category_id': self.first.category_id})
        self.assertEqual(response.status_code, 302)
        created = Place.objects.get(name_az='Yeni filial')
        self.assertEqual((created.owner_id, created.created_by_id, created.organization_id), (self.owner.pk,self.manager.pk,self.org.pk))
        self.assertEqual(self.client.get(reverse('organization_workspace_branch',args=[self.org.pk,created.pk])).status_code,404)

    def test_place_owner_can_request_join_without_organization_view(self):
        external = create_quality_place(owner=self.stranger, created_by=self.stranger, name_az='Qoşulmaq')
        self.client.force_login(self.stranger)
        response = self.client.post(reverse('organization_workspace_join',args=[self.org.pk]), {'place_id':external.pk})
        self.assertEqual(response.status_code,302)
        self.assertTrue(OrganizationPlaceRequest.objects.filter(place=external,organization=self.org,status='pending').exists())
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,404)

    def test_organization_draft_reappears_on_reload_and_never_changes_live_name(self):
        from catalog.services import server_drafts, publication
        draft = server_drafts.save(user=self.owner, data={
            'target_type':'organization','target_id':self.org.pk,
            'schema_version':publication.SCHEMA_VERSION,'source_version':self.org.content_version,
            'expected_version':0,'fields':{'name_az':'Saxlanmış qaralama'},
        })
        self.client.force_login(self.owner)
        detail = self.client.get(reverse('organization_workspace_detail',args=[self.org.pk]))
        self.assertEqual(detail.status_code,200)
        self.assertContains(detail,'Saxlanmış qaralama')
        self.org.refresh_from_db()
        self.assertEqual(self.org.name_az,'Şəbəkə')
        self.assertContains(detail,str(draft.pk))

    def test_foreign_actor_cannot_create_branch_or_save_organization(self):
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.post(reverse('organization_workspace_branch_create',args=[self.org.pk]), {'name_az':'No','category_id':self.first.category_id}).status_code,404)
        self.assertEqual(self.client.post(reverse('organization_workspace_save',args=[self.org.pk]), {'name_az':'No','expected_version':1,'revision_version':0,'submit':'1'}).status_code,404)
        self.assertFalse(Place.objects.filter(name_az='No').exists())

    def test_standalone_places_are_visible_beside_zero_org_state(self):
        self.client.force_login(self.manager)
        standalone = create_quality_place(owner=self.manager,created_by=self.manager,name_az='Ayrı məkan')
        index = self.client.get(reverse('organization_workspace_index'))
        self.assertEqual(index.status_code,200)
        self.assertContains(index,'Ayrı məkan')
        self.assertNotContains(index,self.second.name_az)
        self.client.force_login(self.stranger)
        self.assertNotContains(self.client.get(reverse('organization_workspace_index')),'Ayrı məkan')

    def test_place_owner_can_detach_without_organization_view(self):
        external = create_quality_place(owner=self.stranger,created_by=self.stranger,name_az='Ayrılan')
        req = organization_ownership.request_join(actor=self.owner,place_id=external.pk,organization_id=self.org.pk)
        organization_ownership.confirm_join(actor=self.stranger,request_id=req.pk)
        external.refresh_from_db()
        self.assertEqual(external.organization_id,self.org.pk)
        self.client.force_login(self.stranger)
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,404)
        response = self.client.post(reverse('organization_workspace_detach',args=[self.org.pk,external.pk]), {'expected_ownership_version':external.ownership_version})
        self.assertRedirects(response,reverse('organization_detach_preview',args=[self.org.pk,external.pk]),fetch_redirect_response=False)
        external.refresh_from_db()
        self.assertEqual(external.organization_id,self.org.pk)
        review=self.client.get(response.url)
        self.assertEqual(review.status_code,200)
        confirmed=self.client.post(response.url,{'action':'confirm','preview_id':review.context['operation'].pk,
            'idempotency_key':review.context['idempotency_key'],'consent':'1'})
        self.assertEqual(confirmed.status_code,302)
        external.refresh_from_db()
        self.assertIsNone(external.organization_id)
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,404)

    def test_organization_create_get_screen_and_duplicate_collision(self):
        self.client.force_login(self.owner)
        create_url = reverse('organization_workspace_create')
        # GET renders dedicated creation screen
        get_res = self.client.get(create_url)
        self.assertEqual(get_res.status_code, 200)
        self.assertContains(get_res, 'data-org-create-form')
        self.assertContains(get_res, 'id_name_az')

        # POST with duplicate name without allow_separate raises 409 and flags duplicate_detected
        dup_res = self.client.post(create_url, {'name_az': 'Şəbəkə', 'allow_separate': ''})
        self.assertEqual(dup_res.status_code, 409)
        self.assertTrue(dup_res.context.get('duplicate_detected'))

        # POST with allow_separate=True creates separate organization
        sep_res = self.client.post(create_url, {'name_az': 'Şəbəkə', 'allow_separate': '1'})
        self.assertEqual(sep_res.status_code, 302)
        self.assertEqual(Organization.objects.filter(name_az='Şəbəkə').count(), 2)
