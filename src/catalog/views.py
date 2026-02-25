from django.conf import settings
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .controllers.home_controller import HomeController
from .controllers.place_controller import PlaceController
from .models import CatalogContentSettings, Place, SiteReview
from .services.reactions import (
    create_or_update_review,
    liked_place_ids,
    toggle_place_like as toggle_like_service,
)
from .services.seo import build_seo_landing_schema_payload

home_controller = HomeController.build_default()
place_controller = PlaceController.build_default()


def home(request):
    liked_ids = liked_place_ids(request)
    context = home_controller.build_context(
        language_code=request.LANGUAGE_CODE,
        liked_ids=liked_ids,
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


def _render_place_list(request, force_new_only=False, created_after=None):
    liked_ids = liked_place_ids(request)
    context = place_controller.build_list_context(
        request,
        liked_ids=liked_ids,
        force_new_only=force_new_only,
        created_after=created_after,
    )

    return render(request, "catalog/place_list.html", context)


def place_detail_legacy(request, pk):
    place = place_controller.get_active_place_for_legacy_redirect(pk=pk)
    return redirect(place.get_absolute_url(), permanent=True)


def place_detail(request, pk, slug):
    place = place_controller.get_active_place_with_gallery(pk=pk)
    if slug != place.slug:
        return redirect(place.get_absolute_url(), permanent=True)

    liked_ids = liked_place_ids(request)
    context = place_controller.build_detail_context(request, place=place, liked_ids=liked_ids)

    return render(
        request,
        "catalog/place_detail.html",
        context,
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


@require_POST
def add_site_review(request):
    if getattr(settings, "REVIEWS_REQUIRE_AUTH", False) and not request.user.is_authenticated:
        messages.error(request, _("Оставлять отзывы могут только зарегистрированные пользователи."))
        return redirect(f"{reverse('home')}#site-reviews")

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
        return redirect(f"{reverse('home')}#site-reviews")

    if is_anonymous:
        author_name = ""
    elif not author_name:
        author_name = "Гость"

    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key or ""

    if request.user.is_authenticated:
        review = SiteReview.objects.filter(user=request.user).first()
    else:
        review = SiteReview.objects.filter(user__isnull=True, session_key=session_key).first()

    if review:
        review.rating = rating
        review.text = review_text
        review.author_name = author_name
        review.is_anonymous = is_anonymous
        review.is_approved = True
        review.save()
        created = False
    else:
        SiteReview.objects.create(
            user=request.user if request.user.is_authenticated else None,
            rating=rating,
            text=review_text,
            author_name=author_name,
            is_anonymous=is_anonymous,
            session_key=session_key,
            is_approved=True,
        )
        created = True

    if request.user.is_authenticated and not created:
        messages.success(request, _("Спасибо! Ваша оценка сайта обновлена."))
    else:
        messages.success(request, _("Спасибо! Ваша оценка сайта сохранена."))

    return redirect(f"{reverse('home')}#site-reviews")


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
