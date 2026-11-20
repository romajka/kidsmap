from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.models import PlaceReview, Specialist, SpecialistReview
from catalog.services.account_review_feeds import review_page, written_queries
from catalog.services.business_team import accessible_place_ids
from catalog.services.features import is_specialists_section_enabled
from catalog.services.moderation_sla import submission_message
from catalog.services.public_review_replies import published_target_reviews, with_answer_status


@dataclass(slots=True)
class OwnerReviewsActionResult:
    ok: bool
    message: str


class OwnerReviewsController:
    @classmethod
    def build_default(cls):
        return cls()

    def build_context(self, *, request):
        user = request.user
        if not user.is_authenticated or not user.is_active:
            return {}, OwnerReviewsActionResult(False, _("Для доступа войдите в аккаунт и повторите действие."))

        reply_ids = set(accessible_place_ids(user=user, action="place.reviews.reply"))
        report_ids = set(accessible_place_ids(user=user, action="place.reviews.report"))
        place_ids = reply_ids | report_ids
        specialists_enabled = is_specialists_section_enabled()
        specialist_ids = set()
        if specialists_enabled:
            specialist_ids = set(Specialist.objects.filter(
                verified_person_user=user, person_verified_at__isnull=False,
                is_active=True, status="published",
            ).values_list("pk", flat=True))
        has_inbox = bool(place_ids or specialist_ids)
        specialist_filter = request.GET.get("specialist")
        if specialist_filter:
            place_ids = set()
            specialist_ids = {pk for pk in specialist_ids if str(pk) == specialist_filter}
        incoming = {
            "place": with_answer_status(published_target_reviews("place").filter(place_id__in=place_ids), "place"),
            "specialist": with_answer_status(published_target_reviews("specialist").filter(specialist_id__in=specialist_ids), "specialist"),
        }
        pending = {"is_current": True, "candidate_revision__status": "pending"}
        pending_count = PlaceReview.objects.filter(
            **pending, place_id__in=place_ids, place__status="published", place__is_active=True,
            place__deleted_at__isnull=True,
        ).count() + SpecialistReview.objects.filter(**pending, specialist_id__in=specialist_ids).count()
        unanswered = request.GET.get("filter") == "unanswered"
        approved_count = sum(rows.count() for rows in incoming.values()) if unanswered else None
        if unanswered:
            incoming = {kind: rows.filter(has_answer=False) for kind, rows in incoming.items()}
        page = review_page(incoming, request.GET.get("page"), by_publication=True)
        for review in page:
            review.can_reply = review.review_kind == "specialist" or review.place_id in reply_ids
            review.can_report = review.review_kind == "specialist" or review.place_id in report_ids

        written = review_page(written_queries(user), request.GET.get("written_page"))
        for review in written:
            target = review.target
            available = target.is_active and target.status == "published"
            review.target_available = available and (
                target.deleted_at is None if review.review_kind == "place" else specialists_enabled
            )
        return {
            "can_moderate_reviews": has_inbox,
            "owner_reviews_pending_count": pending_count,
            "owner_reviews_approved_count": page.paginator.count if approved_count is None else approved_count,
            "specialist_filter": specialist_filter,
            "owner_reviews": page, "unanswered": unanswered,
            "user_written_reviews": written, "user_reviews_count": written.paginator.count,
            "review_moderation_sla_message": submission_message("review"),
        }, OwnerReviewsActionResult(True, "")

    def set_review_approval(self, *, request, review_id: int, is_approved: bool):
        return OwnerReviewsActionResult(False, _("Отзывы проверяет KidsMap. Бизнес может ответить или пожаловаться."))
