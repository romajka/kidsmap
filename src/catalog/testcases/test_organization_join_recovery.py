"""User outcomes for explicit cancellation and fresh bilateral consent."""
import json
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.test import TestCase
from django.urls import reverse
from catalog.models import Organization, OrganizationPlaceRequest, Place
from catalog.services import organization_ownership as service
from catalog.testcases.utils import create_quality_place

class JoinRecoveryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.network_owner = User.objects.create_user(username='recovery_network')
        self.place_owner = User.objects.create_user(username='recovery_place')
        self.outsider = User.objects.create_user(username='recovery_other')
        self.org = Organization.objects.create(owner=self.network_owner, name_az='Recovery network')
        self.place = create_quality_place(owner=self.place_owner, created_by=self.place_owner, name_az='Recovery branch')
        self.item = service.request_join(actor=self.network_owner, place_id=self.place.pk, organization_id=self.org.pk)
        Place.objects.filter(pk=self.place.pk).update(content_version=F('content_version')+1)
        self.place.refresh_from_db()

    def token(self, actor=None):
        self.assertTrue(callable(getattr(service, 'join_recovery_state', None)), 'No safe explicit recovery for stale join')
        return service.join_recovery_state(actor=actor or self.network_owner, request_id=self.item.pk)

    def cancel(self, actor=None, token=None):
        return service.cancel_join(actor=actor or self.network_owner, request_id=self.item.pk, expected_state=token or self.token(actor))

    def test_cancel_then_new_request_requires_new_other_owner_consent(self):
        old_consent=self.item.organization_owner_confirmed_at
        self.cancel()
        self.item.refresh_from_db()
        self.assertEqual(self.item.status,'canceled')
        self.assertEqual(self.item.organization_owner_confirmed_at,old_consent)
        fresh=service.request_join(actor=self.network_owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.assertNotEqual(fresh.pk,self.item.pk)
        self.assertEqual(fresh.base_place_content_version,self.place.content_version)
        self.assertIsNone(fresh.place_owner_confirmed_at)
        self.assertEqual(fresh.status,'pending')
        with self.assertRaises(ValidationError):service.confirm_join(actor=self.place_owner,request_id=self.item.pk)
        service.confirm_join(actor=self.place_owner,request_id=fresh.pk)
        self.place.refresh_from_db();self.assertEqual(self.place.organization_id,self.org.pk)

    def test_repeat_cancel_does_not_cancel_new_pending(self):
        token=self.token();self.cancel(token=token)
        fresh=service.request_join(actor=self.network_owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.assertEqual(self.cancel(token=token).status,'canceled')
        fresh.refresh_from_db();self.assertEqual(fresh.status,'pending')

    def test_changed_content_rejects_cancel_without_writes(self):
        token=self.token();Place.objects.filter(pk=self.place.pk).update(content_version=F('content_version')+1)
        with self.assertRaises(ValidationError) as cm:self.cancel(token=token)
        self.assertEqual(cm.exception.code,'request_conflict')
        self.item.refresh_from_db();self.assertEqual(self.item.status,'pending')

    def test_outsider_and_actor_token_swap_denied(self):
        token=self.token()
        with self.assertRaises(PermissionDenied):self.cancel(actor=self.outsider,token=token)
        with self.assertRaises(ValidationError):self.cancel(actor=self.place_owner,token=token)

    def test_former_owner_cannot_cancel(self):
        token=self.token();Organization.objects.filter(pk=self.org.pk).update(owner=self.outsider,ownership_version=F('ownership_version')+1)
        with self.assertRaises(PermissionDenied):self.cancel(token=token)

    def test_archived_organization_can_stop_pending_without_link(self):
        from django.utils import timezone
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.cancel();self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)

    def test_deleted_place_can_stop_pending_without_link(self):
        from django.utils import timezone
        Place.objects.filter(pk=self.place.pk).update(deleted_at=timezone.now())
        self.cancel();self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)

    def test_approved_request_cannot_be_canceled(self):
        self.cancel();fresh=service.request_join(actor=self.network_owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.item=fresh;token=self.token();service.confirm_join(actor=self.place_owner,request_id=fresh.pk)
        with self.assertRaises(ValidationError):self.cancel(token=token)
        self.place.refresh_from_db();self.assertEqual(self.place.organization_id,self.org.pk)

    def test_informational_request_not_in_business_recovery(self):
        OrganizationPlaceRequest.objects.filter(pk=self.item.pk).update(relationship_kind='informational')
        with self.assertRaises(PermissionDenied):self.token()

    def test_private_place_metadata_hidden_but_network_owner_can_cancel(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False)
        self.client.force_login(self.network_owner)
        response=self.client.get(reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,self.place.name_az)
        self.assertContains(response,'name="expected_state"')
        self.assertEqual(self.client.get(reverse('organization_workspace_detail',args=[self.org.pk])).status_code,200)

    def test_json_cancel_strict_payload_and_replay(self):
        token=self.token();self.client.force_login(self.network_owner)
        url=reverse('organization_ownership_action',args=['cancel-join','place',self.item.pk])
        self.assertEqual(self.client.get(url).status_code,405)
        self.assertEqual(self.client.post(url,data=json.dumps({}),content_type='application/json').status_code,400)
        for _ in range(2):
            response=self.client.post(url,data=json.dumps({'expected_state':token}),content_type='application/json')
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json(),{'request_id':self.item.pk,'status':'canceled'})

    def test_html_cancel_requires_csrf_and_explicit_state(self):
        from django.test import Client
        url=reverse('organization_workspace_cancel',args=[self.org.pk,self.item.pk])
        client=Client(enforce_csrf_checks=True);client.force_login(self.network_owner)
        self.assertEqual(client.post(url,{'expected_state':self.token()}).status_code,403)
        self.client.force_login(self.network_owner)
        self.assertEqual(self.client.get(url).status_code,405)
        response=self.client.post(url,{'expected_state':self.token()})
        self.assertEqual(response.status_code,302)
        self.item.refresh_from_db();self.assertEqual(self.item.status,'canceled')

    def test_cancel_preserves_place_and_does_not_grant_access(self):
        before=Place.objects.filter(pk=self.place.pk).values().get()
        self.cancel()
        self.assertEqual(Place.objects.filter(pk=self.place.pk).values().get(),before)
        from catalog.services.business_team import has_action
        self.assertFalse(has_action(user=self.network_owner,target=self.place,action='place.edit'))

    def test_employee_with_view_permissions_cannot_cancel(self):
        from catalog.models import OrganizationGrant
        OrganizationGrant.objects.create(organization=self.org,owner=self.network_owner,member=self.outsider,base_ownership_version=self.org.ownership_version,role='MANAGER',actions=['organization.view','place.view'],scope='all_network')
        with self.assertRaises(PermissionDenied):self.token(self.outsider)

    def test_expired_and_tampered_tokens_do_not_cancel(self):
        from unittest.mock import patch
        token=self.token()
        with self.assertRaises(ValidationError):self.cancel(token=token+'x')
        import time
        with patch('django.core.signing.time.time',return_value=time.time()+1900):
            with self.assertRaises(ValidationError) as cm:self.cancel(token=token)
        self.assertEqual(cm.exception.code,'request_conflict')
        self.item.refresh_from_db();self.assertEqual(self.item.status,'pending')

    def test_place_owner_can_restart_to_private_network_without_names(self):
        self.cancel(actor=self.place_owner)
        self.client.force_login(self.place_owner)
        response=self.client.get(reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))
        self.assertNotContains(response,self.org.name_az)
        self.assertContains(response,reverse('organization_connections',args=[self.org.pk]))
        self.assertEqual(self.client.get(reverse('organization_connections',args=[self.org.pk])).status_code,200)
        fresh=service.request_join(actor=self.place_owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.assertIsNone(fresh.organization_owner_confirmed_at)
        self.assertEqual(fresh.status,'pending')

    def test_private_pending_is_visible_only_as_neutral_recovery(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False)
        self.client.force_login(self.network_owner)
        response=self.client.get(reverse('organization_workspace_detail',args=[self.org.pk]))
        self.assertNotContains(response,self.place.name_az)
        self.assertContains(response,reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(reverse('organization_join_recovery',args=[self.org.pk,self.item.pk])).status_code,404)

    def test_old_preview_cannot_connect_after_cancel_and_new_request(self):
        import uuid
        from catalog.services import organization_connections as connections
        preview=connections.preview_connections(actor=self.network_owner,organization_id=self.org.pk,relationship_kind='business',place_ids=[self.place.pk])
        self.cancel();service.request_join(actor=self.network_owner,place_id=self.place.pk,organization_id=self.org.pk)
        connections.execute_connections(actor=self.network_owner,preview_id=preview.pk,idempotency_key=uuid.uuid4())
        self.place.refresh_from_db();self.assertIsNone(self.place.organization_id)

    def test_stale_search_and_preview_have_recovery_link_not_executable(self):
        from catalog.services import organization_connections as connections
        result=connections.search_places(actor=self.network_owner,organization_id=self.org.pk,query='Recovery branch')
        self.assertTrue(result['rows'][0]['recovery_required'])
        self.client.force_login(self.network_owner)
        response=self.client.get(reverse('organization_connections',args=[self.org.pk]),{'q':'Recovery branch'})
        self.assertContains(response,reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))

    def test_real_csrf_html_cancel_then_reload(self):
        from django.test import Client
        c=Client(enforce_csrf_checks=True);c.force_login(self.network_owner)
        page=c.get(reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))
        self.assertEqual(page.status_code,200)
        response=c.post(reverse('organization_workspace_cancel',args=[self.org.pk,self.item.pk]),{'csrfmiddlewaretoken':c.cookies['csrftoken'].value,'expected_state':self.token()})
        self.assertEqual(response.status_code,302)
        self.assertContains(c.get(response.url),'data-recovery-result')


    def test_browser_token_does_not_disclose_private_owner_or_versions(self):
        from django.core import signing
        Place.objects.filter(pk=self.place.pk).update(status='draft',is_active=False)
        self.client.force_login(self.network_owner)
        page=self.client.get(reverse('organization_join_recovery',args=[self.org.pk,self.item.pk]))
        payload=signing.loads(page.context['expected_state'],salt=service.JOIN_RECOVERY_SALT)
        self.assertEqual(set(payload),{'actor','request','state'})
        self.assertIsInstance(payload['state'],str,'Private owner IDs and versions must not be shipped in a readable token')


from django.test import TransactionTestCase
class JoinRecoveryConcurrencyTests(TransactionTestCase):
    def setUp(self):
        from catalog.testcases.utils import ensure_quality_subcategory
        ensure_quality_subcategory('EDU')
        U=get_user_model();self.a=U.objects.create_user(username='cancel_network');self.b=U.objects.create_user(username='cancel_place')
        self.org=Organization.objects.create(owner=self.a,name_az='Race network')
        self.place=create_quality_place(owner=self.b,name_az='Race branch')
        self.item=service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        self.token=service.join_recovery_state(actor=self.a,request_id=self.item.pk)

    def race(self, confirm=False):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections, connection
        self.assertEqual(connection.vendor,'postgresql')
        gate=Barrier(2)
        def job(other):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=self.b.pk if other and confirm else self.a.pk)
                gate.wait(timeout=10)
                try:
                    row=service.confirm_join(actor=actor,request_id=self.item.pk) if other and confirm else service.cancel_join(actor=actor,request_id=self.item.pk,expected_state=self.token)
                    return row.status
                except ValidationError:return 'conflict'
            finally:close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            fs=[pool.submit(job,x) for x in (False,True)]
            return [f.result(timeout=30) for f in fs]

    def test_double_cancel_has_one_history_change(self):
        self.assertEqual(self.race(),['canceled','canceled'])
        self.item.refresh_from_db();self.assertEqual(self.item.note.count('Explicit withdrawal'),1)

    def test_confirm_and_cancel_have_exactly_one_winner(self):
        results=self.race(confirm=True)
        self.item.refresh_from_db();self.place.refresh_from_db()
        self.assertIn(self.item.status,('approved','canceled'))
        self.assertEqual(results.count('conflict'),1)
        self.assertEqual(self.place.organization_id,self.org.pk if self.item.status=='approved' else None)
