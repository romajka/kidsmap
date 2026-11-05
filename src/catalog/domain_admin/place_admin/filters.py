"""Changelist filters for the place and event admin."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from catalog.models import (
    Place,
)


class PlaceCoordinatesFilter(admin.SimpleListFilter):
    title = _("Координаты")
    parameter_name = "coordinates_status"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Есть координаты")),
            ("no", _("Нужны координаты")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(km_saved_has_coordinates=True)
        if value == "no":
            return queryset.filter(km_saved_has_coordinates=False)
        return queryset

class PlaceMapReadyFilter(admin.SimpleListFilter):
    title = _("На карте")
    parameter_name = "map_ready_status"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Готово для карты")),
            ("no", _("Не готово для карты")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.filter(is_active=True).exclude(lat__isnull=True).exclude(lng__isnull=True)
        if value == "no":
            return queryset.filter(Q(is_active=False) | Q(lat__isnull=True) | Q(lng__isnull=True))
        return queryset

class PlacePublicationFilter(admin.SimpleListFilter):
    title = _("Публикация")
    parameter_name = "publication_state"

    def __init__(self, request, params, model, model_admin):
        self.model_admin = model_admin
        super().__init__(request, params, model, model_admin)

    def lookups(self, request, model_admin):
        return (
            ("published", _("Опубликованы")),
            ("ready", _("Готовы к публикации")),
            ("unpublished", _("Не опубликованы")),
            ("review", _("На модерации")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "published":
            return queryset.filter(km_in_public_catalog=True)
        if value == "ready":
            return queryset.filter(pk__in=self.model_admin._ready_place_ids(request))
        if value == "unpublished":
            return queryset.filter(km_in_public_catalog=False)
        if value == "review":
            return queryset.filter(Q(status=Place.STATUS_PENDING) | Q(
                km_saved_candidate_allowed=True, volunteer_revision__status="pending"))
        return queryset

class PlaceDeletedFilter(admin.SimpleListFilter):
    title = _("Удаление")
    parameter_name = "deleted_state"

    def lookups(self, request, model_admin):
        return (
            ("active", _("Не удалено")),
            ("deleted", _("В удаленных")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "deleted":
            return queryset.filter(deleted_at__isnull=False)
        if value == "active":
            return queryset.filter(deleted_at__isnull=True)
        # Default behavior: hide deleted places!
        return queryset.filter(deleted_at__isnull=True)

class PlaceCreatedByFilter(admin.SimpleListFilter):
    title = _("Добавил")
    parameter_name = "created_by"
    field_path = "created_by"

    def lookups(self, request, model_admin):
        model = getattr(model_admin, "model", Place)
        user_ids = (
            model.objects
            .filter(deleted_at__isnull=True)
            .exclude(created_by_id__isnull=True)
            .order_by()
            .values_list("created_by_id", flat=True)
            .distinct()
        )
        users = get_user_model().objects.filter(pk__in=user_ids).order_by("first_name", "last_name", "username")
        lookups = [(str(user.pk), model_admin._user_label(user)) for user in users]
        if model.objects.filter(deleted_at__isnull=True, created_by_id__isnull=True).exists():
            lookups.append(("__unknown__", _("Не указан — старые карточки")))
        return tuple(lookups)

    def queryset(self, request, queryset):
        value = self.value()
        if value == "__unknown__":
            return queryset.filter(created_by_id__isnull=True)
        if value and value.isdigit():
            return queryset.filter(created_by_id=int(value))
        return queryset

class PlaceCreatedDateFilter(admin.SimpleListFilter):
    title = _("Период создания")
    parameter_name = "created_date"
    field_path = "created_date"

    def lookups(self, request, model_admin):
        return (
            ("today", _("Сегодня")),
            ("7d", _("Новые (за 7 дней)")),
            ("30d", _("Новые (за 30 дней)")),
            ("90d", _("За 90 дней")),
            ("older_90d", _("Старые (более 90 дней)")),
            ("older_1y", _("Старые (более года)")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        now = timezone.now()
        if value == "today":
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=start_of_day)
        if value == "7d":
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=7))
        if value == "30d":
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=30))
        if value == "90d":
            return queryset.filter(created_at__gte=now - timezone.timedelta(days=90))
        if value == "older_90d":
            return queryset.filter(created_at__lt=now - timezone.timedelta(days=90))
        if value == "older_1y":
            return queryset.filter(created_at__lt=now - timezone.timedelta(days=365))
        return queryset

class PlaceSortFilter(admin.SimpleListFilter):
    title = _("Сортировка")
    parameter_name = "sort"
    field_path = "sort"

    def lookups(self, request, model_admin):
        return (
            ("created_desc", _("Создано: сначала новые")),
            ("created_asc", _("Создано: сначала старые")),
            ("updated_desc", _("Обновлено: сначала новые")),
            ("updated_asc", _("Обновлено: сначала старые")),
            ("name_asc", _("По названию (А → Я)")),
            ("name_desc", _("По названию (Я → А)")),
        )

    def queryset(self, request, queryset):
        return queryset

class EventDeletedFilter(admin.SimpleListFilter):
    title = _("Удаление")
    parameter_name = "deleted_at__isnull"

    def lookups(self, request, model_admin):
        return (
            ("True", _("Не удалено")),
            ("False", _("В удаленных")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "False":
            return queryset.filter(deleted_at__isnull=False)
        if value == "True":
            return queryset.filter(deleted_at__isnull=True)
        # Default behavior: hide deleted events!
        return queryset.filter(deleted_at__isnull=True)
