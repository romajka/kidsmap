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


def _build_review_payload(request, *, require_text: bool = False) -> tuple[ReviewPayload | None, str]:
    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()
    author_name = (request.POST.get("author_name") or "").strip()
    is_anonymous = request.POST.get("is_anonymous") == "1"

    if not rating_raw:
        return None, _("Выберите оценку от 1 до 5, чтобы отправить отзыв.")

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return None, _("Оценка должна быть числом от 1 до 5. Выберите нужное количество звезд.")

    if rating < 1 or rating > 5:
        return None, _("Оценка вне диапазона. Укажите значение от 1 до 5.")

    if is_anonymous:
        author_name = ""
    elif not author_name:
        author_name = _("Гость")
    elif len(author_name) > 80:
        return None, _("Имя слишком длинное. Используйте до 80 символов.")

    if require_text and not review_text:
        return None, _("Добавьте текст отзыва, чтобы другим пользователям было полезно ваше мнение.")
    if review_text and len(review_text) > 5000:
        return None, _("Текст отзыва слишком длинный. Сократите его до 5000 символов.")

    return (
        ReviewPayload(
            rating=rating,
            text=review_text,
            author_name=author_name,
            is_anonymous=is_anonymous,
        ),
        "",
    )


def submit_place_review(*, request, place, require_auth: bool) -> ReviewSubmissionResult:
    if require_auth and not request.user.is_authenticated:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=_("Оставлять отзывы могут только зарегистрированные пользователи."),
        )

    payload, error_message = _build_review_payload(request, require_text=True)
    if payload is None:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=error_message,
        )

    review_obj, created = create_or_update_review(
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

    payload, error_message = _build_review_payload(request, require_text=False)
    if payload is None:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=error_message,
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
        site_review_obj, created = SiteReview.objects.update_or_create(
            user=request.user,
            defaults=defaults,
        )
    else:
        site_review_obj, created = SiteReview.objects.update_or_create(
            user__isnull=True,
            session_key=session_key,
            defaults=defaults,
        )

    if request.user.is_authenticated and not created:
        message = _("Спасибо! Ваша оценка сайта обновлена.")
    else:
        message = _("Спасибо! Ваша оценка сайта сохранена.")

    return ReviewSubmissionResult(ok=True, created=created, message=message)
