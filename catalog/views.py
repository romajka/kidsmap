from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .content_data import HOME_CATEGORIES
from .models import CatalogContentSettings, Place
from .services.filtering import PlaceListFilters, build_new_page_stats
from .services.reactions import (
    create_or_update_review,
    liked_place_ids,
    mark_liked_flags,
    toggle_place_like as toggle_like_service,
)
from .services.seo import build_place_seo_payload, build_seo_landing_schema_payload


def home(request):
    content_settings = CatalogContentSettings.get_solo()
    seo_pages = content_settings.seo_pages()
    liked_ids = liked_place_ids(request)
    popular_places = list(Place.objects.filter(is_active=True).order_by("-likes_count", "-updated_at")[:4])
    mark_liked_flags(popular_places, liked_ids)

    map_places = [
        {
            "name": place.name_i18n(request.LANGUAGE_CODE),
            "lat": place.lat,
            "lng": place.lng,
            "url": place.get_absolute_url(),
            "category": place.get_category_display(),
        }
        for place in Place.objects.filter(is_active=True).exclude(lat__isnull=True).exclude(lng__isnull=True)
    ]

    return render(
        request,
        "pages/home.html",
        {
            "home_categories": HOME_CATEGORIES,
            "meta_description": "KidsMap: каталог детских кружков и секций в Баку с фильтрами по району, возрасту и цене.",
            "seo_pages": seo_pages,
            "popular_places": popular_places,
            "map_places": map_places,
            "google_maps_api_key": settings.GOOGLE_MAPS_API_KEY,
        },
    )


def place_list(request):
    return _render_place_list(request)


def place_new(request):
    return _render_place_list(request, force_new_only=True)


def _render_place_list(request, force_new_only=False, created_after=None):
    content_settings = CatalogContentSettings.get_solo()
    filters = PlaceListFilters.from_request(request, force_new_only=force_new_only)
    qs = filters.apply(Place.objects.filter(is_active=True), created_after=created_after)
    liked_ids = liked_place_ids(request)

    timeline_places = []
    stats_qs = None
    if force_new_only:
        stats_qs = qs
        timeline_places = list(qs.order_by("-created_at")[:5])
        qs = qs.exclude(id__in=[place.id for place in timeline_places])

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    params = request.GET.copy()
    params.pop("page", None)
    query_without_page = params.urlencode()

    context = {
        "places": page_obj.object_list,
        "timeline_places": timeline_places,
        "page_obj": page_obj,
        "language": request.LANGUAGE_CODE,
        "query_without_page": query_without_page,
        "meta_description": (
            "Новые кружки и курсы в Баку за последние 30 дней. Смотрите свежие добавления на KidsMap."
            if force_new_only
            else "Каталог детских секций и кружков в Баку. Фильтры по категории, району, метро, возрасту и цене."
        ),
        "selected": filters.selected(),
        "categories": Place.CATEGORY_CHOICES,
        "district_options": content_settings.districts(),
        "metro_options": content_settings.metro_stations(),
        "is_new_page": force_new_only,
    }

    mark_liked_flags(context["places"], liked_ids)
    mark_liked_flags(context["timeline_places"], liked_ids)

    if force_new_only:
        now = timezone.now()
        for item in context["timeline_places"]:
            item.days_since_added = max((now - item.created_at).days, 0)
        for item in context["places"]:
            item.days_since_added = max((now - item.created_at).days, 0)

        stats_qs = stats_qs if stats_qs is not None else Place.objects.none()
        context["new_stats_days"] = int(filters.days) if filters.days.isdigit() else 30
        context["new_stats"] = build_new_page_stats(stats_qs)

    return render(request, "catalog/place_list.html", context)


def place_detail_legacy(request, pk):
    place = get_object_or_404(Place.objects.filter(is_active=True), pk=pk)
    return redirect(place.get_absolute_url(), permanent=True)


def place_detail(request, pk, slug):
    place = get_object_or_404(Place.objects.filter(is_active=True).prefetch_related("gallery"), pk=pk)
    if slug != place.slug:
        return redirect(place.get_absolute_url(), permanent=True)

    liked_ids = liked_place_ids(request)
    place.is_liked = place.id in liked_ids

    seo_payload = build_place_seo_payload(place, request, request.LANGUAGE_CODE)
    place_reviews = list(place.reviews.filter(is_approved=True).order_by("-created_at"))

    return render(
        request,
        "catalog/place_detail.html",
        {
            "place": place,
            "language": request.LANGUAGE_CODE,
            "meta_description": seo_payload["description"][:160],
            "seo_image_url": seo_payload["first_image_url"],
            "place_schema_json": seo_payload["schema_json"],
            "map_embed_url": seo_payload["map_embed_url"],
            "map_open_url": seo_payload["map_open_url"],
            "place_reviews": place_reviews,
            "reviews_count": len(place_reviews),
        },
    )


@require_POST
def toggle_place_like(request, pk):
    place = get_object_or_404(Place, pk=pk, is_active=True)
    liked, likes_count = toggle_like_service(place, request)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "liked": liked, "likes_count": likes_count})

    return redirect(request.POST.get("next") or place.get_absolute_url())


@require_POST
def add_place_review(request, pk):
    place = get_object_or_404(Place.objects.filter(is_active=True), pk=pk)

    if getattr(settings, "REVIEWS_REQUIRE_AUTH", False) and not request.user.is_authenticated:
        messages.error(request, _("Оставлять отзывы могут только зарегистрированные пользователи."))
        return redirect(f"{place.get_absolute_url()}#reviews")

    rating_raw = (request.POST.get("rating") or "").strip()
    review_text = (request.POST.get("text") or "").strip()
    author_name = (request.POST.get("author_name") or "").strip()
    is_anonymous = request.POST.get("is_anonymous") == "1"

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        rating = 0

    if rating < 1 or rating > 5:
        messages.error(request, _("Пожалуйста, выберите оценку от 1 до 5."))
        return redirect(f"{place.get_absolute_url()}#reviews")

    if is_anonymous:
        author_name = ""
    elif not author_name:
        author_name = "Гость"

    _, created = create_or_update_review(
        place,
        request,
        rating=rating,
        review_text=review_text,
        author_name=author_name,
        is_anonymous=is_anonymous,
    )

    if request.user.is_authenticated and not created:
        messages.success(request, _("Спасибо! Ваш отзыв обновлен."))
    else:
        messages.success(request, _("Спасибо! Ваш отзыв добавлен."))

    return redirect(f"{place.get_absolute_url()}#reviews")


def seo_landing(request, seo_slug):
    seo_pages = CatalogContentSettings.get_solo().seo_pages()
    page = seo_pages.get(seo_slug)
    if not page:
        raise Http404("SEO page not found")

    schema_payload = build_seo_landing_schema_payload(request, page)
    return render(
        request,
        "catalog/seo_landing.html",
        {
            "seo_page": page,
            "seo_pages": seo_pages,
            "meta_description": page["meta_description"],
            "breadcrumb_schema_json": schema_payload["breadcrumb_schema_json"],
            "faq_schema_json": schema_payload["faq_schema_json"],
        },
    )


def about(request):
    return render(
        request,
        "pages/about.html",
        {"meta_description": "О проекте KidsMap: каталог детских кружков и секций в Баку."},
    )


def contacts(request):
    return render(
        request,
        "pages/contacts.html",
        {"meta_description": "Контакты проекта KidsMap."},
    )
