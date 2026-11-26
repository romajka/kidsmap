"""Read-only public map, using the same query rules as catalog cards."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils import translation
from django.utils.translation import ngettext
from django.utils.cache import patch_cache_control
from catalog.services.public_cache import cached

from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.filtering import PlaceListFilters
from catalog.services.public_map_page import build_map_page, request_window
from django.core.exceptions import ValidationError


@require_GET
def public_map(request):
    language = request.GET.get("lang", request.LANGUAGE_CODE)
    if language not in {"az", "ru", "en"}:
        return JsonResponse({"error": "Invalid map language."}, status=400)
    try:
        after,bounds=request_window(request.GET)
    except ValidationError:
        return JsonResponse({'error':'Invalid map window.'},status=400)
    newest = request.GET.get("map_order") == "newest"
    with translation.override(language):
        filters = PlaceListFilters.from_request(request)
        def build():
            qs = filters.apply(DjangoPlaceRepository().active_queryset())
            return build_map_page(qs, language, filters, after=after, bounds=bounds, newest_first=newest)
        # selected() normalizes price/age for controls. Keep all accepted filter
        # values as well: visually equivalent controls may select different rows.
        parts = (language, sorted(request.GET.lists()), after, bounds, newest)
        page = cached("public_map_page", parts, build, timeout=300)
    if request.GET.get("compact") == "1":
        from catalog.services.map_payload import compact_map_point
        total = len(page["points"])
        with translation.override(language):
            label = (f"{total} xəritə nöqtəsi" if language == "az" else f"{total} map points" if language == "en"
                     else ngettext("%(total)s точка на карте", "%(total)s точки на карте", total) % {"total": total})
        page = {**page, "points_label": label, "points": [compact_map_point(point) for point in page["points"]]}
    response = JsonResponse(page, json_dumps_params={"ensure_ascii": False, "separators": (",", ":")})
    response.headers["Content-Language"] = language
    patch_cache_control(response, public=True, max_age=300)
    return response
