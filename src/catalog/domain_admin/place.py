from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django import forms
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from django.utils.html import format_html, format_html_join

from catalog.models import Place, PlacePhoto, PlaceChangeAudit, Event, PlaceReviewsByClub
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.content_quality import place_quality_check
from catalog.services.geocoding import PlaceGeocodingService
from .review import PlaceReviewInline


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
    extra = 0
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


class PlaceAdminForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = "__all__"
        labels = {
            "slug": _("URL-слаг"),
            "name_ru": _("Название (Русский)"),
            "name_az": _("Название (Азербайджанский)"),
            "name_en": _("Название (English)"),
            "description_ru": _("Описание (Русский)"),
            "description_az": _("Описание (Азербайджанский)"),
            "description_en": _("Описание (English)"),
            "likes_count": _("Количество лайков"),
            "rating_avg": _("Средний рейтинг"),
            "rating_count": _("Количество отзывов"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "lesson_duration_minutes": _("Длительность урока (мин)"),
        }


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
            return queryset.exclude(lat__isnull=True).exclude(lng__isnull=True)
        if value == "no":
            return queryset.filter(Q(lat__isnull=True) | Q(lng__isnull=True))
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
        if value == "active":
            return queryset.filter(deleted_at__isnull=True)
        if value == "deleted":
            return queryset.filter(deleted_at__isnull=False)
        return queryset


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "category",
        "start_datetime",
        "end_datetime",
        "owner",
        "status",
        "updated_at",
    )
    list_filter = ("status", "category", "start_datetime", "owner")
    search_fields = ("name", "name_az", "name_ru", "name_en", "address", "phone", "owner__username", "owner__email")
    readonly_fields = ("slug", "created_at", "updated_at")
    list_select_related = ("owner", "related_place")
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "owner",
                    "related_place",
                    "status",
                    "rejection_reason",
                    "published_at",
                    "name",
                    "slug",
                    "name_az",
                    "name_ru",
                    "name_en",
                    "description_az",
                    "description_ru",
                    "description_en",
                    "category",
                )
            },
        ),
        (
            _("Дата, место и контакты"),
            {
                "fields": (
                    "start_datetime",
                    "end_datetime",
                    "age_from",
                    "age_to",
                    "price_text",
                    "address",
                    "phone",
                    "instagram",
                    "photo",
                )
            },
        ),
        (_("Служебное"), {"fields": ("moderation_note", "deleted_at", "created_at", "updated_at")}),
    )

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        return obj.name_i18n()

    def save_model(self, request, obj, form, change):
        if obj.status == Event.STATUS_PUBLISHED and not obj.published_at:
            obj.published_at = timezone.now()
        if obj.status != Event.STATUS_REJECTED:
            obj.rejection_reason = obj.rejection_reason if obj.status == Event.STATUS_PUBLISHED else obj.rejection_reason
        super().save_model(request, obj, form, change)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    AUDIT_TRACKED_FIELDS = (
        "name",
        "name_ru",
        "name_az",
        "name_en",
        "description_ru",
        "description_az",
        "description_en",
        "category",
        "subcategory",
        "age_from",
        "age_to",
        "district",
        "metro",
        "address",
        "phone1",
        "owner_id",
        "instagram",
        "website",
        "schedule",
        "lesson_duration_minutes",
        "is_temporary",
        "temporary_start",
        "temporary_end",
        "lat",
        "lng",
        "price_from",
        "price_to",
        "price_per_lesson",
        "price_per_month",
        "price_per_8_lessons",
        "extra_conditions",
        "additional_info",
        "is_active",
        "is_verified",
        "status",
        "rejection_reason",
        "last_verified_at",
        "published_at",
        "deleted_at",
        "deleted_by_id",
    )
    form = PlaceAdminForm
    geocoding_service = PlaceGeocodingService.build_default()
    place_audit_repository = DjangoPlaceChangeAuditRepository()
    change_list_template = "admin/catalog/place/change_list.html"
    change_form_template = "admin/catalog/place/change_form.html"
    delete_confirmation_template = "admin/catalog/place_delete_confirmation.html"
    delete_selected_confirmation_template = "admin/catalog/place_delete_selected_confirmation.html"
    list_select_related = ("owner",)
    list_display = (
        "display_name",
        "category",
        "location_summary",
        "publication_status",
        "map_status_summary",
        "owner_display",
        "engagement_summary",
        "updated_at",
        "row_actions",
    )
    list_filter = (
        PlaceDeletedFilter,
        PlaceCoordinatesFilter,
        PlaceMapReadyFilter,
        "category",
        "is_temporary",
        "district",
        "metro",
        "owner",
        "is_active",
        "is_verified",
        "status",
        "age_from",
        "age_to",
    )
    search_fields = ("name_ru", "name_en", "name", "address", "instagram", "phone1", "owner__username", "owner__email")
    readonly_fields = (
        "slug",
        "rating_avg",
        "rating_count",
        "lifecycle_status_display",
        "coordinates_status_display",
        "map_ready_status_display",
        "quality_status_display",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_per_page = 30
    save_on_top = True

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        from django.conf import settings
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    actions = (
        "mark_active",
        "mark_inactive",
        "mark_draft",
        "mark_verified",
        "mark_unverified",
        "mark_pending",
        "mark_published",
        "mark_rejected",
        "move_selected_to_deleted",
        "restore_selected",
        "refresh_coordinates",
    )
    inlines = [PlacePhotoInline, PlaceReviewInline, PlaceChangeAuditInline]
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "subcategory",
                    "is_temporary",
                    "temporary_start",
                    "temporary_end",
                    "is_active",
                    "is_verified",
                    "status",
                    "rejection_reason",
                    "last_verified_at",
                    "published_at",
                    "owner",
                    "likes_count",
                    "rating_avg",
                    "rating_count",
                    "lifecycle_status_display",
                    "quality_status_display",
                )
            },
        ),
        (_("Названия и описания (i18n)"), {"classes": ("collapse",), "fields": ("name_ru", "name_az", "name_en", "description_ru", "description_az", "description_en")}),
        (
            _("Возраст и цена"),
            {
                "fields": (
                    "age_from",
                    "age_to",
                    "price_from",
                    "price_to",
                    "price_per_lesson",
                    "price_per_month",
                    "price_per_8_lessons",
                    "lesson_duration_minutes",
                )
            },
        ),
        (_("Локация"), {"fields": ("district", "metro", "address", "lat", "lng", "coordinates_status_display", "map_ready_status_display")}),
        (_("Контакты"), {"fields": ("phone1", "instagram", "website", "schedule", "extra_conditions", "additional_info")}),
        (_("Фото"), {"fields": ("cover_photo", "photo")}),
        (_("Удаление"), {"classes": ("collapse",), "fields": ("deleted_at", "deleted_by")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_ru or obj.name
        meta: list[str] = []
        if obj.slug:
            meta.append(f"ID {obj.pk} · /{obj.slug}/")
        else:
            meta.append(f"ID {obj.pk}")
        if obj.is_deleted:
            meta.append(str(_("Сейчас скрыта в разделе удалённых")))
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div>',
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((item,) for item in meta)),
        )

    def _render_place_state_badge(self, *, label: str, tone: str = "muted"):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            tone,
            label,
        )

    @admin.display(description=_("Статус"))
    def lifecycle_status(self, obj):
        if obj.is_deleted:
            return self._render_place_state_badge(label=_("В удаленных"), tone="muted")
        if obj.is_active:
            return self._render_place_state_badge(label=_("Опубликовано"), tone="good")
        return self._render_place_state_badge(label=_("Неактивно"), tone="warn")

    @admin.display(description=_("Статус"))
    def lifecycle_status_display(self, obj):
        return self.lifecycle_status(obj)

    @admin.display(description=_("Координаты"))
    def coordinates_status(self, obj):
        return self._render_place_state_badge(
            label=_("Есть координаты") if obj.has_coordinates else _("Нужны координаты"),
            tone="good" if obj.has_coordinates else "warn",
        )

    @admin.display(description=_("Координаты"))
    def coordinates_status_display(self, obj):
        return self.coordinates_status(obj)

    @admin.display(description=_("На карте"))
    def map_ready_status(self, obj):
        return self._render_place_state_badge(
            label=_("Готово для карты") if obj.is_map_ready else _("Не готово для карты"),
            tone="good" if obj.is_map_ready else "muted",
        )

    @admin.display(description=_("На карте"))
    def map_ready_status_display(self, obj):
        return self.map_ready_status(obj)

    @admin.display(description=_("Качество"))
    def quality_status_display(self, obj):
        check = place_quality_check(obj)
        tone = "good" if check.is_ready else "warn"
        label = _("Готово к публикации") if check.is_ready else _("Нужна доработка")
        details = ", ".join(check.errors[:4]) if check.errors else _("Критичных замечаний нет")
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-badge km-admin-badge--{}">{} / 100</span><span class="km-admin-meta">{} · {}</span></div>',
            tone,
            check.score,
            label,
            details,
        )

    @admin.display(description=_("Локация"))
    def location_summary(self, obj):
        lines: list[str] = []
        if obj.district:
            lines.append(str(obj.district))
        if obj.metro:
            lines.append(str(obj.metro))
        if obj.address:
            lines.append(str(obj.address))

        if not lines:
            return format_html('<div class="km-admin-stack"><span class="km-admin-meta">{}</span></div>', _("Локация не заполнена"))

        title = " / ".join(lines[:2])
        address_line = lines[2] if len(lines) > 2 else ""
        if address_line:
            return format_html(
                '<div class="km-admin-stack">'
                '<span class="km-admin-title">{}</span>'
                '<span class="km-admin-meta">{}</span>'
                "</div>",
                title,
                address_line,
            )
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>',
            title,
        )

    @admin.display(description=_("Публикация"))
    def publication_status(self, obj):
        status_tone = {
            obj.STATUS_DRAFT: "muted",
            obj.STATUS_PENDING: "warn",
            obj.STATUS_PUBLISHED: "good",
            obj.STATUS_REJECTED: "danger",
        }.get(obj.status, "muted")
        badges = [
            self._render_place_state_badge(label=obj.get_status_display(), tone=status_tone),
            self.lifecycle_status(obj),
        ]
        badges.append(
            self._render_place_state_badge(
                label=_("Проверено") if obj.is_verified else _("Без проверки"),
                tone="good" if obj.is_verified else "warn",
            )
        )
        badges.append(
            self._render_place_state_badge(
                label=_("Временное") if obj.is_temporary else _("Постоянное"),
                tone="info" if obj.is_temporary else "muted",
            )
        )
        return format_html(
            '<div class="km-admin-stack"><div class="km-admin-badges">{} {} {} {}</div></div>',
            badges[0],
            badges[1],
            badges[2],
            badges[3],
        )

    @admin.display(description=_("Карта"))
    def map_status_summary(self, obj):
        coords_line = _("lat %(lat)s, lng %(lng)s") % {"lat": round(obj.lat, 5), "lng": round(obj.lng, 5)} if obj.has_coordinates else _("Координаты не заполнены")
        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">{} {}</div>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            self.coordinates_status(obj),
            self.map_ready_status(obj),
            coords_line,
        )

    @admin.display(description=_("Владелец"))
    def owner_display(self, obj):
        if not obj.owner:
            return format_html('<div class="km-admin-stack"><span class="km-admin-meta">{}</span></div>', _("Не назначен"))

        owner_email = (obj.owner.email or "").strip()
        if owner_email:
            return format_html(
                '<div class="km-admin-stack">'
                '<span class="km-admin-title">{}</span>'
                '<span class="km-admin-meta">{}</span>'
                "</div>",
                obj.owner.username,
                owner_email,
            )
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>',
            obj.owner.username,
        )

    @admin.display(description=_("Вовлеченность"))
    def engagement_summary(self, obj):
        likes_value = int(obj.likes_count or 0)
        rating_value = f"{float(obj.rating_avg or 0):.1f}"
        reviews_value = int(obj.rating_count or 0)
        return format_html(
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">♥ {} · ★ {}</span>'
            '<span class="km-admin-meta">{}: {}</span>'
            "</div>",
            likes_value,
            rating_value,
            _("Отзывы"),
            reviews_value,
        )

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def get_deleted_objects(self, objs, request):
        objects = list(objs)
        if not objects:
            return [], {}, set(), []

        model_label = str(self.opts.verbose_name if len(objects) == 1 else self.opts.verbose_name_plural)
        deleted_objects = [str(obj) for obj in objects]
        model_count = {model_label: len(objects)}
        return deleted_objects, model_count, set(), []

    def _build_soft_delete_changes(self, *, place: Place, previous: dict[str, object]) -> dict[str, tuple[object, object]]:
        changes: dict[str, tuple[object, object]] = {}
        for field_name in ("is_active", "deleted_at", "deleted_by_id"):
            old_value = previous.get(field_name)
            new_value = getattr(place, field_name)
            if old_value != new_value:
                changes[field_name] = (old_value, new_value)
        return changes

    def _soft_delete_place(self, *, place: Place, user) -> bool:
        previous = {
            "is_active": place.is_active,
            "deleted_at": place.deleted_at,
            "deleted_by_id": place.deleted_by_id,
        }
        changed = place.soft_delete(deleted_by=user)
        if changed:
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=user,
                source=PlaceChangeAudit.SOURCE_ADMIN,
                changes=self._build_soft_delete_changes(place=place, previous=previous),
            )
        return changed

    def _restore_place(self, *, place: Place, user, activate: bool = False) -> bool:
        previous = {
            "is_active": place.is_active,
            "deleted_at": place.deleted_at,
            "deleted_by_id": place.deleted_by_id,
        }
        changed = place.restore_from_deleted(activate=activate)
        if changed:
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=user,
                source=PlaceChangeAudit.SOURCE_ADMIN,
                changes=self._build_soft_delete_changes(place=place, previous=previous),
            )
        return changed

    def _response_after_place_soft_delete(self, request):
        changelist_url = reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
            current_app=self.admin_site.name,
        )
        return HttpResponseRedirect(changelist_url)

    @staticmethod
    def _build_coordinate_changes(*, place: Place, previous_coordinates: dict[str, object]) -> dict[str, tuple[object, object]]:
        coordinate_changes: dict[str, tuple[object, object]] = {}
        for field_name in ("lat", "lng"):
            old_value = previous_coordinates[field_name]
            new_value = getattr(place, field_name)
            if old_value != new_value:
                coordinate_changes[field_name] = (old_value, new_value)
        return coordinate_changes

    def _refresh_place_coordinates_with_audit(self, *, place: Place, changed_by):
        previous_coordinates = {"lat": place.lat, "lng": place.lng}
        geocoding_result = self.geocoding_service.geocode_place(place=place, overwrite=True)
        coordinate_changes = self._build_coordinate_changes(place=place, previous_coordinates=previous_coordinates)
        if coordinate_changes:
            self.place_audit_repository.create_entries(
                place=place,
                changed_by=changed_by,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                changes=coordinate_changes,
            )
        return geocoding_result

    def _place_change_url(self, obj: Place) -> str:
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_change",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

    def _place_delete_url(self, obj: Place) -> str:
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_delete",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

    def _place_restore_url(self, obj: Place) -> str:
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_restore",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

    def _build_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
        params = request.GET.copy()
        params.pop("p", None)
        for key in clear:
            params.pop(key, None)
        for key, value in updates.items():
            params.pop(key, None)
            if value not in (None, ""):
                params[key] = value
        encoded = params.urlencode()
        return f"?{encoded}" if encoded else ""

    def _place_quick_filters(self, request):
        status_keys = ("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")
        current_deleted = request.GET.get("deleted_state")
        current_active = request.GET.get("is_active__exact")
        current_coordinates = request.GET.get("coordinates_status")
        current_map_ready = request.GET.get("map_ready_status")
        current_status = request.GET.get("status__exact")
        return (
            {
                "label": _("Все карточки"),
                "url": self._build_changelist_query_string(request, clear=status_keys),
                "active": not any((current_deleted, current_active, current_coordinates, current_map_ready, current_status)),
            },
            {
                "label": _("Опубликованы"),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="1",
                ),
                "active": current_deleted == "active" and current_active == "1" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Неактивные"),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="0",
                ),
                "active": current_deleted == "active" and current_active == "0" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Черновики"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_DRAFT),
                "active": current_status == Place.STATUS_DRAFT and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("На модерации"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_PENDING),
                "active": current_status == Place.STATUS_PENDING and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("Отклонены"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_REJECTED),
                "active": current_status == Place.STATUS_REJECTED and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("В удалённых"),
                "url": self._build_changelist_query_string(request, clear=status_keys, deleted_state="deleted"),
                "active": current_deleted == "deleted" and not current_active and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Без координат"),
                "url": self._build_changelist_query_string(request, clear=status_keys, coordinates_status="no"),
                "active": current_coordinates == "no" and not current_deleted and not current_active and not current_map_ready and not current_status,
            },
            {
                "label": _("Не готовы для карты"),
                "url": self._build_changelist_query_string(request, clear=status_keys, map_ready_status="no"),
                "active": current_map_ready == "no" and not current_deleted and not current_active and not current_coordinates and not current_status,
            },
        )

    def _place_bulk_actions(self):
        return (
            {
                "name": "mark_active",
                "label": _("Опубликовать"),
                "tone": "good",
                "description": _("Сделать выбранные карточки активными и вернуть их в каталог."),
            },
            {
                "name": "mark_inactive",
                "label": _("Снять с публикации"),
                "tone": "muted",
                "description": _("Оставить карточки в базе, но скрыть их с сайта."),
            },
            {
                "name": "mark_verified",
                "label": _("Отметить проверенными"),
                "tone": "info",
                "description": _("Показать, что карточки прошли проверку."),
            },
            {
                "name": "refresh_coordinates",
                "label": _("Обновить координаты"),
                "tone": "info",
                "description": _("Повторно рассчитать координаты по адресу."),
            },
            {
                "name": "restore_selected",
                "label": _("Восстановить"),
                "tone": "good",
                "confirm": _("Вы собираетесь восстановить {count} выбранных карточек из удалённых.\n\nПосле восстановления карточки останутся неактивными, их можно будет отдельно опубликовать.\n\nПродолжить?"),
                "description": _("Вернуть карточки из удалённых в базовый список."),
            },
            {
                "name": "move_selected_to_deleted",
                "label": _("В удалённые"),
                "tone": "danger",
                "confirm": _("Вы собираетесь переместить в удалённые {count} выбранных карточек.\n\nКарточки исчезнут с сайта, но останутся в базе и их можно будет восстановить.\n\nПродолжить?"),
                "description": _("Безопасное мягкое удаление с возможностью восстановления."),
            },
        )

    def _build_admin_coordinate_refresh_feedback(self, *, geocoding_result, saved_prefix: str) -> tuple[str, int]:
        point = geocoding_result.point
        if geocoding_result.updated and point is not None:
            return (
                _("%(prefix)s Координаты обновлены: %(lat).6f, %(lng).6f.")
                % {
                    "prefix": saved_prefix,
                    "lat": point.lat,
                    "lng": point.lng,
                },
                messages.SUCCESS,
            )
        if geocoding_result.reason in {"unchanged", "coordinates_present"}:
            return _("%(prefix)s Координаты уже актуальны.") % {"prefix": saved_prefix}, messages.SUCCESS
        if geocoding_result.reason == "provider_not_configured":
            return (
                _("%(prefix)s Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY.")
                % {"prefix": saved_prefix},
                messages.ERROR,
            )
        if geocoding_result.reason == "not_found":
            return (
                _("%(prefix)s Координаты по указанному адресу не найдены.")
                % {"prefix": saved_prefix},
                messages.WARNING,
            )
        return _("%(prefix)s Для геокодирования нужен адрес.") % {"prefix": saved_prefix}, messages.WARNING

    def _handle_refresh_coordinates_submit(self, request, obj: Place, *, saved_prefix: str):
        geocoding_result = self._refresh_place_coordinates_with_audit(
            place=obj,
            changed_by=request.user,
        )
        message, level = self._build_admin_coordinate_refresh_feedback(
            geocoding_result=geocoding_result,
            saved_prefix=saved_prefix,
        )
        self.message_user(request, message, level=level)
        return HttpResponseRedirect(self._place_change_url(obj))

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/restore/",
                self.admin_site.admin_view(self.restore_view),
                name="catalog_place_restore",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "place_quick_filters": self._place_quick_filters(request),
            "place_bulk_actions": self._place_bulk_actions(),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description=_("Сделать активными"))
    def mark_active(self, request, queryset):
        updated_count = queryset.update(
            is_active=True,
            deleted_at=None,
            deleted_by=None,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "Опубликована %(count)d карточка.",
                "Опубликовано %(count)d карточки.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Сделать неактивными"))
    def mark_inactive(self, request, queryset):
        updated_count = queryset.update(is_active=False, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                "С публикации снята %(count)d карточка.",
                "С публикации снято %(count)d карточки.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Вернуть в черновик"))
    def mark_draft(self, request, queryset):
        updated_count = queryset.update(
            status=Place.STATUS_DRAFT,
            is_active=False,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("%(count)d карточка переведена в черновик.", "%(count)d карточки переведены в черновик.", updated_count)
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отметить как проверенные"))
    def mark_verified(self, request, queryset):
        updated_count = queryset.update(is_verified=True, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                "Отмечена как проверенная %(count)d карточка.",
                "Отмечено как проверенные %(count)d карточки.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Снять отметку проверки"))
    def mark_unverified(self, request, queryset):
        updated_count = queryset.update(is_verified=False, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext(
                "Снята отметка проверки у %(count)d карточки.",
                "Снята отметка проверки у %(count)d карточек.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отправить на модерацию"))
    def mark_pending(self, request, queryset):
        updated_count = queryset.update(status=Place.STATUS_PENDING, rejection_reason="", updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("%(count)d карточка отправлена на модерацию.", "%(count)d карточки отправлены на модерацию.", updated_count)
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Опубликовать после проверки качества"))
    def mark_published(self, request, queryset):
        now = timezone.now()
        published_count = 0
        skipped_count = 0
        for place in queryset.prefetch_related("gallery").iterator():
            if not place_quality_check(place).is_ready:
                skipped_count += 1
                continue
            place.status = Place.STATUS_PUBLISHED
            place.is_active = True
            place.rejection_reason = ""
            if place.published_at is None:
                place.published_at = now
            place.save(update_fields=["status", "is_active", "rejection_reason", "published_at", "updated_at"])
            published_count += 1
        self.message_user(
            request,
            _("Опубликовано карточек: %(published)d. Пропущено из-за качества: %(skipped)d.")
            % {"published": published_count, "skipped": skipped_count},
            level=messages.SUCCESS if published_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить карточки"))
    def mark_rejected(self, request, queryset):
        default_reason = _("Məkan admin moderasiyasından keçmədi. Zəhmət olmasa məlumatları yeniləyin.")
        updated_count = 0
        for place in queryset.iterator():
            place.status = Place.STATUS_REJECTED
            place.is_active = False
            if not (place.rejection_reason or "").strip():
                place.rejection_reason = default_reason
            place.save(update_fields=["status", "is_active", "rejection_reason", "updated_at"])
            updated_count += 1
        self.message_user(
            request,
            ngettext("%(count)d карточка отклонена.", "%(count)d карточки отклонены.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Переместить выбранные кружки в удаленные"))
    def move_selected_to_deleted(self, request, queryset):
        if request.POST.get("post"):
            moved_count = 0
            for place in queryset.iterator():
                if self._soft_delete_place(place=place, user=request.user):
                    moved_count += 1

            self.message_user(
                request,
                ngettext(
                    "В удалённые перемещена %(count)d карточка. Её можно восстановить из админки.",
                    "В удалённые перемещено %(count)d карточки. Их можно восстановить из админки.",
                    moved_count,
                )
                % {"count": moved_count},
                level=messages.SUCCESS if moved_count else messages.WARNING,
            )
            return None

        context = {
            **self.admin_site.each_context(request),
            "title": _("Переместить выбранные кружки в удаленные"),
            "subtitle": None,
            "objects_name": str(self.opts.verbose_name_plural),
            "queryset": queryset,
            "opts": self.opts,
            "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
            "action_name": "move_selected_to_deleted",
            "media": self.media,
            "undo_hint": _("Это мягкое удаление: карточки останутся в базе и их можно будет восстановить."),
        }
        return TemplateResponse(request, self.delete_selected_confirmation_template, context)

    @admin.action(description=_("Восстановить выбранные кружки из удаленных"))
    def restore_selected(self, request, queryset):
        restored_count = 0
        for place in queryset.iterator():
            if self._restore_place(place=place, user=request.user, activate=False):
                restored_count += 1

        self.message_user(
            request,
            ngettext(
                "Из удалённых восстановлена %(count)d карточка. Она осталась неактивной.",
                "Из удалённых восстановлено %(count)d карточки. Они остались неактивными.",
                restored_count,
            )
            % {"count": restored_count},
            level=messages.SUCCESS if restored_count else messages.WARNING,
        )

    @admin.action(description=_("Повторно геокодировать выбранные карточки"))
    def refresh_coordinates(self, request, queryset):
        if not self.geocoding_service.geocoding_repository.is_configured():
            self.message_user(
                request,
                _("Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY."),
                level=messages.ERROR,
            )
            return

        updated_count = 0
        unchanged_count = 0
        missing_query_count = 0
        not_found_count = 0

        for place in queryset.iterator():
            geocoding_result = self._refresh_place_coordinates_with_audit(
                place=place,
                changed_by=request.user,
            )
            if geocoding_result.updated:
                updated_count += 1
                continue

            if geocoding_result.reason in {"unchanged", "coordinates_present"}:
                unchanged_count += 1
            elif geocoding_result.reason == "not_found":
                not_found_count += 1
            else:
                missing_query_count += 1

        self.message_user(
            request,
            _("Повторное геокодирование завершено: обновлено %(updated)s, без изменений %(unchanged)s, без адреса %(missing)s, не найдено %(not_found)s.")
            % {
                "updated": updated_count,
                "unchanged": unchanged_count,
                "missing": missing_query_count,
                "not_found": not_found_count,
            },
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            changelist_url = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(changelist_url)

        deleted_objects, model_count, perms_needed, protected = self.get_deleted_objects([obj], request)
        if request.POST and not protected:
            if perms_needed:
                raise PermissionDenied
            moved = self._soft_delete_place(place=obj, user=request.user)
            if moved:
                self.message_user(
                    request,
                    _("Карточка “%(name)s” перемещена в удалённые. Её можно восстановить из списка карточек.") % {"name": obj},
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    _("Карточка “%(name)s” уже находится в удалённых.") % {"name": obj},
                    level=messages.WARNING,
                )
            return self._response_after_place_soft_delete(request)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Переместить в удаленные"),
            "subtitle": None,
            "object_name": str(self.opts.verbose_name),
            "object": obj,
            "deleted_objects": deleted_objects,
            "model_count": dict(model_count).items(),
            "perms_lacking": perms_needed,
            "protected": protected,
            "opts": self.opts,
            "app_label": self.opts.app_label,
            "preserved_filters": self.get_preserved_filters(request),
            **(extra_context or {}),
        }
        return self.render_delete_form(request, context)

    def restore_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            changelist_url = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(changelist_url)

        if request.method == "POST":
            restored = self._restore_place(place=obj, user=request.user, activate=False)
            if restored:
                self.message_user(
                    request,
                    _("Карточка “%(name)s” восстановлена из удалённых и оставлена неактивной.") % {"name": obj},
                    level=messages.SUCCESS,
                )
            else:
                self.message_user(
                    request,
                    _("Карточка “%(name)s” уже доступна в основном списке.") % {"name": obj},
                    level=messages.WARNING,
                )
            changelist_url = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
                current_app=self.admin_site.name,
            )
            return HttpResponseRedirect(changelist_url)

        context = {
            **self.admin_site.each_context(request),
            "title": _("Восстановить карточку"),
            "subtitle": None,
            "object_name": str(self.opts.verbose_name),
            "object": obj,
            "opts": self.opts,
            "app_label": self.opts.app_label,
            "preserved_filters": self.get_preserved_filters(request),
        }
        return TemplateResponse(request, "admin/catalog/place_restore_confirmation.html", context)

    def delete_model(self, request, obj):
        self._soft_delete_place(place=obj, user=request.user)

    def delete_queryset(self, request, queryset):
        for place in queryset.iterator():
            self._soft_delete_place(place=place, user=request.user)

    def _stringify_audit_value(self, value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def save_model(self, request, obj, form, change):
        old_values = {}
        if change and obj.pk:
            old_obj = Place.objects.filter(pk=obj.pk).first()
            if old_obj:
                for field in self.AUDIT_TRACKED_FIELDS:
                    old_values[field] = getattr(old_obj, field)

        super().save_model(request, obj, form, change)

        if change and old_values:
            audit_entries = []
            for field_name in self.AUDIT_TRACKED_FIELDS:
                old_value = old_values.get(field_name)
                new_value = getattr(obj, field_name)
                if old_value == new_value:
                    continue
                audit_entries.append(
                    PlaceChangeAudit(
                        place=obj,
                        changed_by=request.user,
                        source=PlaceChangeAudit.SOURCE_ADMIN,
                        field_name=field_name,
                        old_value=self._stringify_audit_value(old_value),
                        new_value=self._stringify_audit_value(new_value),
                    )
                )
            if audit_entries:
                PlaceChangeAudit.objects.bulk_create(audit_entries)

    def response_add(self, request, obj, post_url_continue=None):
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Карточка сохранена."),
            )
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Изменения сохранены."),
            )
        return super().response_change(request, obj)

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = self._place_change_url(obj)
        action_links = [
            format_html(
                '<a class="km-admin-action km-admin-action--primary" href="{}">{}</a>',
                edit_url,
                _("Редактировать"),
            )
        ]
        if obj.is_deleted:
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--good" href="{}">{}</a>',
                    self._place_restore_url(obj),
                    _("Восстановить"),
                )
            )
            action_links.append(
                format_html('<span class="km-admin-action km-admin-action--muted">{}</span>', _("В каталоге скрыта"))
            )
        else:
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--secondary" href="{}" target="_blank" rel="noopener">{}</a>',
                    obj.get_absolute_url(),
                    _("Открыть"),
                )
            )
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--danger" href="{}">{}</a>',
                    self._place_delete_url(obj),
                    _("В удалённые"),
                )
            )
        return format_html('<div class="km-place-row-actions">{}</div>', format_html_join("", "{}", ((link,) for link in action_links)))


@admin.register(PlaceReviewsByClub)
class PlaceReviewsByClubAdmin(admin.ModelAdmin):
    list_display = ("display_name", "rating_count", "rating_avg", "reviews_link", "updated_at")
    list_filter = ("category", "district", "is_active", "is_verified")
    search_fields = ("name_ru", "name_en", "name_az", "name")
    ordering = ("-rating_count", "-rating_avg", "-updated_at")
    readonly_fields = ("rating_count", "rating_avg")

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        return obj.name_ru or obj.name

    @admin.display(description=_("Отзывы"))
    def reviews_link(self, obj):
        url = reverse("admin:catalog_placereview_changelist")
        return format_html('<a href="{}?place__id__exact={}">{}</a>', url, obj.id, _("Открыть отзывы"))
