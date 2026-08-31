from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.models import PlaceReview, SiteReview
from catalog.services.review_moderation import moderate_review_content
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


def _author_name_from_account(user) -> str:
    if not getattr(user, "is_authenticated", False):
        return ""

    candidates = (
        user.get_full_name(),
        user.get_username(),
        getattr(user, "email", ""),
    )
    for value in candidates:
        value = (value or "").strip()
        if value:
            return value[:80]
    return str(_("Гость"))


def _build_review_payload(
    request,
    *,
    require_text: bool = False,
    use_account_author: bool = False,
) -> tuple[ReviewPayload | None, str]:
    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()
    if use_account_author:
        author_name = _author_name_from_account(request.user)
    else:
        author_name = (request.POST.get("author_name") or "").strip()

    if not rating_raw:
        return None, _("Выберите оценку от 1 до 5, чтобы отправить отзыв.")

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return None, _("Оценка должна быть числом от 1 до 5. Выберите нужное количество звезд.")

    if rating < 1 or rating > 5:
        return None, _("Оценка вне диапазона. Укажите значение от 1 до 5.")

    if not author_name:
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

    payload, error_message = _build_review_payload(
        request,
        require_text=True,
        use_account_author=request.user.is_authenticated,
    )
    if payload is None:
        return ReviewSubmissionResult(
            ok=False,
            created=False,
            message=error_message,
        )

    moderated = moderate_review_content(author_name=payload.author_name, text=payload.text)

    review_obj, created = create_or_update_review(
        place,
        request,
        rating=payload.rating,
        review_text=moderated.text,
        author_name=moderated.author_name,
        is_anonymous=False,
        contains_profanity=moderated.contains_profanity,
    )
    review_obj.status = PlaceReview.STATUS_PENDING
    review_obj.is_approved = False
    review_obj.rejection_reason = ""
    review_obj.save(update_fields=["status", "is_approved", "rejection_reason", "updated_at"])

    message = _("Ваш отзыв отправлен на модерацию и будет опубликован после проверки.")
    if moderated.contains_profanity:
        message = f"{message} {_('Нецензурные слова были автоматически скрыты.')}"

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

    moderated = moderate_review_content(author_name=payload.author_name, text=payload.text)

    session_key = ensure_session_key(request) or ""
    defaults = {
        "rating": payload.rating,
        "text": moderated.text,
        "author_name": moderated.author_name,
        "is_anonymous": False,
        "contains_profanity": moderated.contains_profanity,
        "is_approved": False,
        "status": SiteReview.STATUS_PENDING,
        "rejection_reason": "",
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

    message = _("Ваш отзыв отправлен на модерацию и будет опубликован после проверки.")
    if moderated.contains_profanity:
        message = f"{message} {_('Нецензурные слова были автоматически скрыты.')}"

    return ReviewSubmissionResult(ok=True, created=created, message=message)
