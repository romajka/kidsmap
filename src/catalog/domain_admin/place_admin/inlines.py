"""Admin inlines for place and event photos and audit history."""

from django.contrib import admin

from catalog.models import (
    PlacePhoto,
    PlaceChangeAudit,
    EventPhoto,
)
from .forms import CandidatePlacePhotoFormSet


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
    formset = CandidatePlacePhotoFormSet
    template = "admin/catalog/place/placephoto_inline.html"
    extra = 0
    max_num = 10
    fields = ("image", "caption", "order")
    ordering = ("order", "id")

class EventPhotoInline(admin.TabularInline):
    model = EventPhoto
    template = "admin/catalog/place/placephoto_inline.html"
    extra = 0
    max_num = 10
    fields = ("image", "caption", "order")
    ordering = ("order", "id")

class PlaceChangeAuditInline(admin.TabularInline):
    model = PlaceChangeAudit
    extra = 0
    can_delete = False
    fields = ("created_at", "changed_by", "source", "field_name", "old_value", "new_value")
    readonly_fields = fields
    ordering = ("-created_at",)

    def has_add_permission(self, request, obj=None):
        return False
