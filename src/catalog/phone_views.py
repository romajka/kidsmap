import hashlib
from ipaddress import ip_address

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from catalog.models import Place
from catalog.services.content_quality import published_place_queryset


@never_cache
@require_POST
@csrf_protect
def reveal_place_phones(request, pk):
    # Nginx overwrites X-Real-IP. Trust it only from explicitly configured
    # proxies; accepting it from arbitrary clients defeats throttling.
    address = request.META.get('REMOTE_ADDR', 'unknown')
    if address in getattr(settings, 'PHONE_REVEAL_TRUSTED_PROXIES', []):
        try:
            address = str(ip_address(request.META.get('HTTP_X_REAL_IP', '')))
        except ValueError:
            pass
    key = 'phone-reveal:' + hashlib.sha256(address.encode()).hexdigest()
    window = 60
    limit = max(1, int(getattr(settings, 'PHONE_REVEAL_RATE_LIMIT', 30)))
    if cache.add(key, 1, timeout=window):
        count = 1
    else:
        try:
            count = cache.incr(key)
        except ValueError:
            cache.add(key, 1, timeout=window)
            count = 1
    if count > limit:
        response = JsonResponse({'error': 'rate_limited'}, status=429)
        response['Retry-After'] = str(window)
        return response
    place = get_object_or_404(published_place_queryset(Place.objects.all()), pk=pk)
    from catalog.services.public_presentation import contact_data, revealed_contacts
    contacts = contact_data(place)
    if not contacts['has_contact']:
        return JsonResponse({'error': 'no_phone'}, status=404)
    return JsonResponse(revealed_contacts(contacts))
