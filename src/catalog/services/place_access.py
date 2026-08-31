from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _


PLACE_ROLE_MANAGER = "MANAGER"
PLACE_ROLE_MODERATOR = "MODERATOR"
PLACE_ROLE_EDITOR = "EDITOR"
PLACE_ROLE_CHOICES = (
    (PLACE_ROLE_MANAGER, _("Менеджер")),
    (PLACE_ROLE_MODERATOR, _("Модератор")),
    (PLACE_ROLE_EDITOR, _("Редактор")),
)

PLACE_PERMISSION_VIEW = "place.view"
PLACE_PERMISSION_EDIT = "place.edit"
PLACE_PERMISSION_VIEW_STATS = "place.stats.view"
PLACE_PERMISSION_MODERATE_REVIEWS = "place.reviews.moderate"
PLACE_PERMISSION_MANAGE_TEAM = "place.team.manage"
PLACE_PERMISSION_PUBLISH = "place.publish"

PLACE_ROLE_DEFAULT_PERMISSIONS = {
    PLACE_ROLE_MANAGER: frozenset(
        {
            PLACE_PERMISSION_VIEW,
            PLACE_PERMISSION_EDIT,
            PLACE_PERMISSION_VIEW_STATS,
            PLACE_PERMISSION_MODERATE_REVIEWS,
            PLACE_PERMISSION_MANAGE_TEAM,
        }
    ),
    PLACE_ROLE_MODERATOR: frozenset(
        {
            PLACE_PERMISSION_VIEW,
            PLACE_PERMISSION_VIEW_STATS,
            PLACE_PERMISSION_MODERATE_REVIEWS,
        }
    ),
    PLACE_ROLE_EDITOR: frozenset(
        {
            PLACE_PERMISSION_VIEW,
            PLACE_PERMISSION_EDIT,
        }
    ),
}


def permissions_for_role(role: str) -> set[str]:
    return set(PLACE_ROLE_DEFAULT_PERMISSIONS.get(role, PLACE_ROLE_DEFAULT_PERMISSIONS[PLACE_ROLE_EDITOR]))


def is_direct_place_manager(*, user, place) -> bool:
    """True for the account that currently owns the place.

    `Place.created_by` is audit history and never a standing grant: it only
    stands in while a card has no owner at all, so that a card someone created
    but nobody owns yet does not become unreachable. The moment an owner is
    set, the creator holds nothing — a handover therefore removes their
    control, and created_by is left untouched as the record of who made it.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if place.owner_id is not None:
        return place.owner_id == user.id
    return place.created_by_id == user.id


def direct_place_permissions(*, user, place) -> set[str]:
    if not is_direct_place_manager(user=user, place=place):
        return set()
    # These permissions belong to this one listing only. They do not turn the
    # user into a global owner account and deliberately exclude publication.
    return set(PLACE_ROLE_DEFAULT_PERMISSIONS[PLACE_ROLE_MANAGER])


def staff_has_place_permission(*, user, permission_code: str) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    if permission_code == PLACE_PERMISSION_PUBLISH:
        return user.has_perm("catalog.change_place")
    return False


def has_place_permission(*, user, place, permission_code: str) -> bool:
    if staff_has_place_permission(user=user, permission_code=permission_code):
        return True
    if permission_code in direct_place_permissions(user=user, place=place):
        return True
    for membership in place.team_memberships.filter(member=user, is_active=True):
        if permission_code in membership.get_permissions():
            return True
    return False


@dataclass(slots=True)
class PlacePermissionScope:
    place_id: int
    role: str
    permissions: set[str]
    source: str
    membership_id: int | None = None
