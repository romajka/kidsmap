import hashlib
from ipaddress import ip_address
import re

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
    phones = []
    for number in place.phone_numbers:
        digits = re.sub(r'[^0-9]', '', number)
        if digits:
            phones.append({'number': number, 'href': 'tel:' + ('+' if number.strip().startswith('+') else '') + digits})
    if not phones:
        return JsonResponse({'error': 'no_phone'}, status=404)
    whatsapp = re.sub(r'[^0-9]', '', phones[0]['number'])
    if whatsapp.startswith('0'):
        whatsapp = '994' + whatsapp[1:]
    return JsonResponse({'phones': phones, 'whatsapp': 'https://wa.me/' + whatsapp})
