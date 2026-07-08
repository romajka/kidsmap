from django import template
from django.contrib.auth import get_user_model
from catalog.models.place import Place, Event
from catalog.models.review import PlaceReview
from catalog.models.owner import PlaceOwnershipRequest
from catalog.services.content_quality import public_place_queryset
from django.utils import timezone

register = template.Library()
User = get_user_model()


@register.simple_tag
def admin_filter_choices(cl, spec):
    return list(spec.choices(cl))


@register.simple_tag
def get_dashboard_stats():
    public_places_count = public_place_queryset(Place.objects.all()).count()
    public_events_count = Event.objects.filter(
        status=Event.STATUS_PUBLISHED,
        deleted_at__isnull=True,
        start_datetime__isnull=False,
        end_datetime__gte=timezone.now(),
    ).count()

    places_pending = Place.objects.filter(status=Place.STATUS_PENDING).count()
    events_pending = Event.objects.filter(status=Event.STATUS_PENDING).count()
    reviews_pending = PlaceReview.objects.filter(status=PlaceReview.STATUS_PENDING).count()
    requests_pending = PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
    
    total_pending = places_pending + events_pending + reviews_pending + requests_pending

    return {
        'kpi': {
            'total_places': Place.objects.count(),
            'places_published': public_places_count,
            'total_events': Event.objects.count(),
            'events_active': public_events_count,
            'total_users': User.objects.filter(is_staff=False, is_superuser=False).count(),
        },
        'pending': {
            'total': total_pending,
            'places': places_pending,
            'events': events_pending,
            'reviews': reviews_pending,
            'requests': requests_pending,
        }
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
