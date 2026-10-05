"""Task33 D07 versioned reviews: publication is independent of candidate editing."""
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection, close_old_connections, IntegrityError, transaction
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import override
from datetime import timedelta
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from catalog.models import PlaceReview, Category
from catalog.testcases.utils import create_quality_place


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=0)
class ReviewVersionContractTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='version-author')
        self.staff = get_user_model().objects.create_superuser(username='version-reviewer', email='reviewer@example.test', password='fixture')
        self.place = create_quality_place()

    def test_typed_review_page_uses_requested_language(self):
        from catalog.services.review_versions import submit_review, moderate_candidate

        head, revision = submit_review(target=self.place, user=self.user, rating=5, text='Published review', author_name='Author')
        moderate_candidate(head=head, revision_id=revision.pk, actor=self.staff, approve=True)
        for language, heading, label in (
            ('az', 'Rəylər', 'Yayımlanmış rəylər'),
            ('ru', 'Отзывы', 'Опубликованные отзывы'),
            ('en', 'Reviews', 'Published reviews'),
        ):
            with self.subTest(language=language), override(language):
                response = self.client.get(reverse('typed_reviews', args=['place', self.place.pk]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, f'<h1>{heading}:', html=False)
                self.assertContains(response, label)

    def test_pending_edit_keeps_approved_projection_and_one_rating(self):
        from catalog.services.review_versions import submit_review, moderate_candidate
        head, first = submit_review(target=self.place, user=self.user, rating=5, text='Original approved text', author_name='Author')
        moderate_candidate(head=head, revision_id=first.pk, actor=self.staff, approve=True)
        same, second = submit_review(target=self.place, user=self.user, rating=1, text='New pending text', author_name='Author')
        self.assertEqual(head.pk, same.pk)
        same.refresh_from_db()
        self.assertEqual(same.text, 'Original approved text')
        self.assertEqual(same.current_revision_id, first.pk)
        self.assertEqual(same.candidate_revision_id, second.pk)
        self.place.refresh_from_db()
        self.assertEqual((self.place.rating_avg, self.place.rating_count), (5, 1))
        moderate_candidate(head=same, revision_id=second.pk, actor=self.staff, approve=False)
        same.refresh_from_db()
        self.assertEqual(same.text, 'Original approved text')
        self.assertEqual(same.revisions.count(), 2)

    def test_nonstaff_and_stale_decision_cannot_publish(self):
        from catalog.services.review_versions import submit_review, moderate_candidate, ReviewConflict
        head, first = submit_review(target=self.place, user=self.user, rating=5, text='First candidate', author_name='Author')
        with self.assertRaises(PermissionError):
            moderate_candidate(head=head, revision_id=first.pk, actor=self.user, approve=True)
        _, second = submit_review(target=self.place, user=self.user, rating=3, text='Second candidate', author_name='Author')
        with self.assertRaises(ReviewConflict):
            moderate_candidate(head=head, revision_id=first.pk, actor=self.staff, approve=True)
        head.refresh_from_db()
        self.assertEqual(head.candidate_revision_id, second.pk)
        self.assertFalse(head.is_approved)

    def test_unknown_sources_remain_independent(self):
        from catalog.services.review_versions import normalize_reviews
        a = PlaceReview.objects.create(place=self.place, author_name='Same', text='Source A', rating=2)
        b = PlaceReview.objects.create(place=self.place, author_name='Same', text='Source B', rating=4)
        normalize_reviews(PlaceReview)
        self.assertEqual(PlaceReview.objects.filter(place=self.place, is_current=True).count(), 2)
        self.assertEqual(a.revisions.get().text, 'Source A')
        self.assertEqual(b.revisions.get().text, 'Source B')

    def test_latest_approved_effective_timestamp_and_archive_preserved(self):
        from catalog.services.review_versions import normalize_reviews
        now = timezone.now()
        sources = PlaceReview.objects.bulk_create([
            PlaceReview(place=self.place, user=self.user, text='Approved older ID newer decision', rating=5, status='approved', is_approved=True, moderated_at=now, is_current=False),
            PlaceReview(place=self.place, user=self.user, text='Approved newer ID older decision', rating=1, status='approved', is_approved=True, moderated_at=now-timedelta(days=1), is_current=False),
            PlaceReview(place=self.place, user=self.user, text='Latest pending source', rating=2, status='pending', is_approved=False, is_current=False),
        ])
        ids = [r.pk for r in sources]
        normalize_reviews(PlaceReview)
        self.assertEqual(PlaceReview.objects.get(user=self.user, is_current=True).pk, ids[0])
        self.assertEqual(list(PlaceReview.objects.filter(pk__in=ids).order_by('pk').values_list('text', flat=True)), [r.text for r in sources])
        self.assertEqual(PlaceReview.objects.filter(pk__in=ids, is_current=False).count(), 2)
        for source in sources:
            self.assertEqual(source.revisions.get().text, source.text)
        normalize_reviews(PlaceReview)
        self.assertEqual(sum(r.revisions.count() for r in sources), 3)

    def test_reaction_ids_and_original_revision_are_preserved(self):
        from catalog.models import PlaceReviewReaction
        from catalog.services.review_versions import submit_review, moderate_candidate, ReviewConflict
        from catalog.services.reactions import toggle_place_review_reaction
        head, first = submit_review(target=self.place, user=self.user, rating=5, text='Version one', author_name='Author')
        moderate_candidate(head=head, revision_id=first.pk, actor=self.staff, approve=True)
        head.refresh_from_db()
        voter = get_user_model().objects.create_user(username='version-voter')
        request = RequestFactory().post('/', {'revision_id': str(first.pk)})
        request.user = voter
        toggle_place_review_reaction(head, request, 1)
        original = PlaceReviewReaction.objects.get(user=voter)
        _, second = submit_review(target=self.place, user=self.user, rating=3, text='Version two', author_name='Author')
        moderate_candidate(head=head, revision_id=second.pk, actor=self.staff, approve=True)
        head.refresh_from_db()
        self.assertEqual(head.likes_count, 0)
        original.refresh_from_db()
        self.assertEqual(original.revision_id, first.pk)
        self.assertEqual(original.revision.text, 'Version one')
        with self.assertRaises(ReviewConflict):
            toggle_place_review_reaction(head, request, 1)
        request.POST = request.POST.copy()
        request.POST['revision_id'] = str(second.pk)
        toggle_place_review_reaction(head, request, -1)
        self.assertEqual(PlaceReviewReaction.objects.filter(user=voter).count(), 2)
        self.assertTrue(PlaceReviewReaction.objects.filter(pk=original.pk, revision=first).exists())
        head.refresh_from_db()
        self.assertEqual((head.likes_count, head.dislikes_count), (0, 1))

    def test_retention_clears_all_labels_and_pending_candidate(self):
        from catalog.services.review_versions import submit_review, moderate_candidate, normalize_reviews
        from catalog.services.review_retention import dispose_typed_reviews
        head, first = submit_review(target=self.place, user=self.user, rating=5, text='Retained approved text', author_name='Private label')
        moderate_candidate(head=head, revision_id=first.pk, actor=self.staff, approve=True)
        _, pending = submit_review(target=self.place, user=self.user, rating=1, text='Pending private text', author_name='Private candidate label')
        count, anonymized = dispose_typed_reviews(user_id=self.user.pk, disposition='anonymize_approved_delete_other')
        self.assertEqual((count, anonymized), (0, 1))
        head.refresh_from_db()
        self.assertIsNone(head.user_id)
        self.assertEqual(head.author_name, '')
        self.assertTrue(head.is_anonymous)
        self.assertFalse(head.revisions.filter(pk=pending.pk).exists())
        self.assertEqual(list(head.revisions.values_list('author_name', flat=True)), [''])
        normalize_reviews(PlaceReview)
        self.assertEqual(head.revisions.count(), 1)

    def test_bulk_second_current_known_head_is_denied_by_database(self):
        PlaceReview.objects.create(place=self.place, user=self.user, text='Current', rating=5)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlaceReview.objects.bulk_create([PlaceReview(place=self.place, user=self.user, text='Duplicate current', rating=3, is_current=True)])


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=120)
class ReviewVersionPostgresConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, 'postgresql', 'Task33 concurrency requires PostgreSQL launcher')
        Category.objects.get_or_create(code='EDU', defaults={'name':'Fixture education'})
        self.user = get_user_model().objects.create_user(username='race-author')
        self.staff = get_user_model().objects.create_superuser(username='race-reviewer', email='race@example.test', password='fixture')
        self.place = create_quality_place()

    def race(self, fn):
        barrier = Barrier(2)
        def worker(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return fn(index)
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, [0, 1]))

    def test_two_first_submits_one_claim_and_one_candidate(self):
        from catalog.services.review_versions import submit_review, ReviewCooldown
        def attempt(index):
            try:
                submit_review(target=self.place, user=self.user, rating=4, text='Race candidate ' + str(index), enforce_cooldown=True)
                return 'accepted'
            except ReviewCooldown:
                return 'cooldown'
        self.assertCountEqual(self.race(attempt), ['accepted', 'cooldown'])
        head = PlaceReview.objects.get(user=self.user, place=self.place, is_current=True)
        self.assertEqual(head.revisions.count(), 1)

    def test_two_edits_compare_and_swap_then_two_approvals(self):
        from catalog.services.review_versions import submit_review, moderate_candidate, ReviewConflict
        head, first = submit_review(target=self.place, user=self.user, rating=5, text='Approved original')
        moderate_candidate(head=head, revision_id=first.pk, actor=self.staff, approve=True)
        def edit(index):
            try:
                submit_review(target=self.place, user=self.user, rating=3, text='Edit ' + str(index), expected_revision_id=first.pk)
                return 'accepted'
            except ReviewConflict:
                return 'conflict'
        self.assertCountEqual(self.race(edit), ['accepted', 'conflict'])
        head.refresh_from_db()
        candidate_id = head.candidate_revision_id
        def approve(index):
            try:
                moderate_candidate(head=head, revision_id=candidate_id, actor=self.staff, approve=True)
                return 'approved'
            except ReviewConflict:
                return 'conflict'
        self.assertCountEqual(self.race(approve), ['approved', 'conflict'])
        head.refresh_from_db()
        self.assertEqual(head.current_revision_id, candidate_id)
        self.assertEqual(head.revisions.count(), 2)
        self.place.refresh_from_db()
        self.assertEqual((self.place.rating_avg, self.place.rating_count), (3, 1))
