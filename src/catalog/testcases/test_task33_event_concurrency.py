"""PostgreSQL contenders cannot overwrite occurrence history with a stale token."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from django.db import connections
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from catalog.models import Event
from catalog.testcases import test_task33_event_domain as domain_tests


class EventConcurrencyTests(TransactionTestCase):
    setUp=domain_tests.EventDomainTests.setUp
    api=domain_tests.EventDomainTests.api
    values=domain_tests.EventDomainTests.values
    create=domain_tests.EventDomainTests.create

    def contend(self,event,actions):
        barrier=Barrier(2)
        token=event.updated_at.isoformat()
        def worker(action):
            connections.close_all()
            try:
                barrier.wait(timeout=15)
                action(token)
                return 'saved'
            except ValidationError as exc:
                return exc.code if hasattr(exc,'code') else 'invalid'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(worker,actions))
        self.assertCountEqual(results,['saved','stale_version'])
        event.refresh_from_db()
        self.assertEqual(event.occurrence_changes.count(),1)
        self.assertEqual(event.occurrence_version,1)

    def test_two_cancellation_contenders_commit_only_one_history_entry(self):
        event=self.create()
        def action(token):
            self.api().cancel_event(actor=self.person,event_id=event.pk,expected_updated_at=token,reason='Real concurrent cancellation')
        self.contend(event,[action,action])
        self.assertEqual(event.occurrence_state,'cancelled')

    def test_cancel_and_reschedule_contenders_preserve_single_winning_period(self):
        event=self.create();start,end=event.start_datetime,event.end_datetime
        cancel=lambda token:self.api().cancel_event(actor=self.person,event_id=event.pk,expected_updated_at=token,reason='Cancel')
        move=lambda token:self.api().reschedule_event(actor=self.person,event_id=event.pk,start_datetime=start+timedelta(days=2),end_datetime=end+timedelta(days=2),expected_updated_at=token,reason='Move')
        self.contend(event,[cancel,move])
        entry=event.occurrence_changes.get()
        self.assertEqual(entry.before['start_datetime'],start.isoformat())
        if event.occurrence_state=='cancelled':self.assertEqual(event.start_datetime,start)
        else:self.assertEqual(event.start_datetime,start+timedelta(days=2))
