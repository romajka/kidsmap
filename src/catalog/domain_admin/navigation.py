"""Compact admin navigation over existing, permission-filtered destinations."""
from urllib.parse import parse_qs, urlencode, urlsplit

from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.translation import get_language, gettext as _

from catalog.models import Activity, OfferingGroup, Organization, Place, Program
from catalog.services.business_team import has_action
from catalog.services.staff_roles import is_volunteer


def _normalized(url):
    value = urlsplit(url).path.strip('/')
    parts = value.split('/')
    if parts and parts[0] in {code for code, _label in settings.LANGUAGES}:
        value = '/'.join(parts[1:])
    return '/' + value.rstrip('/') + '/'


def _matches(request, url):
    return _normalized(request.path).startswith(_normalized(url))


def _legacy(request):
    from . import _build_legacy_sidebar_sections, _get_sidebar_metrics
    return _build_legacy_sidebar_sections(request, metrics=_get_sidebar_metrics(request))


def _section(key, label, icon, items):
    items = [dict(item) for item in items if item]
    return {'key': key, 'label': str(label), 'icon': icon, 'items': items,
            'active': any(item.get('active', False) for item in items),
            'has_pending': key == 'moderation' and any(item.get('badge_count', 0) > 0 for item in items)}


def _renamed(item, label):
    return {**item, 'label': str(label)} if item else None


def _model_item(sections, model_name, *, trash=False):
    for section in sections:
        for item in section['items']:
            if f'/catalog/{model_name}/' in item['url']:
                is_trash = parse_qs(urlsplit(item['url']).query).get('deleted_state') == ['deleted']
                if is_trash == trash:
                    return item
    return None


def navigation_groups(request, kind, sections=None):
    if is_volunteer(request.user):
        return []
    sections = _legacy(request) if sections is None else sections
    by_key = {section['key']: section for section in sections}
    if kind == 'directories':
        items = by_key.get('directories', {}).get('items', [])
        geography = {'region', 'district', 'metrostation'}
        return [group for group in (
            {'label': _('Категории и специализации'), 'items': [item for item in items
                if not any(f'/catalog/{model}/' in item['url'] for model in geography)]},
            {'label': _('Города, районы и метро'), 'items': [item for item in items
                if any(f'/catalog/{model}/' in item['url'] for model in geography)]},
        ) if group['items']]
    if kind == 'technical':
        accounts = by_key.get('accounts', {}).get('items', [])
        children = [
            _renamed(_model_item(sections, 'program'), _('Программы сети')),
            _renamed(_model_item(sections, 'activity'), _('Занятия и услуги')),
            _model_item(sections, 'offeringgroup'),
            _renamed(_model_item(sections, 'organizationgrant'), _('Команда и доступы')),
        ]
        children = [item for item in children if item]
        return [group for group in (
            {'label': _('Аккаунты и вход'), 'items': accounts},
            {'label': _('Дополнительные списки каталога'), 'items': children},
        ) if group['items']]
    raise PermissionDenied


def _hub_item(request, kind, label, sections):
    groups = navigation_groups(request, kind, sections)
    if not groups:
        return None
    url = reverse(f'admin:kidsmap_navigation_{kind}')
    active = _matches(request, url)
    if kind == 'directories':
        active = active or any(_matches(request, item['url']) for group in groups for item in group['items'])
    else:
        active = active or any(_matches(request, item['url']) for group in groups
            if group['label'] == _('Аккаунты и вход') for item in group['items'])
    return {'label': str(label), 'url': url, 'icon': 'fas fa-key' if kind == 'technical' else 'fas fa-map-marked-alt',
            'active': active}


def compact_sections(request, legacy):
    if not legacy or is_volunteer(request.user):
        return []
    by_key = {section['key']: section for section in legacy}
    place = _renamed(_model_item(legacy, 'place'), _('Места'))
    organization = _renamed(_model_item(legacy, 'organization'), _('Организации и сети'))
    trash_request = request.GET.get('deleted_state') == 'deleted' or request.GET.get('deleted_at__isnull') == 'False'
    if place:
        place['active'] = not trash_request and (_matches(request, place['url']) or
            any(f'/catalog/{name}/' in request.path for name in ('activity', 'offeringgroup')))
    if organization:
        organization['active'] = _matches(request, organization['url']) or any(
            f'/catalog/{name}/' in request.path for name in ('program', 'organizationgrant'))
    catalog = _section('catalog', _('Каталог'), 'far fa-folder-open', [place,
        _renamed(_model_item(legacy, 'event'), _('Мероприятия')),
        _model_item(legacy, 'specialist'), organization, _model_item(legacy, 'placereview')])
    users = by_key.get('users', {}).get('items', [])
    user_items = []
    administrators = None
    for item in users:
        if '/staffaccessuser/' in item['url']:
            if not item['url'].rstrip('/').endswith('/add'):
                administrators = _renamed(item, _('Администраторы'))
            elif administrators is None:
                administrators = _renamed(item, _('Администраторы'))
        else:
            user_items.append(_renamed(item, _('Доступы к местам') if '/ownerteammembership/' in item['url'] else _('Пользователи сайта')))
    if administrators:
        administrators['active'] = _matches(request, administrators['url'])
        user_items.insert(1, administrators)
    settings_items = []
    for item in by_key.get('content', {}).get('items', []):
        settings_items.append(_renamed(item, _('Фото и баннеры') if '/sitegalleryimage/' in item['url'] else _('Оформление и тексты')))
    directories = _hub_item(request, 'directories', _('Справочники'), legacy)
    technical = _hub_item(request, 'technical', _('Технические настройки входа'), legacy)
    if technical:
        if not place and any(f'/catalog/{name}/' in request.path for name in ('activity', 'offeringgroup')):
            technical['active'] = True
        if not organization and any(f'/catalog/{name}/' in request.path for name in ('program', 'organizationgrant')):
            technical['active'] = True
    settings_items.extend([directories, technical])
    settings_items.extend(_renamed(item, _('История действий')) for item in by_key.get('system', {}).get('items', []))
    trash = _renamed(_model_item(legacy, 'place', trash=True), _('Корзина мест'))
    if trash:
        trash['active'] = trash_request and _matches(request, trash['url'])
    settings_items.append(trash)
    analytics = [_renamed(item, _('Рейтинг мест по отзывам')) if '/placereviewsbyclub/' in item['url'] else item
        for item in by_key.get('analytics', {}).get('items', [])]
    seo_items = sorted(by_key.get('seo_monitoring', {}).get('items', []), key=lambda item: '/seoissue/' not in item['url'])
    result = [catalog,
        _section('moderation', _('Модерация'), 'far fa-shield-alt', by_key.get('moderation', {}).get('items', [])),
        _section('users', _('Пользователи и доступы'), 'far fa-user', user_items),
        _section('analytics', _('Аналитика'), 'fas fa-chart-line', analytics),
        _section('seo_monitoring', _('SEO'), 'fas fa-search', seo_items),
        _section('settings', _('Настройки'), 'fas fa-cogs', settings_items)]
    return [section for section in result if section['items']]


def merge_moderation_sections(sections):
    extras = [section for section in sections if section['key'] in {'volunteer_review', 'moderation_sla'}]
    result = [section for section in sections if section not in extras]
    if extras:
        moderation = next((section for section in result if section['key'] == 'moderation'), None)
        if moderation is None:
            moderation = _section('moderation', _('Модерация'), 'far fa-shield-alt', [])
            result.append(moderation)
        for section in extras:
            label = _('Центр модерации') if section['key'] == 'volunteer_review' else _('Сроки проверки')
            moderation['items'].extend(_renamed(item, label) for item in section['items'])
    for section in result:
        section['active'] = any(item.get('active', False) for item in section['items'])
        section['has_pending'] = section['key'] == 'moderation' and any(
            item.get('badge_count', 0) > 0 for item in section['items'])
    return result


def _hub(request, kind):
    groups = navigation_groups(request, kind)
    if not groups:
        raise PermissionDenied
    return TemplateResponse(request, 'admin/catalog/navigation_hub.html', {
        **admin.site.each_context(request), 'title': _('Справочники') if kind == 'directories' else _('Технические настройки входа'),
        'navigation_title': _('Справочники') if kind == 'directories' else _('Технические настройки входа'),
        'navigation_groups': groups,
    })


def install_navigation_urls():
    if getattr(admin.site, '_kidsmap_navigation_registered', False):
        return
    original = admin.site.get_urls
    def get_urls():
        return [path('navigation/directories/', admin.site.admin_view(lambda request: _hub(request, 'directories')),
                     name='kidsmap_navigation_directories'),
                path('navigation/technical/', admin.site.admin_view(lambda request: _hub(request, 'technical')),
                     name='kidsmap_navigation_technical')] + original()
    admin.site.get_urls = get_urls
    admin.site._kidsmap_navigation_registered = True


def _link(request, model, label, *, obj=None, query=None, add=False, fragment=''):
    editor = admin.site._registry.get(model)
    if editor is None or is_volunteer(request.user):
        return None
    allowed = editor.has_add_permission(request) if add else editor.has_view_or_change_permission(request, obj)
    if not allowed:
        return None
    action = 'add' if add else ('change' if obj else 'changelist')
    url = reverse(f'admin:{model._meta.app_label}_{model._meta.model_name}_{action}', args=[obj.pk] if obj and not add else None)
    if query:
        url += '?' + urlencode(query)
    return (str(label), url + fragment)


def _name(obj):
    language = (get_language() or 'az').split('-')[0]
    return getattr(obj, f'name_{language}', '') or getattr(obj, 'name_az', '') or str(obj)


def place_navigation(request, obj):
    if not obj or not obj.pk or is_volunteer(request.user):
        return []
    links = [_link(request, Activity, _('Занятия и услуги'), query={'place__id__exact': obj.pk})]
    if has_action(user=request.user, target=obj, action='place.edit'):
        links.append(_link(request, Activity, _('Добавить занятие'), query={'place': obj.pk}, add=True))
    return [{'label': label, 'url': url} for item in links if item for label, url in [item]]


def business_navigation(request, obj):
    links = []
    if isinstance(obj, Organization):
        links = [_link(request, Place, _('Филиалы'), query={'organization__id__exact': obj.pk}),
            _link(request, Program, _('Программы сети'), query={'organization__id__exact': obj.pk})]
        from catalog.models import OrganizationGrant
        links.append(_link(request, OrganizationGrant, _('Команда и доступы'), query={'organization__id__exact': obj.pk}))
    elif isinstance(obj, Program):
        links.append(_link(request, Organization, _('Вернуться к организации') + ': ' + _name(obj.organization), obj=obj.organization))
    else:
        activity = obj.activity if isinstance(obj, OfferingGroup) else obj
        place = activity.place
        links.append(_link(request, Place, _('Вернуться к месту') + ': ' + _name(place), obj=place))
        if isinstance(obj, OfferingGroup):
            links.append(_link(request, Activity, _('Занятия и услуги') + ': ' + _name(activity), obj=activity))
        else:
            links.append(_link(request, OfferingGroup, _('Группы и тарифы'), query={'activity__id__exact': obj.pk}))
            if has_action(user=request.user, target=obj, action='place.edit'):
                links.append(_link(request, OfferingGroup, _('Добавить группу'), query={'activity': obj.pk}, add=True))
        links.append(_link(request, Place, _('Тарифы места'), obj=place, fragment='#pricing'))
    return [item for item in links if item]


def authorized_initial(request, model, initial):
    config = {Activity: ('place', Place, 'place.edit'), OfferingGroup: ('activity', Activity, 'place.edit'),
              Program: ('organization', Organization, 'program.manage')}
    if model not in config:
        return initial
    field, parent_model, action = config[model]
    if field not in request.GET:
        return initial
    value = request.GET.get(field, '')
    if not value.isdecimal() or len(value) > 18:
        raise PermissionDenied
    obj = parent_model.objects.filter(pk=value).first()
    parent_admin = admin.site._registry.get(parent_model)
    if obj is None or parent_admin is None or not parent_admin.has_view_or_change_permission(request, obj) or not has_action(user=request.user, target=obj, action=action):
        raise PermissionDenied
    initial[field] = obj.pk
    return initial
