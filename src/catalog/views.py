from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .controllers.engagement_controller import EngagementController
from .controllers.home_controller import HomeController
from .controllers.place_controller import PlaceController
from .controllers.seo_controller import SeoController
from .controllers.tracking_controller import TrackingController

home_controller = HomeController.build_default()
place_controller = PlaceController.build_default()
engagement_controller = EngagementController.build_default()
seo_controller = SeoController.build_default()
tracking_controller = TrackingController.build_default()


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


def _render_place_list(request, force_new_only=False, created_after=None):
    context = place_controller.build_list_context(
        request,
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

    context = place_controller.build_detail_context(request, place=place)

    return render(
        request,
        "catalog/place_detail.html",
        context,
    )


@require_POST
def toggle_place_like(request, pk):
    result = engagement_controller.toggle_place_like(request=request, place_id=pk)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "liked": result.liked, "likes_count": result.likes_count})

    return redirect(request.POST.get("next") or result.place.get_absolute_url())


@require_POST
def add_place_review(request, pk):
    place, result = engagement_controller.add_place_review(
        request=request,
        place_id=pk,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", False),
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{place.get_absolute_url()}#reviews")


@require_POST
def add_site_review(request):
    result = engagement_controller.add_site_review(
        request=request,
        require_auth=getattr(settings, "REVIEWS_REQUIRE_AUTH", False),
    )
    if result.ok:
        messages.success(request, result.message)
    else:
        messages.error(request, result.message)
    return redirect(f"{reverse('home')}#site-reviews")


@csrf_exempt
@require_POST
def track_event(request):
    result = tracking_controller.track_cta_event_from_json(request=request, raw_body=request.body)
    return JsonResponse(result.as_payload(), status=result.status_code)


def seo_landing(request, seo_slug):
    context = seo_controller.build_landing_context(request=request, seo_slug=seo_slug)
    return render(request, "catalog/seo_landing.html", context)


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
