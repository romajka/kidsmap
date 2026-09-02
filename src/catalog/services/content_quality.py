from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Exists, OuterRef, Q, QuerySet, TextField, Value
from django.db.models.functions import Concat, Length, Lower, Replace
from django.utils.translation import gettext_lazy as _


PLACE_STATUS_PUBLISHED = "published"
REVIEW_STATUS_APPROVED = "approved"


# Keep presentation labels next to the codes emitted by ``place_quality_check``.
# Both admin and owner flows use these helpers, so a new code cannot silently
# leak its internal identifier into a visitor-facing message.
PLACE_QUALITY_ERROR_LABELS = {
    "missing_name": _("Название: заполните название на азербайджанском."),
    "missing_category": _("Категория: выберите основную категорию."),
    "description_too_short": _("Описание: напишите не менее 120 символов."),
    "test_content": _("Данные: удалите тестовый текст вроде «test», «lorem» или «123456»."),
    "missing_contact": _("Контакты: укажите телефон, сайт или Instagram."),
    "missing_address": _("Адрес: укажите улицу, дом или понятный ориентир."),
    "missing_coordinates": _("Точка на карте: выберите точку вручную или проверьте адрес и обновите координаты."),
    "missing_age": _("Возраст: укажите возраст «от» или «до»."),
    "missing_price": _("Цена: заполните «Цена от» или добавьте тариф."),
    "missing_schedule": _("Расписание: добавьте дни и время работы или текстовое расписание."),
    "missing_photo": _("Фото: загрузите основное фото или хотя бы одно фото в галерею."),
    "events_section_disabled": _("Мероприятия: раздел временных мероприятий отключён на сайте."),
    "temporary_event_expired": _("Мероприятие: дата окончания уже прошла."),
}
UNKNOWN_PLACE_QUALITY_ERROR_LABEL = _("Карточка не проходит проверку качества.")


def place_quality_error_label(code: str) -> str:
    """Return a human-readable quality issue without exposing an internal code."""

    return str(PLACE_QUALITY_ERROR_LABELS.get(code, UNKNOWN_PLACE_QUALITY_ERROR_LABEL))


def place_quality_error_labels(errors) -> list[str]:
    return [place_quality_error_label(code) for code in errors]


def format_place_quality_errors(errors) -> str:
    return ", ".join(place_quality_error_labels(errors))

TEST_CONTENT_TOKENS = ("aaa", "aaaa", "aaaaa", "test", "lorem", "ipsum", "123456", "qwerty", "asdf", "йцукен")
# This deliberately is a finite, portable definition of a token separator.
# Python and both supported databases apply the exact same substitutions below.
# Whitespace is already preserved. Keep punctuation set intentionally small:
# each separator becomes a nested SQL REPLACE, and a long chain over nine text
# fields overflows SQLite's parser before the query can run.
TEST_TOKEN_SEPARATORS = ".,;:!?-"
PLACE_JUNK_FIELDS = (
    "name",
    "name_ru",
    "name_az",
    "name_en",
    "description_ru",
    "description_az",
    "description_en",
    "schedule",
    "address",
)


def contains_test_content(value: str | None) -> bool:
    """Whether a standalone junk token occurs in user-entered text."""

    text = (value or "").lower()
    for separator in TEST_TOKEN_SEPARATORS:
        text = text.replace(separator, " ")
    padded = f" {text} "
    return any(f" {token} " in padded for token in TEST_CONTENT_TOKENS)


def _normalized_junk_expression(field_name: str):
    """Database equivalent of :func:`contains_test_content`.

    ``regex`` word boundaries differ between SQLite and PostgreSQL. Replacing a
    shared set of separators and searching padded text gives both backends the
    same rule without flagging words such as ``contest`` or ``latest``.
    """

    expression = Lower(field_name)
    for separator in TEST_TOKEN_SEPARATORS:
        expression = Replace(expression, Value(separator), Value(" "), output_field=TextField())
    return Concat(Value(" "), expression, Value(" "), output_field=TextField())


def place_junk_q() -> Q:
    """Build the predicate for normalized junk-text annotations."""

    predicate = Q()
    for token in TEST_CONTENT_TOKENS:
        for field in PLACE_JUNK_FIELDS:
            predicate |= Q(**{f"km_junk_{field}__contains": f" {token} "})
    return predicate


def _pricing_plan_price_q(*, prefix: str = "") -> Q:
    """A tariff that represents a public, primary price rather than an add-on."""

    field = lambda name: f"{prefix}{name}"
    return Q(**{field("is_active"): True, field("charge_role"): "primary"}) & (
        Q(**{field("price_kind__in"): ("exact", "free"), field("price__isnull"): False})
        | Q(**{field("price_kind"): "from", field("price_min__isnull"): False})
        | Q(**{field("price_kind"): "range", field("price_min__isnull"): False, field("price_max__isnull"): False})
    )


def _plan_has_public_price(plan) -> bool:
    if not getattr(plan, "is_active", False) or getattr(plan, "charge_role", "primary") != "primary":
        return False
    kind = getattr(plan, "price_kind", "exact")
    if kind in {"exact", "free"}:
        return getattr(plan, "price", None) is not None
    if kind == "from":
        return getattr(plan, "price_min", None) is not None
    if kind == "range":
        return getattr(plan, "price_min", None) is not None and getattr(plan, "price_max", None) is not None
    return False


def _mapping_has_public_price(plan: dict) -> bool:
    if not isinstance(plan, dict) or not plan.get("is_active", True) or plan.get("charge_role", "primary") != "primary":
        return False
    kind = plan.get("price_kind", "exact")
    if kind in {"exact", "free"}:
        return plan.get("price") not in (None, "")
    if kind == "from":
        return plan.get("price_min") not in (None, "")
    if kind == "range":
        return plan.get("price_min") not in (None, "") and plan.get("price_max") not in (None, "")
    return False


def _place_has_pricing_plan_price(place) -> bool:
    """Use prefetched tariff rows when available; support unsaved legacy forms."""

    relation = getattr(place, "pricing_plan_records", None)
    cached_records = getattr(place, "_prefetched_objects_cache", {}).get("pricing_plan_records")
    if cached_records is not None:
        if any(_plan_has_public_price(plan) for plan in cached_records):
            return True
    elif relation is not None and getattr(place, "pk", None):
        if relation.filter(_pricing_plan_price_q()).exists():
            return True

    return any(_mapping_has_public_price(plan) for plan in (getattr(place, "pricing_plans", None) or []))


def _has_price_q() -> Q:
    return (
        Q(price_from__isnull=False)
        | Q(price_to__isnull=False)
        | Q(price_per_lesson__isnull=False)
        | Q(price_per_month__isnull=False)
        | Q(price_per_8_lessons__isnull=False)
    )


def _has_description_q(min_length: int = 120) -> Q:
    return Q(description_ru_len__gte=min_length) | Q(description_az_len__gte=min_length) | Q(description_en_len__gte=min_length)


def _has_pricing_plan_q() -> Exists:
    """Whether a place has an active relational tariff with an actual price."""

    from catalog.models import PricingPlan

    return Exists(
        PricingPlan.objects.filter(place_id=OuterRef("pk")).filter(_pricing_plan_price_q())
    )


def public_place_queryset(queryset: QuerySet) -> QuerySet:
    """Return only places safe enough for public catalog/detail/sitemap usage."""

    qs = queryset.annotate(
        description_ru_len=Length("description_ru"),
        description_az_len=Length("description_az"),
        description_en_len=Length("description_en"),
        **{f"km_junk_{field}": _normalized_junk_expression(field) for field in PLACE_JUNK_FIELDS},
    )
    qs = qs.filter(
        is_active=True,
        deleted_at__isnull=True,
        status=PLACE_STATUS_PUBLISHED,
    )
    qs = qs.exclude(category="").exclude(address="")
    qs = qs.filter(Q(schedule__gt="") | Q(schedule_days__isnull=False)).distinct()
    qs = qs.filter(Q(phone1__gt="") | Q(instagram__gt="") | Q(website__gt=""))
    qs = qs.filter(Q(age_from__isnull=False) | Q(age_to__isnull=False))
    # Legacy scalar price fields and relational tariffs are both public price
    # sources. A place must not disappear merely because its price lives only
    # in pricing_plan_records.
    qs = qs.filter(_has_price_q() | _has_pricing_plan_q())
    qs = qs.filter(_has_description_q())

    from catalog.services.features import is_events_section_enabled
    if not is_events_section_enabled():
        qs = qs.exclude(is_temporary=True)

    # Exclude temporary events that have already ended
    from django.utils import timezone
    qs = qs.exclude(is_temporary=True, temporary_end__lt=timezone.now())

    return qs.exclude(place_junk_q())


def place_catalog_visibility_reasons(place) -> tuple[str, ...]:
    """Return reason codes for why *place* misses the public queryset.

    Keep this in lockstep with ``public_place_queryset``. It is intentionally
    about catalog visibility, not moderation status: the admin needs to explain
    why an otherwise published, active card is absent from the site.
    """

    errors: list[str] = []
    if getattr(place, "category_id", None) in (None, ""):
        errors.append("missing_category")
    if place.address == "":
        errors.append("missing_address")
    if not (place.phone1 > "" or place.instagram > "" or place.website > ""):
        errors.append("missing_contact")
    if place.age_from is None and place.age_to is None:
        errors.append("missing_age")

    has_legacy_price = any(
        value is not None
        for value in (
            place.price_from,
            place.price_to,
            place.price_per_lesson,
            place.price_per_month,
            place.price_per_8_lessons,
        )
    )
    has_pricing_plan = _place_has_pricing_plan_price(place)
    if not has_legacy_price and not has_pricing_plan:
        errors.append("missing_price")

    if not (place.schedule > "" or place.schedule_days.exists()):
        errors.append("missing_schedule")
    if not any(len(getattr(place, field) or "") >= 120 for field in ("description_ru", "description_az", "description_en")):
        errors.append("description_too_short")

    if any(contains_test_content(getattr(place, field)) for field in PLACE_JUNK_FIELDS):
        errors.append("test_content")

    from catalog.services.features import is_events_section_enabled
    if place.is_temporary and not is_events_section_enabled():
        errors.append("events_section_disabled")

    from django.utils import timezone
    if place.is_temporary and place.temporary_end and place.temporary_end < timezone.now():
        errors.append("temporary_event_expired")

    return tuple(errors)


def published_place_queryset(queryset: QuerySet) -> QuerySet:
    """Return places that are published and active, without catalog-quality gating."""

    return queryset.filter(
        is_active=True,
        deleted_at__isnull=True,
        status=PLACE_STATUS_PUBLISHED,
    )


def public_review_filter(prefix: str = "") -> Q:
    """Build the reusable condition for a review that may affect a public rating."""

    def field(name: str) -> str:
        return f"{prefix}{name}"

    valid_q = Q(
        **{
            field("is_approved"): True,
            field("status"): REVIEW_STATUS_APPROVED,
            field("rating__gte"): 1,
            field("rating__lte"): 5,
        }
    )
    # PostgreSQL and SQLite disagree on the regular-expression meaning of
    # ``\b``. Use Django's portable case-insensitive containment lookup so a
    # review that was rejected as test content cannot reappear after a DB move.
    junk_q = Q()
    for token in ("aaa", "test", "lorem", "ipsum", "123456", "qwerty", "asdf", "йцукен"):
        junk_q |= Q(**{field("text__icontains"): token}) | Q(**{field("author_name__icontains"): token})
    return valid_q & ~junk_q


def public_review_queryset(queryset: QuerySet) -> QuerySet:
    """Return only moderated reviews that are approved and have a valid rating."""

    return queryset.filter(public_review_filter())


def approved_review_queryset(queryset: QuerySet) -> QuerySet:
    """Return reviews allowed for reactions and review feeds after moderation."""

    return queryset.filter(
        is_approved=True,
        status=REVIEW_STATUS_APPROVED,
        rating__gte=1,
        rating__lte=5,
    )


@dataclass(frozen=True)
class QualityCheck:
    score: int
    errors: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return self.score >= 70 and not self.errors


def place_quality_check(place) -> QualityCheck:
    errors: list[str] = []
    score = 0

    if (place.name_i18n("az") or place.name or "").strip():
        score += 10
    else:
        errors.append("missing_name")

    if place.category:
        score += 10
    else:
        errors.append("missing_category")

    descriptions = [place.description_ru, place.description_az, place.description_en]
    longest_description = max((len((item or "").strip()) for item in descriptions), default=0)
    if longest_description >= 120:
        score += 20
    else:
        errors.append("description_too_short")

    if any(contains_test_content(getattr(place, field)) for field in PLACE_JUNK_FIELDS):
        errors.append("test_content")

    if place.phone1 or place.instagram or place.website:
        score += 15
    else:
        errors.append("missing_contact")

    if place.address:
        score += 10
    else:
        errors.append("missing_address")

    if place.lat is not None and place.lng is not None:
        score += 10
    else:
        errors.append("missing_coordinates")

    if place.age_from is not None or place.age_to is not None:
        score += 10
    else:
        errors.append("missing_age")

    has_legacy_price = any(
        value is not None
        for value in (
            place.price_from,
            place.price_to,
            place.price_per_lesson,
            place.price_per_month,
            place.price_per_8_lessons,
        )
    )
    has_pricing_plan = _place_has_pricing_plan_price(place)
    if has_legacy_price or has_pricing_plan:
        score += 10
    else:
        errors.append("missing_price")

    if getattr(place, "has_schedule_content", False):
        score += 10
    else:
        errors.append("missing_schedule")

    has_gallery_photo = bool(getattr(place, "pk", None) and place.gallery.exists())
    if place.photo or place.cover_photo or has_gallery_photo:
        score += 5
    else:
        errors.append("missing_photo")

    return QualityCheck(score=min(score, 100), errors=tuple(errors))


def review_quality_check(review) -> QualityCheck:
    text = (review.text or "").strip()
    errors: list[str] = []
    score = 0

    if 1 <= int(review.rating or 0) <= 5:
        score += 30
    else:
        errors.append("missing_rating")

    if len(text) >= 20:
        score += 50
    else:
        errors.append("text_too_short")

    if contains_test_content(text) or contains_test_content(review.author_name):
        errors.append("test_content")
    else:
        score += 20

    return QualityCheck(score=min(score, 100), errors=tuple(errors))
