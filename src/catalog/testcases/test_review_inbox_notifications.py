from urllib.parse import unquote

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import (
    Category, EmailOutbox, Place, SiteSettings, Specialist, WorkflowNotification,
)
from catalog.services.review_versions import moderate_candidate, respond_to_review, submit_review
from catalog.testcases.utils import create_quality_place


class ReviewInboxNotificationTests(TestCase):
    def setUp(self):
        self.enterContext(translation.override("ru"))
        users = get_user_model().objects
        self.parent = users.create_user("review-parent", email="parent@example.invalid")
        self.owner = users.create_user("card-representative", email="owner@example.invalid")
        self.other = users.create_user("other-member")
        self.staff = users.create_superuser("review-staff", "staff@example.invalid", None)
        Category.objects.get_or_create(code="EDU", defaults={"name": "Education"})
        self.place = create_quality_place(owner=self.owner)
        self.person = Specialist.objects.create(
            name="Teacher", owner=self.other, created_by=self.other,
            verified_person_user=self.owner, person_verified_at=timezone.now(),
            status="published", is_active=True,
        )
        config = SiteSettings.get_solo()
        config.specialists_section_enabled = True
        config.save(update_fields=["specialists_section_enabled"])

    def publish(self, target):
        head, version = submit_review(target=target, user=self.parent, text="Family experience", rating=4)
        moderate_candidate(head=head, revision_id=version.pk, actor=self.staff, approve=True)
        head.refresh_from_db()
        return head, version

    def answer(self, head, version, kind="reply"):
        return respond_to_review(head=head, actor=self.owner, revision_id=version.pk,
                                 kind=kind, text="Thank you for visiting")

    def inbox(self, user):
        self.client.force_login(user)
        return self.client.get("/ru/account/notifications/")

    def test_published_review_and_reply_reach_only_their_recipients(self):
        for kind, target in [("place", self.place), ("specialist", self.person)]:
            with self.subTest(kind=kind):
                head, version = self.publish(target)
                url = reverse("typed_reviews", args=[kind, target.pk])
                self.assertContains(self.inbox(self.owner), f'{url}#review-{head.pk}')
                self.assertContains(self.inbox(self.owner), "Новый отзыв")
                self.assertNotContains(self.inbox(self.other), f'{url}#review-{head.pk}')
                self.answer(head, version, "report")
                self.assertFalse(WorkflowNotification.objects.filter(
                    recipient_user=self.parent, entity_type=f"{kind}_review").exists())
                reply = self.answer(head, version)
                parent_inbox = self.inbox(self.parent)
                self.assertContains(parent_inbox, f'{url}#reply-{reply.pk}')
                self.assertContains(parent_inbox, "Ответ на ваш отзыв")
                self.assertNotContains(parent_inbox, "Thank you for visiting")
        notices = WorkflowNotification.objects.filter(entity_type__in=["place_review", "specialist_review"])
        self.assertEqual(notices.count(), 4)
        self.assertFalse(notices.exclude(event_context={}).exists())
        self.assertFalse(notices.exclude(recipient_email="").exists())
        self.assertFalse(EmailOutbox.objects.filter(notification__in=notices).exists())

    def test_notification_loses_link_after_reply_hidden_card_unpublished_or_access_revoked(self):
        head, version = self.publish(self.place)
        reply = self.answer(head, version)
        path = reverse("typed_reviews", args=["place", self.place.pk])
        self.assertContains(self.inbox(self.parent), f'{path}#reply-{reply.pk}')
        type(reply).objects.filter(pk=reply.pk).update(kind="hidden", hidden_at=timezone.now())
        self.assertNotContains(self.inbox(self.parent), f'{path}#reply-{reply.pk}')
        Place.objects.filter(pk=self.place.pk).update(owner=self.other)
        self.assertNotContains(self.inbox(self.owner), f'{path}#review-{head.pk}')
        type(reply).objects.filter(pk=reply.pk).update(kind="reply", hidden_at=None)
        Place.objects.filter(pk=self.place.pk).update(status="draft")
        self.assertNotContains(self.inbox(self.parent), f'{path}#reply-{reply.pk}')

    def test_replacement_revision_removes_old_links_and_rollback_leaves_no_notification(self):
        head, first = self.publish(self.person)
        reply = self.answer(head, first)
        path = reverse("typed_reviews", args=["specialist", self.person.pk])
        _, updated = submit_review(target=self.person, user=self.parent, rating=5, text="Another visit")
        with transaction.atomic():
            moderate_candidate(head=head, revision_id=updated.pk, actor=self.staff, approve=True)
            transaction.set_rollback(True)
        self.assertContains(self.inbox(self.parent), f'{path}#reply-{reply.pk}')
        self.assertEqual(WorkflowNotification.objects.filter(recipient_user=self.owner).count(), 1)
        moderate_candidate(head=head, revision_id=updated.pk, actor=self.staff, approve=True)
        self.assertNotContains(self.inbox(self.parent), f'{path}#reply-{reply.pk}')
        self.assertEqual(WorkflowNotification.objects.filter(recipient_user=self.owner).count(), 2)

    def test_contacts_offers_exact_link_only_for_public_official_reply(self):
        head, rev = self.publish(self.place)
        reply = self.answer(head, rev)
        params = {"review_kind": "place", "target": self.place.pk, "reply": reply.pk}
        path = reverse("typed_reviews", args=["place", self.place.pk]) + f'#reply-{reply.pk}'
        page = self.client.get(reverse("contacts"), params)
        self.assertContains(page, 'name="robots" content="noindex,follow"')
        self.assertIn(path, unquote(page.content.decode()))
        self.assertContains(page, "Сообщить об ответе")
        report = self.answer(head, rev, "report")
        self.assertNotContains(self.client.get(reverse("contacts"), {**params, "reply": report.pk}),
                               "Сообщить об ответе")
        self.assertNotContains(self.client.get(reverse("contacts"), {**params, "target": self.place.pk + 1}),
                               "Сообщить об ответе")

    def test_moderating_an_unpublished_card_does_not_notify_its_representative(self):
        Place.objects.filter(pk=self.place.pk).update(status="draft")
        self.publish(self.place)
        self.assertFalse(WorkflowNotification.objects.filter(recipient_user=self.owner).exists())

    def test_unverified_profile_and_anonymized_author_receive_no_notice(self):
        Specialist.objects.filter(pk=self.person.pk).update(person_verified_at=None)
        head, version = self.publish(self.person)
        self.assertFalse(WorkflowNotification.objects.filter(recipient_user=self.owner).exists())
        Specialist.objects.filter(pk=self.person.pk).update(person_verified_at=timezone.now())
        type(head).objects.filter(pk=head.pk).update(user_id=None, is_anonymous=True)
        head.refresh_from_db()
        self.answer(head, version)
        self.assertFalse(WorkflowNotification.objects.filter(event_kind="review_replied").exists())
