"""Audit-only RED tests of intended behavior; no application monkeypatches."""
import copy
import json
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place
from catalog.services.volunteer_places import revision_base_matches
from catalog.testcases.test_task33_publication import PublicationFixture


class MixedProjectionTests(PublicationFixture, TestCase):
    def setUp(self):
        super().setUp()
        plan = self.place.pricing_plan_records.get()
        plan.price = Decimal('15.00')
        plan.save()
        self.place.refresh_from_db()

    def mixed_draft(self):
        patch = self.s.snapshot(self.place, 'place')
        patch['name_ru'] = 'QA candidate identity'
        patch['address'] = 'QA candidate address'
        patch['pricing_plans'][0]['price'] = '18.00'
        revision = self.propose(patch, submit=False)
        self.place.refresh_from_db()
        return revision

    def resubmit(self, revision):
        patch = self.s.snapshot(self.place, 'place')
        patch.update(copy.deepcopy(revision.payload))
        return self.propose(patch, revision_version=revision.version, submit=True)

    def record(self, revision, **extra):
        self.place.refresh_from_db()
        revision.refresh_from_db()
        live = self.s.snapshot(self.place, 'place')
        row = {'case': self._testMethodName, 'revision_status': revision.status,
               'changed_fields': revision.changed_fields,
               'projection_base_mismatch_keys': sorted(k for k in self.s.PRICES if revision.base_snapshot.get(k) != live[k]),
               'review_conflict_keys': sorted(k for k in revision.changed_fields if revision.base_snapshot.get(k) != live.get(k)),
               'live_price_from': str(self.place.price_from), 'live_price_to': str(self.place.price_to),
               'live_identity_is_candidate': self.place.name_ru == 'QA candidate identity',
               'base_matches': revision_base_matches(revision, self.place), **extra}
        with (Path(__file__).parent / 'diagnostic.jsonl').open('a', encoding='utf-8') as out:
            out.write(json.dumps(row, ensure_ascii=False) + '\n')

    def test_mixed_draft_rebases_scalar_projections(self):
        revision = self.mixed_draft()
        self.record(revision)
        self.assertEqual(self.place.price_from, Decimal('18.00'))
        self.assertNotEqual(self.place.name_ru, 'QA candidate identity')
        live = self.s.snapshot(self.place, 'place')
        for name in self.s.PRICES:
            self.assertEqual(revision.base_snapshot[name], live[name], name)

    def test_mixed_save_resubmit_has_approve_button_and_no_conflict(self):
        revision = self.resubmit(self.mixed_draft())
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:volunteer_review', args=[self.place.pk]))
        self.record(revision, review_http=response.status_code,
                    review_page_conflict=response.context['conflict'],
                    approve_button_present=b'value="approve"' in response.content)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['conflict'])
        self.assertContains(response, 'value="approve"')

    def test_mixed_save_resubmit_service_can_approve(self):
        revision = self.resubmit(self.mixed_draft())
        self.record(revision)
        self.approve(revision)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, 'QA candidate identity')
        self.assertEqual(self.place.address, 'QA candidate address')
        self.assertEqual(self.place.price_from, Decimal('18.00'))

    def test_price_only_immediate_update_still_works(self):
        plans = copy.deepcopy(self.place.pricing_plans)
        identity = self.place.name_ru
        plan_id = plans[0]['id']
        plans[0]['price'] = '18.00'
        revision = self.propose({'pricing_plans': plans})
        self.approve(revision)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('18.00'))
        self.assertEqual(self.place.pricing_plans[0]['id'], plan_id)
        self.assertEqual(self.place.name_ru, identity)

    def test_actual_overlapping_source_change_is_still_detected(self):
        revision = self.propose({'name_ru': 'QA candidate identity'})
        # Controlled second-writer mutation; browser actor flow remains NOT RUN.
        Place.objects.filter(pk=self.place.pk).update(name_ru='QA second writer')
        self.place.refresh_from_db()
        self.assertFalse(revision_base_matches(revision, self.place))
        with self.assertRaisesMessage(ValidationError, 'Publication source conflict.'):
            self.approve(revision)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, 'QA second writer')

    def test_stale_version_is_rejected_before_a_second_write(self):
        initial_version = self.place.content_version
        revision = self.mixed_draft()
        with self.assertRaisesMessage(ValidationError, 'Publication source conflict.'):
            self.propose({'name_ru': 'QA stale tab'}, expected_version=initial_version,
                         revision_version=revision.version)
        self.place.refresh_from_db()
        self.assertEqual(self.place.price_from, Decimal('18.00'))
