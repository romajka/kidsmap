from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _
from catalog.services.staff_roles import is_volunteer


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
        }
    ),
    PLACE_ROLE_MODERATOR: frozenset(
        {
            PLACE_PERMISSION_VIEW,
            PLACE_PERMISSION_VIEW_STATS,
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
    return set(PLACE_ROLE_DEFAULT_PERMISSIONS.get(role, ()))


def is_direct_place_manager(*, user, place) -> bool:
    """True for the account that currently owns the place.

    `Place.created_by` is audit history and never a standing grant: it only
    stands in while a card has no owner at all, so that a card someone created
    but nobody owns yet does not become unreachable. The moment an owner is
    set, the creator holds nothing — a handover therefore removes their
    control, and created_by is left untouched as the record of who made it.
    """
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    if place.owner_id is not None:
        return place.owner_id == user.id
    return place.created_by_id == user.id


def direct_place_permissions(*, user, place) -> set[str]:
    if is_volunteer(user):
        return set()
    if not is_direct_place_manager(user=user, place=place):
        return set()
    # These permissions belong to this one listing only. They do not turn the
    # user into a global owner account and deliberately exclude publication.
    return set(PLACE_ROLE_DEFAULT_PERMISSIONS[PLACE_ROLE_MANAGER]) | {PLACE_PERMISSION_MANAGE_TEAM, "place.reviews.reply", "place.reviews.report"}


def staff_has_place_permission(*, user, permission_code: str) -> bool:
    from catalog.services.business_team import platform_has_action
    return platform_has_action(user=user, action=permission_code)


def organization_place_permissions(*, user, place) -> set[str]:
    if is_volunteer(user) or not getattr(user,'is_active',False) or not getattr(user,'is_authenticated',False):
        return set()
    from catalog.models import Place
    from catalog.services.organization_ownership import affiliation_current
    current=Place.objects.select_related('organization').filter(pk=place.pk,deleted_at__isnull=True).first()
    if current is None or current.organization_id is None:
        return set()
    org=current.organization
    if org.owner_id!=user.pk or current.organization_relationship_kind!='business' or not affiliation_current(current,org):
        return set()
    return {PLACE_PERMISSION_VIEW, PLACE_PERMISSION_EDIT, PLACE_PERMISSION_VIEW_STATS}


def has_place_permission(*, user, place, permission_code: str) -> bool:
    from catalog.services.business_team import has_action
    return has_action(user=user, target=place, action=permission_code)


PLACE_BUSINESS_ACTIONS = frozenset({"place.view", "place.edit", "place.stats.view", "place.reviews.reply", "place.reviews.report"})
ORGANIZATION_BUSINESS_ACTIONS = frozenset({"organization.view", "organization.edit", "program.manage", "branch.create"})
GRANTABLE_ACTIONS = PLACE_BUSINESS_ACTIONS | ORGANIZATION_BUSINESS_ACTIONS


def validated_business_actions(value, *, target_type="organization"):
    allowed = PLACE_BUSINESS_ACTIONS if target_type == "place" else GRANTABLE_ACTIONS
    if not isinstance(value, list) or any(not isinstance(item, str) or item not in allowed for item in value):
        return set()
    return set(value)


def permission_configuration():
    return {"grantable_actions": sorted(GRANTABLE_ACTIONS), "place_actions": sorted(PLACE_BUSINESS_ACTIONS),
            "organization_actions": sorted(ORGANIZATION_BUSINESS_ACTIONS), "scopes": ["selected_places", "all_network"],
            "presets": {key: sorted(value) for key, value in PLACE_ROLE_DEFAULT_PERMISSIONS.items()},
            "owner_only": ["place.team.manage", "organization.team.manage", "ownership.transfer"],
            "platform_only": ["place.publish", "place.reviews.moderate"]}


@dataclass(slots=True)
class PlacePermissionScope:
    place_id: int
    role: str
    permissions: set[str]
    source: str
    membership_id: int | None = None
