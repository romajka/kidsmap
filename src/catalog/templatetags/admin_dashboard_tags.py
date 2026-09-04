from django import template
from django.contrib.admin.views.main import PAGE_VAR
from django.contrib.auth import get_user_model
from catalog.models.place import Place, Event
from catalog.models.specialist import Specialist
from catalog.models.review import PlaceReview
from catalog.models.owner import PlaceOwnershipRequest
from catalog.services.content_quality import public_place_queryset
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from catalog.models.seo import SEOIssue
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

register = template.Library()
User = get_user_model()


@register.simple_tag
def admin_filter_choices(cl, spec):
    return list(spec.choices(cl))


@register.simple_tag
def get_dashboard_stats():
    permanent_places = Place.objects.filter(deleted_at__isnull=True, is_temporary=False)
    public_places_count = public_place_queryset(permanent_places).count()
    public_events_count = Event.objects.filter(
        status=Event.STATUS_PUBLISHED,
        deleted_at__isnull=True,
        start_datetime__isnull=False,
        end_datetime__gte=timezone.now(),
    ).count()

    places_pending = permanent_places.filter(status=Place.STATUS_PENDING).count()
    events_pending = Event.objects.filter(deleted_at__isnull=True, status=Event.STATUS_PENDING).count()
    specialists_pending = Specialist.objects.filter(status=Specialist.STATUS_PENDING).count()
    reviews_pending = PlaceReview.objects.filter(status=PlaceReview.STATUS_PENDING).count()
    requests_pending = PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
    pending_reviews = []
    for review in (
        PlaceReview.objects
        .filter(status=PlaceReview.STATUS_PENDING)
        .select_related("place", "user")
        .order_by("-created_at")[:3]
    ):
        author = (review.author_name or "").strip()
        if not author and review.user_id:
            author = review.user.get_full_name() or review.user.username or review.user.email
        pending_reviews.append({
            "id": review.pk,
            "place": review.place.name_ru or review.place.name,
            "author": author or "Без имени",
            "rating": review.rating,
            "text": (review.text or "").strip(),
            "created_at": review.created_at,
        })

    total_pending = places_pending + events_pending + specialists_pending + reviews_pending + requests_pending

    return {
        'kpi': {
            'total_places': permanent_places.count(),
            'places_published': public_places_count,
            'total_events': Event.objects.filter(deleted_at__isnull=True).count(),
            'events_active': public_events_count,
            'total_specialists': Specialist.objects.count(),
            'total_users': User.objects.filter(is_staff=False, is_superuser=False).count(),
        },
        'pending': {
            'total': total_pending,
            'places': places_pending,
            'events': events_pending,
            'specialists': specialists_pending,
            'reviews': reviews_pending,
            'requests': requests_pending,
        },
        'pending_reviews': pending_reviews,
    }


PLURAL_MAP = {
    'place': {
        'ru': ('место', 'места', 'мест'),
        'az': ('məkan', 'məkan', 'məkan'),
        'en': ('place', 'places', 'places'),
    },
    'event': {
        'ru': ('мероприятие', 'мероприятия', 'мероприятий'),
        'az': ('tədbir', 'tədbir', 'tədbir'),
        'en': ('event', 'events', 'events'),
    },
    'placereview': {
        'ru': ('отзыв', 'отзыва', 'отзывов'),
        'az': ('rəy', 'rəy', 'rəy'),
        'en': ('review', 'reviews', 'reviews'),
    },
    'sitereview': {
        'ru': ('отзыв', 'отзыва', 'отзывов'),
        'az': ('rəy', 'rəy', 'rəy'),
        'en': ('review', 'reviews', 'reviews'),
    },
    'user': {
        'ru': ('пользователь', 'пользователя', 'пользователей'),
        'az': ('istifadəçi', 'istifadəçi', 'istifadəçi'),
        'en': ('user', 'users', 'users'),
    },
    'group': {
        'ru': ('группа', 'группы', 'групп'),
        'az': ('qrup', 'qrup', 'qrup'),
        'en': ('group', 'groups', 'groups'),
    },
    'placeownershiprequest': {
        'ru': ('запрос', 'запроса', 'запросов'),
        'az': ('sorğu', 'sorğu', 'sorğu'),
        'en': ('request', 'requests', 'requests'),
    },
    'placechangeaudit': {
        'ru': ('действие', 'действия', 'действий'),
        'az': ('əməliyyat', 'əməliyyat', 'əməliyyat'),
        'en': ('action', 'actions', 'actions'),
    }
}


def get_plural_form(count, forms, lang='ru'):
    if lang == 'az':
        return forms[0]
    if lang == 'en':
        return forms[0] if count == 1 else forms[1]

    # Russian plural rules
    n = abs(count) % 100
    n1 = n % 10
    if 10 < n < 20:
        return forms[2]
    if 1 < n1 < 5:
        return forms[1]
    if n1 == 1:
        return forms[0]
    return forms[2]


@register.simple_tag
def paginator_count_label(cl):
    from django.utils import translation
    count = cl.result_count
    model_name = cl.opts.model_name.lower()
    lang = translation.get_language() or 'ru'
    lang = lang[:2].lower()

    if model_name in PLURAL_MAP:
        forms = PLURAL_MAP[model_name].get(lang, PLURAL_MAP[model_name]['en'])
        word = get_plural_form(count, forms, lang)
        return f"{count} {word}"

    # Fallback to model's verbose name
    if count == 1:
        return f"{count} {cl.opts.verbose_name}"
    else:
        return f"{count} {cl.opts.verbose_name_plural}"


@register.simple_tag
def paginator_page_range(cl):
    return cl.paginator.get_elided_page_range(number=cl.page_num, on_each_side=2, on_ends=1)


@register.simple_tag
def paginator_page_url(cl, page_number):
    return cl.get_query_string({PAGE_VAR: page_number})


@register.simple_tag
def paginator_range_label(cl):
    total = cl.result_count
    if total == 0:
        return "0 из 0"
    start = (cl.page_num - 1) * cl.list_per_page + 1
    end = min(cl.page_num * cl.list_per_page, total)
    return f"{start}–{end} из {total}"


@register.simple_tag
def get_active_filter_chips(cl):
    chips = []
    ignored_params = {
        'is_temporary', 'is_temporary__exact',
        'status', 'status__exact',
        'deleted_at', 'deleted_at__isnull',
        'p', 'o', 'q'
    }
    for spec in getattr(cl, 'filter_specs', []):
        field_name = getattr(spec, 'parameter_name', getattr(spec, 'field_path', ''))
        if not field_name:
            continue
        if field_name in ignored_params or field_name.replace('__exact', '') in ignored_params:
            continue
        try:
            choices = list(spec.choices(cl))
        except Exception:
            continue
        if not choices:
            continue
        all_choice = choices[0]
        for choice in choices[1:]:
            if choice.get('selected'):
                remove_url = all_choice.get('query_string', '?')
                chips.append({
                    'title': getattr(spec, 'title', field_name),
                    'label': choice.get('display', ''),
                    'remove_url': remove_url,
                    'param': field_name,
                })
    return chips


@register.simple_tag
def get_recent_admin_actions(limit=8, user=None):
    """
    Returns recent admin actions formatted for dashboard timeline.
    Shows system-wide actions for administrators or filtered actions.
    """
    qs = LogEntry.objects.select_related('user', 'content_type').order_by('-action_time')
    if user and not user.is_staff:
        qs = qs.filter(user=user)

    entries = qs[:limit]
    actions = []

    friendly_models = {
        'place': _('Постоянное место'),
        'event': _('Мероприятие'),
        'specialist': _('Специалист'),
        'specialistspecialization': _('Специализация'),
        'category': _('Категория'),
        'subcategory': _('Подкатегория'),
        'region': _('Регион'),
        'district': _('Район'),
        'metrostation': _('Станция метро'),
        'placereview': _('Отзыв о месте'),
        'specialistreview': _('Отзыв о специалисте'),
        'sitereview': _('Отзыв о сайте'),
        'placereviewsbyclub': _('Рейтинг мест'),
        'placeownershiprequest': _('Заявка на владение'),
        'siteregistereduser': _('Пользователь сайта'),
        'staffaccessuser': _('Сотрудник админки'),
        'useremailverification': _('Подтверждение email'),
        'sitegalleryimage': _('Фото галереи'),
        'sitesettings': _('Настройки сайта'),
        'sitevisibilitysettings': _('Видимость разделов'),
        'siteanalytics': _('Аналитика'),
        'seoissue': _('SEO-проблема'),
        'seochange': _('SEO-изменение'),
        'seoauditrun': _('SEO-аудит'),
        'placechangeaudit': _('История изменений'),
        'user': _('Пользователь'),
        'group': _('Группа'),
    }

    for e in entries:
        ct = e.content_type
        model_name = ct.model.lower() if ct else ''
        model_label = friendly_models.get(model_name)
        if not model_label:
            if ct and ct.model_class():
                model_label = ct.model_class()._meta.verbose_name
            else:
                model_label = ct.name if ct else _('Объект')

        if e.action_flag == ADDITION:
            flag = 'add'
            flag_label = _('Создание')
        elif e.action_flag == DELETION:
            flag = 'delete'
            flag_label = _('Удаление')
        else:
            flag = 'change'
            flag_label = _('Изменение')

        url = None
        if e.action_flag != DELETION:
            try:
                url = e.get_admin_url()
            except Exception:
                url = None

        user_display = _('Система')
        if e.user:
            user_display = e.user.get_full_name() or e.user.username or e.user.email

        actions.append({
            'id': e.pk,
            'user': user_display,
            'action_flag': flag,
            'action_label': flag_label,
            'model_name': model_label,
            'object_repr': e.object_repr,
            'url': url,
            'action_time': e.action_time,
        })
    return actions


@register.simple_tag
def get_dashboard_workspace_hubs(dashboard_list, stats=None):
    """
    Groups Jazzmin's flat model list into 4 logical domain workspaces:
    1. Каталог и контент
    2. Модерация и заявки
    3. Пользователи и доступ
    4. SEO, аудит и система
    Plus a fallback for any unmapped models.
    """
    if not dashboard_list:
        return []

    # Flatten all available models from jazzmin dashboard_list
    all_models = {}
    for app in dashboard_list:
        for m in app.get('models', []):
            obj_name = m.get('object_name')
            if obj_name:
                all_models[obj_name] = m

    kpi = (stats or {}).get('kpi', {})
    pending = (stats or {}).get('pending', {})

    friendly_names = {
        'Place': _('Постоянные места'),
        'Event': _('Мероприятия'),
        'Specialist': _('Специалисты'),
        'SpecialistSpecialization': _('Специализации'),
        'PlaceReview': _('Отзывы по кружкам'),
        'SpecialistReview': _('Отзывы о специалистах'),
        'SiteReview': _('Отзывы о сайте'),
        'PlaceReviewsByClub': _('Рейтинги мест'),
        'Category': _('Категории'),
        'Region': _('Регионы'),
        'District': _('Районы'),
        'MetroStation': _('Станции метро'),
        'SiteGalleryImage': _('Фото для блоков сайта'),
        'ModerationPlace': _('Места на проверке'),
        'ModerationEvent': _('Мероприятия на проверке'),
        'ModerationSpecialist': _('Специалисты на проверке'),
        'ModerationReview': _('Отзывы на проверке'),
        'ModerationPlaceOwnershipRequest': _('Заявки на владение'),
        'PlaceOwnershipRequest': _('Заявки на владение кружком'),
        'SiteRegisteredUser': _('Пользователи сайта'),
        'StaffAccessUser': _('Сотрудники админки'),
        'UserEmailVerification': _('Подтверждение email'),
        'User': _('Пользователи'),
        'Group': _('Группы доступа'),
        'SEOIssue': _('SEO-проблемы'),
        'SEOAuditRun': _('Запуски SEO-аудитов'),
        'SEOChange': _('Записи изменений SEO'),
        'PlaceChangeAudit': _('История изменений карточек'),
        'SiteAnalytics': _('Статистика аналитики'),
        'SiteSettings': _('Настройки сайта'),
    }

    # Use ModerationPlaceOwnershipRequest if available, otherwise PlaceOwnershipRequest
    req_model = 'ModerationPlaceOwnershipRequest' if 'ModerationPlaceOwnershipRequest' in all_models else 'PlaceOwnershipRequest'

    HUB_CONFIG = [
        {
            'id': 'catalog_content',
            'title': _('Каталог и контент'),
            'badge': _('Контент'),
            'icon': 'folder',
            'description': _('Кружки, секции, события, специалисты и справочники структуры'),
            'models': [
                ('Place', 'place', kpi.get('total_places')),
                ('Event', 'event', kpi.get('total_events')),
                ('Specialist', 'person', kpi.get('total_specialists')),
                ('SpecialistSpecialization', 'category', None),
                ('PlaceReview', 'rate_review', None),
                ('SpecialistReview', 'rate_review', None),
                ('PlaceReviewsByClub', 'star', None),
                ('Category', 'folder', None),
                ('Region', 'place', None),
                ('District', 'place', None),
                ('MetroStation', 'location_on', None),
                ('SiteGalleryImage', 'photo_library', None),
            ]
        },
        {
            'id': 'moderation_requests',
            'title': _('Модерация и заявки'),
            'badge': _('Контроль'),
            'icon': 'shield',
            'description': _('Входящие материалы и запросы владельцев на проверку'),
            'models': [
                ('ModerationPlace', 'schedule', pending.get('places')),
                ('ModerationEvent', 'event', pending.get('events')),
                ('ModerationSpecialist', 'person', pending.get('specialists')),
                ('ModerationReview', 'rate_review', pending.get('reviews')),
                (req_model, 'shield', pending.get('requests')),
            ]
        },
        {
            'id': 'users_access',
            'title': _('Пользователи и доступ'),
            'badge': _('Доступ'),
            'icon': 'group',
            'description': _('Зарегистрированные пользователи, права доступа и сотрудники'),
            'models': [
                ('SiteRegisteredUser', 'group', kpi.get('total_users')),
                ('StaffAccessUser', 'admin_panel_settings', None),
                ('UserEmailVerification', 'verified_user', None),
                ('User', 'person', None),
                ('Group', 'groups', None),
            ]
        },
        {
            'id': 'seo_system',
            'title': _('SEO, аудит и система'),
            'badge': _('Система'),
            'icon': 'analytics',
            'description': _('Мониторинг позиций, история изменений, аудит и настройки'),
            'models': [
                ('SEOIssue', 'warning', None),
                ('SEOAuditRun', 'analytics', None),
                ('SEOChange', 'history', None),
                ('PlaceChangeAudit', 'history', None),
                ('SiteAnalytics', 'insights', None),
                ('SiteSettings', 'settings', None),
                ('SiteReview', 'rate_review', None),
            ]
        },
    ]

    assigned = set()
    hubs = []

    for config in HUB_CONFIG:
        items = []
        for obj_name, icon, count in config['models']:
            if obj_name in all_models and obj_name not in assigned:
                model_data = all_models[obj_name].copy()
                model_data['icon'] = icon
                model_data['display_name'] = friendly_names.get(obj_name, model_data.get('name'))
                model_data['count'] = count
                if config['id'] == 'moderation_requests' and count and count > 0:
                    model_data['has_pending'] = True
                items.append(model_data)
                assigned.add(obj_name)

        if items:
            hubs.append({
                'id': config['id'],
                'title': config['title'],
                'badge': config['badge'],
                'icon': config['icon'],
                'description': config['description'],
                'items_count': len(items),
                'items': items,
            })

    # Unassigned fallback so no model is ever lost
    unassigned_items = []
    for obj_name, m in all_models.items():
        if obj_name not in assigned:
            model_data = m.copy()
            model_data['icon'] = 'folder'
            model_data['display_name'] = m.get('name')
            unassigned_items.append(model_data)

    if unassigned_items:
        hubs.append({
            'id': 'other_modules',
            'title': _('Прочие разделы'),
            'badge': _('Модули'),
            'icon': 'folder',
            'description': _('Дополнительные приложения и системные разделы'),
            'items_count': len(unassigned_items),
            'items': unassigned_items,
        })

    return hubs
