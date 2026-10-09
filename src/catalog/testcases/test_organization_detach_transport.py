"""HTTP detach requires a reviewed, actor-bound receipt; private display stays private."""
import json
import uuid
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.middleware.csrf import get_token
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Organization, OrganizationConnectionOperation, OrganizationPlaceRequest, Place
from catalog.services import organization_connections as connections, organization_ownership as ownership
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory


class DetachTransportTests(TestCase):
    def setUp(self):
        ensure_quality_subcategory('EDU')
        self.owner = get_user_model().objects.create_user(username='detach_transport_owner')
        self.other = get_user_model().objects.create_user(username='detach_transport_other')
        self.staff = get_user_model().objects.create_user(username='detach_transport_staff', is_staff=True, is_superuser=True)
        self.org = Organization.objects.create(owner=self.owner, name_az='Synthetic detach network')
        self.place = create_quality_place(owner=self.owner, name_az='Synthetic detach place')
        ownership.request_join(actor=self.owner, place_id=self.place.pk, organization_id=self.org.pk)
        self.place.refresh_from_db()
        self.client = self.csrf_client(self.owner)

    def csrf_client(self, user):
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        token = get_token(RequestFactory().get('/'))
        client.cookies['csrftoken'] = token
        client.defaults['HTTP_X_CSRFTOKEN'] = token
        return client

    def url(self, name='organization_detach_preview', place=None, org=None):
        return reverse(name, args=[(org or self.org).pk, (place or self.place).pk])

    def attached(self):
        self.place.refresh_from_db()
        self.assertEqual(self.place.organization_id, self.org.pk)

    def review(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        return response.context['operation'], response.context['idempotency_key']

    def confirm(self, op, key, **overrides):
        data = dict(action='confirm', preview_id=str(op.pk), idempotency_key=str(key), consent='1')
        data.update(overrides)
        return self.client.post(self.url(), data)

    def test_legacy_html_redirects_without_mutation_or_receipt(self):
        response = self.client.post(self.url('organization_workspace_detach'), {'expected_ownership_version': self.place.ownership_version})
        self.attached()
        self.assertRedirects(response, self.url(), fetch_redirect_response=False)
        self.assertFalse(OrganizationConnectionOperation.objects.exists())

    def test_legacy_json_requires_confirmation_without_mutation(self):
        response = self.client.post(reverse('organization_ownership_action', args=['detach', 'place', self.place.pk]), json.dumps({'organization_id': self.org.pk, 'expected_ownership_version': self.place.ownership_version}), content_type='application/json')
        self.attached()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {'error': 'confirmation_required', 'preview_url': self.url()})
        self.assertFalse(OrganizationConnectionOperation.objects.exists())

    def test_actual_csrf_required_on_all_transports(self):
        client = Client(enforce_csrf_checks=True); client.force_login(self.owner)
        for url, data in [(self.url('organization_workspace_detach'), {'expected_ownership_version': self.place.ownership_version}), (reverse('organization_ownership_action', args=['detach','place',self.place.pk]), '{}'), (self.url(), {'action':'confirm'})]:
            self.assertEqual(client.post(url, data, content_type='application/json' if isinstance(data,str) else 'application/x-www-form-urlencoded').status_code, 403)
        self.attached()

    def test_consent_receipt_required_and_valid_repeat_is_idempotent(self):
        op, key = self.review(); self.attached()
        self.assertEqual(self.confirm(op, key, consent='0').status_code, 409); self.attached()
        self.assertEqual(self.confirm(op, key, preview_id=str(uuid.uuid4())).status_code, 404); self.attached()
        before = (self.place.owner_id, self.place.status, self.place.photo.name)
        self.assertEqual(self.confirm(op, key).status_code, 302)
        self.place.refresh_from_db(); self.assertIsNone(self.place.organization_id)
        version = self.place.content_version
        self.assertEqual((self.place.owner_id,self.place.status,self.place.photo.name), before)
        self.assertEqual(self.confirm(op,key).status_code,302)
        self.place.refresh_from_db(); self.assertEqual(self.place.content_version,version)
        self.assertEqual(self.confirm(op,uuid.uuid4()).status_code,409)

    def test_foreign_and_staff_get_no_receipt_or_metadata(self):
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False)
        for user in (self.other,self.staff):
            client=self.csrf_client(user)
            for url in (self.url(),self.url('organization_workspace_detach')):
                response=client.get(url) if url==self.url() else client.post(url,{'expected_ownership_version':self.place.ownership_version})
                self.assertEqual(response.status_code,404)
                self.assertNotContains(response,self.place.name_az,status_code=404)
            response=client.post(reverse('organization_ownership_action',args=['detach','place',self.place.pk]),json.dumps({'organization_id':self.org.pk,'expected_ownership_version':self.place.ownership_version}),content_type='application/json')
            self.assertEqual(response.status_code,403); self.assertNotIn('preview_url',response.json())
        self.assertFalse(OrganizationConnectionOperation.objects.exists()); self.attached()

    def test_archived_network_lawful_private_detach_is_redacted(self):
        private=create_quality_place(owner=self.other,name_az='DO NOT DISCLOSE PLACE',address='DO NOT DISCLOSE ADDRESS',status='published')
        req=ownership.request_join(actor=self.owner,place_id=private.pk,organization_id=self.org.pk)
        ownership.confirm_join(actor=self.other,request_id=req.pk)
        Place.objects.filter(pk=private.pk).update(status='draft',is_active=False)
        Organization.objects.filter(pk=self.org.pk).update(archived_at=timezone.now())
        self.assertFalse(connections.visible_places(self.owner).filter(pk=private.pk).exists())
        response=self.client.get(self.url(place=private)); self.assertEqual(response.status_code,200)
        for secret in (private.name_az,private.address): self.assertNotContains(response,secret)
        op=response.context['operation']; result=connections.connection_result(actor=self.owner,operation_id=op.pk)
        row=result['rows'][0]
        self.assertEqual(set(row),{'id','code','complete','executable','redacted'})
        self.assertTrue(row['redacted']); self.assertTrue(row['executable']); self.assertNotIn('impact',result)
        confirmed=self.client.post(self.url(place=private),dict(action='confirm',preview_id=str(op.pk),idempotency_key=str(response.context['idempotency_key']),consent='1'))
        self.assertEqual(confirmed.status_code,302)
        private.refresh_from_db(); self.assertIsNone(private.organization_id)
        final=self.client.get(confirmed['Location']); self.assertEqual(final.status_code,200)
        self.assertNotContains(final,private.name_az)
        self.assertFalse(connections.visible_places(self.owner).filter(pk=private.pk).exists())
        with self.assertRaises(PermissionDenied): connections.preview_connections(actor=self.owner,organization_id=self.org.pk,relationship_kind='business',place_ids=[private.pk])

    def test_stale_version_and_extra_api_consent_fields_rejected(self):
        url=reverse('organization_ownership_action',args=['detach','place',self.place.pk])
        data={'organization_id':self.org.pk,'expected_ownership_version':self.place.ownership_version+1}
        self.assertEqual(self.client.post(url,json.dumps(data),content_type='application/json').status_code,400)
        self.assertEqual(self.client.post(self.url('organization_workspace_detach'),data).status_code,409)
        data['expected_ownership_version']=self.place.ownership_version; data['consent']=True
        self.assertEqual(self.client.post(url,json.dumps(data),content_type='application/json').status_code,400)
        self.attached()

    def test_expired_and_other_actor_receipts_do_not_detach(self):
        op,key=self.review()
        OrganizationConnectionOperation.objects.filter(pk=op.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
        self.assertEqual(self.confirm(op,key).status_code,409); self.attached()
        other=self.csrf_client(self.other)
        response=other.post(self.url(),dict(action='confirm',preview_id=str(op.pk),idempotency_key=str(key),consent='1'))
        self.assertEqual(response.status_code,404); self.attached()

    def test_place_org_action_binding(self):
        op,key=self.review()
        other_place=create_quality_place(owner=self.owner,name_az='Synthetic other')
        org=Organization.objects.create(owner=self.owner,name_az='Synthetic other org')
        payload=dict(action='confirm',preview_id=str(op.pk),idempotency_key=str(key),consent='1')
        for url in (self.url(place=other_place),self.url(org=org),reverse('organization_connections',args=[self.org.pk])):
            self.assertEqual(self.client.post(url,payload).status_code,404)
        connect=connections.preview_connections(actor=self.owner,organization_id=self.org.pk,relationship_kind='business',place_ids=[self.place.pk])
        self.assertEqual(self.confirm(connect,key).status_code,404); self.attached()

    def test_content_conflict_preserves_link(self):
        op,key=self.review()
        Place.objects.filter(pk=self.place.pk).update(content_version=F('content_version')+1)
        self.assertEqual(self.confirm(op,key).status_code,302)
        self.assertEqual(op.items.get().result,'changed'); self.attached()

    def test_lost_authority_preserves_link_and_does_not_reveal_private(self):
        op,key=self.review()
        Organization.objects.filter(pk=self.org.pk).update(owner=self.other,ownership_version=F('ownership_version')+1)
        Place.objects.filter(pk=self.place.pk).update(owner=self.other,ownership_version=F('ownership_version')+1,status='draft',is_active=False)
        self.assertEqual(self.confirm(op,key).status_code,302)
        self.assertIn(op.items.get().result,('no_rights','unavailable')); self.attached()
        self.assertNotIn(self.place.name_az,str(connections.connection_result(actor=self.owner,operation_id=op.pk)))

    def test_old_receipt_after_rejoin_does_not_detach_again(self):
        op,key=self.review(); self.confirm(op,key)
        ownership.request_join(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.assertEqual(self.confirm(op,key).status_code,302); self.attached()

    def test_org_owner_cannot_review_unattached_private_without_history(self):
        private=create_quality_place(owner=self.other,status='draft',is_active=False)
        with self.assertRaises(PermissionDenied):
            connections.preview_detach(actor=self.owner,place_id=private.pk,organization_id=self.org.pk)
        self.assertFalse(OrganizationConnectionOperation.objects.exists())

    def test_failed_canonical_transition_rolls_back_and_replay_does_not_retry(self):
        op,key=self.review()
        with patch.object(ownership,'detach',side_effect=RuntimeError('synthetic transition failure')):
            result=connections.execute_detach(actor=self.owner,preview_id=op.pk,idempotency_key=key)
        self.assertEqual(result.items.get().result,'failed'); self.attached()
        connections.execute_detach(actor=self.owner,preview_id=op.pk,idempotency_key=key); self.attached()

    def test_reviewed_detach_preserves_program_media_group_price_and_hours(self):
        from catalog.models import Activity, Program, OfferingGroup, PricingPlan, PlacePhoto, PlaceScheduleDay, PlaceScheduleInterval
        from datetime import time
        program=Program.objects.create(organization=self.org,name_az='Synthetic approved program',description_az='Approved common text',status='published',approved_at=timezone.now())
        activity=Activity.objects.create(place=self.place,program=program,supplement_az='Local supplement')
        group=OfferingGroup.objects.create(activity=activity,age_from=4,age_to=8,schedule_text='Saturday 14:00')
        price=PricingPlan.objects.create(place=self.place,product_type='membership',billing_mode='recurring',billing_interval='month',billing_interval_count=1,price_kind='exact',price=77)
        PlacePhoto.objects.create(place=self.place,image='synthetic/first.png',order=7)
        PlacePhoto.objects.create(place=self.place,image='synthetic/second.png',order=2)
        day=PlaceScheduleDay.objects.create(place=self.place,weekday='mon',is_closed=False)
        PlaceScheduleInterval.objects.create(schedule_day=day,start_time=time(9),end_time=time(18))
        gallery=list(self.place.gallery.values_list('pk','image','order'))
        hours=list(PlaceScheduleInterval.objects.filter(schedule_day=day).values())
        op,key=self.review(); self.assertEqual(self.confirm(op,key).status_code,302)
        activity.refresh_from_db(); group.refresh_from_db(); price.refresh_from_db()
        self.assertIsNone(activity.program_id); self.assertEqual(activity.source_program_id,program.pk)
        self.assertEqual(activity.program_snapshot['description_az'],'Approved common text')
        self.assertEqual(activity.supplement_az,'Local supplement'); self.assertEqual(group.schedule_text,'Saturday 14:00')
        self.assertEqual(price.price,77); self.assertEqual(list(self.place.gallery.values_list('pk','image','order')),gallery)
        self.assertEqual(list(PlaceScheduleInterval.objects.filter(schedule_day=day).values()),hours)

    def test_detach_dependency_conflicts_require_new_review(self):
        from catalog.models import Activity, OfferingGroup, PricingPlan, OrganizationGrant
        activity=Activity.objects.create(place=self.place,name_az='Synthetic class')
        group=OfferingGroup.objects.create(activity=activity,name_az='Synthetic group')
        price=PricingPlan.objects.create(place=self.place,product_type='membership',billing_mode='recurring',billing_interval='month',billing_interval_count=1,price_kind='exact',price=77)
        mutations=[lambda:OfferingGroup.objects.filter(pk=group.pk).update(content_version=F('content_version')+1),
            lambda:PricingPlan.objects.filter(pk=price.pk).update(price=88,updated_at=timezone.now()),
            lambda:OrganizationGrant.objects.create(organization=self.org,owner=self.owner,member=self.other,base_ownership_version=self.org.ownership_version,scope='all_network',actions=['place.view'])]
        for mutate in mutations:
            op,key=self.review(); mutate(); self.assertEqual(self.confirm(op,key).status_code,302)
            self.assertEqual(op.items.get().result,'changed'); self.attached()
