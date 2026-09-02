from django import template
from django.utils.translation import get_language, pgettext


register = template.Library()


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
