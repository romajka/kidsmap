from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import resolve
from django.utils import timezone

from catalog.models import Category, Event, Place, PlaceOwnershipRequest, SiteReview, Specialist, VolunteerPlaceRevision, WorkflowNotification
from catalog.services import event_domain, place_moderation_decision, review_versions, specialist_moderation
from catalog.testcases.utils import create_quality_place


class AppealSourceTests(TestCase):
    def setUp(self):
        users = get_user_model().objects
        self.author = users.create_user("decision-author")
        self.other = users.create_user("other-author")
        self.reviewer = users.create_superuser("first-reviewer", "first@example.invalid", None)
        Category.objects.get_or_create(code="EDU", defaults={"name": "Education"})
        self.place = create_quality_place(owner=self.author, created_by=self.author)
        self.request = RequestFactory().post("/")
        self.request.user = self.reviewer

    def decisions(self, user=None):
        from moderation_appeals.sources import rejected_decisions
        return list(rejected_decisions(user or self.author))

    def test_only_owner_of_real_rejection_can_lookup_stable_decision(self):
        from moderation_appeals.sources import rejected_decision
        Place.objects.filter(pk=self.place.pk).update(status="pending")
        place_moderation_decision.decide(actor=self.reviewer, place_id=self.place.pk,
                                        decision="rejected", reason="Incorrect details")
        decision, = self.decisions()
        self.assertEqual((decision.kind, decision.reason, decision.reviewer_id),
                         ("place", "Incorrect details", self.reviewer.pk))
        args = decision.kind, decision.source_id, decision.version
        self.assertEqual(rejected_decision(self.author, *args, lock=True), decision)
        self.assertIsNone(rejected_decision(self.other, *args, lock=True))
        self.assertIsNone(rejected_decision(self.author, decision.kind, decision.source_id, "wrong"))
        self.assertEqual(self.decisions(AnonymousUser()), [])
        self.assertEqual(self.decisions(get_user_model()()), [])
        self.assertIsNone(rejected_decision(self.author, decision.kind, None, decision.version))
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        self.assertEqual(self.decisions(self.other), [])

    def test_bulk_place_refusal_cannot_replace_first_moderator_on_repeat(self):
        controller = admin.site._registry[Place]
        with patch.object(controller, "message_user"):
            controller.mark_rejected(self.request, Place.objects.filter(pk=self.place.pk))
            first, = self.decisions()
            self.request.user = self.other
            controller.mark_rejected(self.request, Place.objects.filter(pk=self.place.pk))
        current, = self.decisions()
        self.assertEqual(current, first)
        self.assertEqual(current.reviewer_id, self.reviewer.pk)
        self.assertIsNotNone(current.decided_at)

    def test_site_review_form_pins_first_refusal_before_later_admin_edits(self):
        review = SiteReview.objects.create(user=self.author, text="Original feedback", status="pending")
        review.status = "rejected"
        review.rejection_reason = "Initial reason"
        controller = admin.site._registry[SiteReview]
        controller.save_model(self.request, review, None, True)
        original, = self.decisions()
        review.rejection_reason = "Later edit"
        controller.save_model(self.request, review, None, True)
        self.assertEqual(self.decisions(), [original])
        self.assertEqual(original.reason, "Initial reason")
        self.assertEqual(original.reviewer_id, self.reviewer.pk)
        review.user = self.other
        controller.save_model(self.request, review, None, True)
        self.assertEqual(self.decisions(self.other), [])

    def test_candidate_return_excluded_and_final_refusal_includes_review_note(self):
        revision = VolunteerPlaceRevision.objects.create(place=self.place, author=self.author, status="rejected",
            version=4, reviewed_by=self.reviewer, review_note="Improve the title", payload={"name_az": "Studio"})
        self.assertEqual(self.decisions(), [])
        revision.status = "declined"
        revision.version += 1
        revision.review_note = "Duplicate submission"
        revision.save()
        result, = self.decisions()
        self.assertEqual((result.source_id, result.reason, result.reviewer_id),
                         (revision.pk, "Duplicate submission", self.reviewer.pk))

    def test_rejected_review_edit_is_visible_even_when_old_review_is_published(self):
        head, published = review_versions.submit_review(target=self.place, user=self.author, rating=5, text="Original")
        review_versions.moderate_candidate(head=head, revision_id=published.pk, actor=self.reviewer, approve=True)
        head, edit = review_versions.submit_review(target=self.place, user=self.author, rating=4, text="Edited review")
        review_versions.moderate_candidate(head=head, revision_id=edit.pk, actor=self.reviewer, approve=False,
                                           reason="Off-topic change")
        head.refresh_from_db()
        self.assertEqual(head.status, "approved")
        result, = self.decisions()
        self.assertEqual((result.kind, result.source_id, result.title, result.reason, result.reviewer_id),
                         ("place_review", head.pk, "Edited review", "Off-topic change", self.reviewer.pk))
        self.assertEqual(self.decisions(self.other), [])

    def test_specialist_receipt_is_shared_by_author_and_verified_owner_only(self):
        person = Specialist.objects.create(name="Synthetic tutor", created_by=self.author, verified_person_user=self.other,
                                           status="rejected", rejection_reason="Original reason")
        specialist_moderation.notify_decision(person, "rejected", "Original reason", actor=self.reviewer)
        Specialist.objects.filter(pk=person.pk).update(rejection_reason="Changed after the decision")
        result, = self.decisions()
        copy, = self.decisions(self.other)
        self.assertEqual((result.version, result.reviewer_id, result.reason),
                         (copy.version, self.reviewer.pk, "Original reason"))

    def test_bulk_specialist_refusal_does_not_overwrite_first_reason(self):
        person = Specialist.objects.create(name="Teacher", created_by=self.author, status="pending")
        controller = admin.site._registry[Specialist]
        queryset = Specialist.objects.filter(pk=person.pk)
        with patch.object(controller, "message_user"):
            self.request.POST = {"moderation_comment": "First reason"}
            controller.mark_rejected(self.request, queryset)
            self.request.POST = {"moderation_comment": "Different reason"}
            controller.mark_rejected(self.request, queryset)
        person.refresh_from_db()
        self.assertEqual(person.rejection_reason, "First reason")
        result, = self.decisions()
        self.assertEqual((result.reviewer_id, result.reason), (self.reviewer.pk, "First reason"))

    def test_malformed_or_mismatched_snapshot_never_discloses_text(self):
        person = Specialist.objects.create(name="Tutor", created_by=self.author, status="rejected")
        specialist_moderation.notify_decision(person, "rejected", "Untrusted", actor=self.reviewer)
        notes = WorkflowNotification.objects.filter(entity_type="specialist", entity_id=person.pk)
        valid = notes.get().event_context
        for context in ([], {**valid, "titles": []}, {**valid, "reason": ["Untrusted"]},
                        {**valid, "target_id": person.pk + 1}, {**valid, "titles": {"az": {"bad": 1}}}):
            with self.subTest(context=context):
                notes.update(event_context=context)
                self.assertEqual(self.decisions(), [])

    def test_original_specialist_recipient_is_identifiable_after_transfer(self):
        from moderation_appeals.sources import is_other_decision_recipient
        person = Specialist.objects.create(name="Tutor", created_by=self.author, verified_person_user=self.other,
                                           status="rejected")
        specialist_moderation.notify_decision(person, "rejected", "Reason", actor=self.reviewer)
        result, = self.decisions()
        Specialist.objects.filter(pk=person.pk).update(verified_person_user=None)
        self.assertTrue(is_other_decision_recipient(self.other, result.kind, result.source_id, result.version))
        self.assertFalse(is_other_decision_recipient(self.reviewer, result.kind, result.source_id, result.version))
        self.assertFalse(is_other_decision_recipient(self.other, result.kind, result.source_id, "invalid"))

    def test_site_review_legacy_null_attribution_remains_unknown(self):
        SiteReview.objects.create(user=self.author, text="Legacy", status="rejected", rejection_reason="")
        result, = self.decisions()
        self.assertIsNone(result.reviewer_id)
        self.assertIsNone(result.decided_at)
        self.assertEqual(result.reason, "")

    def test_explicit_event_rejection_records_reviewer_and_return_does_not(self):
        from catalog.domain_admin.place import EventAdmin
        category, _ = Category.objects.get_or_create(code="EDU", defaults={"name": "Educational"})
        start = timezone.now() + timedelta(days=14)
        event = Event.objects.create(owner=self.author, name="Workshop", category=category,
            start_datetime=start, end_datetime=start + timedelta(hours=1), status="pending")
        event_domain.review_event(actor=self.reviewer, event_id=event.pk, expected_updated_at=event.updated_at,
                                  decision="return", reason="Confirm time")
        self.assertEqual(self.decisions(), [])
        controller = EventAdmin(Event, admin.site)
        with patch.object(controller, "message_user"):
            controller.mark_rejected(self.request, Event.objects.filter(pk=event.pk))
        decision, = self.decisions()
        self.assertEqual((decision.kind, decision.reviewer_id, decision.source_id), ("event", self.reviewer.pk, event.pk))
        self.assertTrue(decision.reason)
        self.assertEqual(self.decisions(self.other), [])
        event.refresh_from_db()
        event.name = "New spelling"
        event.save(update_fields=["name", "updated_at"])
        self.assertEqual(self.decisions(), [decision])
        Event.objects.filter(pk=event.pk).update(status="pending")
        event_domain.review_event(actor=self.reviewer, event_id=event.pk, expected_updated_at=event.updated_at,
                                  decision="return", reason="Now correct the address")
        self.assertEqual(self.decisions(), [])

    def test_standalone_publication_refusal_is_distinct_from_claim_and_candidate_return(self):
        from catalog.services.organization_ownership import moderate_place_request
        # A stale candidate reference on this request must not turn its independent
        # explicit refusal into a decision on a newer candidate.
        item = PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.author, request_kind="PUBLICATION")
        PlaceOwnershipRequest.objects.filter(pk=item.pk).update(base_candidate_version=99)
        moderate_place_request(actor=self.reviewer, request_id=item.pk, new_status="REJECTED", note="Duplicate request")
        PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.author, request_kind="CLAIM", status="REJECTED")
        returned = PlaceOwnershipRequest.objects.create(place=self.place, applicant=self.author,
                                                       request_kind="PUBLICATION", status="REJECTED")
        PlaceOwnershipRequest.objects.filter(pk=returned.pk).update(base_candidate_version=5)
        result, = self.decisions()
        self.assertEqual((result.kind, result.source_id, result.reviewer_id, result.reason),
                         ("publication_request", item.pk, self.reviewer.pk, "Duplicate request"))
        self.assertEqual(self.decisions(self.other), [])

    def test_admin_link_resolves_every_supported_kind(self):
        from moderation_appeals.sources import PERMISSIONS, admin_source_url
        for kind in PERMISSIONS:
            with self.subTest(kind=kind):
                self.assertEqual(resolve(admin_source_url(kind, self.place.pk)).namespace, "admin")
        self.assertEqual(admin_source_url("unknown", 1), "")
