from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q
from django.utils.translation import gettext as _

from catalog.models import Place
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
    """Authentication gate only.

    What a user may do is decided per place by `has_place_permission`. Nothing
    here may consult UserProfile: a public profile role must never widen or
    narrow access to a place.
    """
    if not user.is_authenticated:
        return OwnerAccessResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))
    return OwnerAccessResult(ok=True, message="")


def resolve_owner_permission_scopes(*, user, team_repository) -> list[OwnerPermissionScope]:
    """Return permissions scoped to individual places, never to a user role."""
    if not user.is_authenticated:
        return []

    scopes: dict[int, OwnerPermissionScope] = {}
    # Ownership decides; created_by only stands in while nobody owns the card.
    direct_places = Place.objects.filter(
        Q(owner=user) | Q(owner__isnull=True, created_by=user),
        deleted_at__isnull=True,
    ).distinct()
    for place in direct_places:
        scopes[place.id] = OwnerPermissionScope(
            place_id=place.id,
            role="DIRECT",
            permissions=direct_place_permissions(user=user, place=place),
            source="direct",
        )

    for membership in team_repository.list_active_memberships_for_user(user=user):
        if membership.place_id is None:
            # Owner-wide memberships predate place-scoped access. They remain
            # stored for migration, but no longer grant access to every place.
            continue
        permissions = membership.get_permissions()
        existing = scopes.get(membership.place_id)
        if existing is None:
            scopes[membership.place_id] = OwnerPermissionScope(
                place_id=membership.place_id,
                role=membership.role,
                permissions=set(permissions),
                source="team",
                membership_id=membership.id,
            )
            continue
        existing.permissions.update(permissions)
        if existing.source != "direct":
            existing.role = membership.role
            existing.membership_id = membership.id

    return list(scopes.values())


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
