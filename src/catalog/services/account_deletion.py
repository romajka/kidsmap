from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from django.conf import settings
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.models import Session
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from catalog.models import (
    AccountDeletionAudit,
    AccountDeletionRequest,
    Event,
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceLike,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    PlaceReview,
    PlaceReviewCooldown,
    PlaceReviewReaction,
    SiteReview,
    SiteReviewReaction,
    Specialist,
    SpecialistReview,
    StaffRoleAudit,
    UserEmailVerification,
    UserProfile,
)
from catalog.models.review import sync_place_rating_stats
from catalog.models.specialist import sync_specialist_rating_stats


STATUS_TOKEN_SALT = "catalog.account-deletion-status.v1"
SUPPORTED_LANGUAGES = ("az", "ru", "en")
REQUIRED_PUBLIC_COPY_KEYS = ("deleted", "anonymized", "legal_hold", "owner_content", "backups")


class AccountDeletionError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    version: str
    effective_date: str
    approved_by: str
    grace_period_days: int
    processor_cadence: str
    review_disposition: str
    owner_content_disposition: str
    moderation_history_disposition: str
    analytics_disposition: str
    audit_retention_days: int
    backup_expiry_days: int
    public_copy: dict[str, dict[str, str]]

    @classmethod
    def from_mapping(cls, value: Any, *, require_active: bool = True) -> "RetentionPolicy":
        if not isinstance(value, dict) or (require_active and value.get("active") is not True):
            raise AccountDeletionError("retention_policy_not_active")
        required = {
            "version",
            "effective_date",
            "approved_by",
            "grace_period_days",
            "processor_cadence",
            "review_disposition",
            "owner_content_disposition",
            "moderation_history_disposition",
            "analytics_disposition",
            "audit_retention_days",
            "backup_expiry_days",
            "public_copy",
        }
        if required - set(value):
            raise AccountDeletionError("retention_policy_incomplete")
        if any(
            not str(value.get(field) or "").strip()
            for field in ("version", "effective_date", "approved_by", "processor_cadence")
        ):
            raise AccountDeletionError("retention_policy_incomplete")
        try:
            grace_days = int(value["grace_period_days"])
            audit_days = int(value["audit_retention_days"])
            backup_days = int(value["backup_expiry_days"])
        except (TypeError, ValueError):
            raise AccountDeletionError("retention_policy_incomplete") from None
        if grace_days < 1 or audit_days < 1 or backup_days < 1:
            raise AccountDeletionError("retention_policy_incomplete")
        if value["review_disposition"] not in {"anonymize_approved_delete_other", "delete_all"}:
            raise AccountDeletionError("retention_policy_unsupported")
        if value["owner_content_disposition"] != "unlink_public_delete_team_access":
            raise AccountDeletionError("retention_policy_unsupported")
        if value["moderation_history_disposition"] != "anonymize":
            raise AccountDeletionError("retention_policy_unsupported")
        if value["analytics_disposition"] != "delete_user_events":
            raise AccountDeletionError("retention_policy_unsupported")
        public_copy = value["public_copy"]
        if not isinstance(public_copy, dict):
            raise AccountDeletionError("retention_policy_incomplete")
        for language in SUPPORTED_LANGUAGES:
            language_copy = public_copy.get(language)
            if not isinstance(language_copy, dict) or any(not str(language_copy.get(key) or "").strip() for key in REQUIRED_PUBLIC_COPY_KEYS):
                raise AccountDeletionError("retention_policy_incomplete")
        return cls(
            version=str(value["version"]).strip(),
            effective_date=str(value["effective_date"]).strip(),
            approved_by=str(value["approved_by"]).strip(),
            grace_period_days=grace_days,
            processor_cadence=str(value["processor_cadence"]).strip(),
            review_disposition=value["review_disposition"],
            owner_content_disposition=value["owner_content_disposition"],
            moderation_history_disposition=value["moderation_history_disposition"],
            analytics_disposition=value["analytics_disposition"],
            audit_retention_days=audit_days,
            backup_expiry_days=backup_days,
            public_copy={lang: {key: str(public_copy[lang][key]) for key in REQUIRED_PUBLIC_COPY_KEYS} for lang in SUPPORTED_LANGUAGES},
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "active": True,
            "version": self.version,
            "effective_date": self.effective_date,
            "approved_by": self.approved_by,
            "grace_period_days": self.grace_period_days,
            "processor_cadence": self.processor_cadence,
            "review_disposition": self.review_disposition,
            "owner_content_disposition": self.owner_content_disposition,
            "moderation_history_disposition": self.moderation_history_disposition,
            "analytics_disposition": self.analytics_disposition,
            "audit_retention_days": self.audit_retention_days,
            "backup_expiry_days": self.backup_expiry_days,
            "public_copy": self.public_copy,
        }

    def disclosure(self, language_code: str | None) -> dict[str, str]:
        language = _normalize_language(language_code)
        return dict(self.public_copy.get(language) or self.public_copy["ru"])


@dataclass(frozen=True, slots=True)
class FinalizationResult:
    outcome: str
    counters: dict[str, int]


def _normalize_language(language_code: str | None) -> str:
    language = (language_code or "ru").split("-", 1)[0].lower()
    return language if language in SUPPORTED_LANGUAGES else "ru"


def get_active_retention_policy() -> RetentionPolicy:
    return RetentionPolicy.from_mapping(getattr(settings, "ACCOUNT_DELETION_RETENTION_POLICY", None))


def policy_from_request(deletion: AccountDeletionRequest) -> RetentionPolicy:
    return RetentionPolicy.from_mapping(deletion.policy_snapshot, require_active=False)


def typed_confirmation_phrase(language_code: str | None) -> str:
    return {
        "az": "HESABIMI SİL",
        "en": "DELETE MY ACCOUNT",
        "ru": "УДАЛИТЬ МОЙ АККАУНТ",
    }[_normalize_language(language_code)]


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _code_ttl_minutes() -> int:
    return max(int(getattr(settings, "ACCOUNT_DELETION_CODE_TTL_MINUTES", 10)), 1)


def confirmation_code_ttl_minutes() -> int:
    return _code_ttl_minutes()


def _max_attempts() -> int:
    return max(int(getattr(settings, "ACCOUNT_DELETION_CODE_MAX_ATTEMPTS", 5)), 1)


def _status_token_max_age_seconds(deletion: AccountDeletionRequest) -> int:
    try:
        grace_days = policy_from_request(deletion).grace_period_days
    except AccountDeletionError:
        grace_days = 1
    configured = int(getattr(settings, "ACCOUNT_DELETION_STATUS_TOKEN_MAX_AGE_SECONDS", 0) or 0)
    return configured if configured > 0 else (grace_days + 2) * 24 * 60 * 60


def make_status_token(subject_reference: UUID | str) -> str:
    return signing.dumps({"subject": str(subject_reference)}, salt=STATUS_TOKEN_SALT, compress=True)


def verify_status_token(subject_reference: UUID | str, token: str) -> bool:
    try:
        deletion = AccountDeletionRequest.objects.only("policy_snapshot").get(subject_reference=subject_reference)
        value = signing.loads(token, salt=STATUS_TOKEN_SALT, max_age=_status_token_max_age_seconds(deletion))
    except (AccountDeletionRequest.DoesNotExist, signing.BadSignature, signing.SignatureExpired, TypeError, ValueError):
        return False
    return value == {"subject": str(subject_reference)}


def _send_confirmation_email(*, email: str, code: str, purpose: str, language_code: str, policy: RetentionPolicy) -> None:
    language = _normalize_language(language_code)
    if purpose == AccountDeletionRequest.CodePurpose.CANCEL:
        subjects = {
            "az": "KidsMap hesab silinməsinin ləğvi üçün kod",
            "en": "Code to cancel KidsMap account deletion",
            "ru": "Код отмены удаления аккаунта KidsMap",
        }
        intros = {
            "az": "Hesabın silinməsini ləğv etmək üçün kod:",
            "en": "Code to cancel account deletion:",
            "ru": "Код для отмены удаления аккаунта:",
        }
    else:
        subjects = {
            "az": "KidsMap hesabının silinməsi üçün təsdiq kodu",
            "en": "KidsMap account deletion confirmation code",
            "ru": "Код подтверждения удаления аккаунта KidsMap",
        }
        intros = {
            "az": "Hesabın silinməsini təsdiqləmək üçün kod:",
            "en": "Code to confirm account deletion:",
            "ru": "Код для подтверждения удаления аккаунта:",
        }
    minutes = _code_ttl_minutes()
    validity = {
        "az": f"Kod {minutes} dəqiqə ərzində etibarlıdır. Siyasət: {policy.version}.",
        "en": f"The code is valid for {minutes} minutes. Policy: {policy.version}.",
        "ru": f"Код действует {minutes} минут. Политика: {policy.version}.",
    }
    safety = {
        "az": "Bu əməliyyatı siz tələb etməmisinizsə, KidsMap dəstəyi ilə əlaqə saxlayın.",
        "en": "If you did not request this action, contact KidsMap support.",
        "ru": "Если вы не запрашивали это действие, обратитесь в поддержку KidsMap.",
    }
    body = (
        f"{intros[language]} {code}\n\n"
        f"{validity[language]}\n"
        f"{safety[language]}"
    )
    send_mail(
        subject=subjects[language],
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def _audit(deletion: AccountDeletionRequest, event_type: str, counters: dict[str, int] | None = None) -> None:
    policy = policy_from_request(deletion)
    AccountDeletionAudit.objects.create(
        subject_reference=deletion.subject_reference,
        event_type=event_type,
        policy_version=deletion.policy_version,
        counters=counters or {},
        retain_until=timezone.now() + timedelta(days=policy.audit_retention_days),
    )


def _verified_email_for(user) -> str:
    try:
        verification = user.email_verification
    except UserEmailVerification.DoesNotExist as exc:
        raise AccountDeletionError("verified_email_required") from exc
    email = (user.email or "").strip().lower()
    if not verification.is_verified or (verification.email or "").strip().lower() != email or not email:
        raise AccountDeletionError("verified_email_required")
    return email


def request_account_deletion(*, user, language_code: str | None = None) -> AccountDeletionRequest:
    policy = get_active_retention_policy()
    if not getattr(user, "pk", None) or not user.is_active:
        raise AccountDeletionError("account_not_available")
    if user.is_staff or user.is_superuser:
        raise AccountDeletionError("staff_self_service_forbidden")
    language = _normalize_language(language_code)
    now = timezone.now()
    with transaction.atomic():
        locked_user = get_user_model().objects.select_for_update().get(pk=user.pk)
        email = _verified_email_for(locked_user)
        existing = AccountDeletionRequest.objects.select_for_update().filter(
            user=locked_user,
            status__in=AccountDeletionRequest.ACTIVE_STATUSES,
        ).first()
        if existing is not None:
            if (
                existing.status == AccountDeletionRequest.Status.CONFIRMATION_SENT
                and existing.policy_version == policy.version
                and existing.confirmation_expires_at
                and existing.confirmation_expires_at > now
            ):
                return existing
            if existing.status != AccountDeletionRequest.Status.CONFIRMATION_SENT:
                raise AccountDeletionError("account_deletion_already_active")
            if existing.policy_version != policy.version:
                existing.status = AccountDeletionRequest.Status.CANCELED
                existing.canceled_at = now
                existing.purge_after = now + timedelta(days=policy_from_request(existing).audit_retention_days)
                _clear_code(existing)
                existing.save(
                    update_fields=[
                        "status",
                        "canceled_at",
                        "purge_after",
                        "confirmation_code_hash",
                        "confirmation_expires_at",
                        "confirmation_attempts_left",
                        "code_purpose",
                        "updated_at",
                    ]
                )
                _audit(existing, "request_superseded")
                existing = None
        code = _generate_code()
        try:
            _send_confirmation_email(email=email, code=code, purpose=AccountDeletionRequest.CodePurpose.DELETE, language_code=language, policy=policy)
        except Exception as exc:
            raise AccountDeletionError("confirmation_email_failed") from exc
        if existing is None:
            deletion = AccountDeletionRequest.objects.create(
                user=locked_user,
                status=AccountDeletionRequest.Status.CONFIRMATION_SENT,
                policy_version=policy.version,
                policy_snapshot=policy.snapshot(),
                confirmation_code_hash=make_password(code),
                confirmation_expires_at=now + timedelta(minutes=_code_ttl_minutes()),
                confirmation_attempts_left=_max_attempts(),
                confirmation_sent_at=now,
                code_purpose=AccountDeletionRequest.CodePurpose.DELETE,
            )
        else:
            deletion = existing
            deletion.confirmation_code_hash = make_password(code)
            deletion.confirmation_expires_at = now + timedelta(minutes=_code_ttl_minutes())
            deletion.confirmation_attempts_left = _max_attempts()
            deletion.confirmation_sent_at = now
            deletion.code_purpose = AccountDeletionRequest.CodePurpose.DELETE
            deletion.save(
                update_fields=[
                    "confirmation_code_hash",
                    "confirmation_expires_at",
                    "confirmation_attempts_left",
                    "confirmation_sent_at",
                    "code_purpose",
                    "updated_at",
                ]
            )
        _audit(deletion, "confirmation_sent")
    return deletion


def _validate_code_locked(deletion: AccountDeletionRequest, *, code: str, purpose: str, now) -> str | None:
    if deletion.code_purpose != purpose or not deletion.confirmation_code_hash:
        return "confirmation_code_unavailable"
    if deletion.confirmation_expires_at is None or now > deletion.confirmation_expires_at:
        return "confirmation_code_expired"
    if deletion.confirmation_attempts_left <= 0:
        return "confirmation_attempts_exhausted"
    if not check_password((code or "").strip(), deletion.confirmation_code_hash):
        deletion.confirmation_attempts_left = max(deletion.confirmation_attempts_left - 1, 0)
        deletion.save(update_fields=["confirmation_attempts_left", "updated_at"])
        return "confirmation_code_invalid" if deletion.confirmation_attempts_left else "confirmation_attempts_exhausted"
    return None


def _clear_code(deletion: AccountDeletionRequest) -> None:
    deletion.confirmation_code_hash = ""
    deletion.confirmation_expires_at = None
    deletion.confirmation_attempts_left = 0
    deletion.code_purpose = ""


def _delete_user_sessions(user_id: int) -> int:
    deleted = 0
    for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator():
        try:
            session_user_id = session.get_decoded().get("_auth_user_id")
        except Exception:
            continue
        if str(session_user_id) == str(user_id):
            session.delete()
            deleted += 1
    return deleted


def confirm_account_deletion(
    *,
    user,
    code: str,
    typed_confirmation: str,
    language_code: str | None = None,
    http_request=None,
    now=None,
) -> AccountDeletionRequest:
    policy = get_active_retention_policy()
    language = _normalize_language(language_code)
    if (typed_confirmation or "") != typed_confirmation_phrase(language):
        raise AccountDeletionError("typed_confirmation_invalid")
    now = now or timezone.now()
    error_code = None
    with transaction.atomic():
        deletion = AccountDeletionRequest.objects.select_for_update().filter(
            user=user,
            status=AccountDeletionRequest.Status.CONFIRMATION_SENT,
        ).first()
        if deletion is None:
            raise AccountDeletionError("account_deletion_not_confirmable")
        if deletion.policy_version != policy.version:
            raise AccountDeletionError("retention_policy_changed")
        error_code = _validate_code_locked(deletion, code=code, purpose=AccountDeletionRequest.CodePurpose.DELETE, now=now)
        if error_code is None:
            locked_user = get_user_model().objects.select_for_update().get(pk=user.pk)
            deletion.status = AccountDeletionRequest.Status.SCHEDULED
            deletion.confirmed_at = now
            deletion.scheduled_for = now + timedelta(days=policy.grace_period_days)
            deletion.failure_code = ""
            _clear_code(deletion)
            deletion.save(
                update_fields=[
                    "status",
                    "confirmed_at",
                    "scheduled_for",
                    "failure_code",
                    "confirmation_code_hash",
                    "confirmation_expires_at",
                    "confirmation_attempts_left",
                    "code_purpose",
                    "updated_at",
                ]
            )
            locked_user.is_active = False
            locked_user.set_unusable_password()
            locked_user.save(update_fields=["is_active", "password"])
            UserEmailVerification.objects.filter(user=locked_user).delete()
            _delete_user_sessions(locked_user.pk)
            _audit(deletion, "deletion_scheduled")
    if error_code:
        raise AccountDeletionError(error_code)
    if http_request is not None:
        logout(http_request)
    deletion.refresh_from_db()
    return deletion


def issue_cancellation_code(*, subject_reference: UUID | str, language_code: str | None = None, now=None) -> AccountDeletionRequest:
    now = now or timezone.now()
    language = _normalize_language(language_code)
    with transaction.atomic():
        deletion = AccountDeletionRequest.objects.select_for_update().select_related("user").get(subject_reference=subject_reference)
        if deletion.status != AccountDeletionRequest.Status.SCHEDULED or deletion.user is None:
            raise AccountDeletionError("account_deletion_not_cancelable")
        if deletion.scheduled_for is None or now >= deletion.scheduled_for:
            raise AccountDeletionError("cancellation_period_expired")
        policy = policy_from_request(deletion)
        code = _generate_code()
        email = (deletion.user.email or "").strip().lower()
        if not email:
            raise AccountDeletionError("cancellation_email_unavailable")
        try:
            _send_confirmation_email(email=email, code=code, purpose=AccountDeletionRequest.CodePurpose.CANCEL, language_code=language, policy=policy)
        except Exception as exc:
            raise AccountDeletionError("confirmation_email_failed") from exc
        deletion.confirmation_code_hash = make_password(code)
        deletion.confirmation_expires_at = now + timedelta(minutes=_code_ttl_minutes())
        deletion.confirmation_attempts_left = _max_attempts()
        deletion.confirmation_sent_at = now
        deletion.code_purpose = AccountDeletionRequest.CodePurpose.CANCEL
        deletion.save(
            update_fields=[
                "confirmation_code_hash",
                "confirmation_expires_at",
                "confirmation_attempts_left",
                "confirmation_sent_at",
                "code_purpose",
                "updated_at",
            ]
        )
        _audit(deletion, "cancellation_confirmation_sent")
    return deletion


def cancel_account_deletion(*, subject_reference: UUID | str, code: str, now=None) -> AccountDeletionRequest:
    now = now or timezone.now()
    error_code = None
    with transaction.atomic():
        deletion = AccountDeletionRequest.objects.select_for_update().select_related("user").get(subject_reference=subject_reference)
        if deletion.status != AccountDeletionRequest.Status.SCHEDULED or deletion.user is None:
            raise AccountDeletionError("account_deletion_not_cancelable")
        if deletion.scheduled_for is None or now >= deletion.scheduled_for:
            raise AccountDeletionError("cancellation_period_expired")
        error_code = _validate_code_locked(deletion, code=code, purpose=AccountDeletionRequest.CodePurpose.CANCEL, now=now)
        if error_code is None:
            locked_user = get_user_model().objects.select_for_update().get(pk=deletion.user_id)
            locked_user.is_active = True
            locked_user.save(update_fields=["is_active"])
            UserEmailVerification.objects.update_or_create(
                user=locked_user,
                defaults={
                    "email": (locked_user.email or "").strip().lower(),
                    "is_verified": True,
                    "verified_at": now,
                    "code_hash": "",
                    "expires_at": None,
                    "resend_available_at": None,
                    "attempts_left": 0,
                },
            )
            deletion.status = AccountDeletionRequest.Status.CANCELED
            deletion.canceled_at = now
            deletion.purge_after = now + timedelta(days=policy_from_request(deletion).audit_retention_days)
            deletion.failure_code = ""
            _clear_code(deletion)
            deletion.save(
                update_fields=[
                    "status",
                    "canceled_at",
                    "purge_after",
                    "failure_code",
                    "confirmation_code_hash",
                    "confirmation_expires_at",
                    "confirmation_attempts_left",
                    "code_purpose",
                    "updated_at",
                ]
            )
            _audit(deletion, "deletion_canceled")
    if error_code:
        raise AccountDeletionError(error_code)
    deletion.refresh_from_db()
    return deletion


def _delete_count(queryset) -> int:
    return int(queryset.delete()[0])


def _finalize_locked(deletion: AccountDeletionRequest, *, now) -> FinalizationResult:
    if deletion.status == AccountDeletionRequest.Status.COMPLETED:
        return FinalizationResult("completed", {})
    if deletion.status == AccountDeletionRequest.Status.HELD or deletion.hold_code:
        return FinalizationResult("held", {})
    if deletion.status not in {AccountDeletionRequest.Status.SCHEDULED, AccountDeletionRequest.Status.FAILED}:
        return FinalizationResult("skipped", {})
    if deletion.scheduled_for is None or deletion.scheduled_for > now:
        return FinalizationResult("skipped", {})

    deletion.status = AccountDeletionRequest.Status.PROCESSING
    deletion.processing_started_at = now
    deletion.failure_code = ""
    deletion.save(update_fields=["status", "processing_started_at", "failure_code", "updated_at"])
    user = deletion.user
    counters: dict[str, int] = {}
    if user is not None:
        user_id = user.pk
        user_email = (user.email or "").strip().lower()

        profile = UserProfile.objects.filter(user_id=user_id).first()
        if profile is not None and profile.avatar:
            profile.avatar.delete(save=False)
        counters["profiles_deleted"] = _delete_count(UserProfile.objects.filter(user_id=user_id))
        counters["verification_records_deleted"] = _delete_count(UserEmailVerification.objects.filter(user_id=user_id))
        counters["favorites_deleted"] = _delete_count(PlaceLike.objects.filter(user_id=user_id))
        counters["place_reactions_deleted"] = _delete_count(PlaceReviewReaction.objects.filter(user_id=user_id))
        counters["site_reactions_deleted"] = _delete_count(SiteReviewReaction.objects.filter(user_id=user_id))
        counters["cooldowns_deleted"] = _delete_count(PlaceReviewCooldown.objects.filter(user_id=user_id))
        counters["analytics_events_deleted"] = _delete_count(FunnelEvent.objects.filter(user_id=user_id))

        policy = policy_from_request(deletion)
        place_ids = set(PlaceReview.objects.filter(user_id=user_id).values_list("place_id", flat=True))
        specialist_ids = set(SpecialistReview.objects.filter(user_id=user_id).values_list("specialist_id", flat=True))
        if policy.review_disposition == "delete_all":
            counters["reviews_deleted"] = (
                _delete_count(PlaceReview.objects.filter(user_id=user_id))
                + _delete_count(SiteReview.objects.filter(user_id=user_id))
                + _delete_count(SpecialistReview.objects.filter(user_id=user_id))
            )
            counters["public_reviews_anonymized"] = 0
        else:
            place_public = PlaceReview.objects.filter(user_id=user_id, status=PlaceReview.STATUS_APPROVED)
            site_public = SiteReview.objects.filter(user_id=user_id, status=SiteReview.STATUS_APPROVED)
            specialist_public = SpecialistReview.objects.filter(user_id=user_id, status=SpecialistReview.STATUS_APPROVED)
            counters["public_reviews_anonymized"] = (
                place_public.update(user=None, author_name="", is_anonymous=True, session_key="")
                + site_public.update(user=None, author_name="", is_anonymous=True, session_key="")
                + specialist_public.update(user=None, author_name="")
            )
            counters["reviews_deleted"] = (
                _delete_count(PlaceReview.objects.filter(user_id=user_id))
                + _delete_count(SiteReview.objects.filter(user_id=user_id))
                + _delete_count(SpecialistReview.objects.filter(user_id=user_id))
            )
        sync_place_rating_stats(place_ids)
        sync_specialist_rating_stats(specialist_ids)

        ownership_ids = list(PlaceOwnershipRequest.objects.filter(applicant_id=user_id).values_list("id", flat=True))
        if ownership_ids:
            PlaceOwnershipRequestAudit.objects.filter(ownership_request_id__in=ownership_ids).update(note="")
        counters["ownership_records_anonymized"] = PlaceOwnershipRequest.objects.filter(applicant_id=user_id).update(
            applicant=None,
            note="",
            moderation_note="",
        )
        counters["staff_audit_actor_labels_anonymized"] = StaffRoleAudit.objects.filter(actor_id=user_id).update(
            actor_display=""
        )
        counters["staff_audit_target_labels_anonymized"] = StaffRoleAudit.objects.filter(target_id=user_id).update(
            target_display=""
        )
        counters["team_memberships_deleted"] = _delete_count(
            OwnerTeamMembership.objects.filter(Q(owner_id=user_id) | Q(member_id=user_id) | Q(invited_by_id=user_id))
        )
        invitation_filter = Q(owner_id=user_id) | Q(invited_user_id=user_id) | Q(invited_by_id=user_id)
        if user_email:
            invitation_filter |= Q(email__iexact=user_email)
        counters["team_invitations_deleted"] = _delete_count(OwnerTeamInvitation.objects.filter(invitation_filter))
        counters["places_unlinked"] = Place.objects.filter(owner_id=user_id).update(owner=None)
        counters["events_unlinked"] = Event.objects.filter(owner_id=user_id).update(owner=None)
        counters["specialists_unlinked"] = Specialist.objects.filter(owner_id=user_id).update(owner=None)
        counters["sessions_deleted"] = _delete_user_sessions(user_id)

        deletion.user = None
        deletion.save(update_fields=["user", "updated_at"])
        user.delete()

    deletion.status = AccountDeletionRequest.Status.COMPLETED
    deletion.completed_at = now
    deletion.purge_after = now + timedelta(days=policy_from_request(deletion).audit_retention_days)
    deletion.failure_code = ""
    _clear_code(deletion)
    deletion.save(
        update_fields=[
            "status",
            "completed_at",
            "purge_after",
            "failure_code",
            "confirmation_code_hash",
            "confirmation_expires_at",
            "confirmation_attempts_left",
            "code_purpose",
            "updated_at",
        ]
    )
    _audit(deletion, "deletion_completed", counters)
    return FinalizationResult("completed", counters)


def finalize_account_deletion(request_id: int, *, now=None) -> FinalizationResult:
    now = now or timezone.now()
    try:
        with transaction.atomic():
            deletion = AccountDeletionRequest.objects.select_for_update().select_related("user").get(pk=request_id)
            return _finalize_locked(deletion, now=now)
    except AccountDeletionRequest.DoesNotExist:
        return FinalizationResult("skipped", {})
    except Exception:
        with transaction.atomic():
            deletion = AccountDeletionRequest.objects.select_for_update().filter(pk=request_id).first()
            if deletion is not None and deletion.status != AccountDeletionRequest.Status.COMPLETED:
                deletion.status = AccountDeletionRequest.Status.FAILED
                deletion.failure_code = "processor_error"
                deletion.save(update_fields=["status", "failure_code", "updated_at"])
                try:
                    _audit(deletion, "deletion_failed")
                except AccountDeletionError:
                    # A malformed stored snapshot must not make the retry worker
                    # crash after it has recorded the stable failure state.
                    pass
        return FinalizationResult("failed", {})
