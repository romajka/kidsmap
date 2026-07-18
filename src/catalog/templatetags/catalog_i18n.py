from django import template
from django.utils.translation import get_language, pgettext

from catalog.services.images import image_variant_url


register = template.Library()


@register.filter
def image_variant(file_field, variant: str) -> str:
    """Return an optimized derivative URL, falling back to the original."""
    return image_variant_url(file_field, variant)


def _review_plural_form(count: int, language_code: str) -> str:
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
    plural_form = _review_plural_form(count, language_code)
    if plural_form == "one":
        message = pgettext("review count: one", "%(count)s reviews")
    elif plural_form == "few":
        message = pgettext("review count: few", "%(count)s reviews")
    else:
        message = pgettext("review count: many", "%(count)s reviews")
    return message % {"count": count}
