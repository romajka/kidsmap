from django.db.utils import OperationalError, ProgrammingError
from django.http import Http404

def is_specialists_section_enabled() -> bool:
    from catalog.models.site import SiteSettings
    try:
        # Defaulting to False on DB errors or missing settings as requested.
        return bool(getattr(SiteSettings.get_solo(), "specialists_section_enabled", False))
    except (OperationalError, ProgrammingError):
        return False

def require_specialists_section_enabled():
    if not is_specialists_section_enabled():
        raise Http404()


def is_events_section_enabled() -> bool:
    from catalog.models.site import SiteSettings
    try:
        return bool(getattr(SiteSettings.get_solo(), "events_section_enabled", False))
    except (OperationalError, ProgrammingError):
        return False


def require_events_section_enabled():
    if not is_events_section_enabled():
        raise Http404()
