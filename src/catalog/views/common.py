"""Shared view helpers and the controller instances used by all views."""

from urllib.parse import urlencode
from uuid import uuid4
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme
from ..controllers.account_controller import AccountController
from ..controllers.auth_controller import AuthController
from ..controllers.engagement_controller import EngagementController
from ..controllers.home_controller import HomeController
from ..controllers.owner_places_controller import OwnerPlacesController
from ..controllers.owner_reviews_controller import OwnerReviewsController
from ..controllers.owner_team_controller import OwnerTeamController
from ..controllers.ownership_controller import OwnershipController
from ..controllers.place_controller import PlaceController
from ..controllers.place_reviews_controller import PlaceReviewsController
from ..controllers.seo_controller import SeoController
from ..controllers.site_reviews_controller import SiteReviewsController
from ..controllers.tracking_controller import TrackingController
from ..models import Place
from ..services.reactions import ensure_session_key
from ..services.auth_redirects import resolve_safe_next_url
from ..services.place_access import PLACE_PERMISSION_EDIT, has_place_permission


home_controller = HomeController.build_default()

place_controller = PlaceController.build_default()

engagement_controller = EngagementController.build_default()

auth_controller = AuthController.build_default()

ownership_controller = OwnershipController.build_default()

owner_places_controller = OwnerPlacesController.build_default()

owner_team_controller = OwnerTeamController.build_default()

owner_reviews_controller = OwnerReviewsController.build_default()

seo_controller = SeoController.build_default()

tracking_controller = TrackingController.build_default()

account_controller = AccountController.build_default()

site_reviews_controller = SiteReviewsController.build_default()

place_reviews_controller = PlaceReviewsController()

def _resolve_safe_next_url(request, fallback_url: str) -> str:
    return resolve_safe_next_url(request, fallback_url)

def _is_ajax_request(request) -> bool:
    return request.headers.get("x-requested-with") == "XMLHttpRequest"

def _build_login_redirect_url(request, fallback_url: str) -> str:
    target = _resolve_safe_next_url(request, fallback_url)
    query = urlencode({"next": target})
    return f"{reverse('account_login')}?{query}"

def _build_owner_create_draft_key(request, *, prefix: str) -> str:
    has_session = hasattr(request, "session")
    if request.method == "GET" and request.GET.get("fresh") == "1":
        key = f"{prefix}-{uuid4().hex}"
        if has_session:
            request.session[f"{prefix}_last_key"] = key
        return key

    existing = (request.POST.get("draft_client_key") or request.GET.get("draft_session") or "").strip()
    if existing.startswith(prefix + "-"):
        if has_session:
            request.session[f"{prefix}_last_key"] = existing
        return existing
    if existing:
        key = f"{prefix}-{existing}"
        if has_session:
            request.session[f"{prefix}_last_key"] = key
        return key

    session_key = request.session.get(f"{prefix}_last_key") if has_session else None
    if session_key and session_key.startswith(prefix + "-"):
        return session_key

    key = f"{prefix}-{uuid4().hex}"
    if has_session:
        request.session[f"{prefix}_last_key"] = key
    return key

def _engagement_login_required_response(request, fallback_url: str):
    message = _("Чтобы ставить лайки и оставлять отзывы, войдите или зарегистрируйтесь.")
    login_url = _build_login_redirect_url(request, fallback_url)
    messages.info(request, message)
    if _is_ajax_request(request):
        return JsonResponse(
            {
                "ok": False,
                "auth_required": True,
                "redirect_url": login_url,
                "message": message,
            },
            status=401,
        )
    return redirect(login_url)

def _allowed_tracking_hosts(request) -> set[str]:
    hosts = {request.get_host().lower()}
    for origin in getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
        if "://" not in origin:
            continue
        host = origin.split("://", 1)[1].split("/", 1)[0].lower()
        if host:
            hosts.add(host)
    return hosts

def _has_allowed_tracking_origin(request) -> bool:
    allowed_hosts = _allowed_tracking_hosts(request)
    origin = (request.headers.get("Origin") or "").strip()
    referer = (request.headers.get("Referer") or "").strip()

    if origin and origin.lower() != "null":
        return url_has_allowed_host_and_scheme(
            origin,
            allowed_hosts=allowed_hosts,
            require_https=request.is_secure(),
        )

    if referer:
        return url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts=allowed_hosts,
            require_https=request.is_secure(),
        )

    fetch_site = (request.headers.get("Sec-Fetch-Site") or "").strip().lower()
    return fetch_site in {"", "same-origin", "same-site", "none"}

def _tracking_rate_limit_exceeded(request) -> bool:
    limit = max(int(getattr(settings, "TRACKING_EVENT_RATE_LIMIT", 60) or 60), 1)
    window_seconds = max(int(getattr(settings, "TRACKING_EVENT_RATE_WINDOW_SECONDS", 60) or 60), 1)
    session_key = ensure_session_key(request) or "anonymous"
    remote_addr = (request.META.get("REMOTE_ADDR") or "unknown").strip()
    cache_key = f"tracking-rate:{session_key}:{remote_addr}"

    added = cache.add(cache_key, 1, timeout=window_seconds)
    if added:
        return False

    try:
        current_count = cache.incr(cache_key)
    except ValueError:
        cache.set(cache_key, 1, timeout=window_seconds)
        return False
    return current_count > limit

def _redirect_to_login(request):
    query = urlencode({"next": request.get_full_path()})
    return redirect(f"{reverse('account_login')}?{query}")

def _build_managed_places_summary(user) -> dict:
    from catalog.services.business_team import accessible_place_ids
    managed_places = list(Place.objects.filter(pk__in=accessible_place_ids(user=user)).order_by("-updated_at"))
    active_managed_places_count = sum(
        1 for place in managed_places if place.status == Place.STATUS_PUBLISHED and place.is_active
    )
    draft_managed_places_count = sum(
        1
        for place in managed_places
        if place.status != Place.STATUS_PUBLISHED or not place.is_active
    )
    actionable_draft_places = [
        place
        for place in managed_places
        if place.status in {Place.STATUS_DRAFT, Place.STATUS_REJECTED} or not place.is_active
    ]
    can_edit_managed_places = any(
        has_place_permission(user=user, place=place, permission_code=PLACE_PERMISSION_EDIT)
        for place in managed_places
    )
    return {
        "managed_places": managed_places,
        "managed_places_count": len(managed_places),
        "active_managed_places_count": active_managed_places_count,
        "draft_managed_places_count": draft_managed_places_count,
        "actionable_draft_places_count": len(actionable_draft_places),
        "latest_actionable_draft_place": actionable_draft_places[0] if actionable_draft_places else None,
        "can_edit_managed_places": can_edit_managed_places,
    }

AUTH_INTENT_ADD_PLACE = "add_place"

# "owner_place" is the historical value; keep accepting it so old links keep working.
LEGACY_AUTH_INTENT_ADD_PLACE = "owner_place"

def _resolve_auth_intent(request) -> str:
    intent = (request.POST.get("intent") or request.GET.get("intent") or "").strip()
    if intent in {AUTH_INTENT_ADD_PLACE, LEGACY_AUTH_INTENT_ADD_PLACE}:
        return AUTH_INTENT_ADD_PLACE
    return ""
