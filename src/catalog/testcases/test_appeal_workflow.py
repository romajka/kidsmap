from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature

from catalog.models import EmailOutbox, SiteReview, Specialist, WorkflowNotification
from catalog.services.staff_roles import VOLUNTEER_GROUP


class AppealWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.author = users.create_user("appellant")
        cls.first = users.create_user("original", is_staff=True)
        cls.second = users.create_user("second", is_staff=True)
        cls.third = users.create_user("third", is_staff=True)
        cls.permission = Permission.objects.get(content_type__app_label="catalog", codename="change_sitereview")
        for user in (cls.first, cls.second, cls.third):
            user.user_permissions.add(cls.permission)
        cls.review = SiteReview.objects.create(
            user=cls.author, text="Original review", status="rejected",
            rejection_reason="Missing details", moderated_by=cls.first,
        )

    def rejection(self):
        from moderation_appeals.sources import rejected_decisions
        return next(d for d in rejected_decisions(self.author) if d.kind == "site_review")

    def submit(self):
        from moderation_appeals.services import submit_appeal
        return submit_appeal(self.author, self.rejection(), "  Please review independently  ", "https://example.org/info")

    def test_appellant_gets_one_historical_record_per_rejection(self):
        # The old moderation flow has no separate record of a user's appeal.
        self.assertTrue(apps.is_installed("moderation_appeals"))
        appeal = self.submit()
        self.assertEqual((appeal.status, appeal.explanation), ("submitted", "Please review independently"))
        self.assertEqual(appeal.original_reviewer_id, self.first.pk)
        self.assertEqual(appeal.original_reason, "Missing details")
        self.assertEqual(appeal.evidence_url, "https://example.org/info")
        self.assertEqual(self.submit().pk, appeal.pk)
        self.review.rejection_reason = "Later wording"
        self.review.save(update_fields=["rejection_reason"])
        appeal.refresh_from_db()
        self.assertEqual(appeal.original_reason, "Missing details")

    def test_submission_checks_source_ownership_version_and_original_metadata(self):
        from moderation_appeals.services import AppealError, submit_appeal
        decision = self.rejection()
        with self.assertRaises(AppealError):
            submit_appeal(self.second, decision, "Not my submission")
        with self.assertRaises(AppealError):
            submit_appeal(self.author, replace(decision, version="obsolete"), "Old decision")
        altered = replace(decision, reason="Invented", reviewer_id=self.second.pk)
        result = submit_appeal(self.author, altered, "Please check")
        self.assertEqual((result.original_reason, result.original_reviewer_id), ("Missing details", self.first.pk))

    def test_invalid_reason_or_evidence_leaves_no_record(self):
        from moderation_appeals.models import Appeal
        from moderation_appeals.services import AppealError, submit_appeal
        decision = self.rejection()
        for explanation, url in (("   ", ""), ("x" * 4001, ""), ("context", "ftp://example.org/info"),
                                 ("context", "unlinked evidence"), ("context", "https://example.org/" + "x" * 2000)):
            with self.subTest(url=url[:25]), self.assertRaises(AppealError):
                submit_appeal(self.author, decision, explanation, url)
        self.assertFalse(Appeal.objects.exists())

    def test_independent_second_review_records_outcome_without_publishing(self):
        from moderation_appeals.services import AppealError, claim_appeal, resolve_appeal, review_queue
        appeal = self.submit()
        self.assertTrue(review_queue(self.first).filter(pk=appeal.pk).exists())
        with self.assertRaises(AppealError):
            claim_appeal(self.first, appeal.pk)
        claimed = claim_appeal(self.second, appeal.pk)
        self.assertEqual(claimed.status, "second_review")
        self.assertEqual(claim_appeal(self.second, appeal.pk).claimed_at, claimed.claimed_at)
        with self.assertRaises(AppealError):
            claim_appeal(self.third, appeal.pk)
        with self.assertRaises(AppealError):
            resolve_appeal(self.third, appeal.pk, True, "Intervening decision")
        with self.assertRaises(AppealError):
            resolve_appeal(self.second, appeal.pk, True, " ")
        resolved = resolve_appeal(self.second, appeal.pk, True, "Evidence accepted")
        self.assertEqual((resolved.status, resolved.final_reason), ("approved", "Evidence accepted"))
        replay = resolve_appeal(self.second, appeal.pk, True, "Evidence accepted")
        self.assertEqual(replay.resolved_at, resolved.resolved_at)
        with self.assertRaises(AppealError):
            resolve_appeal(self.second, appeal.pk, False, "Reverse the decision")
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, "rejected")
        note = WorkflowNotification.objects.get(recipient_user=self.author, event_kind="appeal_decided")
        self.assertEqual((note.entity_type, note.entity_id, note.event_context), ("moderation_appeal", appeal.pk, {}))
        self.assertFalse(EmailOutbox.objects.filter(notification=note).exists())

    def test_no_appeal_review_by_appellant_volunteer_or_unrelated_staff(self):
        from moderation_appeals.services import AppealError, can_access_queue, can_claim, claim_appeal, review_queue
        appeal = self.submit()
        self.author.is_staff = True
        self.author.save(update_fields=["is_staff"])
        self.author.user_permissions.add(self.permission)
        self.assertFalse(can_claim(self.author, appeal))
        with self.assertRaises(AppealError):
            claim_appeal(self.author, appeal.pk)
        self.second.groups.add(Group.objects.create(name=VOLUNTEER_GROUP))
        self.third.user_permissions.remove(self.permission)
        for user in (self.second, self.third):
            self.assertFalse(can_access_queue(user))
            self.assertFalse(review_queue(user).exists())
            with self.assertRaises(AppealError):
                claim_appeal(user, appeal.pk)

    def test_missing_original_moderator_cannot_be_silently_routed_to_second_review(self):
        from moderation_appeals.services import AppealError, can_claim, claim_appeal
        self.review.moderated_by = None
        self.review.save(update_fields=["moderated_by"])
        appeal = self.submit()
        self.assertIsNone(appeal.original_reviewer_key)
        self.assertFalse(can_claim(self.second, appeal))
        with self.assertRaises(AppealError):
            claim_appeal(self.second, appeal.pk)

    def test_cached_staff_permissions_cannot_authorize_a_decision_after_revocation(self):
        from moderation_appeals.services import AppealError, claim_appeal, resolve_appeal
        appeal = self.submit()
        self.assertTrue(self.second.has_perm("catalog.change_sitereview"))
        claim_appeal(self.second, appeal.pk)
        self.second.user_permissions.remove(self.permission)
        with self.assertRaises(AppealError):
            resolve_appeal(self.second, appeal.pk, False, "Lost permission")
        claimed = claim_appeal(self.third, appeal.pk)
        self.assertEqual(list(claimed.assignments.values_list("reviewer_key", flat=True)), [self.second.pk, self.third.pk])
        get_user_model().objects.filter(pk=self.third.pk).update(is_active=False)
        with self.assertRaises(AppealError):
            resolve_appeal(self.third, appeal.pk, True, "Lost access")

    def test_second_eligible_recipient_cannot_split_the_case_or_adjudicate_it(self):
        from catalog.services.specialist_moderation import notify_decision
        from moderation_appeals.models import Appeal
        from moderation_appeals.services import AppealError, can_claim, claim_appeal, review_queue, submit_appeal
        from moderation_appeals.sources import rejected_decisions

        self.second.user_permissions.add(Permission.objects.get(
            content_type__app_label="catalog", codename="change_specialist"))
        person = Specialist.objects.create(name="Synthetic tutor", created_by=self.author,
                                           verified_person_user=self.second, status="rejected")
        notify_decision(person, "rejected", "Original decision", actor=self.first)
        original = next(d for d in rejected_decisions(self.author) if d.kind == "specialist")
        shared = next(d for d in rejected_decisions(self.second) if d.kind == "specialist")
        appeal = submit_appeal(self.author, original, "Private explanation")
        with self.assertRaises(AppealError) as error:
            submit_appeal(self.second, shared, "Other explanation")
        self.assertEqual(error.exception.code, "already_appealed")
        self.assertFalse(Appeal.objects.filter(appellant=self.second).exists())
        self.assertTrue(review_queue(self.second).filter(pk=appeal.pk).exists())
        self.assertFalse(can_claim(self.second, appeal))
        with self.assertRaises(AppealError):
            claim_appeal(self.second, appeal.pk)
        self.assertEqual(Appeal.objects.get().explanation, "Private explanation")

    def test_historical_original_reviewer_key_survives_a_deleted_staff_account(self):
        from catalog.services.specialist_moderation import notify_decision
        from moderation_appeals.services import submit_appeal
        from moderation_appeals.sources import rejected_decisions

        first_key = self.first.pk
        person = Specialist.objects.create(name="Synthetic tutor", created_by=self.author, status="rejected")
        notify_decision(person, "rejected", "Original decision", actor=self.first)
        self.first.delete()
        decision = next(d for d in rejected_decisions(self.author) if d.kind == "specialist")
        appeal = submit_appeal(self.author, decision, "Please reconsider")
        self.assertEqual(appeal.original_reviewer_key, first_key)
        self.assertIsNone(appeal.original_reviewer_id)


@skipUnlessDBFeature("has_select_for_update")
class AppealRaceTests(TransactionTestCase):
    def test_duplicate_submission_then_competing_claims(self):
        from moderation_appeals.models import Appeal
        from moderation_appeals.services import AppealError, claim_appeal, submit_appeal
        from moderation_appeals.sources import rejected_decisions

        users = get_user_model().objects
        author = users.create_user("race-author")
        first = users.create_user("race-first", is_staff=True)
        reviewers = [users.create_user(name, is_staff=True) for name in ("race-a", "race-b")]
        permission = Permission.objects.get(content_type__app_label="catalog", codename="change_sitereview")
        for reviewer in reviewers:
            reviewer.user_permissions.add(permission)
        SiteReview.objects.create(user=author, text="Source", status="rejected", moderated_by=first)
        decision = next(d for d in rejected_decisions(author) if d.kind == "site_review")

        def race(user_ids, operation):
            barrier = Barrier(2)

            def run(user_id):
                try:
                    actor = users.get(pk=user_id)
                    barrier.wait(timeout=10)
                    return operation(actor)
                except AppealError as exc:
                    return exc.code
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(run, user_ids))

        created = race([author.pk, author.pk], lambda actor: submit_appeal(actor, decision, "Evidence").pk)
        appeal = Appeal.objects.get()
        self.assertEqual(created, [appeal.pk, appeal.pk])
        results = race([u.pk for u in reviewers], lambda actor: claim_appeal(actor, appeal.pk).status)
        self.assertCountEqual(results, ["second_review", "conflict"])
