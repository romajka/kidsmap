"""Approved complete offer trees remove omitted rows without erasing history."""
from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from catalog.models import Activity, OfferingGroup, PricingPlan
from catalog.services import publication
from catalog.services.pricing_plans import (
    place_pricing_records, replace_group_pricing_plans, replace_nested_pricing,
    serialize_nested_pricing,
)
from catalog.testcases import test_task33_pricing as pricing_fixtures
from catalog.testcases.utils import create_quality_place


class ApprovedGroupRemovalTests(TestCase):
    def setUp(self):
        pricing_fixtures.GroupPricingTests.setUp(self)
        replace_group_pricing_plans(self.group, [{'product_type': 'lesson', 'price': '20'}])
        replace_group_pricing_plans(self.other, [{'product_type': 'lesson', 'price': '80'}])
        self.kept_plan = PricingPlan.objects.get(offering_group=self.group)
        self.removed_plan = PricingPlan.objects.get(offering_group=self.other)
        self.staff = get_user_model().objects.create_superuser(
            username='fictional_offer_reviewer', email='offer@example.invalid', password=None)

    def removal_tree(self):
        tree = serialize_nested_pricing(self.place)
        tree['activities'][0]['groups'] = [
            row for row in tree['activities'][0]['groups'] if row['id'] != self.other.pk]
        return tree

    def propose(self, tree):
        self.place.refresh_from_db()
        return publication.propose(
            actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'nested_pricing': tree}, schema_version=publication.SCHEMA_VERSION,
            expected_version=self.place.content_version, revision_version=0, submit=True)

    def approve(self, tree):
        revision = self.propose(tree)
        publication.review(actor=self.staff, revision_id=revision.pk,
                           version=revision.version, approve=True)
        return revision

    def public_ids(self):
        return set(place_pricing_records(self.place).values_list('pk', flat=True))

    def state(self):
        self.place.refresh_from_db()
        return {
            'groups': list(OfferingGroup.objects.filter(activity__place=self.place).order_by('pk')
                           .values('pk', 'archived_at', 'content_version', 'name_az')),
            'activities': list(Activity.objects.filter(place=self.place).order_by('pk')
                               .values('pk', 'archived_at', 'content_version', 'name_az')),
            'plans': list(PricingPlan.objects.filter(offering_group__activity__place=self.place)
                          .order_by('pk').values('pk', 'offering_group_id', 'price')),
            'place': (self.place.content_version, self.place.price_from, self.place.price_to),
        }

    def test_group_removal_waits_for_approval_and_retains_history(self):
        revision = self.propose(self.removal_tree())
        self.other.refresh_from_db()
        self.assertIsNone(self.other.archived_at)
        self.assertIn(self.removed_plan.pk, self.public_ids())
        old_version = self.other.content_version
        publication.review(actor=self.staff, revision_id=revision.pk,
                           version=revision.version, approve=True)
        self.other.refresh_from_db()
        self.assertIsNotNone(self.other.archived_at)
        self.assertEqual(self.other.content_version, old_version + 1)
        self.assertTrue(PricingPlan.objects.filter(pk=self.removed_plan.pk).exists())
        self.assertEqual(self.public_ids(), {self.kept_plan.pk})
        self.place.refresh_from_db()
        self.assertEqual((self.place.price_from, self.place.price_to), (Decimal('20'), Decimal('20')))

    def test_omitted_activity_archives_its_groups_and_keeps_history(self):
        activity = Activity.objects.create(place=self.place, name_az='Another offer', status='published')
        group = OfferingGroup.objects.create(activity=activity, name_az='Another group')
        plan = PricingPlan.objects.create(offering_group=group, product_type='lesson', price=Decimal('30'))
        tree = serialize_nested_pricing(self.place)
        tree['activities'] = [row for row in tree['activities'] if row['id'] != self.activity.pk]
        self.approve(tree)
        self.activity.refresh_from_db(); self.group.refresh_from_db(); self.other.refresh_from_db()
        self.assertIsNotNone(self.activity.archived_at)
        self.assertIsNotNone(self.group.archived_at)
        self.assertIsNotNone(self.other.archived_at)
        self.assertTrue(PricingPlan.objects.filter(pk=self.removed_plan.pk).exists())
        self.assertEqual(self.public_ids(), {plan.pk})

    def test_empty_complete_tree_preserves_direct_tariff_and_history(self):
        direct = PricingPlan.objects.create(place=self.place, product_type='admission', price=Decimal('5'))
        self.approve({'pricing_schema_version': 2, 'activities': []})
        self.activity.refresh_from_db(); self.other.refresh_from_db()
        self.assertIsNotNone(self.activity.archived_at)
        self.assertIsNotNone(self.other.archived_at)
        self.assertTrue(PricingPlan.objects.filter(pk=self.removed_plan.pk).exists())
        self.assertEqual(self.public_ids(), {direct.pk})
        self.place.refresh_from_db()
        self.assertEqual((self.place.price_from, self.place.price_to), (Decimal('5'), Decimal('5')))

    def test_rejection_does_not_archive_live_group(self):
        before = self.state()
        revision = self.propose(self.removal_tree())
        publication.review(actor=self.staff, revision_id=revision.pk,
                           version=revision.version, approve=False, note='Fictional correction')
        self.assertEqual(self.state(), before)

    def test_default_partial_writer_preserves_omitted_rows(self):
        replace_nested_pricing(self.place, self.removal_tree())
        self.other.refresh_from_db()
        self.assertIsNone(self.other.archived_at)
        self.assertEqual(self.public_ids(), {self.kept_plan.pk, self.removed_plan.pk})
        replace_nested_pricing(self.place, {'pricing_schema_version': 2, 'activities': []})
        self.activity.refresh_from_db()
        self.assertIsNone(self.activity.archived_at)

    def test_explicit_complete_writer_archives_omitted_rows(self):
        replace_nested_pricing(self.place, self.removal_tree(), complete_tree=True)
        self.other.refresh_from_db()
        self.assertIsNotNone(self.other.archived_at)
        self.assertEqual(self.public_ids(), {self.kept_plan.pk})

    def test_foreign_ids_fail_before_any_complete_mutation(self):
        foreign_place = create_quality_place(name_az='Foreign fictional place')
        foreign_activity = Activity.objects.create(place=foreign_place, name_az='Foreign activity')
        foreign_group = OfferingGroup.objects.create(activity=foreign_activity, name_az='Foreign group')
        foreign_plan = PricingPlan.objects.create(offering_group=foreign_group, product_type='lesson', price=Decimal('50'))
        base = self.removal_tree()
        for kind, foreign_id in [('activity', foreign_activity.pk), ('group', foreign_group.pk), ('plan', foreign_plan.pk)]:
            with self.subTest(kind=kind):
                tree = deepcopy(base)
                row = tree['activities'][0]
                if kind == 'activity': row['id'] = foreign_id
                elif kind == 'group': row['groups'][0]['id'] = foreign_id
                else: row['groups'][0]['pricing_plans'][0]['id'] = foreign_id
                before = self.state()
                with self.assertRaises(ValidationError):
                    replace_nested_pricing(self.place, tree, complete_tree=True)
                self.assertEqual(self.state(), before)
        foreign_group.refresh_from_db()
        self.assertIsNone(foreign_group.archived_at)

    def test_failure_after_real_archive_rolls_back_tree_and_projections(self):
        before = self.state()
        original = OfferingGroup.archive
        def archive_then_fail(group):
            original(group)
            raise RuntimeError('Injected after actual archival')
        with patch.object(OfferingGroup, 'archive', archive_then_fail):
            with self.assertRaisesRegex(RuntimeError, 'Injected after actual archival'):
                replace_nested_pricing(self.place, self.removal_tree(), complete_tree=True)
        self.assertEqual(self.state(), before)

    def test_removed_tariff_of_retained_group_uses_existing_replacement(self):
        extra = PricingPlan.objects.create(offering_group=self.group, product_type='admission', price=Decimal('7'))
        tree = serialize_nested_pricing(self.place)
        for group in tree['activities'][0]['groups']:
            if group['id'] == self.group.pk:
                group['pricing_plans'] = [row for row in group['pricing_plans'] if row['id'] != extra.pk]
        self.approve(tree)
        self.assertFalse(PricingPlan.objects.filter(pk=extra.pk).exists())
        self.assertTrue(PricingPlan.objects.filter(pk=self.kept_plan.pk).exists())
        self.other.refresh_from_db()
        self.assertIsNone(self.other.archived_at)

    def test_repeat_and_stale_requests_do_not_mutate_approved_tree(self):
        stale_version = self.place.content_version
        revision = self.approve(self.removal_tree())
        before = self.state()
        with self.assertRaises(ValidationError):
            publication.review(actor=self.staff, revision_id=revision.pk,
                               version=revision.version, approve=True)
        with self.assertRaises(ValidationError):
            publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
                patch={'nested_pricing': serialize_nested_pricing(self.place)},
                schema_version=publication.SCHEMA_VERSION, expected_version=stale_version,
                revision_version=revision.version, submit=True)
        with self.assertRaises(ValidationError):
            publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
                patch={'nested_pricing': serialize_nested_pricing(self.place)},
                schema_version=publication.SCHEMA_VERSION, expected_version=self.place.content_version,
                revision_version=0, submit=True)
        self.assertEqual(self.state(), before)
        revision.refresh_from_db()
        updated = publication.propose(actor=self.staff, target_type='place', target_id=self.place.pk,
            patch={'nested_pricing': serialize_nested_pricing(self.place)},
            schema_version=publication.SCHEMA_VERSION, expected_version=self.place.content_version,
            revision_version=revision.version, submit=False)
        self.assertEqual(updated.status, 'draft')
