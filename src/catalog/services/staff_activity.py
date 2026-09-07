"""Read-only creator statistics. Live state and proposed revisions are independent."""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from catalog.models import Place


def staff_activity_context(request, user, admin_site):
    places = Place.objects.filter(created_by=user)
    present = Q(deleted_at__isnull=True)
    filters = {
        'total': Q(),
        'published': present & Q(status=Place.STATUS_PUBLISHED, is_active=True),
        'draft': present & Q(status=Place.STATUS_DRAFT),
        'pending': present & Q(status=Place.STATUS_PENDING),
        'rejected': present & Q(status=Place.STATUS_REJECTED),
        'hidden': present & Q(status=Place.STATUS_PUBLISHED, is_active=False),
        'deleted': Q(deleted_at__isnull=False),
        **{f'revision_{state}': present & Q(volunteer_revision__status=state)
           for state in ('draft', 'pending', 'rejected')},
    }
    labels = {
        'total': _('Всего создано'), 'published': _('Опубликовано'),
        'draft': _('Черновики мест'), 'pending': _('Места на модерации'),
        'rejected': _('Отклонённые места'), 'hidden': _('Снято с публикации'),
        'deleted': _('Удалённые места'), 'revision_draft': _('Черновики правок'),
        'revision_pending': _('Правки на проверке'), 'revision_rejected': _('Правки на доработке'),
    }
    stats = places.aggregate(**{key: Count('pk', filter=value) for key, value in filters.items()})
    state = request.GET.get('place_state', 'total')
    if state not in filters:
        state = 'total'
    search = request.GET.get('place_q', '').strip()[:200]
    selected = places.filter(filters[state])
    if search:
        selected = selected.filter(Q(name_az__icontains=search) | Q(name_ru__icontains=search) | Q(name_en__icontains=search))
    page = Paginator(selected.select_related('volunteer_revision').order_by('-created_at', '-pk'), 15).get_page(request.GET.get('place_page'))
    place_admin = admin_site._registry.get(Place)
    for place in page:
        place.staff_change_url = ''
        if place_admin and place_admin.has_view_or_change_permission(request, place):
            place.staff_change_url = reverse('admin:catalog_place_change', args=[place.pk])
        revision = getattr(place, 'volunteer_revision', None)
        place.staff_revision = revision
        place.staff_review_url = (
            reverse('admin:volunteer_review', args=[place.pk])
            if revision and revision.status == 'pending' and request.user.is_superuser else ''
        )
    return {
        'staff_stats': stats, 'staff_places': page,
        'staff_place_state': state, 'staff_place_query': search,
        'staff_stat_items': [{'key': key, 'label': labels[key], 'count': stats[key]} for key in filters],
    }
