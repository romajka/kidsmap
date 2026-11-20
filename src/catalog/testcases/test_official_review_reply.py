"""The public reply belongs to a single approved revision and survives retries."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import Place, PlaceReviewResponse, SiteSettings, Specialist
from catalog.services.staff_roles import ADMIN_ROLE_MODERATOR, role_permissions
from catalog.services.review_versions import ReviewConflict, moderate_candidate, respond_to_review, submit_review
from catalog.testcases.test_task33_review_independent import ReviewFixtures


class OfficialReplyTests(ReviewFixtures, TestCase):
    def setUp(self):
        super().setUp()
        self.enterContext(translation.override('en'))
        Specialist.objects.filter(pk=self.specialist.pk).update(
            verified_person_user=self.owner, person_verified_at=timezone.now())
        self.specialist.refresh_from_db()
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save(update_fields=['specialists_section_enabled'])
        self.client.force_login(self.owner)

    def test_one_reply_per_submission_and_distinct_followup(self):
        for kind, target in [('place', self.place), ('specialist', self.specialist)]:
            with self.subTest(kind=kind):
                head, revision = self.approved(target)
                action = reverse('typed_review_action', args=[kind, head.pk, 'reply'])
                feed = reverse('typed_reviews', args=[kind, target.pk])
                self.assertContains(self.client.get(feed), 'name="request_id"')
                data = {'revision_id': revision.pk, 'request_id': str(uuid4()), 'text': 'Thank you.'}
                first = self.client.post(action, data)
                second = self.client.post(action, data)
                self.assertEqual(revision.responses.count(), 1)
                reply = revision.responses.get()
                self.assertEqual(first.url, f'{feed}#reply-{reply.pk}')
                self.assertEqual(second.url, first.url)
                conflict = self.client.post(action, {**data, 'text': 'New information'})
                self.assertContains(conflict, 'New information', status_code=409)
                self.assertEqual(revision.responses.count(), 1)
                self.assertEqual(self.client.post(action, {**data, 'request_id': uuid4()}).status_code, 302)
                self.assertEqual(self.client.post(action, {'text': 'Legacy form', 'revision_id': revision.pk}).status_code, 302)
                self.assertEqual(revision.responses.count(), 3)

    def test_failed_notification_rolls_back_response_and_allows_the_same_retry(self):
        head, revision = self.approved()
        values = {'head': head, 'actor': self.owner, 'revision_id': revision.pk, 'kind': 'reply',
                  'text': 'Retry after a database failure', 'request_id': uuid4()}
        with patch('catalog.services.review_notifications.notify_review_reply', side_effect=RuntimeError('write interrupted')):
            with self.assertRaises(RuntimeError):
                respond_to_review(**values)
        self.assertFalse(revision.responses.exists())
        reply = respond_to_review(**values)
        self.assertEqual(respond_to_review(**values).pk, reply.pk)
        self.assertEqual(revision.responses.count(), 1)

    def test_invalid_or_stale_form_keeps_draft_and_shows_current_text(self):
        head, previous = self.approved()
        action = reverse('typed_review_action', args=['place', head.pk, 'reply'])
        data = {'revision_id': previous.pk, 'request_id': str(uuid4()), 'text': 'Original draft'}
        error = self.client.post(action, {**data, 'text': ' '})
        self.assertContains(error, 'role="alert"', status_code=400)
        self.assertContains(error, f'action="{action}#reply-text-{head.pk}"', status_code=400)
        self.assertContains(error, f'aria-describedby="reply-note-{head.pk} reply-error-{head.pk}"', status_code=400)
        malformed = self.client.post(action, {**data, 'request_id': 'invalid'})
        self.assertContains(malformed, 'Original draft', status_code=400)
        head, candidate = submit_review(target=self.place, user=self.author, rating=5, text='Updated parent review')
        moderate_candidate(head=head, revision_id=candidate.pk, actor=self.staff, approve=True)
        changed = self.client.post(action, data)
        self.assertContains(changed, 'Original draft', status_code=409)
        self.assertContains(changed, f'action="{action}#reply-text-{head.pk}"', status_code=409)
        self.assertContains(changed, 'Updated parent review', status_code=409)
        self.assertEqual(previous.responses.count(), 0)
        self.assertEqual(candidate.responses.count(), 0)

    def test_unpublished_target_cannot_accept_an_official_reply(self):
        head, revision = self.approved()
        Place.objects.filter(pk=self.place.pk).update(is_active=False)
        with self.assertRaises(ReviewConflict):
            respond_to_review(head=head, revision_id=revision.pk, actor=self.owner,
                              kind='reply', text='Reply to withdrawn page')
        self.assertEqual(revision.responses.count(), 0)

    def test_database_enforces_public_and_hidden_states(self):
        for target in (self.place, self.specialist):
            head, revision = self.approved(target)
            reply = respond_to_review(head=head, actor=self.owner, kind='reply',
                                      revision_id=revision.pk, text='Moderated independently')
            for kind, hidden_at in [('hidden', None), ('reply', timezone.now()), ('report', timezone.now())]:
                with self.subTest(target=type(target).__name__, kind=kind):
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        type(reply).objects.filter(pk=reply.pk).update(kind=kind, hidden_at=hidden_at)

    def test_old_release_cannot_redisplay_hidden_reply_and_retry_cannot_restore_it(self):
        for kind, target in [('place', self.place), ('specialist', self.specialist)]:
            with self.subTest(kind=kind):
                head, revision = self.approved(target)
                data = {'actor': self.owner, 'kind': 'reply', 'head': head,
                        'revision_id': revision.pk, 'request_id': uuid4(), 'text': 'Private on request'}
                reply = respond_to_review(**data)
                report = respond_to_review(head=head, actor=self.owner, kind='report',
                                           text='Report stays private', revision_id=revision.pk)
                old_public_feed = revision.responses.filter(kind='reply')
                self.client.force_login(self.staff)
                hide = reverse(f'admin:catalog_{kind}reviewresponse_hide', args=[reply.pk])
                restore = reverse(f'admin:catalog_{kind}reviewresponse_restore', args=[reply.pk])
                self.assertEqual(self.client.post(hide, {'reason': 'Privacy request'}).status_code, 302)
                self.assertFalse(old_public_feed.exists())
                self.assertEqual(respond_to_review(**data).pk, reply.pk)
                self.assertFalse(old_public_feed.exists())
                self.assertEqual(revision.responses.get(pk=report.pk).kind, 'report')
                self.assertEqual(self.client.post(restore, {}).status_code, 302)
                self.assertEqual(list(old_public_feed.values_list('pk', flat=True)), [reply.pk])

    def test_moderation_requires_reason_hides_only_the_reply_and_restores(self):
        head, revision = self.approved()
        reply = respond_to_review(head=head, revision_id=revision.pk, actor=self.owner,
                                  kind='reply', text='Reply to moderate')
        feed = reverse('typed_reviews', args=['place', self.place.pk])
        hide = reverse('admin:catalog_placereviewresponse_hide', args=[reply.pk])
        restore = reverse('admin:catalog_placereviewresponse_restore', args=[reply.pk])
        moderator = get_user_model().objects.create_user('official-reply-moderator', is_staff=True)
        self.client.force_login(moderator)
        self.assertEqual(self.client.get(hide).status_code, 403)
        moderator.user_permissions.set(role_permissions(ADMIN_ROLE_MODERATOR))
        self.assertEqual(self.client.get(hide).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin:catalog_placereviewresponse_change',
                                                  args=[reply.pk])).status_code, 200)
        self.assertEqual(self.client.post(hide, {'reason': '  '}).status_code, 400)
        self.assertEqual(self.client.post(hide, {'reason': 'Privacy request'}).status_code, 302)
        reply.refresh_from_db()
        self.assertIsNotNone(reply.hidden_at)
        self.assertEqual(reply.moderated_by, moderator)
        self.assertEqual(reply.moderation_reason, 'Privacy request')
        self.assertNotContains(self.client.get(feed), reply.text)
        self.assertEqual(self.client.post(hide, {'reason': 'stale second action'}).status_code, 409)
        private = respond_to_review(head=head, revision_id=revision.pk, actor=self.owner,
                                    kind='report', text='Private report')
        self.assertEqual(self.client.get(reverse('admin:catalog_placereviewresponse_hide',
                                                  args=[private.pk])).status_code, 404)
        self.assertContains(self.client.get(feed), head.text)
        self.assertEqual(self.client.post(restore, {}).status_code, 302)
        self.assertContains(self.client.get(feed), reply.text)


@skipUnless(connection.vendor == 'postgresql', 'Row-lock concurrency requires PostgreSQL')
class ConcurrentOfficialReplies(ReviewFixtures, TransactionTestCase):
    def test_same_request_in_two_transactions_returns_same_saved_reply(self):
        head, revision = self.approved()
        request_id = uuid4()
        barrier = Barrier(2)

        def send():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return respond_to_review(head=head, revision_id=revision.pk, actor=self.owner,
                                         kind='reply', text='One reply.', request_id=request_id).pk
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: send(), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(PlaceReviewResponse.objects.filter(revision=revision).count(), 1)
