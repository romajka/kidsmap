"""Read-only public map, using the same query rules as catalog cards."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.filtering import PlaceListFilters
from catalog.services.public_map_page import build_map_page, request_window
from django.core.exceptions import ValidationError


@require_GET
@never_cache
def public_map(request):
    repository = DjangoPlaceRepository()
    filters = PlaceListFilters.from_request(request)
    queryset = filters.apply(repository.active_queryset())
    try:
        after,bounds=request_window(request.GET)
    except ValidationError:
        return JsonResponse({'error':'Invalid map window.'},status=400)
    return JsonResponse(build_map_page(queryset,request.LANGUAGE_CODE,filters,after=after,bounds=bounds))
