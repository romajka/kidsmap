from dataclasses import asdict

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.utils.translation import gettext as _

from catalog.services.district_geometry import resolve_location
from catalog.services.locations import AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP
from django.utils.translation import get_language, override


@login_required(login_url="account_login")
@require_GET
@never_cache
def location_resolve(request):
    result = resolve_location(request.GET.get('lat'), request.GET.get('lng'))
    data = asdict(result)
    requested_language = request.GET.get('language', '')
    lang = requested_language if requested_language in ('az', 'ru', 'en') else (get_language() or 'az').split('-')[0]
    data['language'] = lang
    data['city_label'] = AZERBAIJAN_REGIONS_MAP.get(result.city_key, {}).get(lang, result.city_key)
    data['district_label'] = BAKU_DISTRICTS_MAP.get(result.district_key, {}).get(lang, result.district_key)
    data['lat'], data['lng'] = request.GET.get('lat'), request.GET.get('lng')
    with override(lang):
        data['message'] = {
            'resolved': _('Город и район определены по точке на карте.'),
            'ambiguous': _('Точка находится у границы районов. Уточните её или отправьте на проверку.'),
            'outside_coverage': _('Для этой территории пока нет проверенных границ. Сохраните черновик для проверки.'),
            'invalid_coordinates': _('Поставьте точку на карте, чтобы определить город и район.'),
            'unavailable': _('Не удалось определить район. Повторите попытку или сохраните черновик.'),
        }[result.status]

    return JsonResponse(data, status=400 if result.status == 'invalid_coordinates' else 503 if result.status == 'unavailable' else 200)
