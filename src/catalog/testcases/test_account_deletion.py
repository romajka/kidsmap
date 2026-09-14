from __future__ import annotations

import copy
import io
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import (
    AccountDeletionAudit,
    AccountDeletionRequest,
    Category,
    Event,
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceLike,
    PlaceOwnershipRequest,
    PlaceReview,
    PlaceReviewCooldown,
    PlaceReviewReaction,
    SiteReview,
    Specialist,
    SpecialistReview,
    StaffRoleAudit,
    UserEmailVerification,
    UserProfile,
)
from catalog.services.account_deletion import (
    AccountDeletionError,
    cancel_account_deletion,
    confirm_account_deletion,
    finalize_account_deletion,
    issue_cancellation_code,
    make_status_token,
    request_account_deletion,
    typed_confirmation_phrase,
)


TEST_POLICY = {
    "active": True,
    "version": "ADRP-TEST-01",
    "effective_date": "2026-09-13",
    "approved_by": "Automated test privacy owner",
    "grace_period_days": 30,
    "processor_cadence": "daily",
    "review_disposition": "anonymize_approved_delete_other",
    "owner_content_disposition": "unlink_public_delete_team_access",
    "moderation_history_disposition": "anonymize",
    "analytics_disposition": "delete_user_events",
    "audit_retention_days": 365,
    "backup_expiry_days": 15,
    "public_copy": {
        "ru": {
            "deleted": "Профиль, избранное, реакции и активные приглашения будут удалены.",
            "anonymized": "Опубликованные отзывы сохранятся без связи с аккаунтом и имени автора.",
            "legal_hold": "Обработка может быть отложена только по утверждённому правовому основанию.",
            "owner_content": "Опубликованные карточки сохранятся, а владелец будет отвязан.",
            "backups": "Резервные копии истекают максимум через 15 дней.",
        },
        "az": {
            "deleted": "Profil və şəxsi hesab məlumatları silinəcək.",
            "anonymized": "Dərc edilmiş rəylər hesabla əlaqə olmadan saxlanacaq.",
            "legal_hold": "Təsdiqlənmiş hüquqi əsas olduqda emal təxirə salına bilər.",
            "owner_content": "Dərc edilmiş kartlar saxlanacaq, sahib əlaqəsi silinəcək.",
            "backups": "Ehtiyat nüsxələri ən gec 15 günə silinir.",
        },
        "en": {
            "deleted": "The profile, favorites, reactions and active invitations will be deleted.",
            "anonymized": "Published reviews remain without an account link or author name.",
            "legal_hold": "Processing may be delayed only under an approved legal basis.",
            "owner_content": "Published listings remain and their owner link is removed.",
            "backups": "Backups expire within at most 15 days.",
        },
    },
}


@override_settings(
    ACCOUNT_DELETION_RETENTION_POLICY=TEST_POLICY,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountDeletionWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="delete_me",
            email="delete-me@example.com",
            password="StrongPass123!!",
            first_name="Delete",
            last_name="Me",
        )
        self.profile = UserProfile.objects.create(user=self.user, phone="+994501112233")
        self.verification = UserEmailVerification.objects.create(
            user=self.user,
            email=self.user.email,
            is_verified=True,
            verified_at=timezone.now(),
        )
        self.category = Category.objects.create(code="DELBASE", name_ru="Удаление")

    def request_with_code(self, code="123456"):
        with patch("catalog.services.account_deletion._generate_code", return_value=code):
            deletion = request_account_deletion(user=self.user, language_code="en")
        self.assertIn(code, mail.outbox[-1].body)
        return deletion

    def schedule(self, code="123456"):
        deletion = self.request_with_code(code)
        return confirm_account_deletion(
            user=self.user,
            code=code,
            typed_confirmation=typed_confirmation_phrase("en"),
            language_code="en",
        )

    @override_settings(ACCOUNT_DELETION_RETENTION_POLICY={"active": False})
    def test_request_requires_active_retention_policy(self):
        with self.assertRaisesMessage(AccountDeletionError, "retention_policy_not_active"):
            request_account_deletion(user=self.user, language_code="en")
        self.assertFalse(AccountDeletionRequest.objects.exists())

    def test_policy_rejects_blank_effective_date_and_processor_cadence(self):
        for field in ("effective_date", "processor_cadence"):
            with self.subTest(field=field):
                policy = copy.deepcopy(TEST_POLICY)
                policy[field] = "  "
                with override_settings(ACCOUNT_DELETION_RETENTION_POLICY=policy):
                    with self.assertRaisesMessage(AccountDeletionError, "retention_policy_incomplete"):
                        request_account_deletion(user=self.user, language_code="en")
        self.assertFalse(AccountDeletionRequest.objects.exists())

    def test_request_requires_verified_current_email(self):
        self.verification.is_verified = False
        self.verification.save(update_fields=["is_verified"])
        with self.assertRaisesMessage(AccountDeletionError, "verified_email_required"):
            request_account_deletion(user=self.user, language_code="en")

    def test_confirmation_email_uses_requested_language(self):
        with patch("catalog.services.account_deletion._generate_code", return_value="123456"):
            request_account_deletion(user=self.user, language_code="az")
        self.assertIn("10 dəqiqə", mail.outbox[-1].body)
        self.assertIn("KidsMap dəstəyi", mail.outbox[-1].body)

    def test_staff_cannot_use_self_service_deletion(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        with self.assertRaisesMessage(AccountDeletionError, "staff_self_service_forbidden"):
            request_account_deletion(user=self.user, language_code="en")

    def test_confirmation_requires_exact_phrase_and_valid_code(self):
        deletion = self.request_with_code()
        with self.assertRaisesMessage(AccountDeletionError, "typed_confirmation_invalid"):
            confirm_account_deletion(
                user=self.user,
                code="123456",
                typed_confirmation="delete",
                language_code="en",
            )
        with self.assertRaisesMessage(AccountDeletionError, "confirmation_code_invalid"):
            confirm_account_deletion(
                user=self.user,
                code="000000",
                typed_confirmation=typed_confirmation_phrase("en"),
                language_code="en",
            )
        deletion.refresh_from_db()
        self.assertEqual(deletion.confirmation_attempts_left, 4)

    def test_confirmation_phrase_rejects_leading_or_trailing_whitespace(self):
        self.request_with_code()
        for value in (" DELETE MY ACCOUNT", "DELETE MY ACCOUNT "):
            with self.subTest(value=value):
                with self.assertRaisesMessage(AccountDeletionError, "typed_confirmation_invalid"):
                    confirm_account_deletion(
                        user=self.user,
                        code="123456",
                        typed_confirmation=value,
                        language_code="en",
                    )

    def test_confirmed_request_disables_user_without_deleting_related_rows(self):
        place = Place.objects.create(name="Owned place", category=self.category, owner=self.user, created_by=self.user)
        review = PlaceReview.objects.create(
            place=place,
            user=self.user,
            author_name="Delete Me",
            text="Useful review",
            rating=5,
        )
        deletion = self.schedule()
        self.user.refresh_from_db()
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.SCHEDULED)
        self.assertFalse(self.user.is_active)
        self.assertFalse(self.user.has_usable_password())
        self.assertTrue(Place.objects.filter(pk=place.pk).exists())
        self.assertTrue(PlaceReview.objects.filter(pk=review.pk).exists())
        self.assertFalse(UserEmailVerification.objects.filter(user=self.user).exists())

    def test_expired_code_is_rejected_and_attempts_are_limited(self):
        deletion = self.request_with_code()
        deletion.confirmation_expires_at = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["confirmation_expires_at"])
        with self.assertRaisesMessage(AccountDeletionError, "confirmation_code_expired"):
            confirm_account_deletion(
                user=self.user,
                code="123456",
                typed_confirmation=typed_confirmation_phrase("en"),
                language_code="en",
            )

    def test_expired_confirmation_can_issue_a_fresh_code(self):
        deletion = self.request_with_code("123456")
        deletion.confirmation_expires_at = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["confirmation_expires_at"])
        with patch("catalog.services.account_deletion._generate_code", return_value="222222"):
            refreshed = request_account_deletion(user=self.user, language_code="en")
        self.assertEqual(refreshed.pk, deletion.pk)
        self.assertEqual(refreshed.confirmation_attempts_left, 5)
        self.assertIn("222222", mail.outbox[-1].body)

    def test_policy_change_supersedes_an_expired_unconfirmed_request(self):
        deletion = self.request_with_code("123456")
        deletion.confirmation_expires_at = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["confirmation_expires_at"])
        updated_policy = {**TEST_POLICY, "version": "ADRP-TEST-02"}
        with self.settings(ACCOUNT_DELETION_RETENTION_POLICY=updated_policy):
            with patch("catalog.services.account_deletion._generate_code", return_value="222222"):
                replacement = request_account_deletion(user=self.user, language_code="en")
        deletion.refresh_from_db()
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.CANCELED)
        self.assertNotEqual(replacement.pk, deletion.pk)
        self.assertEqual(replacement.policy_version, "ADRP-TEST-02")

    def test_cancel_before_deadline_restores_access_but_requires_password_reset(self):
        deletion = self.schedule()
        with patch("catalog.services.account_deletion._generate_code", return_value="654321"):
            issue_cancellation_code(subject_reference=deletion.subject_reference, language_code="en")
        canceled = cancel_account_deletion(subject_reference=deletion.subject_reference, code="654321")
        self.user.refresh_from_db()
        self.assertEqual(canceled.status, AccountDeletionRequest.Status.CANCELED)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.has_usable_password())

    def test_canceled_user_can_request_a_new_password(self):
        deletion = self.schedule()
        with patch("catalog.services.account_deletion._generate_code", return_value="654321"):
            issue_cancellation_code(subject_reference=deletion.subject_reference, language_code="en")
        cancel_account_deletion(subject_reference=deletion.subject_reference, code="654321")
        mail.outbox.clear()

        response = self.client.post(reverse("password_reset"), {"email": self.user.email})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)

    def test_confirmation_invalidates_all_existing_sessions(self):
        first_client = Client()
        second_client = Client()
        self.assertTrue(first_client.login(username=self.user.username, password="StrongPass123!!"))
        self.assertTrue(second_client.login(username=self.user.username, password="StrongPass123!!"))
        session_keys = {first_client.session.session_key, second_client.session.session_key}

        self.schedule()

        self.assertFalse(Session.objects.filter(session_key__in=session_keys).exists())

    def test_cancel_after_grace_period_is_rejected(self):
        deletion = self.schedule()
        deletion.scheduled_for = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["scheduled_for"])
        with self.assertRaisesMessage(AccountDeletionError, "cancellation_period_expired"):
            issue_cancellation_code(subject_reference=deletion.subject_reference, language_code="en")

    def test_legal_hold_defers_finalization_without_restoring_login(self):
        deletion = self.schedule()
        deletion.status = AccountDeletionRequest.Status.HELD
        deletion.hold_code = "approved_legal_hold"
        deletion.scheduled_for = timezone.now() - timedelta(days=1)
        deletion.save(update_fields=["status", "hold_code", "scheduled_for"])
        result = finalize_account_deletion(deletion.pk, now=timezone.now())
        self.user.refresh_from_db()
        deletion.refresh_from_db()
        self.assertEqual(result.outcome, "held")
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.HELD)
        self.assertFalse(self.user.is_active)

    def test_finalization_anonymizes_public_content_and_deletes_direct_records(self):
        category = Category.objects.create(code="DELTEST", name_ru="Удаление")
        place = Place.objects.create(name="Public place", category=category, owner=self.user, created_by=self.user, status=Place.STATUS_PUBLISHED)
        event = Event.objects.create(name="Public event", owner=self.user, category=category, status=Event.STATUS_PUBLISHED)
        specialist = Specialist.objects.create(name="Public specialist", owner=self.user, status=Specialist.STATUS_PUBLISHED)
        place_review = PlaceReview.objects.create(
            place=place,
            user=self.user,
            author_name="Delete Me",
            text="Published place review",
            rating=5,
            status=PlaceReview.STATUS_APPROVED,
        )
        site_review = SiteReview.objects.create(
            user=self.user,
            author_name="Delete Me",
            text="Published site review",
            rating=4,
            status=SiteReview.STATUS_APPROVED,
        )
        specialist_review = SpecialistReview.objects.create(
            specialist=specialist,
            user=self.user,
            author_name="Delete Me",
            text="Published specialist review",
            rating=5,
            status=SpecialistReview.STATUS_APPROVED,
        )
        pending_review = PlaceReview.objects.create(
            place=place,
            user=self.user,
            author_name="Delete Me",
            text="Pending review",
            rating=3,
            status=PlaceReview.STATUS_PENDING,
        )
        PlaceLike.objects.create(place=place, user=self.user)
        PlaceReviewReaction.objects.create(review=place_review, user=self.user, value=1)
        PlaceReviewCooldown.objects.create(user=self.user, place=place)
        FunnelEvent.objects.create(event_type=FunnelEvent.EVENT_PLACE_OPEN, user=self.user, session_key="personal-session")
        ownership = PlaceOwnershipRequest.objects.create(place=place, applicant=self.user, note="Personal note")
        OwnerTeamMembership.objects.create(place=place, owner=self.user, member=User.objects.create_user("member"))
        OwnerTeamInvitation.objects.create(place=place, owner=self.user, email="invite@example.com")
        staff_audit = StaffRoleAudit.objects.create(
            actor=self.user,
            target=self.user,
            actor_display=self.user.email,
            target_display=self.user.get_full_name(),
            old_role="admin",
            new_role="user",
            action=StaffRoleAudit.Action.ROLE_CHANGED,
        )

        deletion = self.schedule()
        deletion.scheduled_for = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["scheduled_for"])
        result = finalize_account_deletion(deletion.pk, now=timezone.now())

        self.assertEqual(result.outcome, "completed")
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
        place.refresh_from_db()
        event.refresh_from_db()
        specialist.refresh_from_db()
        place_review.refresh_from_db()
        site_review.refresh_from_db()
        specialist_review.refresh_from_db()
        ownership.refresh_from_db()
        staff_audit.refresh_from_db()
        deletion.refresh_from_db()
        self.assertIsNone(place.owner_id)
        self.assertIsNone(event.owner_id)
        self.assertIsNone(specialist.owner_id)
        self.assertIsNone(place_review.user_id)
        self.assertEqual(place_review.author_name, "")
        self.assertIsNone(site_review.user_id)
        self.assertEqual(site_review.author_name, "")
        self.assertIsNone(specialist_review.user_id)
        self.assertEqual(specialist_review.author_name, "")
        self.assertFalse(PlaceReview.objects.filter(pk=pending_review.pk).exists())
        self.assertIsNone(ownership.applicant_id)
        self.assertEqual(ownership.note, "")
        self.assertIsNone(staff_audit.actor_id)
        self.assertIsNone(staff_audit.target_id)
        self.assertEqual(staff_audit.actor_display, "")
        self.assertEqual(staff_audit.target_display, "")
        self.assertFalse(PlaceLike.objects.filter(user_id=self.user.pk).exists())
        self.assertFalse(FunnelEvent.objects.filter(user_id=self.user.pk).exists())
        self.assertIsNone(deletion.user_id)
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.COMPLETED)
        self.assertTrue(AccountDeletionAudit.objects.filter(subject_reference=deletion.subject_reference).exists())

        again = finalize_account_deletion(deletion.pk, now=timezone.now())
        self.assertEqual(again.outcome, "completed")

    def test_audit_rejects_personal_identifier_counters(self):
        audit = AccountDeletionAudit(
            subject_reference="c3fd5db6-ce10-4da8-9df0-e5b87a02f9b6",
            event_type="test",
            policy_version="ADRP-TEST-01",
            counters={"email": 1},
        )
        with self.assertRaises(ValidationError):
            audit.full_clean()

    def test_processor_dry_run_is_non_mutating_and_due_run_is_idempotent(self):
        deletion = self.schedule()
        deletion.scheduled_for = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["scheduled_for"])
        output = io.StringIO()
        call_command("process_account_deletions", "--dry-run", stdout=output)
        deletion.refresh_from_db()
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.SCHEDULED)
        self.assertNotIn(self.user.email, output.getvalue())

        output = io.StringIO()
        call_command("process_account_deletions", stdout=output)
        deletion.refresh_from_db()
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.COMPLETED)
        self.assertIn("completed=1", output.getvalue())
        output = io.StringIO()
        call_command("process_account_deletions", stdout=output)
        self.assertIn("completed=0", output.getvalue())

    def test_corrupt_policy_snapshot_becomes_stable_processor_failure(self):
        deletion = self.schedule()
        deletion.scheduled_for = timezone.now() - timedelta(minutes=1)
        deletion.policy_snapshot = {"active": True, "version": deletion.policy_version}
        deletion.save(update_fields=["scheduled_for", "policy_snapshot", "updated_at"])

        result = finalize_account_deletion(deletion.pk)

        self.assertEqual(result.outcome, "failed")
        deletion.refresh_from_db()
        self.assertEqual(deletion.status, AccountDeletionRequest.Status.FAILED)
        self.assertEqual(deletion.failure_code, "processor_error")

    def test_one_failed_request_does_not_stop_the_next_due_request(self):
        broken = self.schedule()
        broken.scheduled_for = timezone.now() - timedelta(minutes=2)
        broken.policy_snapshot = {"active": True, "version": broken.policy_version}
        broken.save(update_fields=["scheduled_for", "policy_snapshot", "updated_at"])

        second_user = User.objects.create_user(
            username="delete_second",
            email="delete-second@example.com",
            password="StrongPass123!!",
        )
        UserEmailVerification.objects.create(
            user=second_user,
            email=second_user.email,
            is_verified=True,
            verified_at=timezone.now(),
        )
        with patch("catalog.services.account_deletion._generate_code", return_value="654321"):
            second = request_account_deletion(user=second_user, language_code="en")
        second = confirm_account_deletion(
            user=second_user,
            code="654321",
            typed_confirmation=typed_confirmation_phrase("en"),
            language_code="en",
        )
        second.scheduled_for = timezone.now() - timedelta(minutes=1)
        second.save(update_fields=["scheduled_for", "updated_at"])

        output = io.StringIO()
        with self.assertRaises(CommandError):
            call_command("process_account_deletions", stdout=output)

        broken.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(broken.status, AccountDeletionRequest.Status.FAILED)
        self.assertEqual(second.status, AccountDeletionRequest.Status.COMPLETED)
        self.assertFalse(User.objects.filter(pk=second_user.pk).exists())
        self.assertIn("completed=1", output.getvalue())
        self.assertIn("failed=1", output.getvalue())
        self.assertNotIn("delete-second@example.com", output.getvalue())

    def test_processor_purges_expired_pseudonymous_request_and_audit(self):
        deletion = self.schedule()
        deletion.scheduled_for = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["scheduled_for"])
        finalize_account_deletion(deletion.pk, now=timezone.now())
        deletion.refresh_from_db()
        AccountDeletionAudit.objects.filter(subject_reference=deletion.subject_reference).update(
            retain_until=timezone.now() - timedelta(seconds=1)
        )
        deletion.purge_after = timezone.now() - timedelta(seconds=1)
        deletion.save(update_fields=["purge_after"])

        output = io.StringIO()
        call_command("process_account_deletions", stdout=output)

        self.assertFalse(AccountDeletionRequest.objects.filter(pk=deletion.pk).exists())
        self.assertFalse(AccountDeletionAudit.objects.filter(subject_reference=deletion.subject_reference).exists())
        self.assertIn("audits_purged=", output.getvalue())
        self.assertIn("requests_purged=1", output.getvalue())


@override_settings(
    ACCOUNT_DELETION_RETENTION_POLICY=TEST_POLICY,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountDeletionWebTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="web_delete",
            email="web-delete@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(user=self.user)
        UserEmailVerification.objects.create(
            user=self.user,
            email=self.user.email,
            is_verified=True,
            verified_at=timezone.now(),
        )
        self.client.login(username=self.user.username, password="StrongPass123!!")

    def test_settings_has_delete_account_danger_zone(self):
        response = self.client.get(reverse("account_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hesabı sil")
        self.assertContains(response, reverse("account_deletion_request"))

    def test_request_and_double_confirmation_sign_out_to_private_status(self):
        with patch("catalog.services.account_deletion._generate_code", return_value="123456"):
            response = self.client.post(reverse("account_deletion_request"), {"form_action": "request"})
        deletion = AccountDeletionRequest.objects.get(user=self.user)
        confirm_url = reverse("account_deletion_confirm", args=[deletion.subject_reference])
        self.assertRedirects(response, confirm_url)
        self.assertIn("123456", mail.outbox[-1].body)

        confirmation_page = self.client.get(confirm_url)
        self.assertContains(confirmation_page, TEST_POLICY["public_copy"]["az"]["deleted"])
        self.assertContains(confirmation_page, TEST_POLICY["public_copy"]["az"]["backups"])
        self.assertContains(confirmation_page, "30")

        response = self.client.post(
            confirm_url,
            {
                "form_action": "confirm",
                "confirmation_code": "123456",
                "typed_confirmation": typed_confirmation_phrase("az"),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_deletion_status", args=[deletion.subject_reference]), response["Location"])
        self.assertNotIn("_auth_user_id", self.client.session)
        status_response = self.client.get(response["Location"])
        self.assertEqual(status_response.status_code, 200)
        self.assertContains(status_response, "30")

    def test_anonymous_and_other_user_cannot_access_confirmation(self):
        with patch("catalog.services.account_deletion._generate_code", return_value="123456"):
            deletion = request_account_deletion(user=self.user, language_code="ru")
        self.client.logout()
        anonymous = self.client.get(reverse("account_deletion_confirm", args=[deletion.subject_reference]))
        self.assertEqual(anonymous.status_code, 302)

        other = User.objects.create_user("other_web_user", password="StrongPass123!!")
        self.client.login(username=other.username, password="StrongPass123!!")
        forbidden = self.client.get(reverse("account_deletion_confirm", args=[deletion.subject_reference]))
        self.assertEqual(forbidden.status_code, 404)

    def test_status_requires_a_valid_signed_token(self):
        with patch("catalog.services.account_deletion._generate_code", return_value="123456"):
            deletion = request_account_deletion(user=self.user, language_code="en")
        url = reverse("account_deletion_status", args=[deletion.subject_reference])
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 404)
        token = make_status_token(deletion.subject_reference)
        response = self.client.get(f"{url}?token={token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store, max-age=0")
        self.assertEqual(response["Referrer-Policy"], "origin")

    def test_get_request_page_does_not_mutate_state(self):
        response = self.client.get(reverse("account_deletion_request"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccountDeletionRequest.objects.exists())
        self.assertContains(response, TEST_POLICY["public_copy"]["az"]["deleted"])
        self.assertEqual(response.content.count(b"<main"), 1)
        self.assertContains(
            response,
            'class="account-deletion-icon material-symbols-rounded"',
            html=False,
        )

    def test_staff_profile_explains_authorized_offboarding(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])
        response = self.client.get(reverse("account_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "səlahiyyətli administratora")
        self.assertNotContains(response, f'href="{reverse("account_deletion_request")}"')

        direct = self.client.get(reverse("account_deletion_request"))
        self.assertContains(direct, "Xidməti hesab üçün müraciət tələb olunur")

    def test_request_post_is_csrf_protected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username=self.user.username, password="StrongPass123!!")
        response = csrf_client.post(reverse("account_deletion_request"), {"form_action": "request"})
        self.assertEqual(response.status_code, 403)

    def test_staff_account_deletion_review_flow(self):
        self.user.is_staff = True
        self.user.save(update_fields=["is_staff"])

        # 1. Staff sees active button with modal trigger
        response = self.client.get(reverse("account_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="km-open-staff-deletion-btn"')
        self.assertContains(response, 'id="km-staff-deletion-modal"')
        self.assertContains(response, 'name="reason"')

        # 2. Staff submits deletion review request
        post_data = {
            "form_action": "staff_deletion_request",
            "reason": "leaving_project",
            "details": "Покидаю команду проекта",
        }
        res = self.client.post(reverse("account_settings"), post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # 3. AccountDeletionRequest created in HELD status
        req = AccountDeletionRequest.objects.filter(user=self.user).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, AccountDeletionRequest.Status.HELD)
        self.assertEqual(req.hold_code, "STAFF_OFFBOARDING_REVIEW")
        self.assertEqual(req.policy_snapshot["reason"], "leaving_project")
        self.assertEqual(req.policy_snapshot["details"], "Покидаю команду проекта")
        self.assertTrue(req.policy_snapshot["is_staff_offboarding"])

        # 4. Status card shown on settings page
        self.assertContains(res, "Hesabın silinməsi müraciətiniz baxılmadadır")
        self.assertContains(res, "Müraciəti ləğv et")

        # 5. Cancel request
        cancel_res = self.client.post(
            reverse("account_settings"),
            {"form_action": "cancel_staff_deletion_request"},
            follow=True,
        )
        self.assertEqual(cancel_res.status_code, 200)
        req.refresh_from_db()
        self.assertEqual(req.status, AccountDeletionRequest.Status.CANCELED)
