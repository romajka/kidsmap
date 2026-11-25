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


def is_organizations_section_enabled() -> bool:
    from catalog.models.site import SiteSettings
    try:
        return bool(getattr(SiteSettings.get_solo(), "organizations_section_enabled", False))
    except (OperationalError, ProgrammingError):
        return False


def has_public_organizations() -> bool:
    """At least one organization a visitor can actually open."""
    from catalog.models import Organization
    try:
        return Organization.objects.filter(status="published", approved_at__isnull=False,
                                           archived_at__isnull=True).exists()
    except (OperationalError, ProgrammingError):
        return False


def is_organizations_directory_listed() -> bool:
    """Promote the directory (menus, sitemap, indexing) only once it has content.

    The section itself stays reachable, including the owner registration entry.
    """
    return is_organizations_section_enabled() and has_public_organizations()


def require_organizations_section_enabled():
    if not is_organizations_section_enabled():
        raise Http404()
