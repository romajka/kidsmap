"""Stage 11 conversion on disposable PostgreSQL only."""
from django.test import TestCase, TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from pathlib import Path
import stat
import os
from tempfile import TemporaryDirectory
from copy import deepcopy
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import connection, close_old_connections, IntegrityError, transaction
from catalog.models import PricingPlan, PlacePhoto, PlaceLike, PlaceReview, PlaceReviewReaction, Category
from catalog.services.catalog_conversion import build_plan, apply_plan, reconciliation
from catalog.testcases.utils import create_quality_place


class ConversionTests(TestCase):
    def test_empty_plan_and_read_only_dry_run(self):
        before = self._counts()
        plan = build_plan()
        self.assertEqual(plan['entries'], [])
        self.assertEqual(self._counts(), before)

    def test_populated_dry_run_preserves_all_database_rows(self):
        place = create_quality_place()
        PricingPlan.objects.create(place=place, product_type='lesson', price='20')
        before = self._counts()
        plan = build_plan()
        self.assertEqual(self._counts(), before)
        self.assertEqual({(e['source_type'], e['piece_key']) for e in plan['entries']}, {
            ('place', 'identity'), ('place', 'organization'), ('pricing_plan', 'identity'), ('pricing_plan', 'group_assignment')})

    def test_testing_flag_with_database_url_cannot_apply(self):
        create_quality_place()
        plan = build_plan()
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://unsafe.invalid/db'}):
            with self.assertRaises(RuntimeError):
                build_plan()
            with self.assertRaises(RuntimeError):
                apply_plan(plan)
        with patch.dict(settings.DATABASES['default'], {'HOST': '/tmp/not-qa-socket'}):
            with self.assertRaises(RuntimeError):
                build_plan()
            with self.assertRaises(RuntimeError):
                apply_plan(plan)
        from catalog.models import ConversionRun
        self.assertFalse(ConversionRun.objects.exists())

    def test_failed_batch_rolls_back_mapping_and_checkpoint_together(self):
        create_quality_place()
        plan = build_plan()
        from catalog.models import ConversionMapping, ConversionRun
        real_create = ConversionMapping.objects.create
        calls = 0
        def fail_second(**kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError('Synthetic interruption inside batch')
            return real_create(**kwargs)
        with patch.object(ConversionMapping.objects, 'create', side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                apply_plan(plan, batch_size=2)
        self.assertEqual(ConversionMapping.objects.count(), 0)
        self.assertEqual(ConversionRun.objects.count(), 0)
        result = apply_plan(plan, batch_size=2)
        self.assertEqual(result['checkpoint'], len(plan['entries']))
        self.assertEqual(ConversionMapping.objects.count(), len(plan['entries']))

    def test_database_rejects_applied_mapping_without_target(self):
        place = create_quality_place()
        plan = build_plan()
        apply_plan(plan)
        from catalog.models import ConversionMapping, ConversionRun
        with self.assertRaises(IntegrityError), transaction.atomic():
            ConversionMapping.objects.create(source_type='place', source_id=place.pk + 1,
                rule_version=1, piece_key='identity', source_fingerprint='0' * 64,
                target_type='', target_id=None, state='applied', reason_code='same_place_id',
                run=ConversionRun.objects.get(plan_digest=plan['digest']))

    def test_rehashed_plan_cannot_redirect_an_identity_target(self):
        place = create_quality_place()
        plan = deepcopy(build_plan())
        entry = next(e for e in plan['entries'] if e['piece_key'] == 'identity')
        entry['target_id'] = place.pk + 1000
        from catalog.services.catalog_conversion import _digest
        plan['digest'] = _digest({key: plan[key] for key in ('schema_version', 'rule_version', 'baseline_counts', 'entries')})
        with self.assertRaises(ValueError):
            apply_plan(plan)

    def test_existing_url_media_favorite_review_and_reaction_ids_survive(self):
        place = create_quality_place()
        user = get_user_model().objects.create_user(username='conversion_fixture', password='synthetic')
        photo = PlacePhoto.objects.create(place=place, image='places/gallery/synthetic.jpg')
        favorite = PlaceLike.objects.create(place=place, user=user)
        review = PlaceReview.objects.create(place=place, user=user, rating=4, text='Fixture review')
        reaction = PlaceReviewReaction.objects.create(review=review, user=user, value=1)
        original = (place.pk, place.slug, photo.pk, photo.image.name, favorite.pk, review.pk, reaction.pk)
        plan = build_plan()
        result = apply_plan(plan, batch_size=1)
        self.assertTrue(result['reconciliation']['retained_counts_match'])
        self.assertEqual(result['reconciliation']['retained']['photos'], 1)
        self.assertEqual(result['reconciliation']['retained']['reviews'], 1)
        self.assertEqual((type(place).objects.get(pk=place.pk).pk, type(place).objects.get(pk=place.pk).slug,
                          PlacePhoto.objects.get(pk=photo.pk).pk, PlacePhoto.objects.get(pk=photo.pk).image.name,
                          PlaceLike.objects.get(pk=favorite.pk).pk, PlaceReview.objects.get(pk=review.pk).pk,
                          PlaceReviewReaction.objects.get(pk=reaction.pk).pk), original)

    def test_unknown_legacy_price_is_queued_and_retained(self):
        place = create_quality_place()
        type(place).objects.filter(pk=place.pk).update(price_per_month='80.00')
        before = type(place).objects.get(pk=place.pk).price_per_month
        plan = build_plan()
        self.assertIn('legacy_pricing', {e['piece_key'] for e in plan['entries']})
        result = apply_plan(plan)
        self.assertEqual(result['reconciliation']['manual_review'], 2)
        self.assertEqual(type(place).objects.get(pk=place.pk).price_per_month, before)
        self.assertFalse(PricingPlan.objects.filter(place=place).exists())

    def test_repeat_and_resume_do_not_duplicate_mappings(self):
        place = create_quality_place()
        PricingPlan.objects.create(place=place, product_type='lesson', price='20')
        plan = build_plan()
        first = apply_plan(plan, batch_size=1, max_batches=1)
        self.assertEqual(first['checkpoint'], 1)
        resumed = apply_plan(plan, batch_size=1)
        self.assertEqual(resumed['checkpoint'], len(plan['entries']))
        repeated = apply_plan(plan, batch_size=1)
        self.assertEqual(repeated['checkpoint'], len(plan['entries']))
        counts = reconciliation(plan['digest'])
        self.assertEqual(counts['mapping_total'], len(plan['entries']))
        self.assertEqual(counts['applied'], 2)
        self.assertEqual(counts['manual_review'], 2)
        self.assertTrue(counts['retained_counts_match'])
        self.assertEqual(counts['retained']['places'], 1)
        self.assertEqual(counts['retained']['pricing_plans'], 1)
        self.assertEqual(place.pk, type(place).objects.get(pk=place.pk).pk)

    def test_old_plan_never_overwrites_changed_source(self):
        place = create_quality_place()
        old = build_plan()
        type(place).objects.filter(pk=place.pk).update(name='Fresh edit')
        result = apply_plan(old, batch_size=2)
        self.assertEqual(result['stale'], 3)
        from catalog.models import ConversionMapping
        self.assertFalse(ConversionMapping.objects.filter(source_type='place', source_id=place.pk, state='applied').exists())
        self.assertFalse(ConversionMapping.objects.filter(source_type='place', source_id=place.pk).exclude(target_id=None).exists())
        fresh = build_plan()
        apply_plan(fresh)
        self.assertEqual(ConversionMapping.objects.filter(source_type='place', source_id=place.pk, state='applied').count(), 1)
        self.assertEqual(type(place).objects.get(pk=place.pk).name, 'Fresh edit')

    def test_command_dry_run_writes_plan_only_and_apply_is_explicit(self):
        place = create_quality_place()
        before = self._counts()
        with TemporaryDirectory(prefix='task33-conversion-', dir='/tmp') as directory:
            path = Path(directory) / 'plan.json'
            call_command('convert_task33_catalog', '--dry-run', '--plan', str(path))
            self.assertTrue(path.exists())
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(self._counts(), before)
            with self.assertRaises(CommandError):
                call_command('convert_task33_catalog', '--apply', '--plan', str(path), '--batch-size', '0')
            call_command('convert_task33_catalog', '--apply', '--plan', str(path), '--batch-size', '1')
            from catalog.models import ConversionMapping
            self.assertEqual(ConversionMapping.objects.filter(source_type='place', source_id=place.pk).count(), 3)

    def _counts(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT relname, n_tup_ins, n_tup_upd, n_tup_del FROM pg_stat_user_tables WHERE relname LIKE 'catalog_%' ORDER BY relname")
            stats = cursor.fetchall()
        from catalog.models import ConversionMapping, ConversionRun
        return (ConversionMapping.objects.count(), ConversionRun.objects.count(), stats)


class ConversionConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_parallel_apply_uses_one_ledger_and_complete_checkpoint(self):
        Category.objects.get_or_create(code='EDU', defaults={'name': 'Synthetic education'})
        create_quality_place()
        plan = build_plan()
        barrier = Barrier(2)
        def worker():
            close_old_connections()
            barrier.wait(timeout=10)
            try:
                return apply_plan(plan, batch_size=1)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        from catalog.models import ConversionMapping, ConversionRun
        self.assertEqual(ConversionRun.objects.filter(plan_digest=plan['digest']).count(), 1)
        self.assertEqual(ConversionMapping.objects.count(), len(plan['entries']))
        self.assertEqual({r['checkpoint'] for r in results}, {len(plan['entries'])})
