"""Real PostgreSQL locks, interrupted batches and canonical notification dedupe."""
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from catalog.models import Organization, OrganizationPlaceRequest
from catalog.services import organization_connections as service
from catalog.testcases.utils import create_quality_place, ensure_quality_subcategory


class OrganizationConnectionConcurrencyTests(TransactionTestCase):
    def setUp(self):
        ensure_quality_subcategory('EDU')
        self.owner = get_user_model().objects.create_user(username='connection_race')
        self.org = Organization.objects.create(owner=self.owner, name_az='QA Race')
        self.places = [create_quality_place(owner=self.owner, name_az=f'QA Race {i}') for i in range(2)]

    def preview(self, org=None):
        return service.preview_connections(actor=self.owner, organization_id=(org or self.org).pk,
            relationship_kind='business', place_ids=[p.pk for p in self.places])

    def concurrent(self, jobs):
        if connection.vendor != 'postgresql': self.skipTest('Requires actual PostgreSQL locks')
        gate = Barrier(len(jobs))
        def run(job):
            close_old_connections()
            try:
                actor=get_user_model().objects.get(pk=self.owner.pk);gate.wait(timeout=10)
                operation=service.execute_connections(actor=actor,preview_id=job[0],idempotency_key=job[1])
                return str(operation.pk)
            finally: close_old_connections()
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            futures=[pool.submit(run,job) for job in jobs]
            return [f.result(timeout=30) for f in futures]

    def test_double_submit_same_key_commits_each_row_once(self):
        preview=self.preview();key=uuid.uuid4()
        results=self.concurrent([(preview.pk,key),(preview.pk,key)])
        self.assertEqual(results[0],results[1])
        self.assertEqual(OrganizationPlaceRequest.objects.count(),2)
        self.assertEqual(list(preview.items.values_list('result',flat=True)),['connected','connected'])

    def test_competing_networks_do_not_move_a_linked_place(self):
        other=Organization.objects.create(owner=self.owner,name_az='QA Rival')
        first=self.preview();second=self.preview(other)
        self.concurrent([(first.pk,uuid.uuid4()),(second.pk,uuid.uuid4())])
        results=[list(op.items.values_list('result',flat=True)) for op in (first,second)]
        self.assertEqual(sum(r.count('connected') for r in results),2)
        for place in self.places:
            place.refresh_from_db();self.assertIn(place.organization_id,(self.org.pk,other.pk))
        self.assertEqual(OrganizationPlaceRequest.objects.filter(status='approved').count(),2)

    def test_interrupted_batch_resumes_only_uncommitted_rows(self):
        preview=self.preview();key=uuid.uuid4();original=service._execute_row;calls=[]
        def interrupt(actor,operation,item_id):
            calls.append(item_id)
            if len(calls)==2: raise RuntimeError('QA process interrupted between rows')
            return original(actor,operation,item_id)
        with patch.object(service,'_execute_row',side_effect=interrupt):
            with self.assertRaises(RuntimeError):service.execute_connections(actor=self.owner,preview_id=preview.pk,idempotency_key=key)
        self.assertEqual(preview.items.filter(completed_at__isnull=False).count(),1)
        result=service.execute_connections(actor=self.owner,preview_id=preview.pk,idempotency_key=key)
        self.assertEqual(result.status,'completed')
        self.assertEqual(OrganizationPlaceRequest.objects.count(),2)
