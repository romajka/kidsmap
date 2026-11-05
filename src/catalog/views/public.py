"""Public pages: home, catalog, place and event pages, reviews, static pages."""

from django.conf import settings
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ..legal_content import get_legal_page_content
from ..models import Category, Event, Place, PlaceReview, SiteReview
from ..models import FunnelEvent
from ..services.content_quality import approved_review_queryset, public_place_queryset, public_review_queryset
from ..services.pricing_plans import public_pricing_plans
from ..services.tracking import build_google_analytics_event, queue_google_analytics_event, track_event as track_funnel_event
from ..services.features import is_events_section_enabled
from .common import (
    _engagement_login_required_response,
    _has_allowed_tracking_origin,
    _is_ajax_request,
    _resolve_safe_next_url,
    _tracking_rate_limit_exceeded,
    engagement_controller,
    home_controller,
    ownership_controller,
    place_controller,
    place_reviews_controller,
    seo_controller,
    site_reviews_controller,
    tracking_controller,
)


def place_pricing_api(request, slug):
    from django.shortcuts import get_object_or_404
    from catalog.models import Place
    from catalog.services.pricing_plans import build_public_price_summary, serialize_pricing_plans, place_pricing_records

    language = (request.GET.get("lang") or getattr(request, "LANGUAGE_CODE", "az") or "az").split("-")[0]
    if language not in {"az", "ru", "en"}:
        language = "az"
    place = get_object_or_404(
        Place.objects.prefetch_related("pricing_plan_records"),
        slug=slug, is_active=True, status=Place.STATUS_PUBLISHED, deleted_at__isnull=True,
    )
    plans = [plan for plan in place_pricing_records(place) if plan.is_active]
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

def catalog_search_suggestions(request):
    query = (request.GET.get("q") or "").strip()
    if not query:
        return JsonResponse({"categories": [], "places": []})

    language = (request.GET.get("lang") or getattr(request, "LANGUAGE_CODE", "az") or "az").split("-")[0]
    if language not in {"az", "ru", "en"}:
        language = "az"

    matching_categories = []
    from catalog.models import Category
    q_lower = query.lower()
    for cat in Category.active.all():
        name = cat.name_i18n(language)
        alt_names = [getattr(cat, f"name_{l}", "") for l in ("ru", "az", "en")]
        if q_lower in name.lower() or any(q_lower in (a or "").lower() for a in alt_names):
            matching_categories.append({
                "code": cat.code,
                "name": name,
                "url": f"/catalog/?category={cat.code}",
            })
            if len(matching_categories) >= 4:
                break

    from catalog.services.filtering import PlaceListFilters
    filters = PlaceListFilters(query=query)
    base_qs = place_controller.place_repository.filtered_active_queryset()
    places_qs = filters.apply(base_qs).prefetch_related(None).select_related("category", "subcategory")[:6]
    from catalog.services.public_presentation import prepare_cards, organization_matches
    places = prepare_cards(places_qs, language, filters=filters)

    age_suffix = " yaş" if language == "az" else (" yrs" if language == "en" else " лет")

    places_data = []
    for place in places:
        presentation = place._card_presentation
        if presentation['matched_offers']:
            ages = dict.fromkeys(group['age'] for offer in presentation['matched_offers'] for group in offer['groups'] if group['age'])
            age_str = ', '.join(age + age_suffix for age in ages)
        else:
            age_str = f"{place.age_display}{age_suffix}" if place.age_display else ""
        category_title = place.category.name_i18n(language) if place.category else (place.get_category_display() or "")
        places_data.append({
            "id": place.id,
            "name": presentation["name"],
            "url": presentation["url"],
            "category": category_title,
            "district": place.district_i18n(language) or place.metro_i18n(language) or "",
            "image": place.public_image_url or "",
            "rating": round(float(place.rating_avg or 0), 1) if place.rating_count else None,
            "price": presentation["prices"]["label"],
            "age": age_str,
        })

    return JsonResponse({
        "query": query,
        "categories": matching_categories,
        "organizations": organization_matches(query, language),
        "places": places_data,
    })

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

def _retired_public_page(request):
    return render(request, "pages/public_unavailable.html", status=410)

def events_landing(request):
    # Events are retired rather than temporarily unavailable. A 410 removes
    # obsolete /events/ URLs from search indexes faster than a soft 404.
    from ..services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return _retired_public_page(request)
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

def place_detail_legacy(request, pk, slug=None):
    place = place_controller.get_active_place_for_legacy_redirect(pk=pk)
    if place.is_temporary and not is_events_section_enabled():
        return _retired_public_page(request)
    return redirect(place.get_absolute_url(), permanent=True)

def place_detail(request, pk=None, slug=None):
    from django.utils.encoding import iri_to_uri

    place = place_controller.get_active_place_with_gallery(
        pk=pk, public_slug=slug, language=request.LANGUAGE_CODE)
    if place.is_temporary and not is_events_section_enabled():
        return _retired_public_page(request)
    if iri_to_uri(request.path) != place.get_absolute_url() or request.META.get("QUERY_STRING"):
        return redirect(place.get_absolute_url(), permanent=True)

    request._seo_place = place
    context = place_controller.build_detail_context(request, place=place)
    context.update(ownership_controller.build_place_claim_context(request=request, place=place))
    context["public_pricing_plans"] = public_pricing_plans(place.pricing_plans, context.get("language"))

    from catalog.services.pricing_plans import build_pricing_summary
    context["pricing_summary"] = build_pricing_summary(place, context.get("language"))

    from catalog.services.public_favorite_count import build_public_favorite_count
    context["favorite_social_proof"] = build_public_favorite_count(place_id=place.pk)

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
    event_name = FunnelEvent.EVENT_FAVORITE_ADDED if result.liked else FunnelEvent.EVENT_FAVORITE_REMOVED
    analytics_event = build_google_analytics_event(
        event_name,
        {
            "place_id": result.place.id,
            "page_type": "favorite_toggle",
            "action": action,
        },
    )
    track_funnel_event(
        request=request,
        event_type=event_name,
        place=result.place,
        meta={"source": "favorite-toggle"},
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
        name=event_name,
        params={
            "place_id": result.place.id,
            "page_type": "favorite_toggle",
            "action": action,
        },
    )
    return redirect(result.place.get_absolute_url())

def _review_submission_response(request, *, ok, message, redirect_url, cooldown=None):
    limited = not ok and cooldown and cooldown["active"]
    if _is_ajax_request(request):
        response = JsonResponse({
            "ok": ok,
            "message": message,
            "title": _("Спасибо! Отзыв отправлен на модерацию") if ok else "",
            "cooldown": cooldown,
            "code": "review_cooldown" if limited else "",
        }, status=200 if ok else (429 if limited else 400))
        if limited:
            response["Retry-After"] = str(cooldown["retry_after"])
        return response
    notify = messages.success if ok else (messages.warning if limited else messages.error)
    notify(request, message, extra_tags="review-submission")
    return redirect(redirect_url)

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
    return _review_submission_response(
        request, ok=result.ok, message=result.message, redirect_url=f"{place.get_absolute_url()}#reviews",
        cooldown=result.cooldown,
    )

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
    return _review_submission_response(
        request, ok=result.ok, message=result.message, redirect_url=f"{reverse('site_reviews')}#site-reviews",
    )

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
    from catalog.services.analytics_quality import record_analytics_ingress
    if not _has_allowed_tracking_origin(request):
        record_analytics_ingress(rejected=1)
        return JsonResponse({"ok": False, "error": "forbidden_origin"}, status=403)
    if _tracking_rate_limit_exceeded(request):
        record_analytics_ingress(rejected=1, rate_limited=1)
        return JsonResponse({"ok": False, "error": "rate_limited"}, status=429)
    result = tracking_controller.track_event_from_json(request=request, raw_body=request.body)
    record_analytics_ingress(accepted=1 if result.ok else 0, rejected=0 if result.ok else 1)
    if not result.ok and getattr(request, "_analytics_persistence_failed", False):
        return JsonResponse({"ok": False, "error": "analytics_unavailable"}, status=503)
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

def faq_page(request):
    lang = (request.LANGUAGE_CODE or "az").split("-")[0]
    titles = {
        "az": "KidsMap haqqında tez-tez verilən suallar | FAQ",
        "ru": "Частые вопросы о KidsMap | FAQ",
        "en": "Frequently Asked Questions about KidsMap | FAQ",
    }
    meta_descriptions = {
        "az": "KidsMap haqqında tez-tez verilən suallar: valideynlər üçün dərnək axtarışı, rəylər və məkan sahibləri üçün kartın yerləşdirilməsi.",
        "ru": "Частые вопросы о KidsMap: поиск кружков для родителей, отзывы и размещение карточек для владельцев мест.",
        "en": "Frequently asked questions about KidsMap: finding kids clubs, leaving reviews, and place listing for owners.",
    }
    places_count = public_place_queryset(Place.objects.all()).count()
    categories_count = Category.objects.filter(is_active=True).count()

    return render(
        request,
        "pages/faq.html",
        {
            "page_title": titles.get(lang, titles["az"]),
            "meta_description": meta_descriptions.get(lang, meta_descriptions["az"]),
            "places_count": places_count,
            "categories_count": categories_count,
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

def place_root_redirect(request):
    """/place/ has no page of its own, so send the bare segment to the catalog.

    Place cards live at /place/<id>-<slug>/, and both the visible breadcrumbs and
    the BreadcrumbList markup name the catalog as their parent. Truncating the URL
    should land on that parent instead of a 404.
    """
    return _permanent_redirect_with_query(request, reverse("place_list"))

def legacy_owner_section_redirect(request, subpath: str = ""):
    """Keep historical /account/owner/... URLs alive after the move to /account/places/..."""
    if subpath == "places" or subpath.startswith("places/"):
        subpath = subpath[len("places/"):]
    return _permanent_redirect_with_query(request, f"{reverse('owner_places_dashboard')}{subpath}")

def legal_page(request, page_slug):
    language = request.LANGUAGE_CODE if request.LANGUAGE_CODE in {"az", "ru", "en"} else "az"
    if page_slug == "review-rules":
        titles = {
            "az": "Rəy qaydaları | KidsMap",
            "ru": "Правила отзывов | KidsMap",
            "en": "Review Rules | KidsMap",
        }
        descriptions = {
            "az": "KidsMap platformasında rəylərin yerləşdirilməsi, moderasiyası və icma qaydaları.",
            "ru": "Правила публикации и модерации отзывов на платформе KidsMap. Рекомендации для родителей и секций.",
            "en": "Review guidelines, moderation policy and community rules on KidsMap platform.",
        }
        return render(
            request,
            "pages/review_rules.html",
            {
                "page_title": titles.get(language, titles["az"]),
                "meta_description": descriptions.get(language, descriptions["az"]),
                "page_slug": page_slug,
            },
        )
    if page_slug == "listing-rules":
        titles = {
            "az": "Yerləşdirmə qaydaları | KidsMap",
            "ru": "Правила размещения мест | KidsMap",
            "en": "Listing Rules | KidsMap",
        }
        descriptions = {
            "az": "KidsMap platformasında dərnək və məkanların yerləşdirilməsi, 12 vacib tələb və moderasiya qaydaları.",
            "ru": "Правила добавления и модерации карточек детских кружков и секций на платформе KidsMap. 12 обязательных критериев готовности.",
            "en": "Guidelines for listing kids clubs and places on KidsMap. 12 readiness criteria and moderation workflow.",
        }
        return render(
            request,
            "pages/listing_rules.html",
            {
                "page_title": titles.get(language, titles["az"]),
                "meta_description": descriptions.get(language, descriptions["az"]),
                "page_slug": page_slug,
            },
        )
    context = get_legal_page_content(page_slug=page_slug, language=language)
    return render(request, "pages/legal.html", context)

def event_detail(request, pk, slug):
    from ..services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return _retired_public_page(request)
    event = get_object_or_404(
        Event.objects.select_related("related_place", "organizer_organization", "organizer_specialist").prefetch_related("gallery"),
        pk=pk,
        status=Event.STATUS_PUBLISHED,
        deleted_at__isnull=True,
        start_datetime__isnull=False,
    )
    if not event.is_public:
        raise Http404
    if slug != event.slug:
        return redirect(event.get_absolute_url(), permanent=True)
    from catalog.models import EventReview
    from catalog.services.content_quality import public_review_queryset
    from catalog.services.seo import build_event_seo_payload
    from django.utils.dateparse import parse_datetime
    from zoneinfo import ZoneInfo
    language = request.LANGUAGE_CODE.split('-')[0]
    state = event.occurrence_state if event.occurrence_state in {'cancelled', 'rescheduled'} else event.occurrence_status
    labels = {
        'az': {'upcoming':'Qarşıdakı tədbir', 'ongoing':'Tədbir keçirilir', 'completed':'Başa çatıb', 'cancelled':'Ləğv edilib', 'rescheduled':'Vaxtı dəyişdirilib'},
        'en': {'upcoming':'Upcoming', 'ongoing':'Happening now', 'completed':'Ended', 'cancelled':'Cancelled', 'rescheduled':'Rescheduled'},
        'ru': {'upcoming':'Предстоит', 'ongoing':'Мероприятие идёт', 'completed':'Завершено', 'cancelled':'Отменено', 'rescheduled':'Перенесено'},
    }
    reviews = list(public_review_queryset(EventReview.objects.filter(event=event))
        .filter(current_revision__status='approved').select_related('current_revision').order_by('-moderated_at', '-pk'))
    count = len(reviews)
    rating = {'average':sum(review.current_revision.rating for review in reviews)/count if count else 0.0, 'count':count}
    from catalog.services.public_presentation import visible, translated, public_url, present
    from catalog.services.features import is_organizations_section_enabled, is_specialists_section_enabled
    orgs_enabled = is_organizations_section_enabled()
    specs_enabled = is_specialists_section_enabled()

    organizer = None
    org, person = event.organizer_organization, event.organizer_specialist
    if org and visible(org):
        name, name_language = translated(org, 'name', language)
        url = public_url(org, language) if orgs_enabled else None
        organizer = {
            'type': 'Organization',
            'name': name,
            'language': name_language,
            'url': url,
            'website': org.website or '',
            'phone': org.phone or '',
            'whatsapp': org.whatsapp or '',
        }
    elif person and person.status == 'published' and person.is_active and person.person_verified_at and person.verified_person_user_id:
        url = person.get_absolute_url() if specs_enabled else None
        organizer = {
            'type': 'Person',
            'name': person.name,
            'language': language,
            'url': url,
            'photo': person.photo.url if person.photo else None,
            'phone': person.phone or '',
            'whatsapp': person.whatsapp or '',
        }

    related_place_presentation = None
    if event.related_place and visible(event.related_place):
        related_place_presentation = present(event.related_place, language)

    previous_periods = []
    for change in event.occurrence_changes.filter(kind='reschedule').order_by('-happened_at', '-pk'):
        before = change.before if isinstance(change.before, dict) else {}
        try:
            start = parse_datetime(str(before.get('start_datetime') or ''))
            end = parse_datetime(str(before.get('end_datetime') or ''))
        except ValueError:
            continue
        if start and end and timezone.is_aware(start) and timezone.is_aware(end):
            previous_periods.append({'start':start.astimezone(ZoneInfo('Asia/Baku')), 'end':end.astimezone(ZoneInfo('Asia/Baku'))})
    context = {'event':event, 'language':language, 'event_online':event.event_format == 'online',
        'event_venue':event.public_venue(language),
        'related_place_presentation': related_place_presentation,
        'organizations_section_enabled': orgs_enabled,
        'specialists_section_enabled': specs_enabled,
        'event_state_label':labels.get(language, labels['az']).get(state, ''),
        'event_reviews':reviews, 'event_rating':rating, 'event_previous_periods':previous_periods,
        'event_organizer':organizer}
    context.update(build_event_seo_payload(event, request, language, public_context=context))
    return render(request, 'catalog/event_detail.html', context)
