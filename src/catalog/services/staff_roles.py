"""Staff policy markers backed by Django's existing groups, not a second RBAC."""

VOLUNTEER_GROUP = "KidsMap Volunteers"


def is_volunteer(user):
    if not getattr(user, "is_authenticated", False) or user.is_superuser:
        return False
    cached = getattr(user, "_kidsmap_volunteer_role", None)
    if cached is not None:
        return cached
    return user.groups.filter(name=VOLUNTEER_GROUP).exists()


def can_use_volunteer_workspace(user):
    return bool(user.is_authenticated and user.is_active and user.is_staff and is_volunteer(user))
