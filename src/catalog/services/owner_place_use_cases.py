from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q
from django.utils.translation import gettext as _

from catalog.models import Place
from catalog.services.staff_roles import is_volunteer
from catalog.services.place_access import (
    PlacePermissionScope,
    direct_place_permissions,
)


@dataclass(slots=True)
class OwnerAccessResult:
    ok: bool
    message: str


# Compatibility alias while owner-named controllers and routes still exist.
OwnerPermissionScope = PlacePermissionScope


def ensure_owner_permission(*, user) -> OwnerAccessResult:
    """Authentication gate; restricted volunteers use their review workspace.

    What a user may do is decided per place by `has_place_permission`. Nothing
    here may consult UserProfile: a public profile role must never widen or
    narrow access to a place.
    """
    if is_volunteer(user):
        return OwnerAccessResult(ok=False, message=_("Используйте раздел «Мои места» в админке."))
    if not user.is_authenticated or not user.is_active:
        return OwnerAccessResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))
    return OwnerAccessResult(ok=True, message="")


def resolve_owner_permission_scopes(*, user, team_repository) -> list[OwnerPermissionScope]:
    """All business readers use the same fresh target/action resolver as writes."""
    from catalog.services.business_team import accessible_place_ids, has_action
    from catalog.services.place_access import PLACE_BUSINESS_ACTIONS, PLACE_PERMISSION_MANAGE_TEAM
    result = []
    for place in Place.objects.filter(pk__in=accessible_place_ids(user=user)):
        permissions = {action for action in PLACE_BUSINESS_ACTIONS | {PLACE_PERMISSION_MANAGE_TEAM}
                       if has_action(user=user, target=place, action=action)}
        from catalog.services.place_access import is_direct_place_manager
        from catalog.models import OwnerTeamMembership
        from catalog.services.business_team import _place_grant_current
        role, source, membership_id = "ORGANIZATION", "organization", None
        if is_direct_place_manager(user=user, place=place):
            role, source = "DIRECT", "direct"
        else:
            for membership in OwnerTeamMembership.objects.filter(place=place, member=user, is_active=True):
                if _place_grant_current(membership, place) and membership.get_permissions():
                    role, source, membership_id = membership.role, "team", membership.pk
                    break
        result.append(OwnerPermissionScope(place_id=place.pk, role=role, permissions=permissions,
                                           source=source, membership_id=membership_id))
    return result


def place_ids_for_permission(scopes: list[OwnerPermissionScope], permission_code: str) -> list[int]:
    return [scope.place_id for scope in scopes if permission_code in scope.permissions]


# Kept temporarily for import compatibility with owner-named controllers.
owner_ids_for_permission = place_ids_for_permission


def build_owner_places_stats(*, places) -> dict:
    place_list = list(places)
    total_places = len(place_list)
    published_places = sum(1 for place in place_list if place.status == Place.STATUS_PUBLISHED and place.is_active)
    draft_places = total_places - published_places
    places_with_coordinates = sum(1 for place in place_list if place.has_coordinates)
    map_ready_places = sum(1 for place in place_list if place.is_map_ready)
    total_reviews = sum(int(place.rating_count or 0) for place in place_list)
    total_likes = sum(int(place.likes_count or 0) for place in place_list)
    weighted_rating_sum = sum(float(place.rating_avg or 0) * int(place.rating_count or 0) for place in place_list)
    avg_rating = (weighted_rating_sum / total_reviews) if total_reviews else 0.0
    return {
        "total_places": total_places,
        "published_places": published_places,
        "draft_places": draft_places,
        "places_with_coordinates": places_with_coordinates,
        "map_ready_places": map_ready_places,
        "total_reviews": total_reviews,
        "total_likes": total_likes,
        "avg_rating": avg_rating,
    }
