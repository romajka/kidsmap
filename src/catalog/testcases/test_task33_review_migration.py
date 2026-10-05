"""Independent PostgreSQL forward-migration evidence on synthetic historical rows."""
import importlib
import os
import uuid
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.models import Avg, Count
from django.test import TransactionTestCase
from django.utils import timezone


class ReviewForwardMigrationTests(TransactionTestCase):
    databases = {'default'}

    def test_sources_reactions_election_constraints_and_idempotency(self):
        # Never downgrade the main test schema through irreversible normalization.
        self.assertEqual(connection.vendor, 'postgresql')
        self.assertEqual(os.environ.get('DJANGO_TESTING'), '1')
        self.assertTrue(os.environ.get('TASK33_QA_ROOT', '').startswith('/tmp/kidsmap-task33-qa04-'))
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database(), current_setting(\'search_path\')')
            database, original_search_path = cursor.fetchone()
        self.assertEqual(database, 'test_qa_stage04')
        self.assertIn('kidsmap-task33-qa04-socket-', connection.settings_dict['HOST'])
        schema = 'task33_review_migration_' + uuid.uuid4().hex
        quoted_schema = connection.ops.quote_name(schema)
        with connection.cursor() as cursor:
            cursor.execute('CREATE SCHEMA ' + quoted_schema)
            cursor.execute('SET search_path TO ' + quoted_schema)
        try:
            executor = MigrationExecutor(connection)
            before_target = [('catalog', '0127_task33_workflow_notifications')]
            executor.migrate(before_target)
            before = executor.loader.project_state(before_target).apps
            User = before.get_model('auth', 'User')
            Category = before.get_model('catalog', 'Category')
            Place = before.get_model('catalog', 'Place')
            Review = before.get_model('catalog', 'PlaceReview')
            Reaction = before.get_model('catalog', 'PlaceReviewReaction')
            Specialist = before.get_model('catalog', 'Specialist')
            SpecialistReview = before.get_model('catalog', 'SpecialistReview')
            author = User.objects.create(username='migration-author')
            other = User.objects.create(username='migration-other')
            voter = User.objects.create(username='migration-voter')
            category, _ = Category.objects.get_or_create(code='EDU', defaults={'name': 'Synthetic education'})
            place = Place.objects.create(name='Migration fixture', category_id=category.pk)
            specialist = Specialist.objects.create(name='Synthetic Specialist')
            epoch = timezone.now() - timedelta(days=20)
            cases = [
                (author.pk, 'approved', True, 5, 1, 5),
                (author.pk, 'approved', True, 3, 3, None),
                (author.pk, 'pending', False, 1, 8, None),
                (author.pk, 'rejected', False, 2, 9, 10),
                (other.pk, 'pending', False, 4, 1, None),
                (other.pk, 'pending', False, 2, 4, None),
                (None, 'approved', True, 2, 1, None),
                (None, 'approved', True, 4, 2, None),
            ]
            ids = []
            for index, (user_id, status, approved, rating, created_day, moderated_day) in enumerate(cases):
                row = Review.objects.create(place=place, user_id=user_id,
                    author_name='Same unknown author' if user_id is None else 'Synthetic author',
                    text='Immutable legacy text ' + str(index), rating=rating,
                    status=status, is_approved=approved, rejection_reason='Legacy decision ' + str(index),
                    session_key='same-unknown-session' if user_id is None else '',
                    contains_profanity=bool(index % 2))
                Review.objects.filter(pk=row.pk).update(created_at=epoch + timedelta(days=created_day),
                    moderated_at=epoch + timedelta(days=moderated_day) if moderated_day is not None else None)
                ids.append(row.pk)
                Reaction.objects.create(review_id=row.pk, user_id=voter.pk, value=1 if index % 2 else -1)
            specialist_row = SpecialistReview.objects.create(specialist=specialist, user_id=author.pk,
                author_name='Synthetic specialist author', text='Specialist legacy approved', rating=4,
                status='approved', is_approved=True)
            source_fields = ['pk', 'place_id', 'user_id', 'author_name', 'text', 'rating', 'status',
                'is_approved', 'contains_profanity', 'rejection_reason', 'created_at', 'moderated_at', 'session_key']
            original = list(Review.objects.order_by('pk').values(*source_fields))
            reaction_fields = ['pk', 'review_id', 'user_id', 'session_key', 'value', 'created_at', 'updated_at']
            original_reactions = list(Reaction.objects.order_by('pk').values(*reaction_fields))
            original_specialist = SpecialistReview.objects.values('pk', 'text', 'rating', 'status', 'is_approved').get(pk=specialist_row.pk)
            old_stats = Review.objects.filter(status='approved', is_approved=True).aggregate(average=Avg('rating'), count=Count('pk'))
            self.assertEqual(old_stats, {'average': 3.5, 'count': 4})

            after_target = [('catalog', '0130_task33_review_versions')]
            executor = MigrationExecutor(connection)
            executor.migrate(after_target)
            after = executor.loader.project_state(after_target).apps
            Review = after.get_model('catalog', 'PlaceReview')
            Revision = after.get_model('catalog', 'PlaceReviewRevision')
            Reaction = after.get_model('catalog', 'PlaceReviewReaction')
            SpecialistReview = after.get_model('catalog', 'SpecialistReview')
            self.assertEqual(list(Review.objects.order_by('pk').values(*source_fields)), original)
            self.assertEqual(list(Reaction.objects.order_by('pk').values(*reaction_fields)), original_reactions)
            self.assertEqual(SpecialistReview.objects.values(*original_specialist).get(pk=specialist_row.pk), original_specialist)
            self.assertEqual(Revision.objects.count(), 8)
            for row in original:
                baseline = Revision.objects.get(review_id=row['pk'], is_baseline=True)
                for field in ['author_name', 'text', 'rating', 'status', 'contains_profanity', 'rejection_reason', 'created_at', 'moderated_at']:
                    self.assertEqual(getattr(baseline, field), row[field], field)
                self.assertEqual(baseline.source_is_approved, row['is_approved'])
            for reaction in Reaction.objects.select_related('revision'):
                self.assertEqual(reaction.revision.review_id, reaction.review_id)
                self.assertTrue(reaction.revision.is_baseline)
            self.assertEqual(list(Review.objects.filter(user_id=author.pk, is_current=True).values_list('pk', flat=True)), [ids[0]])
            self.assertEqual(list(Review.objects.filter(user_id=other.pk, is_current=True).values_list('pk', flat=True)), [ids[5]])
            self.assertEqual(Review.objects.filter(user_id=None, is_current=True).count(), 2)
            self.assertEqual(set(Review.objects.filter(user_id=author.pk, is_current=False).values_list('archive_head_id', flat=True)), {ids[0]})
            new_stats = Review.objects.filter(is_current=True, status='approved', is_approved=True).aggregate(average=Avg('rating'), count=Count('pk'))
            self.assertEqual(new_stats['count'], 3)
            self.assertAlmostEqual(new_stats['average'], 11 / 3)

            with self.assertRaises(IntegrityError), transaction.atomic():
                Review.objects.create(place_id=place.pk, user_id=author.pk, text='Conflicting head', rating=5, is_current=True)
            with self.assertRaises(IntegrityError), transaction.atomic():
                Reaction.objects.create(review_id=ids[0], user_id=voter.pk, value=1, revision_id=None)
            with self.assertRaises(IntegrityError), transaction.atomic():
                Revision.objects.create(review_id=ids[0], is_baseline=True, rating=5, text='Duplicate baseline')

            # Re-running frozen conversion must not reset a later approved pointer,
            # nor reactivate an archived sibling whose account was anonymized.
            newer = Revision.objects.create(review_id=ids[0], rating=4, text='Later approved version',
                status='approved', created_at=timezone.now())
            Review.objects.filter(pk=ids[0]).update(current_revision_id=newer.pk, rating=4, text=newer.text)
            Review.objects.filter(pk=ids[1]).update(user_id=None, author_name='', is_anonymous=True)
            migration = importlib.import_module('catalog.migrations.0128_task33_review_versions')
            with connection.schema_editor() as editor:
                migration.preserve_review_sources(after, editor)
            self.assertEqual(Review.objects.get(pk=ids[0]).current_revision_id, newer.pk)
            self.assertFalse(Review.objects.get(pk=ids[1]).is_current)
            self.assertEqual(Revision.objects.filter(is_baseline=True).count(), 8)
            self.assertEqual(Reaction.objects.count(), 8)
        finally:
            with connection.cursor() as cursor:
                cursor.execute('SELECT set_config(\'search_path\', %s, false)', [original_search_path])
                # Only this test's freshly created random schema is removed.
                cursor.execute('DROP SCHEMA ' + quoted_schema + ' CASCADE')
