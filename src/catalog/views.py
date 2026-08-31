from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import login as auth_login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.cache import cache
from django.db.models import Q
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponseGone, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import TemplateView

from .controllers.account_controller import AccountController
from .controllers.auth_controller import AuthController
from .controllers.engagement_controller import EngagementController
from .controllers.home_controller import HomeController
from .controllers.owner_places_controller import OwnerPlacesController
from .controllers import owner_events_controller
from .controllers.owner_reviews_controller import OwnerReviewsController
from .controllers.owner_team_controller import OwnerTeamController
from .controllers.ownership_controller import OwnershipController
from .controllers.place_controller import PlaceController
from .controllers.place_reviews_controller import PlaceReviewsController
from .controllers.seo_controller import SeoController
from .controllers.site_reviews_controller import SiteReviewsController
from .controllers.tracking_controller import TrackingController
from .forms import OwnerEventForm, OwnerSpecialistForm
from .legal_content import get_legal_page_content
from .models import Category, Event, Place, PlaceOwnershipRequest, PlaceReview, SiteReview, SiteSettings, Specialist
from .models import FunnelEvent
from .services.content_quality import approved_review_queryset, public_place_queryset, public_review_queryset
from .services.pricing_plans import public_pricing_plans


def place_pricing_api(request, slug):
    from django.shortcuts import get_object_or_404
    from catalog.models import Place
    from catalog.services.pricing_plans import build_public_price_summary, serialize_pricing_plans

    language = (request.GET.get("lang") or getattr(request, "LANGUAGE_CODE", "az") or "az").split("-")[0]
    if language not in {"az", "ru", "en"}:
        language = "az"
    place = get_object_or_404(
        Place.objects.prefetch_related("pricing_plan_records"),
        slug=slug, is_active=True, status=Place.STATUS_PUBLISHED, deleted_at__isnull=True,
    )
    plans = place.pricing_plan_records.filter(is_active=True).order_by("sort_order", "id")
    summary = build_public_price_summary(place, language)
    summary = {
        **summary,
        "min_price": format(summary["min_price"], ".2f") if summary["min_price"] is not None else None,
        "max_price": format(summary["max_price"], ".2f") if summary["max_price"] is not None else None,
    }
    return JsonResponse({
        "place": {"id": place.pk, "slug": place.slug, "name": place.name_i18n(language)},
        "summary": summary,
        "pricing_plans": serialize_pricing_plans(plans, language),
    })
from .services.reactions import ensure_session_key
from .services.owner_specialist_use_cases import save_owner_specialist_profile
from .services.tracking import build_google_analytics_event, queue_google_analytics_event, track_event as track_funnel_event
from .services.features import require_events_section_enabled, require_specialists_section_enabled
from .services.auth_redirects import resolve_safe_next_url
from .services.place_access import PLACE_PERMISSION_EDIT, has_place_permission

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
    hosts = {request.get_host().split(":", 1)[0].lower()}
    for origin in getattr(settings, "CSRF_TRUSTED_ORIGINS", []):
        if "://" not in origin:
            continue
        host = origin.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0].lower()
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
    managed_places = list(
        Place.objects.filter(
            # created_by only stands in while the card has no owner at all.
            Q(owner=user)
            | Q(owner__isnull=True, created_by=user)
            | Q(team_memberships__member=user, team_memberships__is_active=True),
            deleted_at__isnull=True,
        )
        .distinct()
        .order_by("-updated_at")
    )
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


def home(request):
    context = home_controller.build_context(
        request=request,
        google_maps_api_key=settings.GOOGLE_MAPS_API_KEY,
    )

    return render(
        request,
        "pages/home.html",
        context,
    )


def place_list(request):
    return _render_place_list(request)


def place_new(request):
    return _render_place_list(request, force_new_only=True)


def events_landing(request):
    # Events are retired rather than temporarily unavailable. A 410 removes
    # obsolete /events/ URLs from search indexes faster than a soft 404.
    from .services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return HttpResponseGone()
    context = place_controller.build_events_landing_context(request)
    return render(request, "catalog/events_landing.html", context)


def _render_place_list(request, force_new_only=False, created_after=None):
    if request.GET.getlist("view"):
        normalized_query = place_controller.build_normalized_list_query(
            request,
            force_new_only=force_new_only,
        )
        target_url = request.path
        if normalized_query:
            target_url = f"{target_url}?{normalized_query}"
        return redirect(target_url)

    context = place_controller.build_list_context(
        request,
        force_new_only=force_new_only,
        created_after=created_after,
    )
    context["google_maps_api_key"] = settings.GOOGLE_MAPS_API_KEY

    return render(request, "catalog/place_list.html", context)


def place_detail_legacy(request, pk):
    place = place_controller.get_active_place_for_legacy_redirect(pk=pk)
    return redirect(place.get_absolute_url(), permanent=True)


def place_detail(request, pk, slug):
    place = place_controller.get_active_place_with_gallery(pk=pk)
    if slug != place.slug:
        return redirect(place.get_absolute_url(), permanent=True)

    context = place_controller.build_detail_context(request, place=place)
    context.update(ownership_controller.build_place_claim_context(request=request, place=place))
    context["public_pricing_plans"] = public_pricing_plans(place.pricing_plans, context.get("language"))
    
    from catalog.services.pricing_plans import build_pricing_summary
    context["pricing_summary"] = build_pricing_summary(place, context.get("language"))

    return render(
        request,
        "catalog/place_detail.html",
        context,
    )


@require_POST
def toggle_place_like(request, pk):
    place = place_controller.get_active_place_with_gallery(pk=pk)
    if not request.user.is_authenticated:
        return _engagement_login_required_response(request, place.get_absolute_url())

    result = engagement_controller.toggle_place_like(request=request, place_id=pk)
    action = "saved" if result.liked else "removed"
    analytics_event = build_google_analytics_event(
        FunnelEvent.EVENT_FAVORITE_TOGGLE,
        {
            "place_id": result.place.id,
            "page_type": "favorite_toggle",
            "action": action,
        },
    )
    track_funnel_event(
        request=request,
        event_type=FunnelEvent.EVENT_FAVORITE_TOGGLE,
        place=result.place,
        meta={"action": action},
    )

    if _is_ajax_request(request):
        return JsonResponse(
            {
                "ok": True,
                "liked": result.liked,
                "likes_count": result.likes_count,
                "analytics_event": analytics_event,
            }
        )

    queue_google_analytics_event(
        request=request,
        name=FunnelEvent.EVENT_FAVORITE_TOGGLE,
        params={
            "place_id": result.place.id,
            "page_type": "favorite_toggle",
            "action": action,
        },
    )
    return redirect(result.place.get_absolute_url())


@require_POST
def add_place_review(request, pk):
    place = place_controller.get_active_place_with_gallery(pk=pk)
    if getattr(settings, "REVIEWS_REQUIRE_AUTH", True) and not request.user.is_authenticated:
        return _engagement_login_required_response(request, f"{place.get_absolute_url()}#reviews")

    place, result = engagement_controller.add_place_review(
        request=request,
        place_id=pk,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", True),
    )
    if result.ok:
        track_funnel_event(
            request=request,
            event_type=FunnelEvent.EVENT_REVIEW_SUBMIT,
            place=place,
            meta={"scope": "place"},
        )
        queue_google_analytics_event(
            request=request,
            name=FunnelEvent.EVENT_REVIEW_SUBMIT,
            params={
                "place_id": place.id,
                "page_type": "place_review",
                "review_scope": "place",
            },
        )
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{place.get_absolute_url()}#reviews")


@require_POST
def add_site_review(request):
    if getattr(settings, "REVIEWS_REQUIRE_AUTH", True) and not request.user.is_authenticated:
        return _engagement_login_required_response(request, f"{reverse('site_reviews')}#site-reviews")

    result = engagement_controller.add_site_review(
        request=request,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", True),
    )
    if result.ok:
        track_funnel_event(
            request=request,
            event_type=FunnelEvent.EVENT_REVIEW_SUBMIT,
            meta={"scope": "site"},
        )
        queue_google_analytics_event(
            request=request,
            name=FunnelEvent.EVENT_REVIEW_SUBMIT,
            params={
                "page_type": "site_review",
                "review_scope": "site",
            },
        )
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{reverse('site_reviews')}#site-reviews")


def site_reviews(request):
    context = site_reviews_controller.build_context(request)
    return render(request, "pages/site_reviews.html", context)


def place_reviews(request):
    context = place_reviews_controller.build_context(request)
    return render(request, "pages/place_reviews.html", context)


@require_POST
def vote_place_review(request, review_id):
    value = (request.POST.get("value") or "").strip()
    if value not in {"1", "-1"}:
        message = _("Не удалось обработать реакцию на отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(reverse("home"))

    review = approved_review_queryset(PlaceReview.objects.select_related("place")).filter(pk=review_id).first()
    if review is None:
        message = _("Не удалось обработать реакцию на отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=404)
        messages.error(request, message)
        return redirect(reverse("home"))
    if not request.user.is_authenticated:
        return _engagement_login_required_response(request, f"{review.place.get_absolute_url()}#reviews")
    if review.user_id == request.user.id:
        message = _("Нельзя оценивать собственный отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=403)
        messages.error(request, message)
        return redirect(_resolve_safe_next_url(request, f"{review.place.get_absolute_url()}#reviews"))

    result = engagement_controller.toggle_place_review_reaction(
        request=request,
        review_id=review_id,
        value=int(value),
    )
    if _is_ajax_request(request):
        return JsonResponse(
            {
                "ok": True,
                "current_reaction": result.current_reaction,
                "likes_count": result.likes_count,
                "dislikes_count": result.dislikes_count,
            }
        )
    return redirect(_resolve_safe_next_url(request, f"{result.review.place.get_absolute_url()}#reviews"))


@require_POST
def vote_site_review(request, review_id):
    value = (request.POST.get("value") or "").strip()
    if value not in {"1", "-1"}:
        message = _("Не удалось обработать реакцию на отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=400)
        messages.error(request, message)
        return redirect(reverse("site_reviews"))

    review = approved_review_queryset(SiteReview.objects.all()).filter(pk=review_id).first()
    if review is None:
        message = _("Не удалось обработать реакцию на отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=404)
        messages.error(request, message)
        return redirect(reverse("site_reviews"))
    if not request.user.is_authenticated:
        return _engagement_login_required_response(request, reverse("site_reviews"))
    if review.user_id == request.user.id:
        message = _("Нельзя оценивать собственный отзыв.")
        if _is_ajax_request(request):
            return JsonResponse({"ok": False, "message": message}, status=403)
        messages.error(request, message)
        return redirect(reverse("site_reviews"))

    result = engagement_controller.toggle_site_review_reaction(
        request=request,
        review_id=review_id,
        value=int(value),
    )
    if _is_ajax_request(request):
        return JsonResponse(
            {
                "ok": True,
                "current_reaction": result.current_reaction,
                "likes_count": result.likes_count,
                "dislikes_count": result.dislikes_count,
            }
        )
    return redirect(reverse("site_reviews"))


@csrf_exempt
@require_POST
def track_event(request):
    if not _has_allowed_tracking_origin(request):
        return JsonResponse({"ok": False, "error": "forbidden_origin"}, status=403)
    if _tracking_rate_limit_exceeded(request):
        return JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
    result = tracking_controller.track_event_from_json(request=request, raw_body=request.body)
    return JsonResponse(result.as_payload(), status=result.status_code)


def seo_landing(request, seo_slug):
    context = seo_controller.build_landing_context(request=request, seo_slug=seo_slug)
    return render(request, "catalog/seo_landing.html", context)


def about(request):
    lang = (request.LANGUAGE_CODE or "az").split("-")[0]
    titles = {
        "az": "KidsMap haqqında | Uşaq dərnəkləri və idman bölmələri kataloqu",
        "ru": "О проекте KidsMap | Каталог детских кружков и секций в Баку",
        "en": "About KidsMap | Children's Clubs & Sports Directory in Baku",
    }
    meta_descriptions = {
        "az": "KidsMap haqqında: Bakı və Аzərbaycanda uşaq dərnəkləri, bölmələr və inkişaf mərkəzləri kataloqu.",
        "ru": "О проекте KidsMap: полный каталог детских кружков, спортивных секций и центров развития в Баку и Азербайджане.",
        "en": "About KidsMap project: comprehensive directory of children's clubs, sports sections and development centers in Baku, Azerbaijan.",
    }
    places_count = public_place_queryset(Place.objects.all()).count()
    categories_count = Category.objects.filter(is_active=True).count()
    reviews_count = public_review_queryset(PlaceReview.objects.all()).count()

    return render(
        request,
        "pages/about.html",
        {
            "page_title": titles.get(lang, titles["az"]),
            "meta_description": meta_descriptions.get(lang, meta_descriptions["az"]),
            "places_count": places_count,
            "categories_count": categories_count,
            "reviews_count": reviews_count,
        },
    )


def contacts(request):
    lang = (request.LANGUAGE_CODE or "az").split("-")[0]
    titles = {
        "az": "KidsMap Əlaqə | Telefon, ünvan və əlaqə vasitələri",
        "ru": "Контакты KidsMap | Связаться с нами и адрес в Баку",
        "en": "Contact KidsMap | Address, Phone & Support in Baku",
    }
    meta_descriptions = {
        "az": "KidsMap layihəsi ilə əlaqə: telefon, e-poçt, ünvan və rəy forması.",
        "ru": "Контакты проекта KidsMap: телефон, e-mail, адрес и форма обратной связи.",
        "en": "Contact KidsMap team: phone, email, address and feedback form.",
    }
    return render(
        request,
        "pages/contacts.html",
        {
            "page_title": titles.get(lang, titles["az"]),
            "meta_description": meta_descriptions.get(lang, meta_descriptions["az"]),
        },
    )


ADD_PLACE_CONTENT = {
    "az": {
        "title": "Uşaq məkanınızı KidsMap-də yerləşdirin",
        "mobile_title": "Məkanınızı yerləşdirin",
        "eyebrow": "KidsMap-də yerləşdirmə",
        "free_badge": "Əsas yerləşdirmə pulsuzdur",
        "subtitle": "Foto, ünvan, əlaqə məlumatları, iş qrafiki və qiyməti olan kart yaradın. Kart moderasiyadan sonra kataloqda dərc olunur.",
        "moderation_note": "Dərc edilməzdən əvvəl məlumatların dolğunluğunu və qaydalara uyğunluğunu yoxlayırıq.",
        "primary_cta": "Məkan əlavə et",
        "secondary_cta": "Mövcud kartı tap",
        "steps_title": "Kartı necə dərc etmək olar",
        "steps": [
            ("Hesab yaradın", "Daxil olun və ya qısa qeydiyyatdan keçin."),
            ("Kartı doldurun", "Foto, ünvan, kontaktlar, iş qrafiki və qiyməti əlavə edin."),
            ("Moderasiyaya göndərin", "Məlumatların dolğunluğunu və qaydalara uyğunluğunu yoxlayacağıq."),
            ("Kataloqda görünün", "Təsdiqdən sonra kart valideynlər üçün əlçatan olacaq."),
        ],
        "details_title": "Əsas yerləşdirmə haqqında",
        "details_intro": "Kartı yaratmaq və əsas məlumatları kataloqda yerləşdirmək pulsuzdur.",
        "detail_cards": [
            ("Pulsuz nələr daxildir", ["Foto və məkanın təsviri", "Ünvan və xəritədə mövqe", "Telefon və digər əlaqə məlumatları", "İş qrafiki və qiymət"]),
            ("Moderasiya nəyi yoxlayır", ["Məcburi məlumatların doldurulmasını", "Məlumatların aydın və ziddiyyətsiz olmasını", "Məzmunun KidsMap qaydalarına uyğunluğunu", "Test və natamam kartlar dərc edilmir"]),
            ("Məlumatları necə yeniləmək olar", ["Şəxsi kabinetdə kartınızı açın", "Lazım olan sahələri dəyişin", "Yenilənmiş məlumatları yoxlamaya göndərin", "Dəyişikliklər yenidən moderasiya oluna bilər"]),
        ],
    },
    "ru": {
        "title": "Разместите детское место на KidsMap",
        "mobile_title": "Разместите место",
        "eyebrow": "Размещение на KidsMap",
        "free_badge": "Базовое размещение бесплатно",
        "subtitle": "Создайте карточку с фото, адресом, контактами, расписанием и ценой. После модерации она появится в каталоге.",
        "moderation_note": "Перед публикацией мы проверяем полноту данных и соответствие правилам площадки.",
        "primary_cta": "Добавить место",
        "secondary_cta": "Найти существующую карточку",
        "steps_title": "Как опубликовать карточку",
        "steps": [
            ("Создайте аккаунт", "Войдите или пройдите короткую регистрацию."),
            ("Заполните карточку", "Добавьте фото, адрес, контакты, расписание и цену."),
            ("Отправьте на модерацию", "Мы проверим полноту данных и соответствие правилам."),
            ("Появитесь в каталоге", "После одобрения карточка станет доступна родителям."),
        ],
        "details_title": "Всё о базовом размещении",
        "details_intro": "Создание карточки и размещение основной информации в каталоге бесплатны.",
        "detail_cards": [
            ("Что входит бесплатно", ["Фото и описание места", "Адрес и точка на карте", "Телефон и другие контакты", "Расписание и цена"]),
            ("Что проверяет модерация", ["Заполнены ли обязательные данные", "Понятна ли информация и нет ли противоречий", "Соответствует ли содержание правилам KidsMap", "Тестовые и неполные карточки не публикуются"]),
            ("Как обновить данные", ["Откройте карточку в личном кабинете", "Измените нужные поля", "Отправьте обновлённые данные на проверку", "Изменения могут повторно пройти модерацию"]),
        ],
    },
    "en": {
        "title": "List your kids place on KidsMap",
        "mobile_title": "List your place",
        "eyebrow": "Listing on KidsMap",
        "free_badge": "Basic listing is free",
        "subtitle": "Create a listing with photos, address, contacts, schedule and price. It will appear in the catalog after moderation.",
        "moderation_note": "Before publishing, we check that the information is complete and follows the platform rules.",
        "primary_cta": "Add a place",
        "secondary_cta": "Find an existing listing",
        "steps_title": "How to publish your listing",
        "steps": [
            ("Create an account", "Sign in or complete a short registration."),
            ("Fill in the listing", "Add photos, address, contacts, schedule and price."),
            ("Send it for moderation", "We check completeness and compliance with the rules."),
            ("Appear in the catalog", "Once approved, the listing becomes available to parents."),
        ],
        "details_title": "About the basic listing",
        "details_intro": "Creating a listing and publishing its essential information in the catalog is free.",
        "detail_cards": [
            ("What is included for free", ["Photos and place description", "Address and map location", "Phone and other contact details", "Schedule and price"]),
            ("What moderation checks", ["All required information is provided", "Information is clear and consistent", "Content follows the KidsMap rules", "Test and incomplete listings are not published"]),
            ("How to update information", ["Open the listing in your account", "Edit the necessary fields", "Send the updated information for review", "Changes may be moderated again"]),
        ],
    },
}


def add_place(request):
    language = request.LANGUAGE_CODE if request.LANGUAGE_CODE in ADD_PLACE_CONTENT else "az"
    content = ADD_PLACE_CONTENT[language]
    places_count = public_place_queryset(Place.objects.all()).count()
    return render(
        request,
        "pages/add_place.html",
        {
            "content": content,
            "meta_description": content["subtitle"],
            "places_count": places_count,
        },
    )


def _permanent_redirect_with_query(request, target: str):
    query = request.META.get("QUERY_STRING", "")
    if query:
        target = f"{target}?{query}"
    return redirect(target, permanent=True)


def legacy_for_business_redirect(request):
    """Keep the historical /for-business/ URL alive after the rename to /add-place/."""
    return _permanent_redirect_with_query(request, reverse("add_place"))


def legacy_owner_section_redirect(request, subpath: str = ""):
    """Keep historical /account/owner/... URLs alive after the move to /account/places/..."""
    if subpath == "places" or subpath.startswith("places/"):
        subpath = subpath[len("places/"):]
    return _permanent_redirect_with_query(request, f"{reverse('owner_places_dashboard')}{subpath}")


def legal_page(request, page_slug):
    language = request.LANGUAGE_CODE if request.LANGUAGE_CODE in {"az", "ru", "en"} else "az"
    context = get_legal_page_content(page_slug=page_slug, language=language)
    return render(request, "pages/legal.html", context)


def owner_places_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_places_controller.build_dashboard_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("account_profile")

    from .services.features import is_events_section_enabled

    owner_events = []
    if is_events_section_enabled():
        owner_events = list(
            Event.objects.filter(owner=request.user, deleted_at__isnull=True)
            .select_related("related_place")
            .order_by("-updated_at")
        )
    owner_specialists = list(
        request.user.managed_specialists.prefetch_related("specializations").order_by("-updated_at")
    )
    context.update(
        {
            "owner_events": owner_events,
            "owner_specialists": owner_specialists,
            "owner_event_stats": {
                "total": len(owner_events),
                "published": sum(1 for event in owner_events if event.status == Event.STATUS_PUBLISHED and not event.has_ended),
                "drafts": sum(1 for event in owner_events if event.status in {Event.STATUS_DRAFT, Event.STATUS_PENDING, Event.STATUS_REJECTED}),
                "ended": sum(1 for event in owner_events if event.effective_status == Event.STATUS_EXPIRED),
            },
            "owner_specialist_stats": {
                "total": len(owner_specialists),
                "published": sum(1 for item in owner_specialists if item.status == Specialist.STATUS_PUBLISHED and item.is_active),
                "drafts": sum(1 for item in owner_specialists if item.status in {Specialist.STATUS_DRAFT, Specialist.STATUS_PENDING, Specialist.STATUS_REJECTED}),
            },
            "meta_description": _("Мои места KidsMap: редактирование, черновики, модерация и статистика."),
        }
    )
    return render(request, "pages/owner_places.html", context)


def _build_owner_taxonomy_picker_config(form):
    from .models import Category, Subcategory
    from django.db.models import Count

    category_field = form.fields.get("category")
    subcategory_field = form.fields.get("subcategory")
    if category_field is None or subcategory_field is None:
        return {"categories": [], "subcategories": []}

    categories = []
    category_queryset = category_field.queryset.order_by("order", "name_ru", "name")
    subcategory_counts = {
        item["category_id"]: item["total"]
        for item in Subcategory.active.filter(category__in=category_queryset)
        .values("category_id")
        .annotate(total=Count("pk"))
    }
    for category in category_queryset:
        categories.append(
            {
                "code": category.pk,
                "label": str(category.name_i18n()),
                "icon": category.icon_file_url,
                "icon_class": category.icon_name if category.icon_is_font_class else "",
                "color_bg": category.resolved_color_bg,
                "color_text": category.resolved_color_text,
                "subcategory_count": int(subcategory_counts.get(category.pk, 0) or 0),
            }
        )

    subcategories = []
    for subcategory in subcategory_field.queryset.order_by("category__order", "order", "name_ru", "name"):
        subcategories.append(
            {
                "id": str(subcategory.pk),
                "category": subcategory.category_id,
                "label": str(subcategory.name_i18n()),
            }
        )

    return {
        "categories": categories,
        "subcategories": subcategories,
    }


def owner_place_create(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "GET" and request.GET.get("type") != "permanent":
        result = owner_places_controller.build_create_form_context(request=request)
        if not result.ok:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")
        return render(
            request,
            "pages/owner_listing_type_select.html",
            {
                "meta_description": _("Выбор типа объявления KidsMap."),
            },
        )

    if request.method == "POST":
        draft_client_key = _build_owner_create_draft_key(request, prefix="owner-place-create")
        form_action = (request.POST.get("form_action") or "").strip()
        place_post_data = request.POST.copy()
        place_post_data["is_temporary"] = ""
        place_post_data["temporary_start"] = ""
        place_post_data["temporary_end"] = ""
        if form_action == "check_coordinates":
            result = owner_places_controller.preview_create_coordinates(
                request=request,
                data=place_post_data,
                files=request.FILES,
            )
            if result.form is None:
                messages.error(request, result.message)
                return redirect("owner_places_dashboard")
            if result.message:
                if result.ok:
                    messages.success(request, result.message)
                else:
                    messages.error(request, result.message)
            context = {
                "form": result.form,
                "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
                "meta_description": _("Создание места в личном кабинете KidsMap."),
                "draft_client_key": draft_client_key,
                "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
            }
            return render(request, "pages/owner_place_create.html", context)

        if form_action in {"save_draft", "save_draft_exit"}:
            result = owner_places_controller.create_place(
                request=request,
                data=place_post_data,
                files=request.FILES,
                draft_save_only=True,
            )
            if result.ok:
                messages.success(request, result.message)
                return redirect("owner_places_dashboard")

            if result.form is None:
                messages.error(request, result.message)
                return redirect("owner_places_dashboard")

            context = {
                "form": result.form,
                "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
                "meta_description": _("Создание места в личном кабинете KidsMap."),
                "draft_client_key": draft_client_key,
                "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
            }
            return render(request, "pages/owner_place_create.html", context)

        result = owner_places_controller.create_place(
            request=request,
            data=place_post_data,
            files=request.FILES,
        )
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        context = {
            "form": result.form,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Создание места в личном кабинете KidsMap."),
            "draft_client_key": draft_client_key,
            "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
        }
        return render(request, "pages/owner_place_create.html", context)

    result = owner_places_controller.build_create_form_context(request=request)
    if not result.ok or result.form is None:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context = {
        "form": result.form,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "meta_description": _("Создание места в личном кабинете KidsMap."),
        "draft_client_key": _build_owner_create_draft_key(request, prefix="owner-place-create"),
        "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
    }
    return render(request, "pages/owner_place_create.html", context)


def owner_event_create(request):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        result = owner_events_controller.create_event(
            request=request, 
            data=request.POST, 
            files=request.FILES, 
            draft_save_only=draft_save_only
        )
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
        
        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        form = result.form
    else:
        related_place = (request.GET.get("related_place") or "").strip()
        form = OwnerEventForm(
            user=request.user,
            initial={"related_place": related_place} if related_place else None,
        )

    return render(
        request,
        "pages/owner_event_form.html",
        {
            "form": form,
            "event": None,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Создание временного мероприятия KidsMap."),
        },
    )


def owner_event_edit(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        result = owner_events_controller.edit_event(
            request=request, 
            pk=pk, 
            data=request.POST, 
            files=request.FILES, 
            draft_save_only=draft_save_only
        )
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
            
        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")
            
        form = result.form
        event = result.event
    else:
        event = get_object_or_404(Event, pk=pk, owner=request.user, deleted_at__isnull=True)
        if event.status in {Event.STATUS_PENDING, Event.STATUS_PUBLISHED}:
            messages.error(request, _("Tədbir yalnız qaralama və ya rədd edildikdən sonra redaktə oluna bilər."))
            return redirect("owner_places_dashboard")
            
        form = OwnerEventForm(instance=event, user=request.user)

    return render(
        request,
        "pages/owner_event_form.html",
        {
            "form": form,
            "event": event,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Редактирование временного мероприятия KidsMap."),
        },
    )


@require_POST
def owner_event_submit_review(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_events_controller.submit_event_for_review(request=request, pk=pk)
    if result.ok:
        messages.success(request, result.message)
        return redirect("owner_places_dashboard")
        
    messages.error(request, result.message)
    if result.event and result.event.status != Event.STATUS_PENDING:
        return redirect("owner_event_edit", pk=pk)
    return redirect("owner_places_dashboard")


@require_POST
def owner_event_delete(request, pk):
    require_events_section_enabled()
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_events_controller.delete_event(request=request, pk=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


def event_detail(request, pk, slug):
    from .services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return HttpResponseGone()
    event = get_object_or_404(
        Event.objects.select_related("related_place").prefetch_related("gallery"),
        pk=pk,
        status=Event.STATUS_PUBLISHED,
        deleted_at__isnull=True,
        start_datetime__isnull=False,
        end_datetime__gte=timezone.now(),
    )
    if slug != event.slug:
        return redirect(event.get_absolute_url(), permanent=True)
    return render(
        request,
        "catalog/event_detail.html",
        {
            "event": event,
            "language": request.LANGUAGE_CODE,
            "meta_description": event.description_i18n(request.LANGUAGE_CODE) or event.name_i18n(request.LANGUAGE_CODE),
            "seo_title": f"{event.name_i18n(request.LANGUAGE_CODE)} | KidsMap",
        },
    )


def owner_place_edit(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        place_post_data = request.POST.copy()
        place_post_data["is_temporary"] = ""
        place_post_data["temporary_start"] = ""
        place_post_data["temporary_end"] = ""
        result = owner_places_controller.save_edit_form(
            request=request,
            place_id=pk,
            data=place_post_data,
            files=request.FILES,
            force_coordinate_refresh=form_action == "refresh_coordinates",
            draft_save_only=form_action in {"save_draft", "save_draft_exit"},
            submit_for_moderation=form_action == "save_and_publish",
        )
        if result.ok:
            messages.success(request, result.message)
            if form_action == "save_draft_exit":
                return redirect("owner_places_dashboard")
            if form_action in {"refresh_coordinates", "save_draft"}:
                return redirect("owner_place_edit", pk=pk)
            return redirect("owner_places_dashboard")

        if result.form is None:
            messages.error(request, result.message)
            return redirect("owner_places_dashboard")

        context = {
            "form": result.form,
            "place": result.place,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
            "meta_description": _("Редактирование места в личном кабинете KidsMap."),
            "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
        }
        return render(request, "pages/owner_place_edit.html", context)

    result = owner_places_controller.build_edit_form_context(request=request, place_id=pk)
    if not result.ok or result.form is None:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context = {
        "form": result.form,
        "place": result.place,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        "meta_description": _("Редактирование места в личном кабинете KidsMap."),
        "km_place_taxonomy_picker": _build_owner_taxonomy_picker_config(result.form),
    }
    return render(request, "pages/owner_place_edit.html", context)


@require_POST
def owner_place_publish(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.set_publication_state(request=request, place_id=pk, is_active=True)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


@require_POST
def owner_place_draft(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.set_publication_state(request=request, place_id=pk, is_active=False)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


@require_POST
def owner_place_submit_review(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.submit_for_moderation(request=request, place_id=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


@require_POST
def owner_place_delete(request, pk):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.delete_place(request=request, place_id=pk)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


@require_POST
def owner_place_gallery_photo_delete(request, pk, photo_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_places_controller.delete_gallery_photo(
        request=request,
        place_id=pk,
        photo_id=photo_id,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_place_edit", pk=pk)


def owner_team_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, access = owner_team_controller.build_manager_context(request=request)
    if not access.ok:
        messages.error(request, access.message)
        return redirect("owner_places_dashboard")

    context.update(
        {
            "meta_description": _("Команда KidsMap: приглашения, роли и управление доступом к вашим местам."),
        }
    )
    return render(request, "pages/owner_team.html", context)


@require_POST
def owner_team_invite(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.submit_invitation(request=request)
    if result.ok:
        messages.success(request, result.message)
        return redirect("owner_team_dashboard")

    messages.error(request, result.message)
    context, access = owner_team_controller.build_manager_context(request=request, form=result.form)
    if not access.ok:
        return redirect("owner_places_dashboard")
    context.update(
        {
            "meta_description": _("Команда KidsMap: приглашения, роли и управление доступом к вашим местам."),
        }
    )
    return render(request, "pages/owner_team.html", context)


@require_POST
def owner_team_cancel_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.cancel_invitation(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")


@require_POST
def owner_team_update_member_role(request, membership_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.update_member_role(request=request, membership_id=membership_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")


@require_POST
def owner_team_remove_member(request, membership_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.remove_member(request=request, membership_id=membership_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_team_dashboard")


@require_POST
def owner_team_accept_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.accept_invitation_for_user(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


@require_POST
def owner_team_reject_invitation(request, invitation_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_team_controller.reject_invitation_for_user(request=request, invitation_id=invitation_id)
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_places_dashboard")


def owner_reviews_dashboard(request):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    context, result = owner_reviews_controller.build_context(request=request)
    if not result.ok:
        messages.error(request, result.message)
        return redirect("owner_places_dashboard")

    context.update(
        {
            "meta_description": _("Модерация отзывов: управление публикацией отзывов по вашим местам."),
        }
    )
    return render(request, "pages/owner_reviews.html", context)


@require_POST
def owner_review_approve(request, review_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_reviews_controller.set_review_approval(
        request=request,
        review_id=review_id,
        is_approved=True,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_reviews_dashboard")


@require_POST
def owner_review_reject(request, review_id):
    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    result = owner_reviews_controller.set_review_approval(
        request=request,
        review_id=review_id,
        is_approved=False,
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect("owner_reviews_dashboard")


@require_POST
def request_place_ownership(request, pk):
    place, result = ownership_controller.submit_claim_request(request=request, place_id=pk)
    if result.ok:
        track_funnel_event(
            request=request,
            event_type=FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
            place=place,
            meta={"source": "place_claim_form"},
        )
        queue_google_analytics_event(
            request=request,
            name=FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
            params={
                "place_id": place.id,
                "page_type": "claim_place",
            },
        )
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(place.get_absolute_url())


def account_verify_email(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    initial_email = (request.GET.get("email") or "").strip().lower()
    initial_next = _resolve_safe_next_url(request, reverse("account_profile"))
    auth_intent = _resolve_auth_intent(request)
    verify_form = auth_controller.build_email_verification_form(initial={"email": initial_email})
    resend_form = auth_controller.build_email_verification_resend_form(initial={"email": initial_email})

    if request.method == "POST":
        action = (request.POST.get("form_action") or "verify").strip().lower()
        if action == "resend":
            resend_form = auth_controller.build_email_verification_resend_form(data=request.POST)
            verify_form = auth_controller.build_email_verification_form(initial={"email": resend_form.data.get("email", "")})
            if resend_form.is_valid():
                result = auth_controller.resend_registration_verification_code(email=resend_form.cleaned_data["email"])
                if result.ok:
                    messages.success(request, result.message)
                else:
                    messages.error(request, result.message)
                query = urlencode({"email": resend_form.cleaned_data["email"], "next": initial_next, "intent": auth_intent})
                return redirect(f"{reverse('account_verify_email')}?{query}")
            messages.error(request, _("Проверьте email и повторите отправку кода."))
        else:
            verify_form = auth_controller.build_email_verification_form(data=request.POST)
            resend_form = auth_controller.build_email_verification_resend_form(
                initial={"email": verify_form.data.get("email", "")}
            )
            if verify_form.is_valid():
                result = auth_controller.verify_registration_email_code(
                    email=verify_form.cleaned_data["email"],
                    code=verify_form.cleaned_data["code"],
                )
                if result.ok and result.user is not None:
                    auth_login(request, result.user)
                    if auth_intent == AUTH_INTENT_ADD_PLACE:
                        track_funnel_event(
                            request=request,
                            event_type=FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
                            meta={"intent": auth_intent},
                        )
                        queue_google_analytics_event(
                            request=request,
                            name=FunnelEvent.EVENT_ADD_PLACE_SIGNUP_COMPLETE,
                            params={
                                "page_type": "add_place_signup",
                                "intent": auth_intent,
                            },
                        )
                    messages.success(request, result.message)
                    return redirect(_resolve_safe_next_url(request, reverse("account_profile")))
                messages.error(request, result.message)
            else:
                messages.error(request, _("Проверьте email и код подтверждения."))

    return render(
        request,
        "auth/verify_email.html",
        {
            "verify_form": verify_form,
            "resend_form": resend_form,
            "meta_description": _("Подтверждение email в KidsMap."),
            "next_url": initial_next,
            "auth_intent": auth_intent,
        },
    )


class AccountDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account_dashboard.html"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        context.update(dashboard_context)
        context.update(_build_managed_places_summary(self.request.user))
        context.update(
            {
                "meta_description": _("Личный кабинет KidsMap: профиль, избранное, история просмотров и мои места."),
            }
        )
        return context


class AccountFavoritesView(LoginRequiredMixin, TemplateView):
    template_name = "pages/account_favorites.html"
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = account_controller.ensure_profile(user=self.request.user)
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        context.update(dashboard_context)
        context.update(_build_managed_places_summary(self.request.user))
        context.update(
            {
                "profile_model": profile,
                "meta_description": _("Избранные кружки пользователя в KidsMap."),
            }
        )
        return context


class AccountProfileView(LoginRequiredMixin, View):
    login_url = reverse_lazy("account_login")
    redirect_field_name = "next"
    template_name = "pages/account_profile.html"

    def _build_context(self, *, profile, profile_form, password_form):
        dashboard_context = account_controller.build_dashboard_context(user=self.request.user)
        current_route = self.request.resolver_match.url_name if self.request.resolver_match else "account_profile"
        managed_places_summary = _build_managed_places_summary(self.request.user)
        return {
            "profile_model": profile,
            "profile_form": profile_form,
            "password_form": password_form,
            "favorites_count": dashboard_context["favorites_count"],
            "history_count": dashboard_context["history_count"],
            **managed_places_summary,
            "is_settings_view": current_route == "account_settings",
            "meta_description": _("Личный кабинет KidsMap: данные профиля, контакты и безопасность аккаунта."),
        }

    def get(self, request, *args, **kwargs):
        profile = auth_controller.ensure_profile(user=request.user)
        profile_form = auth_controller.build_profile_edit_form(user=request.user)
        password_form = auth_controller.build_password_change_form(user=request.user)
        return render(
            request,
            self.template_name,
            self._build_context(profile=profile, profile_form=profile_form, password_form=password_form),
        )

    def post(self, request, *args, **kwargs):
        profile = auth_controller.ensure_profile(user=request.user)
        profile_form = auth_controller.build_profile_edit_form(user=request.user)
        password_form = auth_controller.build_password_change_form(user=request.user)
        current_route = request.resolver_match.url_name if request.resolver_match else "account_profile"
        if current_route not in {"account_profile", "account_settings"}:
            current_route = "account_profile"

        form_action = (request.POST.get("form_action") or "").strip().lower()
        if form_action == "profile":
            profile_form = auth_controller.build_profile_edit_form(user=request.user, data=request.POST)
            if profile_form.is_valid():
                profile = auth_controller.update_user_profile_from_form(user=request.user, form=profile_form)
                messages.success(request, _("Профиль обновлен."))
                return redirect(current_route)
            messages.error(request, _("Проверьте данные профиля и исправьте ошибки."))
        elif form_action == "password":
            password_form = auth_controller.build_password_change_form(user=request.user, data=request.POST)
            if password_form.is_valid():
                updated_user = auth_controller.update_password_from_form(form=password_form)
                update_session_auth_hash(request, updated_user)
                messages.success(request, _("Пароль успешно изменен."))
                return redirect(current_route)
            messages.error(request, _("Не удалось изменить пароль. Проверьте введенные поля."))
        else:
            messages.error(request, _("Неизвестное действие формы."))
            return redirect(current_route)

        return render(
            request,
            self.template_name,
            self._build_context(profile=profile, profile_form=profile_form, password_form=password_form),
        )


def account_dashboard(request):
    return AccountDashboardView.as_view()(request)


def account_favorites(request):
    return AccountFavoritesView.as_view()(request)


def account_profile(request):
    return AccountProfileView.as_view()(request)


def account_settings(request):
    return AccountProfileView.as_view()(request)


def account_register(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    auth_intent = _resolve_auth_intent(request)
    language = (request.LANGUAGE_CODE or "az").split("-")[0]
    form = auth_controller.build_registration_form(data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = auth_controller.register_user_from_form(form=form)
        verification = auth_controller.send_registration_verification_code(
            user=user,
            email=form.cleaned_data["email"],
        )
        if verification.ok:
            success_message = {
                "az": "Qeydiyyat demək olar ki, tamamlandı. E-poçta göndərilən kodu daxil edib hesabınızı təsdiqləyin.",
                "en": "Registration is almost complete. Enter the code from your email to confirm your account.",
            }.get(language, _("Регистрация почти завершена. Введите код из письма для подтверждения email."))
            messages.success(
                request,
                success_message,
            )
        else:
            messages.error(request, verification.message)
        query = urlencode(
            {
                "email": form.cleaned_data["email"],
                "next": _resolve_safe_next_url(request, reverse("account_profile")),
                "intent": auth_intent,
            }
        )
        return redirect(f"{reverse('account_verify_email')}?{query}")

    return render(
        request,
        "auth/register.html",
        {
            "form": form,
            "meta_description": {
                "az": "KidsMap qeydiyyatı: hesab yaradın və kataloqdan rahat istifadə etməyə başlayın.",
                "en": "Register on KidsMap and start using the catalog.",
            }.get(language, _("Регистрация в KidsMap: создайте аккаунт и начните пользоваться каталогом.")),
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
            "auth_intent": auth_intent,
            "analytics_events": [
                {
                    "name": FunnelEvent.EVENT_ADD_PLACE_SIGNUP_START,
                    "params": {"page_type": "add_place_signup", "intent": auth_intent},
                }
            ]
            if auth_intent == AUTH_INTENT_ADD_PLACE
            else [],
        },
    )


def account_login(request):
    if request.user.is_authenticated:
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    auth_intent = _resolve_auth_intent(request)
    language = (request.LANGUAGE_CODE or "az").split("-")[0]
    form = auth_controller.build_login_form(request=request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        if form.cleaned_data.get("remember_me"):
            request.session.set_expiry(int(getattr(settings, "SESSION_COOKIE_AGE", 1209600)))
        else:
            request.session.set_expiry(0)
        if language == "az":
            messages.success(request, "Hesabınıza daxil oldunuz.")
        elif language == "en":
            messages.success(request, "You are now signed in.")
        else:
            messages.success(request, _("Вы вошли в аккаунт."))
        return redirect(_resolve_safe_next_url(request, reverse("account_profile")))

    if language == "az":
        meta_description = "KidsMap hesabınıza daxil olun."
    elif language == "en":
        meta_description = "Sign in to your KidsMap account."
    else:
        meta_description = _("Вход в аккаунт KidsMap.")

    return render(
        request,
        "auth/login.html",
        {
            "form": form,
            "meta_description": meta_description,
            "next_url": _resolve_safe_next_url(request, reverse("account_profile")),
            "auth_intent": auth_intent,
        },
    )


@require_POST
def account_logout(request):
    auth_logout(request)
    messages.info(request, _("Вы вышли из аккаунта."))
    return redirect(reverse("home"))


def serve_specialist_document(request, document_id):
    require_specialists_section_enabled()
    from catalog.models import SpecialistDocument
    from django.http import FileResponse, Http404

    doc = get_object_or_404(SpecialistDocument, pk=document_id)
    user = request.user
    is_authorized = False

    if user.is_authenticated and (user.is_staff or user.is_superuser):
        is_authorized = True
    elif user.is_authenticated and doc.specialist.owner == user:
        is_authorized = True
    elif doc.document_type in [SpecialistDocument.TYPE_DIPLOMA, SpecialistDocument.TYPE_CERTIFICATE]:
        if doc.is_verified and doc.is_public:
            is_authorized = True

    if not is_authorized:
        raise Http404(_("Документ не найден или доступ ограничен."))

    return FileResponse(doc.file, as_attachment=False)


def specialist_list(request):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistSpecialization, Region, District, MetroStation
    from catalog.services.public_filter_options import build_public_specialist_filter_options
    from django.db import models
    from django.core.paginator import Paginator

    qs = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True)

    # 1. Search Query
    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            models.Q(name__icontains=q)
            | models.Q(name_alt__icontains=q)
            | models.Q(bio_ru__icontains=q)
            | models.Q(bio_az__icontains=q)
            | models.Q(bio_en__icontains=q)
        )

    # 2. Specialization
    spec_code = (request.GET.get("specialization") or "").strip()
    if spec_code:
        qs = qs.filter(specializations__code=spec_code)

    # 3. Consultation Format
    cf = (request.GET.get("format") or "").strip()
    if cf:
        if cf == "online":
            qs = qs.filter(consultation_format__in=[Specialist.FORMAT_ONLINE, Specialist.FORMAT_BOTH])
        elif cf == "offline":
            qs = qs.filter(consultation_format__in=[Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH])

    # 4. Location Filters
    region_key = (request.GET.get("region") or "").strip()
    district_key = (request.GET.get("district") or "").strip()
    metro_key = (request.GET.get("metro") or "").strip()

    if region_key or district_key or metro_key:
        loc_q = models.Q()
        if region_key:
            loc_q &= models.Q(practice_locations__region_id=region_key)
        if district_key:
            loc_q &= models.Q(practice_locations__district_id=district_key)
        if metro_key:
            loc_q &= models.Q(practice_locations__metro_id=metro_key)
        qs = qs.filter(loc_q)

    # 5. Age
    age = (request.GET.get("age") or "").strip()
    if age.isdigit():
        age_val = int(age)
        qs = qs.filter(
            (models.Q(age_from__isnull=True) | models.Q(age_from__lte=age_val))
            & (models.Q(age_to__isnull=True) | models.Q(age_to__gte=age_val))
        )

    # 6. Price range
    price_from = (request.GET.get("price_from") or "").strip()
    price_to = (request.GET.get("price_to") or "").strip()
    if price_from.isdigit():
        p_from = int(price_from)
        qs = qs.filter(
            models.Q(price_from__gte=p_from) |
            models.Q(practice_locations__price_per_session__gte=p_from)
        )
    if price_to.isdigit():
        p_to = int(price_to)
        qs = qs.filter(
            models.Q(price_to__lte=p_to) |
            models.Q(practice_locations__price_per_session__lte=p_to)
        )

    # 6a. Consultation Language
    consult_lang = (request.GET.get("language") or "").strip()
    if consult_lang in ["az", "ru", "en"]:
        qs = qs.filter(**{f"language_{consult_lang}": True})

    # 6b. Verified Specialist
    verified = (request.GET.get("verified") or "").strip()
    if verified in ["1", "true"]:
        qs = qs.filter(is_verified=True)

    # 6c. Minimum Rating
    min_rating = (request.GET.get("min_rating") or "").strip()
    if min_rating:
        try:
            qs = qs.filter(rating_avg__gte=float(min_rating))
        except ValueError:
            pass

    # 7. Sorting
    sort = (request.GET.get("sort") or "new").strip()
    if sort == "rating":
        qs = qs.order_by("-rating_avg", "-rating_count", "-created_at")
    elif sort == "price_asc":
        from django.db.models.functions import Coalesce
        from django.db.models import Min
        qs = qs.annotate(
            min_price=Coalesce(Min("practice_locations__price_per_session"), "price_from")
        ).order_by("min_price", "-created_at")
    elif sort == "price_desc":
        from django.db.models.functions import Coalesce
        from django.db.models import Max
        qs = qs.annotate(
            max_price=Coalesce(Max("practice_locations__price_per_session"), "price_to")
        ).order_by("-max_price", "-created_at")
    elif sort == "experience":
        qs = qs.order_by("-experience_years", "-created_at")
    else:
        qs = qs.order_by("-created_at")

    qs = qs.distinct()

    paginator = Paginator(qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    active_filter_chips = []
    language = (request.LANGUAGE_CODE or "az").split("-")[0]

    def rebuild_url(exclude_param):
        params = request.GET.copy()
        if exclude_param in params:
            del params[exclude_param]
        return f"?{params.urlencode()}" if params else request.path

    specialist_query_params = request.GET.copy()
    specialist_query_params.pop("page", None)

    if q:
        active_filter_chips.append({
            "label": f"{_('Поиск')}: {q}",
            "remove_url": rebuild_url("q")
        })
    if spec_code:
        spec_obj = SpecialistSpecialization.objects.filter(code=spec_code).first()
        if spec_obj:
            active_filter_chips.append({
                "label": spec_obj.name_i18n(language),
                "remove_url": rebuild_url("specialization")
            })
    if cf:
        format_labels = {
            "online": _("Онлайн"),
            "offline": _("Очно"),
        }
        active_filter_chips.append({
            "label": format_labels.get(cf, cf),
            "remove_url": rebuild_url("format")
        })
    if region_key:
        reg_obj = Region.objects.filter(key=region_key).first()
        if reg_obj:
            active_filter_chips.append({
                "label": reg_obj.name_i18n(language),
                "remove_url": rebuild_url("region")
            })
    if district_key:
        dist_obj = District.objects.filter(key=district_key).first()
        if dist_obj:
            active_filter_chips.append({
                "label": dist_obj.name_i18n(language),
                "remove_url": rebuild_url("district")
            })
    if metro_key:
        metro_obj = MetroStation.objects.filter(key=metro_key).first()
        if metro_obj:
            active_filter_chips.append({
                "label": metro_obj.name_i18n(language),
                "remove_url": rebuild_url("metro")
            })
    if age:
        active_filter_chips.append({
            "label": f"{_('Возраст')}: {age}",
            "remove_url": rebuild_url("age")
        })
    if price_from or price_to:
        pf = price_from or "0"
        pt = price_to or "..."
        active_filter_chips.append({
            "label": f"{pf} - {pt} AZN",
            "remove_url": rebuild_url("price_from") if price_from else rebuild_url("price_to")
        })
    if consult_lang:
        lang_labels = {
            "az": _("Азербайджанский"),
            "ru": _("Русский"),
            "en": _("Английский"),
        }
        active_filter_chips.append({
            "label": f"{_('Язык')}: {lang_labels.get(consult_lang, consult_lang)}",
            "remove_url": rebuild_url("language")
        })
    if verified in ["1", "true"]:
        active_filter_chips.append({
            "label": _("Проверен"),
            "remove_url": rebuild_url("verified")
        })
    if min_rating:
        active_filter_chips.append({
            "label": f"{_('Рейтинг')} ≥ {min_rating}",
            "remove_url": rebuild_url("min_rating")
        })

    filter_options = build_public_specialist_filter_options(language_code=language)

    # Count specialists matching the current filters
    count = qs.count()
    if language == "az":
        results_count_label = f"{count} mütəxəssis tapıldı"
    elif language == "en":
        results_count_label = f"Found {count} specialists"
    else:
        results_count_label = f"Найдено {count} специалистов"

    context = {
        "page_obj": page_obj,
        "specialists": page_obj,
        "selected": {
            "q": q,
            "specialization": spec_code,
            "format": cf,
            "region": region_key,
            "district": district_key,
            "metro": metro_key,
            "age": age,
            "price_from": price_from,
            "price_to": price_to,
            "sort": sort,
            "language": consult_lang,
            "verified": verified,
            "min_rating": min_rating,
        },
        "filter_options": filter_options,
        "active_filter_chips": active_filter_chips,
        "specialist_query_without_page": specialist_query_params.urlencode(),
        "reset_filters_url": request.path,
        "results_count_label": results_count_label,
        "language": language,
        "seo_title": _("Педагоги и специалисты для детей — KidsMap"),
        "meta_description": _("Найдите репетитора, педагога, психолога, логопеда, тренера или другого специалиста для ребёнка."),
    }
    return render(request, "catalog/specialist_list.html", context)


def specialist_detail(request, slug):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistReview

    specialist = get_object_or_404(
        Specialist.objects.prefetch_related(
            "specializations",
            "practice_locations",
            "practice_locations__region",
            "practice_locations__district",
            "practice_locations__metro",
            "documents",
        ),
        slug=slug,
        status=Specialist.STATUS_PUBLISHED,
        is_active=True
    )

    reviews = specialist.reviews.filter(status=SpecialistReview.STATUS_APPROVED).order_by("-created_at")
    reviews_count = reviews.count()
    if specialist.rating_count != reviews_count:
        specialist.refresh_rating_stats()

    visible_documents = specialist.documents.filter(
        document_type__in=["diploma", "certificate"],
        status="approved",
        is_published=True
    )

    language = (request.LANGUAGE_CODE or "az").split("-")[0]

    seo_title = f"{specialist.name} — {', '.join(spec.name_i18n(language) for spec in specialist.specializations.all())}"
    meta_description = f"{specialist.name_alt or specialist.name}: {specialist.bio_i18n(language)[:150]}"

    has_coords = any(loc.lat is not None and loc.lng is not None for loc in specialist.practice_locations.all())

    context = {
        "specialist": specialist,
        "reviews": reviews,
        "visible_documents": visible_documents,
        "language": language,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "has_coords": has_coords,
        "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
    }
    return render(request, "catalog/specialist_detail.html", context)


@require_POST
def add_specialist_review(request, pk):
    require_specialists_section_enabled()

    from catalog.models import Specialist, SpecialistReview
    from catalog.services.review_moderation import moderate_review_content
    from django.contrib import messages

    specialist = get_object_or_404(Specialist, pk=pk, status=Specialist.STATUS_PUBLISHED, is_active=True)

    if not request.user.is_authenticated:
        query = urlencode({"next": f"{specialist.get_absolute_url()}#reviews"})
        return redirect(f"{reverse('account_login')}?{query}")

    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()

    if not rating_raw:
        messages.error(request, _("Выберите оценку от 1 до 5, чтобы отправить отзыв."))
        return redirect(f"{specialist.get_absolute_url()}#reviews")

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        messages.error(request, _("Оценка должна быть числом от 1 до 5."))
        return redirect(f"{specialist.get_absolute_url()}#reviews")

    if rating < 1 or rating > 5:
        messages.error(request, _("Оценка вне диапазона. Укажите значение от 1 до 5."))
        return redirect(f"{specialist.get_absolute_url()}#reviews")

    if not review_text:
        messages.error(request, _("Добавьте текст отзыва, чтобы другим пользователям было полезно ваше мнение."))
        return redirect(f"{specialist.get_absolute_url()}#reviews")

    if len(review_text) > 5000:
        messages.error(request, _("Текст отзыва слишком длинный. Сократите его до 5000 символов."))
        return redirect(f"{specialist.get_absolute_url()}#reviews")

    author_name = ""
    if request.user.is_authenticated:
        candidates = (
            request.user.get_full_name(),
            request.user.get_username(),
            getattr(request.user, "email", ""),
        )
        for value in candidates:
            value = (value or "").strip()
            if value:
                author_name = value[:80]
                break
    if not author_name:
        author_name = _("Гость")

    moderated = moderate_review_content(author_name=author_name, text=review_text)

    defaults = {
        "rating": rating,
        "text": moderated.text,
        "author_name": moderated.author_name,
        "status": SpecialistReview.STATUS_PENDING,
        "is_approved": False,
        "rejection_reason": "",
    }

    review_obj, created = SpecialistReview.objects.update_or_create(
        specialist=specialist,
        user=request.user,
        defaults=defaults
    )

    message = _("Ваш отзыв отправлен на модерацию и будет опубликован после проверки.")
    if moderated.contains_profanity:
        message = f"{message} {_('Нецензурные слова были автоматически скрыты.')}"

    messages.success(request, message)
    return redirect(f"{specialist.get_absolute_url()}#reviews")


def owner_specialist_create(request):
    require_specialists_section_enabled()

    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        form = OwnerSpecialistForm(request.POST, request.FILES, draft_save_only=draft_save_only)
        result = save_owner_specialist_profile(user=request.user, form=form, draft_save_only=draft_save_only)
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
        form = result.form or form
    else:
        form = OwnerSpecialistForm()

    specializations = form.fields["specializations"].queryset.order_by("order", "name_ru")
    return render(
        request,
        "pages/owner_specialist_create.html",
        {
            "form": form,
            "specialist": None,
            "specializations": specializations,
            "meta_description": _("Добавление специалиста в каталог KidsMap."),
        },
    )


def owner_specialist_edit(request, pk):
    require_specialists_section_enabled()

    if not request.user.is_authenticated:
        return _redirect_to_login(request)

    specialist = get_object_or_404(Specialist, pk=pk, owner=request.user)

    if request.method == "POST":
        form_action = (request.POST.get("form_action") or "").strip()
        draft_save_only = form_action == "save_draft"
        form = OwnerSpecialistForm(
            request.POST,
            request.FILES,
            instance=specialist,
            draft_save_only=draft_save_only,
        )
        result = save_owner_specialist_profile(user=request.user, form=form, draft_save_only=draft_save_only)
        if result.ok:
            messages.success(request, result.message)
            return redirect("owner_places_dashboard")
        form = result.form or form
    else:
        form = OwnerSpecialistForm(instance=specialist)

    specializations = form.fields["specializations"].queryset.order_by("order", "name_ru")
    return render(
        request,
        "pages/owner_specialist_create.html",
        {
            "form": form,
            "specialist": specialist,
            "specializations": specializations,
            "meta_description": _("Редактирование профиля специалиста KidsMap."),
        },
    )


from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_add_choice(request):
    context = admin.site.each_context(request)
    context.update(
        {
            "title": _("Добавить публикацию"),
            "has_permission": True,
        }
    )
    return render(
        request,
        "admin/add_choice.html",
        context,
    )
