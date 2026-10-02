"""Read-only public map, using the same query rules as catalog cards."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.filtering import PlaceListFilters
from catalog.services.map_payload import serialize_map_places


@require_GET
@never_cache
def public_map(request):
    repository = DjangoPlaceRepository()
    filters = PlaceListFilters.from_request(request)
    queryset = filters.apply(repository.active_queryset())
    points = serialize_map_places(repository.map_ready_queryset(queryset), request.LANGUAGE_CODE, filters)
    return JsonResponse({'points': points, 'count': sum(len(point['members']) for point in points)})
