from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import (
    Category, OwnerTeamMembership, PlaceReview, SiteSettings, Specialist,
    SpecialistReview,
)
from catalog.services.review_versions import respond_to_review
from catalog.testcases.utils import create_quality_place


class OfficialReviewInboxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model().objects
        cls.rep = users.create_user("venue-representative")
        cls.parent = users.create_user("reviewing-parent")
        cls.delegate = users.create_user("reports-only")
        Category.objects.get_or_create(code="EDU", defaults={"name": "Education"})
        config = SiteSettings.get_solo()
        config.specialists_section_enabled = True
        config.save(update_fields=["specialists_section_enabled"])
        cls.place = create_quality_place(owner=cls.rep)
        cls.person = Specialist.objects.create(
            name="Nur Karim", status="published", is_active=True,
            verified_person_user=cls.rep, person_verified_at=timezone.now(),
        )
        cls.venue_review = PlaceReview.objects.create(
            place=cls.place, user=cls.parent, author_name="Ayla", rating=4,
            status="approved", text="Courtyard with shade",
        )
        cls.profile_review = SpecialistReview.objects.create(
            specialist=cls.person, user=cls.parent, author_name="Ayla", rating=5,
            status="approved", text="Clear explanations",
        )
        for head in (cls.venue_review, cls.profile_review):
            head.refresh_from_db()
        cls.reply = respond_to_review(
            head=cls.venue_review, actor=cls.rep, revision_id=cls.venue_review.current_revision_id,
            kind="reply", text="Thank you for visiting us",
        )
        respond_to_review(
            head=cls.profile_review, actor=cls.rep, revision_id=cls.profile_review.current_revision_id,
            kind="report", text="Private complaint",
        )
        OwnerTeamMembership.objects.create(
            owner=cls.rep, member=cls.delegate, place=cls.place,
            actions=["place.reviews.report"],
        )

    def setUp(self):
        self.enterContext(translation.override("ru"))

    def test_inbox_links_to_both_review_types_and_filters_only_visible_replies(self):
        self.client.force_login(self.rep)
        inbox = reverse("owner_reviews_dashboard")
        all_reviews = self.client.get(inbox)
        self.assertContains(all_reviews, "Clear explanations")
        self.assertContains(all_reviews, "Courtyard with shade")
        for kind, head, target in (("place", self.venue_review, self.place),
                                   ("specialist", self.profile_review, self.person)):
            self.assertContains(all_reviews, reverse("typed_reviews", args=[kind, target.pk]) + "#reply-text-" + str(head.pk))
        unanswered = self.client.get(inbox, {"filter": "unanswered"})
        self.assertContains(unanswered, "Clear explanations")
        self.assertNotContains(unanswered, "Courtyard with shade")
        self.assertNotContains(unanswered, "Private complaint")

    def test_report_only_delegate_can_open_review_without_reply_action(self):
        self.client.force_login(self.delegate)
        page = self.client.get(reverse("owner_reviews_dashboard"))
        self.assertContains(page, "Courtyard with shade")
        self.assertContains(page, "Пожаловаться")
        self.assertNotContains(page, "Ответить на отзыв")
        self.assertNotContains(page, "Clear explanations")

    def test_author_sees_both_written_reviews_and_sidebar_count(self):
        self.client.force_login(self.parent)
        page = self.client.get(reverse("owner_reviews_dashboard"))
        self.assertContains(page, "Clear explanations")
        self.assertContains(page, "Courtyard with shade")
        self.assertEqual(page.context["user_reviews_count"], 2)
        home = self.client.get(reverse("account_dashboard"))
        self.assertContains(home, self.person.name)
        self.assertEqual(home.context["user_reviews_count"], 2)

    def test_guest_reads_current_replies_on_cards_and_global_feed(self):
        respond_to_review(
            head=self.profile_review, actor=self.rep, revision_id=self.profile_review.current_revision_id,
            kind="reply", text="Thank you for your question",
        )
        for url, text, title in (
            (self.place.get_absolute_url(), "Thank you for visiting us", "Ответ представителя места"),
            (reverse("place_reviews"), "Thank you for visiting us", "Ответ представителя места"),
            (self.person.get_absolute_url(), "Thank you for your question", "Ответ специалиста"),
        ):
            with self.subTest(url=url):
                page = self.client.get(url, follow=True)
                self.assertContains(page, text)
                self.assertContains(page, title)
                self.assertNotContains(page, "Private complaint")

    def test_paging_and_stable_order_across_types(self):
        self.client.force_login(self.rep)
        for number in range(15):
            PlaceReview.objects.create(place=self.place, rating=5, status="approved",
                                       text=f"Weekend visit {number}", author_name="Ada")
        url = reverse("owner_reviews_dashboard")
        first = self.client.get(url)
        second = self.client.get(url, {"page": 2})
        first_ids = {(r.review_kind, r.pk) for r in first.context["owner_reviews"]}
        second_ids = {(r.review_kind, r.pk) for r in second.context["owner_reviews"]}
        self.assertEqual(len(first_ids), 12)
        self.assertEqual(len(second_ids), 5)
        self.assertFalse(first_ids & second_ids)

    def test_unpublished_targets_do_not_offer_public_replies(self):
        self.place.status = "draft"
        self.place.save(update_fields=["status"])
        self.person.is_active = False
        self.person.save(update_fields=["is_active"])
        self.client.force_login(self.rep)
        inbox = self.client.get(reverse("owner_reviews_dashboard"))
        self.assertNotContains(inbox, "Clear explanations")
        self.assertNotContains(inbox, "Courtyard with shade")
        self.assertNotContains(self.client.get(reverse("place_reviews")), "Thank you for visiting us")

    def test_moderation_counts_are_private_and_written_edit_keeps_its_decision(self):
        from catalog.services.review_versions import submit_review, moderate_candidate
        moderator = get_user_model().objects.create_superuser("review-staff", password=None)
        head, change = submit_review(target=self.person, user=self.parent, rating=4,
                                     text="My unpublished correction", author_name="Ayla",
                                     expected_revision_id=self.profile_review.current_revision_id,
                                     enforce_cooldown=False)
        self.client.force_login(self.rep)
        inbox = reverse("owner_reviews_dashboard")
        page = self.client.get(inbox)
        self.assertEqual(page.context["owner_reviews_pending_count"], 1)
        self.assertNotContains(page, "My unpublished correction")
        self.client.force_login(self.parent)
        self.assertContains(self.client.get(inbox), "Правка на проверке")
        moderate_candidate(head=head, revision_id=change.pk, actor=moderator, approve=False,
                           reason="Please clarify the visit date")
        page = self.client.get(inbox)
        self.assertContains(page, "Правка отклонена")
        self.assertContains(page, "Please clarify the visit date")

    def test_specialist_workspace_filter_opens_only_its_own_inbox(self):
        self.client.force_login(self.rep)
        url = reverse("owner_reviews_dashboard")
        page = self.client.get(url, {"specialist": self.person.pk})
        self.assertContains(page, "Clear explanations")
        self.assertNotContains(page, "Courtyard with shade")
        public_profile = self.client.get(reverse("specialist_workspace_profile", args=[self.person.pk]))
        self.assertContains(public_profile, f"{url}?specialist={self.person.pk}#incoming-reviews")

    def test_guest_loads_several_reviews_responses_in_one_query(self):
        from catalog.services.public_review_replies import attach_public_review_replies

        second = PlaceReview.objects.create(place=self.place, rating=5, text="Second family visit",
                                            author_name="Kamran", status="approved")
        heads = list(PlaceReview.objects.filter(pk__in=[self.venue_review.pk, second.pk]).order_by("pk"))
        with self.assertNumQueries(1):
            displayed = attach_public_review_replies(heads, kind="place")
            self.assertEqual([[reply.text for reply in h.public_replies] for h in displayed],
                             [["Thank you for visiting us"], []])

    def test_hidden_answer_disappears_from_cards_and_counts_as_unanswered(self):
        self.reply.hidden_at = timezone.now()
        self.reply.kind = "hidden"
        self.reply.save(update_fields=["kind", "hidden_at"])
        self.assertNotContains(self.client.get(self.place.get_absolute_url(), follow=True), self.reply.text)
        self.client.force_login(self.rep)
        unanswered = self.client.get(reverse("owner_reviews_dashboard"), {"filter": "unanswered"})
        self.assertContains(unanswered, "Courtyard with shade")
