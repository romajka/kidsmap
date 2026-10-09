from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone
from catalog.services import organization_connections as connections
from catalog.models import Place
from catalog.testcases.test_organization_detach_transport import DetachTransportTests
from catalog.services.staff_roles import VOLUNTEER_GROUP

class ExtraDetachActorTests(TestCase):
    setUp=DetachTransportTests.setUp
    csrf_client=DetachTransportTests.csrf_client
    url=DetachTransportTests.url
    attached=DetachTransportTests.attached
    review=DetachTransportTests.review

    def test_inactive_actor_cannot_preview_execute_or_use_old_transports(self):
        import json,uuid
        from django.urls import reverse
        op,key=self.review()
        get_user_model().objects.filter(pk=self.owner.pk).update(is_active=False)
        for call in (lambda:connections.preview_detach(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk),lambda:connections.execute_detach(actor=self.owner,preview_id=op.pk,idempotency_key=key)):
            with self.assertRaises(PermissionDenied):call()
        res=self.client.post(reverse('organization_ownership_action',args=['detach','place',self.place.pk]),json.dumps({'organization_id':self.org.pk,'expected_ownership_version':self.place.ownership_version}),content_type='application/json')
        self.assertEqual(res.status_code,403)
        res=self.client.post(self.url('organization_workspace_detach'),{'expected_ownership_version':self.place.ownership_version})
        self.assertEqual(res.status_code,302);self.assertIn('/login/',res.url);self.attached()

    def test_volunteer_side_owner_cannot_obtain_or_execute_detach(self):
        op,key=self.review();self.owner.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        for call in (lambda:connections.preview_detach(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk),lambda:connections.execute_detach(actor=self.owner,preview_id=op.pk,idempotency_key=key)):
            with self.assertRaises(PermissionDenied):call()
        self.attached()

    def test_deleted_and_wrong_target_do_not_produce_actionable_receipt(self):
        from catalog.models import Organization
        org=Organization.objects.create(owner=self.owner,name_az='Synthetic different network')
        with self.assertRaises(ValidationError):connections.preview_detach(actor=self.owner,place_id=self.place.pk,organization_id=org.pk)
        Place.objects.filter(pk=self.place.pk).update(deleted_at=timezone.now())
        with self.assertRaises(ValidationError):connections.preview_detach(actor=self.owner,place_id=self.place.pk,organization_id=self.org.pk)
        self.attached()
