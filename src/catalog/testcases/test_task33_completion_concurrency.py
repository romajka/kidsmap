"""Controlled PostgreSQL lock schedules: conflict is explicit, retry is caller-owned."""
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event,current_thread
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.db import close_old_connections
from django.test import RequestFactory,TransactionTestCase
from catalog.models import Place,OwnerTeamMembership,OwnerTeamInvitation
from catalog.services import organization_ownership
from catalog.services.place_access import has_place_permission
from catalog.controllers.organization_ownership_api import organization_ownership_action
from catalog.testcases.test_task33_ownership import OwnershipFixture

class CompletionConcurrencyTests(OwnershipFixture,TransactionTestCase):
    def transfer_http(self):
        close_old_connections()
        try:
            request=RequestFactory().post('/ownership/',json.dumps({'new_owner_id':self.c.pk,'expected_ownership_version':1}),content_type='application/json')
            request.user=self.a;request._dont_enforce_csrf_checks=True
            return organization_ownership_action(request,action='transfer',target_type='place',target_id=self.place.pk)
        finally:close_old_connections()

    def test_join_wins_anchor_conflict_http409_then_explicit_retry_revokes_acl(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        team=OwnerTeamMembership.objects.create(place=self.place,owner=self.a,member=self.b,role='MANAGER')
        invite=OwnerTeamInvitation.objects.create(place=self.place,owner=self.a,email='completion@example.invalid')
        anchor_read=Event();joined=Event();original=organization_ownership._lock
        def controlled(model,ids,using):
            if model is Place and current_thread().name.startswith('completion-transfer'):
                anchor_read.set()
                if not joined.wait(15):raise AssertionError('Join schedule did not finish')
            return original(model,ids,using)
        with patch.object(organization_ownership,'_lock',side_effect=controlled):
            with ThreadPoolExecutor(max_workers=1,thread_name_prefix='completion-transfer') as pool:
                future=pool.submit(self.transfer_http)
                self.assertTrue(anchor_read.wait(15))
                try:self.service.confirm_join(actor=self.b,request_id=item.pk)
                finally:joined.set()
                response=future.result(timeout=20)
        self.assertEqual(response.status_code,409)
        self.assertEqual(json.loads(response.content)['error'],'structure_changed')
        self.assertTrue(json.loads(response.content)['reload_required'])
        self.place.refresh_from_db();self.assertEqual(self.place.owner_id,self.a.pk);self.assertEqual(self.place.ownership_version,1)
        team.refresh_from_db();invite.refresh_from_db();item.refresh_from_db();self.org.refresh_from_db()
        self.assertTrue(team.is_active);self.assertEqual(team.version,1);self.assertEqual(invite.status,'PENDING')
        self.assertEqual(item.status,'approved');self.assertEqual(self.place.content_version,2)
        self.assertEqual(self.org.ownership_version,1)
        self.assertTrue(self.service.affiliation_current(self.place,self.org))
        self.assertTrue(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,new_owner_id=self.c.pk,expected_ownership_version=self.place.ownership_version)
        self.place.refresh_from_db();team.refresh_from_db();invite.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.c.pk);self.assertEqual(self.place.ownership_version,2)
        self.assertFalse(team.is_active);self.assertEqual(team.version,2);self.assertEqual(invite.status,'CANCELED')
        self.assertFalse(has_place_permission(user=self.a,place=self.place,permission_code='place.edit'))
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        self.assertTrue(has_place_permission(user=self.c,place=self.place,permission_code='place.edit'))
        self.assertFalse(self.service.affiliation_current(self.place,self.org))

    def test_transfer_wins_then_old_confirmation_cannot_attach_or_grant(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        team=OwnerTeamMembership.objects.create(place=self.place,owner=self.a,member=self.b,role='MANAGER')
        invite=OwnerTeamInvitation.objects.create(place=self.place,owner=self.a,email='completion-success@example.invalid')
        place_locked=Event();confirmation_entered=Event();release=Event();original=organization_ownership._lock
        def controlled(model,ids,using):
            if current_thread().name.startswith('completion-confirm'):
                confirmation_entered.set()
            result=original(model,ids,using)
            if model is Place and current_thread().name.startswith('completion-transfer'):
                place_locked.set()
                if not release.wait(15):raise AssertionError('Transfer schedule did not release')
            return result
        def confirm():
            close_old_connections()
            try:
                with self.assertRaises(ValidationError):
                    self.service.confirm_join(actor=self.b,request_id=item.pk)
            finally:close_old_connections()
        with patch.object(organization_ownership,'_lock',side_effect=controlled):
            with ThreadPoolExecutor(max_workers=1,thread_name_prefix='completion-transfer') as transfer_pool:
                transfer=transfer_pool.submit(self.transfer_http)
                self.assertTrue(place_locked.wait(15))
                with ThreadPoolExecutor(max_workers=1,thread_name_prefix='completion-confirm') as confirm_pool:
                    confirmation=confirm_pool.submit(confirm)
                    try:self.assertTrue(confirmation_entered.wait(15))
                    finally:release.set()
                    response=transfer.result(timeout=20);confirmation.result(timeout=20)
        self.assertEqual(response.status_code,200)
        self.place.refresh_from_db();item.refresh_from_db()
        team.refresh_from_db();invite.refresh_from_db();self.org.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.c.pk);self.assertEqual(self.place.ownership_version,2)
        self.assertIsNone(self.place.organization_id);self.assertEqual(item.status,'pending')
        self.assertEqual(self.place.content_version,1);self.assertEqual(self.org.ownership_version,1)
        self.assertFalse(team.is_active);self.assertEqual(team.version,2);self.assertEqual(invite.status,'CANCELED')
        self.assertFalse(has_place_permission(user=self.a,place=self.place,permission_code='place.edit'))
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        self.assertTrue(has_place_permission(user=self.c,place=self.place,permission_code='place.edit'))
