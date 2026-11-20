from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import LegalAcceptance, LegalDocumentSnapshot
from .services import RELEASES, published_document


class ReadOnlyRecordAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LegalDocumentSnapshot)
class LegalDocumentSnapshotAdmin(ReadOnlyRecordAdmin):
    list_display = ("title", "version", "language", "generation", "updated_on")
    list_filter = ("slug", "language", "version")
    search_fields = ("title", "fingerprint")
    readonly_fields = ("is_current",)

    @admin.display(boolean=True, description=_("Опубликована сейчас"))
    def is_current(self, obj):
        return obj.slug in RELEASES and published_document(obj.slug, obj.language).fingerprint == obj.fingerprint


@admin.register(LegalAcceptance)
class LegalAcceptanceAdmin(ReadOnlyRecordAdmin):
    list_display = ("user", "document", "accepted_at")
    list_select_related = ("user", "document")
    list_filter = ("document__slug", "document__version", "document__language")
    search_fields = ("=user__username", "=user__email")
    ordering = ("-accepted_at", "-pk")
