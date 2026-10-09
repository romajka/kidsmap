"""Connection coordinator contracts on isolated PostgreSQL; real transitions."""
import importlib
import importlib.util
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.test import TestCase
from django.utils import timezone

from catalog.models import Organization, OrganizationPlaceRequest, Place
from catalog.services import organization_ownership
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory


class OrganizationConnectionTests(TestCase):
    def setUp(self):
        ensure_quality_subcategory('EDU')
        self.owner = get_user_model().objects.create_user(username='connection_owner')
        self.other = get_user_model().objects.create_user(username='connection_other')
        self.staff = get_user_model().objects.create_user(username='connection_staff', is_staff=True, is_superuser=True)
        self.org = Organization.objects.create(owner=self.owner, name_az='QA Şəbəkə')
        self.place = create_quality_place(owner=self.owner, name_az='QA Klub', name_ru='QA Клуб', name_en='QA Club', address='QA küçə 12')

    def service(self):
        name = 'catalog.services.organization_connections'
        self.assertIsNotNone(importlib.util.find_spec(name), 'Approved connection coordinator is missing')
        return importlib.import_module(name)

    def preview(self, places=None, actor=None, kind='business'):
        return self.service().preview_connections(actor=actor or self.owner, organization_id=self.org.pk,
            relationship_kind=kind, place_ids=places or [self.place.pk])

    def execute(self, preview, actor=None, key=None):
        return self.service().execute_connections(actor=actor or self.owner, preview_id=preview.pk,
            idempotency_key=key or uuid.uuid4())

    def test_search_languages_address_and_foreign_private_excluded(self):
        private = create_quality_place(owner=self.other, name_az='QA Klub gizli', status='draft', is_active=False)
        service = self.service()
        for query in ('Klub', 'Клуб', 'Club', 'küçə 12'):
            result = service.search_places(actor=self.owner, organization_id=self.org.pk, query=query)
            self.assertIn(self.place.pk, [row['id'] for row in result['rows']])
            self.assertNotIn(private.pk, [row['id'] for row in result['rows']])

    def test_preview_is_read_only_and_connect_repeat_preserves_identity(self):
        service = self.service(); before = (self.place.pk, self.place.slug, self.place.photo.name, self.place.status)
        preview = self.preview()
        self.assertEqual(preview.items.get().decision, 'connected')
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        key = uuid.uuid4(); operation = self.execute(preview, key=key)
        repeated = self.execute(preview, key=key)
        self.assertEqual(operation.pk, repeated.pk)
        self.assertEqual(operation.items.get().result, 'connected')
        self.assertEqual(OrganizationPlaceRequest.objects.count(), 1)
        self.place.refresh_from_db()
        self.assertEqual((self.place.pk, self.place.slug, self.place.photo.name, self.place.status), before)
        self.assertTrue(organization_ownership.affiliation_current(self.place, self.org))
        self.assertEqual(self.execute(self.preview()).items.get().result, 'already_connected')

    def test_two_owner_consent_without_foreign_workspace_access(self):
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        first = self.execute(self.preview())
        self.assertEqual(first.items.get().result, 'requested')
        self.place.refresh_from_db(); self.assertIsNone(self.place.organization_id)
        second = self.execute(self.preview(actor=self.other), actor=self.other)
        self.assertEqual(second.items.get().result, 'connected')
        self.place.refresh_from_db(); self.assertEqual(self.place.organization_id, self.org.pk)

    def test_staff_neither_side_denied_business_and_explicit_information_does_not_grant_edit(self):
        denied = self.execute(self.preview(actor=self.staff), actor=self.staff)
        self.assertEqual(denied.items.get().result, 'no_rights')
        info = self.execute(self.preview(actor=self.staff, kind='informational'), actor=self.staff)
        self.assertEqual(info.items.get().result, 'connected')
        self.place.refresh_from_db(); self.assertEqual(self.place.organization_relationship_kind, 'informational')
        from catalog.services.business_team import has_action
        self.assertFalse(has_action(user=self.staff, target=self.place, action='place.edit'))
        self.assertEqual(self.preview().items.get().decision, 'kind_conflict')

    def test_partial_batch_other_network_and_changed_row_do_not_rollback_success(self):
        second = create_quality_place(owner=self.owner, name_az='QA İkinci')
        conflict = create_quality_place(owner=self.owner, name_az='QA Başqa şəbəkə')
        other_org = Organization.objects.create(owner=self.owner, name_az='QA Digər')
        organization_ownership.request_join(actor=self.owner, place_id=conflict.pk, organization_id=other_org.pk)
        preview = self.preview([self.place.pk, second.pk, conflict.pk])
        Place.objects.filter(pk=second.pk).update(content_version=F('content_version') + 1)
        operation = self.execute(preview)
        results = dict(operation.items.values_list('place_id', 'result'))
        self.assertEqual(results, {self.place.pk:'connected', second.pk:'changed', conflict.pk:'other_network'})
        conflict.refresh_from_db(); self.assertEqual(conflict.organization_id, other_org.pk)

    def test_actor_expiry_key_mismatch_and_id_validation(self):
        service = self.service()
        for ids in ([True], ['1'], [self.place.pk, self.place.pk], list(range(1, 102)), []):
            with self.assertRaises(ValidationError):
                service.preview_connections(actor=self.owner, organization_id=self.org.pk, relationship_kind='business', place_ids=ids)
        preview = self.preview()
        with self.assertRaises(PermissionDenied): self.execute(preview, actor=self.other)
        type(preview).objects.filter(pk=preview.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        with self.assertRaises(ValidationError): self.execute(preview)
        first = self.preview(); key = uuid.uuid4(); self.execute(first, key=key)
        with self.assertRaises(ValidationError): self.execute(self.preview(), key=key)

    def test_current_acl_rechecked_and_receipt_redacts_after_access_removed(self):
        preview = self.preview()
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied): self.execute(preview)
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=True)
        operation = self.execute(self.preview())
        Place.objects.filter(pk=self.place.pk).update(owner=self.other, ownership_version=F('ownership_version')+1,
            status='draft', is_active=False)
        result = self.service().connection_result(actor=self.owner, operation_id=operation.pk)
        self.assertEqual(result['rows'][0]['code'], 'unavailable')
        self.assertNotIn('QA Klub', str(result))

    def test_transition_and_item_result_roll_back_together_on_exception(self):
        service = self.service(); preview = self.preview(); original = organization_ownership.request_join
        def fault(**kwargs):
            original(**kwargs)
            raise RuntimeError('QA synthetic interruption inside transition')
        with patch.object(organization_ownership, 'request_join', side_effect=fault):
            operation = self.execute(preview)
        self.assertEqual(operation.items.get().result, 'failed')
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        self.place.refresh_from_db(); self.assertIsNone(self.place.organization_id)

    def test_detach_receipt_replay_keeps_media_and_does_not_restore_program_links(self):
        service = self.service(); self.execute(self.preview()); self.place.refresh_from_db()
        before = (self.place.pk, self.place.photo.name, self.place.status, self.place.owner_id)
        preview = service.preview_detach(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        key = uuid.uuid4()
        operation = service.execute_detach(actor=self.owner, preview_id=preview.pk, idempotency_key=key)
        self.assertEqual(operation.items.get().result, 'detached')
        self.assertEqual(service.execute_detach(actor=self.owner, preview_id=preview.pk, idempotency_key=key).pk, operation.pk)
        self.place.refresh_from_db(); self.assertIsNone(self.place.organization_id)
        self.assertEqual((self.place.pk, self.place.photo.name, self.place.status, self.place.owner_id), before)

    def test_owner_pages_require_consent_and_result_cannot_be_read_by_another_actor(self):
        self.client.force_login(self.owner)
        url=f'/ru/account/organizations/{self.org.pk}/connections/'
        search=self.client.get(url, {'q':'küçə 12'})
        self.assertEqual(search.status_code,200)
        self.assertContains(search,'QA Клуб')
        preview=self.client.post(url, {'action':'preview','place_ids':[str(self.place.pk)],'relationship_kind':'business'})
        self.assertEqual(preview.status_code,200)
        operation=preview.context['operation']
        key=str(uuid.uuid4())
        denied=self.client.post(url, {'action':'confirm','preview_id':str(operation.pk),'idempotency_key':key})
        self.assertEqual(denied.status_code,400)
        self.assertFalse(OrganizationPlaceRequest.objects.exists())
        success=self.client.post(url, {'action':'confirm','preview_id':str(operation.pk),'idempotency_key':key,'consent':'1'})
        self.assertEqual(success.status_code,302)
        self.assertEqual(self.client.get(success.url).status_code,200)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(success.url).status_code,404)

    def test_detach_preview_explains_access_and_keeps_direct_grants(self):
        from catalog.models import OrganizationGrant, OwnerTeamMembership
        from catalog.services import business_team
        self.execute(self.preview());self.place.refresh_from_db()
        member=get_user_model().objects.create_user(username='connection_member')
        OrganizationGrant.objects.create(organization=self.org,owner=self.owner,member=member,
            base_ownership_version=self.org.ownership_version,scope='all_network',actions=['place.view'])
        direct=get_user_model().objects.create_user(username='connection_direct')
        grant=OwnerTeamMembership.objects.create(place=self.place,owner=self.owner,member=direct,
            base_ownership_version=self.place.ownership_version,actions=['place.view'])
        preview=self.service().preview_detach(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        result=self.service().connection_result(actor=self.owner,operation_id=preview.pk)
        self.assertIn('impact',result)
        self.assertEqual(result['impact']['network_grants'],1)
        self.assertEqual(result['impact']['direct_grants'],1)
        self.assertIn('programs',result['impact'])
        self.assertTrue(business_team.has_action(user=member,target=self.place,action='place.view'))
        self.service().execute_detach(actor=self.owner,preview_id=preview.pk,idempotency_key=uuid.uuid4())
        self.assertFalse(business_team.has_action(user=member,target=self.place,action='place.view'))
        self.assertTrue(business_team.has_action(user=direct,target=self.place,action='place.view'))
        self.assertTrue(OwnerTeamMembership.objects.filter(pk=grant.pk,is_active=True).exists())

    def test_candidate_or_grant_changed_after_preview_requires_new_review(self):
        from catalog.models import VolunteerPlaceRevision, OrganizationGrant
        service=self.service();preview=self.preview()
        VolunteerPlaceRevision.objects.create(place=self.place,author=self.owner,payload={'name_az':'QA changed'})
        self.assertEqual(self.execute(preview).items.get().result,'changed')
        preview=self.preview()
        OrganizationGrant.objects.create(organization=self.org,owner=self.owner,member=self.other,
            base_ownership_version=self.org.ownership_version,scope='all_network',actions=['place.edit'])
        self.assertEqual(self.execute(preview).items.get().result,'changed')

    def test_admin_signed_selection_and_explicit_information_mode(self):
        from django.contrib import admin
        from catalog.models import OrganizationConnectionOperation
        self.client.force_login(self.staff)
        place_admin=admin.site._registry[Place]
        self.assertIn('connect_to_organization', place_admin.actions)
        listing=self.client.get('/admin/catalog/place/')
        self.assertContains(listing,'name="connection_selection"')
        direct=self.client.post('/admin/catalog/place/organization-connections/',{'connection_selection':'1','_selected_action':[self.place.pk]})
        self.assertEqual(direct.status_code,302)
        response=self.client.post('/admin/catalog/place/', {'action':'connect_to_organization','_selected_action':[self.place.pk]})
        self.assertEqual(response.status_code,302)
        selection=self.client.get(response.url)
        self.assertEqual(selection.status_code,200,response.url)
        token=selection.context['selection']
        denied=self.client.post('/admin/catalog/place/organization-connections/', {'selection':'tampered','action':'preview','organization_id':self.org.pk})
        self.assertEqual(denied.status_code,400)
        preview=self.client.post('/admin/catalog/place/organization-connections/', {'selection':token,'action':'preview','organization_id':self.org.pk,'relationship_kind':'business'})
        self.assertEqual(preview.status_code,200)
        self.assertEqual(preview.context['rows'][0]['code'],'no_rights')
        info=self.client.post('/admin/catalog/place/organization-connections/', {'selection':token,'action':'preview','organization_id':self.org.pk,'relationship_kind':'informational'})
        operation=info.context['operation'];key=uuid.uuid4()
        completed=self.client.post('/admin/catalog/place/organization-connections/', {'selection':token,'action':'confirm','preview_id':operation.pk,'idempotency_key':key,'consent':'1'})
        self.assertEqual(completed.status_code,302)
        self.assertEqual(OrganizationConnectionOperation.objects.get(pk=operation.pk).items.get().result,'connected')
        replay=self.client.post('/admin/catalog/place/organization-connections/',{'action':'confirm','preview_id':operation.pk,'idempotency_key':key,'consent':'1'})
        self.assertEqual(replay.status_code,302)

    def test_owner_return_does_not_make_old_preview_current(self):
        preview=self.preview()
        Place.objects.filter(pk=self.place.pk).update(owner=self.other,ownership_version=F('ownership_version')+1)
        Place.objects.filter(pk=self.place.pk).update(owner=self.owner,ownership_version=F('ownership_version')+1)
        self.assertEqual(self.execute(preview).items.get().result,'changed')
        self.assertFalse(OrganizationPlaceRequest.objects.exists())

    def test_group_edit_after_preview_requires_new_review(self):
        from catalog.models import Activity, OfferingGroup
        activity=Activity.objects.create(place=self.place,name_az='QA Class')
        group=OfferingGroup.objects.create(activity=activity,name_az='QA Group')
        preview=self.preview()
        OfferingGroup.objects.filter(pk=group.pk).update(content_version=F('content_version')+1)
        self.assertEqual(self.execute(preview).items.get().result,'changed')

    def test_pending_request_notifications_are_not_duplicated_by_replay(self):
        from catalog.models import WorkflowNotification, EmailOutbox
        get_user_model().objects.filter(pk=self.other.pk).update(email='connection-recipient@example.invalid')
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        preview=self.preview();key=uuid.uuid4();self.execute(preview,key=key)
        counts=(WorkflowNotification.objects.count(),EmailOutbox.objects.count())
        self.assertGreater(counts[0],0)
        self.assertGreater(counts[1],0)
        self.execute(preview,key=key)
        self.assertEqual((WorkflowNotification.objects.count(),EmailOutbox.objects.count()),counts)

    def test_business_role_label_preserves_actions_and_platform_moderator(self):
        from catalog.services.place_access import PLACE_ROLE_CHOICES,permissions_for_role
        from catalog.services.staff_roles import ADMIN_ROLE_LABELS,ADMIN_ROLE_MODERATOR
        from django.utils.translation import override
        with override('ru'):
            self.assertEqual(str(dict(PLACE_ROLE_CHOICES)['MODERATOR']),'Наблюдатель')
            self.assertEqual(str(ADMIN_ROLE_LABELS[ADMIN_ROLE_MODERATOR]),'Модератор')
        self.assertEqual(permissions_for_role('MODERATOR'),{'place.view','place.stats.view'})

    def test_search_keeps_selection_without_putting_csrf_in_url(self):
        self.client.force_login(self.owner)
        url=f'/ru/account/organizations/{self.org.pk}/connections/'
        response=self.client.post(url,{'action':'search','q':'küçə','place_ids':[self.place.pk]})
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.context.get('search',False))
        self.assertEqual(response.context['selected'],[self.place.pk])
        self.assertContains(response,'method="post" class="org-connect__panel" data-selection-form')
        self.assertFalse(OrganizationPlaceRequest.objects.exists())

    def test_receipt_does_not_block_existing_user_deletion(self):
        from catalog.models import OrganizationConnectionOperation
        operation=self.execute(self.preview())
        self.owner.delete()
        receipt=OrganizationConnectionOperation.objects.get(pk=operation.pk)
        self.assertIsNone(receipt.actor_id)
        with self.assertRaises(PermissionDenied):
            self.service().connection_result(actor=self.other,operation_id=operation.pk)

    def test_regular_reviewer_can_use_information_mode_without_place_edit_permission(self):
        from django.contrib.auth.models import Permission
        reviewer=get_user_model().objects.create_user(username='connection_reviewer',is_staff=True)
        reviewer.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',
            codename__in=['view_place','change_placeownershiprequest']))
        Organization.objects.filter(pk=self.org.pk).update(status='published')
        self.client.force_login(reviewer)
        listing=self.client.get('/admin/catalog/place/')
        self.assertContains(listing,'name="connection_selection"')
        response=self.client.post('/admin/catalog/place/organization-connections/',{'connection_selection':'1','_selected_action':[self.place.pk]})
        self.assertEqual(response.status_code,302)
        selection=self.client.get(response.url);token=selection.context['selection']
        preview=self.client.post('/admin/catalog/place/organization-connections/',{'selection':token,'action':'preview','organization_id':self.org.pk,'relationship_kind':'informational'})
        self.assertEqual(preview.status_code,200)
        operation=preview.context['operation']
        completed=self.client.post('/admin/catalog/place/organization-connections/',{'action':'confirm','preview_id':operation.pk,'idempotency_key':uuid.uuid4(),'consent':'1'})
        self.assertEqual(completed.status_code,302)
        self.place.refresh_from_db();self.assertEqual(self.place.organization_relationship_kind,'informational')
        from catalog.services.business_team import has_action
        self.assertFalse(has_action(user=reviewer,target=self.place,action='place.edit'))

    def test_read_only_staff_cannot_open_connection_action(self):
        from django.contrib.auth.models import Permission
        viewer=get_user_model().objects.create_user(username='connection_readonly',is_staff=True)
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='view_place'))
        self.client.force_login(viewer)
        response=self.client.get('/admin/catalog/place/')
        self.assertNotContains(response,'name="connection_selection"')
        self.assertEqual(self.client.post('/admin/catalog/place/organization-connections/',{'connection_selection':'1','_selected_action':[self.place.pk]}).status_code,404)

    def test_receipt_keeps_historical_result_but_shows_current_request_status(self):
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        operation=self.execute(self.preview())
        self.execute(self.preview(actor=self.other),actor=self.other)
        row=self.service().connection_result(actor=self.owner,operation_id=operation.pk)['rows'][0]
        self.assertEqual(row['code'],'requested')
        self.assertEqual(row.get('request_status'),'approved')
        self.assertIsNone(row['waiting_for'])
