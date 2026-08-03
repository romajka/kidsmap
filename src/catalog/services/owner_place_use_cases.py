from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from catalog.models import OwnerTeamMembership, Place, UserProfile


@dataclass(slots=True)
class OwnerAccessResult:
    ok: bool
    message: str
    profile: UserProfile | None = None


@dataclass(slots=True)
class OwnerPermissionScope:
    owner_id: int
    role: str
    permissions: set[str]
    source: str
    membership_id: int | None = None


def ensure_owner_permission(
    *,
    user,
    profile_repository,
    permission_code: str | None = None,
) -> OwnerAccessResult:
    if not user.is_authenticated:
        return OwnerAccessResult(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))

    profile = profile_repository.get_or_create_for_user(user)
    basic_permissions = {
        UserProfile.OWNER_PERMISSION_VIEW_PLACES,
        UserProfile.OWNER_PERMISSION_EDIT_PLACES,
        UserProfile.OWNER_PERMISSION_VIEW_STATS,
    }
    if permission_code in basic_permissions:
        # A regular account may manage cards it created. Accounts explicitly
        # configured as owner-team roles must still respect that role's grants.
        if profile.role != UserProfile.ROLE_OWNER or profile.has_owner_permission(permission_code):
            return OwnerAccessResult(ok=True, message="", profile=profile)
        return OwnerAccessResult(
            ok=False,
            message=_("Недостаточно прав для редактирования карточек."),
            profile=profile,
        )

    if permission_code and permission_code not in basic_permissions and not profile.has_owner_permission(permission_code):
        return OwnerAccessResult(
            ok=False,
            message=_(
                "Недостаточно прав для выполнения этого действия. "
                "Обратитесь к администратору, чтобы изменить доступ."
            ),
            profile=profile,
        )

    return OwnerAccessResult(ok=True, message="", profile=profile)


def resolve_owner_permission_scopes(
    *,
    user,
    profile_repository,
    team_repository,
) -> list[OwnerPermissionScope]:
    if not user.is_authenticated:
        return []

    scopes_map: dict[int, OwnerPermissionScope] = {}

    profile = profile_repository.get_or_create_for_user(user)
    if profile.role == UserProfile.ROLE_OWNER:
        scopes_map[user.id] = OwnerPermissionScope(
            owner_id=user.id,
            role=profile.owner_role,
            permissions=set(profile.get_owner_permissions()),
            source="self",
        )

    memberships = team_repository.list_active_memberships_for_user(user=user)
    for membership in memberships:
        member_permissions = membership.get_permissions()
        existing = scopes_map.get(membership.owner_id)
        if existing is None:
            scopes_map[membership.owner_id] = OwnerPermissionScope(
                owner_id=membership.owner_id,
                role=membership.role,
                permissions=set(member_permissions),
                source="team",
                membership_id=membership.id,
            )
            continue

        existing.permissions.update(member_permissions)
        if existing.source != "self":
            existing.role = membership.role
            existing.membership_id = membership.id

    return list(scopes_map.values())


def owner_ids_for_permission(scopes: list[OwnerPermissionScope], permission_code: str) -> list[int]:
    return [scope.owner_id for scope in scopes if permission_code in scope.permissions]


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
