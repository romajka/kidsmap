from django.contrib import admin
from catalog.domain_admin.place import PlaceAdmin, EventAdmin
from catalog.domain_admin.review import PlaceReviewAdmin
from catalog.domain_admin.owner import PlaceOwnershipRequestAdmin
from catalog.models.owner import PlaceOwnershipRequest

from .models import (
    ModerationPlace, 
    ModerationEvent, 
    ModerationReview, 
    ModerationPlaceOwnershipRequest
)

class ModerationPlaceAdmin(PlaceAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='pending')

class ModerationEventAdmin(EventAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='pending')

class ModerationReviewAdmin(PlaceReviewAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status='pending')

admin.site.register(ModerationPlace, ModerationPlaceAdmin)
admin.site.register(ModerationEvent, ModerationEventAdmin)
admin.site.register(ModerationReview, ModerationReviewAdmin)

# Unregister from catalog and move to moderation
try:
    admin.site.unregister(PlaceOwnershipRequest)
except admin.sites.NotRegistered:
    pass
admin.site.register(ModerationPlaceOwnershipRequest, PlaceOwnershipRequestAdmin)
