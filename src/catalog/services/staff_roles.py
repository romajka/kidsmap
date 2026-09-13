"""Canonical staff roles backed by Django groups and direct permissions."""

from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _

VOLUNTEER_GROUP = "KidsMap Volunteers"

ADMIN_ROLE_SUPERADMIN = "superadmin"
ADMIN_ROLE_MODERATOR = "moderator"
ADMIN_ROLE_CONTENT_MANAGER = "content_manager"
ADMIN_ROLE_VOLUNTEER = "volunteer"
ADMIN_ROLE_STAFF = "staff"

ADMIN_ROLE_PERMISSION_PRESETS = {
    ADMIN_ROLE_MODERATOR: {
        "view_place",
        "view_event",
        "view_placereview",
        "change_placereview",
        "view_sitereview",
        "change_sitereview",
        "view_placeownershiprequest",
        "change_placeownershiprequest",
    },
    ADMIN_ROLE_CONTENT_MANAGER: {
        "view_place",
        "add_place",
        "change_place",
        "view_event",
        "add_event",
        "change_event",
        "view_category",
        "add_category",
        "change_category",
        "view_subcategory",
        "add_subcategory",
        "change_subcategory",
        "view_placephoto",
        "add_placephoto",
        "change_placephoto",
        "delete_placephoto",
        "view_sitegalleryimage",
        "add_sitegalleryimage",
        "change_sitegalleryimage",
        "delete_sitegalleryimage",
        "view_sitesettings",
        "change_sitesettings",
        "view_sitebrandingsettings",
        "change_sitebrandingsettings",
        "view_siteaboutsettings",
        "change_siteaboutsettings",
        "view_sitecontactssettings",
        "change_sitecontactssettings",
        "view_sitefootersettings",
        "change_sitefootersettings",
        "view_siteemptystatesettings",
        "change_siteemptystatesettings",
    },
}

ADMIN_ROLE_CHOICES = (
    (ADMIN_ROLE_VOLUNTEER, _("Волонтёр — только свои места, публикация после проверки")),
    (ADMIN_ROLE_MODERATOR, _("Модератор")),
    (ADMIN_ROLE_CONTENT_MANAGER, _("Контент-менеджер")),
)

ADMIN_ROLE_LABELS = {
    ADMIN_ROLE_SUPERADMIN: _("Суперадмин"),
    ADMIN_ROLE_VOLUNTEER: _("Волонтёр"),
    ADMIN_ROLE_MODERATOR: _("Модератор"),
    ADMIN_ROLE_CONTENT_MANAGER: _("Контент-менеджер"),
    ADMIN_ROLE_STAFF: _("Сотрудник"),
}


def is_volunteer(user):
    if not getattr(user, "is_authenticated", False) or user.is_superuser:
        return False
    cached = getattr(user, "_kidsmap_volunteer_role", None)
    if cached is not None:
        return cached
    return user.groups.filter(name=VOLUNTEER_GROUP).exists()


def can_use_volunteer_workspace(user):
    return bool(user.is_authenticated and user.is_active and user.is_staff and is_volunteer(user))


def role_permissions(role):
    return Permission.objects.filter(
        content_type__app_label="catalog",
        codename__in=ADMIN_ROLE_PERMISSION_PRESETS.get(role, set()),
    )


def current_staff_role(user):
    if user.is_superuser:
        return ADMIN_ROLE_SUPERADMIN
    if is_volunteer(user):
        return ADMIN_ROLE_VOLUNTEER
    direct_permissions = set(user.user_permissions.filter(
        content_type__app_label="catalog",
    ).values_list("codename", flat=True))
    for role in (ADMIN_ROLE_MODERATOR, ADMIN_ROLE_CONTENT_MANAGER):
        if direct_permissions == ADMIN_ROLE_PERMISSION_PRESETS[role]:
            return role
    return ADMIN_ROLE_STAFF
