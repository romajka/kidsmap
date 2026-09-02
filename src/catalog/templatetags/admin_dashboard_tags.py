from django import template
from django.contrib.admin.views.main import PAGE_VAR
from django.contrib.auth import get_user_model
from catalog.models.place import Place, Event
from catalog.models.specialist import Specialist
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

