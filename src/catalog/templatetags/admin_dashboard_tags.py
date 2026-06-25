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
