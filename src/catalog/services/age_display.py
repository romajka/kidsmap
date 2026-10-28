"""A shared display contract for numeric public age bounds."""
from django.utils.translation import get_language


def format_age_range(low, high, language=None):
    language = (language or get_language() or "az").split("-")[0]
    if low is not None and high is not None:
        return f"{low}–{high}"
    if low is not None:
        return f"{low}+"
    if high is not None:
        return {"az": f"ən çox {high}", "en": f"up to {high}"}.get(language, f"до {high}")
    return ""
