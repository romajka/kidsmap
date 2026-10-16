"""Shared, whitelisted ordering for the Event and Specialist queues."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class QueueSortParameter(admin.SimpleListFilter):
    """Consume the toolbar parameter without adding another visible filter."""

    title = _("Сортировка")
    parameter_name = "sort"

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        return queryset


class QueueSortingAdminMixin:
    sort_orders = {
        "created_desc": ("-created_at", "-pk"),
        "created_asc": ("created_at", "pk"),
        "updated_desc": ("-updated_at", "-pk"),
        "updated_asc": ("updated_at", "pk"),
        "name_asc": ("name", "pk"),
        "name_desc": ("-name", "-pk"),
    }
    sort_labels = {
        "created_desc": _("Создано (новые)"),
        "created_asc": _("Создано (старые)"),
        "updated_desc": _("Обновлено (новые)"),
        "updated_asc": _("Обновлено (старые)"),
        "name_asc": _("По названию (А → Я)"),
        "name_desc": _("По названию (Я → А)"),
    }

    def _queue_sort_key(self, request):
        key = request.GET.get("sort")
        return key if key in self.sort_orders else "updated_desc"

    def get_ordering(self, request):
        return self.sort_orders[self._queue_sort_key(request)]

    def changelist_view(self, request, extra_context=None):
        key = self._queue_sort_key(request)
        context = {**(extra_context or {}), "km_current_sort": key,
                   "km_current_sort_label": self.sort_labels[key]}
        return super().changelist_view(request, extra_context=context)
