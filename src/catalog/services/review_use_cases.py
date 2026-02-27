from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.models import SiteReview
from catalog.services.reactions import create_or_update_review, ensure_session_key


@dataclass(slots=True)
class ReviewSubmissionResult:
    ok: bool
    created: bool
    message: str


@dataclass(slots=True)
class ReviewPayload:
    rating: int
    text: str
    author_name: str
    is_anonymous: bool


def _build_review_payload(request) -> ReviewPayload | None:
    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()
    author_name = (request.POST.get("author_name") or "").strip()
    is_anonymous = request.POST.get("is_anonymous") == "1"

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return None

    if rating < 1 or rating > 5:
        return None

    if is_anonymous:
        author_name = ""
    elif not author_name:
        author_name = _("Гость")

    return ReviewPayload(
        rating=rating,
        text=review_text,
        author_name=author_name,
        is_anonymous=is_anonymous,
    )


def submit_place_review(*, request, place, require_auth: bool) -> ReviewSubmissionResult:
    if require_auth and not request.user.is_authenticated:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=_("Оставлять отзывы могут только зарегистрированные пользователи."),
        )

    payload = _build_review_payload(request)
    if payload is None:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=_("Пожалуйста, выберите оценку от 1 до 5."),
        )

    _, created = create_or_update_review(
        place,
        request,
        rating=payload.rating,
        review_text=payload.text,
        author_name=payload.author_name,
        is_anonymous=payload.is_anonymous,
    )

    if request.user.is_authenticated and not created:
        message = _("Спасибо! Ваш отзыв обновлен.")
    else:
        message = _("Спасибо! Ваш отзыв добавлен.")

    return ReviewSubmissionResult(ok=True, created=created, message=message)


def submit_site_review(*, request, require_auth: bool) -> ReviewSubmissionResult:
    if require_auth and not request.user.is_authenticated:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=_("Оставлять отзывы могут только зарегистрированные пользователи."),
        )

    payload = _build_review_payload(request)
    if payload is None:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=_("Пожалуйста, выберите оценку от 1 до 5."),
        )

    session_key = ensure_session_key(request) or ""
    defaults = {
        "rating": payload.rating,
        "text": payload.text,
        "author_name": payload.author_name,
        "is_anonymous": payload.is_anonymous,
        "is_approved": True,
        "session_key": session_key,
    }

    if request.user.is_authenticated:
        _, created = SiteReview.objects.update_or_create(
            user=request.user,
            defaults=defaults,
        )
    else:
        _, created = SiteReview.objects.update_or_create(
            user__isnull=True,
            session_key=session_key,
            defaults=defaults,
        )

    if request.user.is_authenticated and not created:
        message = _("Спасибо! Ваша оценка сайта обновлена.")
    else:
        message = _("Спасибо! Ваша оценка сайта сохранена.")

    return ReviewSubmissionResult(ok=True, created=created, message=message)
