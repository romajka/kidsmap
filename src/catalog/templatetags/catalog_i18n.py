import re

from django import template
from django.utils.translation import get_language, pgettext


register = template.Library()


@register.simple_tag
def localized_content(obj, field):
    from catalog.services.localized_content import localized_content as display
    return display(obj, field)


@register.simple_tag
def responsive_image(image):
    from catalog.services.responsive_images import responsive_image as image_urls
    return image_urls(image)


def _plural_form(count: int, language_code: str) -> str:
    if language_code == "ru":
        remainder_10 = count % 10
        remainder_100 = count % 100
        if remainder_10 == 1 and remainder_100 != 11:
            return "one"
        if 2 <= remainder_10 <= 4 and not 12 <= remainder_100 <= 14:
            return "few"
        return "many"
    return "one" if count == 1 else "many"


@register.filter
def review_count(value) -> str:
    """Return a localized place-review count with correct Russian declension."""
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        count = 0

    language_code = (get_language() or "az").split("-", 1)[0]
    plural_form = _plural_form(count, language_code)
    if plural_form == "one":
        message = pgettext("review count: one", "%(count)s reviews")
    elif plural_form == "few":
        message = pgettext("review count: few", "%(count)s reviews")
    else:
        message = pgettext("review count: many", "%(count)s reviews")
    return message % {"count": count}


@register.filter
def tariff_count(value) -> str:
    """Return a localized tariff count with correct Russian declension."""
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        count = 0

    language_code = (get_language() or "az").split("-", 1)[0]
    plural_form = _plural_form(count, language_code)
    if plural_form == "one":
        message = pgettext("tariff count: one", "%(count)s tariffs")
    elif plural_form == "few":
        message = pgettext("tariff count: few", "%(count)s tariffs")
    else:
        message = pgettext("tariff count: many", "%(count)s tariffs")
    return message % {"count": count}


@register.filter
def favorite_count(value) -> str:
    """Return concise social-proof copy with correct Russian declension."""
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        count = 0

    language_code = (get_language() or "az").split("-", 1)[0]
    if language_code == "az":
        return f"{count} istifadəçi saxlayıb"
    if language_code == "en":
        noun = "user" if count == 1 else "users"
        return f"Saved by {count} {noun}"

    plural_form = _plural_form(count, "ru")
    if plural_form == "one":
        return f"Сохранил {count} пользователь"
    if plural_form == "few":
        return f"Сохранили {count} пользователя"
    return f"Сохранили {count} пользователей"


@register.simple_tag(takes_context=True)
def public_presentation(context, obj):
    from catalog.services.public_presentation import present
    request = context.get('request')
    cached = getattr(obj, '_card_presentation', None)
    return cached if cached is not None else present(obj, getattr(request, 'LANGUAGE_CODE', None) or get_language())


@register.filter
def parent_review_label(value) -> str:
    """Label paired with the separate homepage review count."""
    try:
        count = int(value or 0)
    except (TypeError, ValueError):
        count = 0
    language = (get_language() or 'az').split('-', 1)[0]
    if language == 'az':
        return 'valideyn rəyi'
    if language == 'en':
        return 'parent review' if count == 1 else 'parent reviews'
    form = _plural_form(count, 'ru')
    return {'one': 'отзыв родителей', 'few': 'отзыва родителей', 'many': 'отзывов родителей'}[form]


@register.filter
def clean_public_note(value) -> str:
    """Keep visiting information separate from photo credits and internal markers."""
    return _public_note_parts(value)[0]


def _public_note_parts(value):
    notes, credits = [], []
    for line in str(value or "").strip().splitlines():
        stripped = line.strip()
        if stripped.startswith("seed:") or stripped.casefold().rstrip(".") in {
            "проверено по источнику", "verified against source", "mənbə üzrə yoxlanılıb",
        }:
            continue
        is_credit = bool(re.match(
            r"^(?:(?:архивные\s+)?фото(?:графии)?(?:[ ,][^:\n]{0,80})?|"
            r"автор(?:\s+фото)?|источник(?:\s+фото)?|лицензия|CC\s+BY(?:-[A-Z]+)*[^:\n]*|"
            r"(?:(?:archive|archival)\s+)?photos?(?:[ ,][^:\n]{0,80})?|"
            r"credits?|author|source|licen[cs]e|"
            r"(?:arxiv\s+)?foto(?:şəkillər)?(?:[ ,][^:\n]{0,80})?|şəkillər|müəllif|mənbə|lisenziya)\s*:", stripped, re.IGNORECASE
        )) or bool(re.search(r"https?://(?:commons\.wikimedia\.org|creativecommons\.org)/", stripped))
        (credits if is_credit else notes).append(line)
    return "\n".join(notes).strip(), "\n".join(credits).strip()


@register.simple_tag
def public_photo_credits(place):
    language = (get_language() or "az").split("-")[0]
    credits = []
    for field in ("extra_conditions_i18n", "additional_info_i18n"):
        # Names and license links remain available if a note's translation is
        # missing; visiting text still follows the normal localization policy.
        for code in dict.fromkeys((language, "az", "ru", "en")):
            value = _public_note_parts(getattr(place, field)(code))[1]
            if value:
                credits.append(value)
                break
    return "\n".join(dict.fromkeys(credits))


@register.simple_tag
def age_range(low, high):
    from catalog.services.age_display import format_age_range
    return format_age_range(low, high)
