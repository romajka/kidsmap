"""QA-only deterministic ordering of an unchanged ownership structure retry."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event, current_thread
from unittest.mock import patch
from django.core.exceptions import ValidationError
from django.db import close_old_connections
from django.test import TransactionTestCase
from catalog.models import Organization
from catalog.services.place_access import has_place_permission
from catalog.testcases import test_task33_ownership as ownership_tests


class OwnershipStructureRetryProbe(ownership_tests.OwnershipFixture, TransactionTestCase):
    def test_anchor_change_rejects_first_transfer_and_retry_revokes_network_acl(self):
        item=self.service.request_join(actor=self.a,place_id=self.place.pk,organization_id=self.org.pk)
        anchor_read=Event();confirmation_committed=Event()
        original_lock=self.service._lock
        def ordered_lock(model,ids,using):
            if model is Organization and ids==[None] and current_thread().name=='probe-transfer':
                anchor_read.set()
                if not confirmation_committed.wait(10):raise AssertionError('Confirmation did not commit')
            return original_lock(model,ids,using)
        def transfer():
            current_thread().name='probe-transfer';close_old_connections()
            try:
                try:
                    self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,
                                                new_owner_id=self.c.pk,expected_ownership_version=1)
                except ValidationError as error:return str(error)
                return 'unexpected success'
            finally:close_old_connections()
        def confirm():
            close_old_connections()
            try:
                if not anchor_read.wait(10):raise AssertionError('Transfer anchor was not read')
                self.service.confirm_join(actor=self.b,request_id=item.pk)
                confirmation_committed.set()
            finally:close_old_connections()
        with patch.object(self.service,'_lock',ordered_lock),ThreadPoolExecutor(max_workers=2) as pool:
            transfer_result=pool.submit(transfer);confirmation=pool.submit(confirm)
            confirmation.result(timeout=20);error=transfer_result.result(timeout=20)
        self.assertIn('Structure changed; reload.',error)
        self.place.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.a.pk)
        self.assertEqual(self.place.ownership_version,1)
        self.assertTrue(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
        self.service.transfer_owner(actor=self.a,target_type='place',target_id=self.place.pk,
                                    new_owner_id=self.c.pk,expected_ownership_version=1)
        self.place.refresh_from_db()
        self.assertEqual(self.place.owner_id,self.c.pk)
        self.assertEqual(self.place.ownership_version,2)
        self.assertFalse(has_place_permission(user=self.b,place=self.place,permission_code='place.edit'))
