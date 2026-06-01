from django import template
from django.contrib.auth import get_user_model
from catalog.models.place import Place, Event
from catalog.models.review import PlaceReview
from catalog.models.owner import PlaceOwnershipRequest

register = template.Library()
User = get_user_model()

@register.simple_tag
def get_dashboard_stats():
    return {
        'total_places': Place.objects.count(),
        'places_published': Place.objects.filter(status='published').count(),
        'places_pending': Place.objects.filter(status='pending').count(),
        'events_pending': Event.objects.filter(status='pending').count(),
        'events_active': Event.objects.filter(status='published').count(),
        'reviews_pending': PlaceReview.objects.filter(status='pending').count(),
        'requests_pending': PlaceOwnershipRequest.objects.filter(status='PENDING').count(),
        'total_users': User.objects.count(),
        'total_events': Event.objects.count(),
    }
