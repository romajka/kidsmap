from django.contrib import admin, messages
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ngettext
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.formats import date_format
from django.contrib.auth import get_user_model

from catalog.models import (
    OwnerTeamMembership,
    OwnerTeamInvitation,
    PlaceChangeAudit,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    Place
)
from .ui_utils import render_primary_action, render_action_menu, render_row_actions_container, build_admin_query_string
from .user import _HiddenFromAdminIndexMixin

User = get_user_model()


@admin.register(OwnerTeamMembership)
class OwnerTeamMembershipAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    list_display = ("owner", "member", "role", "is_active", "invited_by", "created_at", "updated_at")
    list_filter = ("role", "is_active", "created_at")
    search_fields = ("owner__username", "owner__email", "member__username", "member__email")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("owner", "member", "invited_by")


@admin.register(OwnerTeamInvitation)
class OwnerTeamInvitationAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    list_display = ("owner", "email", "role", "status", "invited_user", "created_at", "responded_at")
    list_filter = ("role", "status", "created_at", "responded_at")
    search_fields = ("owner__username", "owner__email", "email", "invited_user__username", "token")
    readonly_fields = ("token", "created_at", "updated_at", "responded_at")
    autocomplete_fields = ("owner", "invited_by", "invited_user")


class PlaceChangeTypeFilter(admin.SimpleListFilter):
    title = _("Тип изменения")
    parameter_name = "change_kind"

    GROUPS = {
        "delete": (_("Удаление / восстановление"), {"deleted_at", "deleted_by_id"}),
        "publication": (_("Публикация"), {"is_active"}),
        "verification": (_("Проверка"), {"is_verified"}),
        "location": (_("Локация"), {"lat", "lng", "district", "metro", "address"}),
        "contacts": (_("Контакты"), {"phone1", "instagram", "website", "schedule"}),
        "photos": (_("Фото"), {"cover_photo", "photo"}),
        "owner": (_("Владелец"), {"owner_id"}),
        "content": (
            _("Данные карточки"),
            {
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
                "price_from",
                "price_to",
                "price_per_lesson",
                "price_per_month",
                "price_per_8_lessons",
                "lesson_duration_minutes",
                "extra_conditions",
                "additional_info",
                "is_temporary",
                "temporary_start",
                "temporary_end",
            },
        ),
    }

    def lookups(self, request, model_admin):
        return tuple((key, label) for key, (label, _field_names) in self.GROUPS.items())

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        group = self.GROUPS.get(value)
        if not group:
            return queryset
        _label, field_names = group
        return queryset.filter(field_name__in=field_names)


@admin.register(PlaceChangeAudit)
class PlaceChangeAuditAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placechangeaudit/change_list.html"
    list_select_related = ("place", "changed_by")
    date_hierarchy = "created_at"
    list_display = ("place_summary", "change_type_badge", "field_changes_summary", "changed_by_summary", "source_badge", "created_at_display", "row_actions")
    list_display_links = None
    list_filter = (PlaceChangeTypeFilter, "source", "changed_by", "place", "created_at")
    search_fields = (
        "place__name_ru",
        "place__name_en",
        "place__name_az",
        "place__slug",
        "changed_by__username",
        "changed_by__email",
        "field_name",
        "old_value",
        "new_value",
    )
    readonly_fields = ("place", "changed_by", "source", "field_name", "old_value", "new_value", "created_at")
    autocomplete_fields = ("place", "changed_by")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def _truthy_audit_value(value) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on", "да", "y"}

    @staticmethod
    def _audit_display_value(value) -> str:
        if value is None:
            return "—"
        text = str(value).strip()
        if not text:
            return "—"
        parsed_dt = parse_datetime(text)
        if parsed_dt is not None:
            if timezone.is_naive(parsed_dt):
                return date_format(parsed_dt, "d.m.Y H:i")
            return date_format(timezone.localtime(parsed_dt), "d.m.Y H:i")
        if text in {"0", "1"}:
            return _("Да") if text == "1" else _("Нет")
        return text

    @staticmethod
    def _audit_user_value(value) -> str:
        text = str(value).strip()
        if not text:
            return "—"
        try:
            user_id = int(text)
        except (TypeError, ValueError):
            return text
        user = User.objects.filter(pk=user_id).only("username", "email").first()
        if not user:
            return text
        if user.email and user.username:
            return f"{user.username} · {user.email}"
        return user.email or user.username or text

    @staticmethod
    def _audit_field_label(field_name: str) -> str:
        labels = {
            "deleted_at": _("Удаление"),
            "deleted_by_id": _("Кто удалил"),
            "is_active": _("Публикация"),
            "is_verified": _("Проверка"),
            "owner_id": _("Владелец"),
            "lat": _("Координаты"),
            "lng": _("Координаты"),
            "district": _("Регион / район"),
            "metro": _("Метро"),
            "address": _("Адрес"),
            "phone1": _("Телефон"),
            "instagram": _("Instagram"),
            "website": _("Сайт"),
            "schedule": _("Расписание"),
            "lesson_duration_minutes": _("Длительность урока"),
            "is_temporary": _("Тип события"),
            "temporary_start": _("Начало события"),
            "temporary_end": _("Окончание события"),
            "price_from": _("Цена от"),
            "price_to": _("Цена до"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "extra_conditions": _("Дополнительные условия"),
            "additional_info": _("Дополнительная информация"),
            "cover_photo": _("Фото для шапки"),
            "photo": _("Главное фото"),
            "name": _("Название"),
            "name_ru": _("Название (RU)"),
            "name_az": _("Название (AZ)"),
            "name_en": _("Название (EN)"),
            "description_ru": _("Описание (RU)"),
            "description_az": _("Описание (AZ)"),
            "description_en": _("Описание (EN)"),
            "category": _("Категория"),
            "subcategory": _("Подкатегория"),
            "age_from": _("Возраст от"),
            "age_to": _("Возраст до"),
        }
        return labels.get(field_name, field_name)

    def _audit_event_metadata(self, obj):
        field_name = obj.field_name
        old_value = obj.old_value
        new_value = obj.new_value

        if field_name in {"deleted_at", "deleted_by_id"}:
            is_restore = not bool(str(new_value).strip())
            return (
                "restore" if is_restore else "delete",
                "good" if is_restore else "warn",
                _("Карточка восстановлена") if is_restore else _("Карточка перемещена в удалённые"),
            )

        if field_name == "is_active":
            became_active = self._truthy_audit_value(new_value)
            return (
                "publication",
                "good" if became_active else "warn",
                _("Карточка опубликована") if became_active else _("Карточка снята с публикации"),
            )

        if field_name == "is_verified":
            became_verified = self._truthy_audit_value(new_value)
            return (
                "verification",
                "info" if became_verified else "muted",
                _("Карточка помечена как проверенная") if became_verified else _("Снята отметка проверки"),
            )

        if field_name in {"lat", "lng"}:
            return ("coordinates", "info", _("Координаты обновлены"))

        if field_name in {"district", "metro", "address"}:
            return ("location", "info", _("Локация карточки обновлена"))

        if field_name in {"phone1", "instagram", "website", "schedule"}:
            return ("contacts", "muted", _("Контакты карточки обновлены"))

        if field_name in {"cover_photo", "photo"}:
            return ("photos", "muted", _("Фото карточки обновлены"))

        if field_name in {
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
            "price_from",
            "price_to",
            "price_per_lesson",
            "price_per_month",
            "price_per_8_lessons",
            "lesson_duration_minutes",
            "extra_conditions",
            "additional_info",
        }:
            return ("content", "muted", _("Изменены данные карточки"))

        if field_name == "owner_id":
            return ("owner", "info", _("Изменён владелец карточки"))

        return ("other", "muted", _("Изменено поле карточки"))

    def _audit_value_pair(self, obj) -> str:
        field_label = self._audit_field_label(obj.field_name)
        old_value = self._audit_display_value(obj.old_value)
        new_value = self._audit_display_value(obj.new_value)
        if obj.field_name == "deleted_at":
            if self._truthy_audit_value(obj.new_value):
                return _("Служебное поле удаления: %(value)s") % {"value": new_value}
            return _("Служебное поле удаления очищено")
        if obj.field_name == "deleted_by_id":
            old_value = self._audit_user_value(obj.old_value)
            new_value = self._audit_user_value(obj.new_value)
            if self._truthy_audit_value(obj.new_value):
                return _("Удалил: %(value)s") % {"value": new_value}
            return _("Удаливший пользователь очищен")
        if obj.field_name == "owner_id":
            old_value = self._audit_user_value(obj.old_value)
            new_value = self._audit_user_value(obj.new_value)
        if old_value == new_value:
            return _("Значение не изменилось")
        return _("%(field)s: %(old)s → %(new)s") % {
            "field": field_label,
            "old": old_value,
            "new": new_value,
        }

    @admin.display(description=_("Карточка"))
    def place_summary(self, obj):
        if not obj.place_id:
            return "-"
        edit_url = reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name)
        meta_bits = [obj.place.get_category_display()]
        if obj.place.district:
            from catalog.services.locations import get_location_translation
            meta_bits.append(get_location_translation(obj.place.district))
        meta = " · ".join(bit for bit in meta_bits if bit)
        return format_html(
            '<div class="km-admin-stack">'
            '<a class="km-audit-place-link" href="{}">{}</a>'
            '{}'
            "</div>",
            edit_url,
            obj.place,
            format_html('<span class="km-admin-meta">{}</span>', meta) if meta else "",
        )

    @admin.display(description=_("Тип изменения"))
    def change_type_badge(self, obj):
        _kind, tone, label = self._audit_event_metadata(obj)
        return format_html(
            '<div class="km-admin-badges">'
            '<span class="km-admin-badge km-audit-kind km-audit-kind--{}">{}</span>'
            "</div>",
            tone,
            label,
        )

    @admin.display(description=_("Что изменилось"))
    def field_changes_summary(self, obj):
        return format_html(
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">{}</span>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            self._audit_field_label(obj.field_name),
            self._audit_value_pair(obj),
        )

    @admin.display(description=_("Кто изменил"))
    def changed_by_summary(self, obj):
        if not obj.changed_by_id:
            return format_html('<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>', _("Система"))
        meta = obj.changed_by.email or obj.changed_by.get_full_name() or ""
        return format_html(
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">{}</span>'
            '{}'
            "</div>",
            obj.changed_by.get_username(),
            format_html('<span class="km-admin-meta">{}</span>', meta) if meta else "",
        )

    @admin.display(description=_("Источник"))
    def source_badge(self, obj):
        source_label = obj.get_source_display()
        tone = {
            PlaceChangeAudit.SOURCE_OWNER_PANEL: "good",
            PlaceChangeAudit.SOURCE_ADMIN: "info",
            PlaceChangeAudit.SOURCE_SYSTEM: "muted",
        }.get(obj.source, "muted")
        return format_html(
            '<span class="km-admin-badge km-audit-source km-audit-source--{}">{}</span>',
            tone,
            source_label,
        )

    @admin.display(description=_("Когда"))
    def created_at_display(self, obj):
        return date_format(timezone.localtime(obj.created_at), "d F Y, H:i")

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name)
        actions = [
            format_html('<a class="button km-audit-action" href="{}">{}</a>', edit_url, _("Редактировать")),
        ]
        if obj.place.is_deleted:
            actions.append(format_html('<span class="km-admin-meta">{}</span>', _("В каталоге скрыта")))
        else:
            actions.append(
                format_html(
                    '<a class="button km-audit-action km-audit-action--secondary" href="{}" target="_blank" rel="noopener">{}</a>',
                    obj.place.get_absolute_url(),
                    _("Открыть"),
                )
            )
        return format_html('<div class="km-audit-actions">{}</div>', format_html_join("", "{}", ((action,) for action in actions)))


class PlaceOwnershipRequestAuditInline(admin.TabularInline):
    model = PlaceOwnershipRequestAudit
    extra = 0
    can_delete = False
    fields = ("created_at", "actor", "action", "from_status", "to_status", "note")
    readonly_fields = fields
    ordering = ("-created_at",)

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PlaceOwnershipRequest)
class PlaceOwnershipRequestAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placeownershiprequest/change_list.html"
    km_primary_filters = ("status", "created_at", "moderated_at")
    list_per_page = 15
    list_display = (
        "id",
        "place",
        "applicant",
        "status_badge",
        "created_at",
        "moderated_at_display",
        "moderated_by_display",
        "row_actions",
    )
    list_filter = ("status", "created_at", "moderated_at")
    search_fields = (
        "place__name_ru",
        "place__name_en",
        "place__name_az",
        "place__name",
        "applicant__username",
        "applicant__email",
        "note",
        "moderation_note",
    )
    readonly_fields = (
        "status",
        "note",
        "place_completion_summary",
        "row_actions",
        "created_at",
        "updated_at",
        "moderated_at",
        "moderated_by",
    )
    autocomplete_fields = ("place", "applicant", "moderated_by")
    actions = ("approve_requests", "reject_requests")
    inlines = (PlaceOwnershipRequestAuditInline,)
    fieldsets = (
        (
            _("Заявка"),
            {
                "fields": (
                    "place",
                    "applicant",
                    "status",
                    "note",
                )
            },
        ),
        (
            _("Заполненность карточки"),
            {
                "fields": ("place_completion_summary",)
            },
        ),
        (
            _("Модерация"),
            {
                "fields": (
                    "moderation_note",
                    ("moderated_by", "moderated_at"),
                )
            },
        ),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": (("created_at", "updated_at"),)
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("place", "applicant", "moderated_by").prefetch_related("place__gallery")

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # The request audit is intentionally non-deletable directly from admin,
        # but it should not block deleting its parent ownership request.
        perms_needed = {
            perm
            for perm in perms_needed
            if perm != str(PlaceOwnershipRequestAudit._meta.verbose_name)
        }
        return deleted_objects, model_count, perms_needed, protected

    def get_urls(self):
        custom_urls = [
            path(
                "<int:request_id>/approve/",
                self.admin_site.admin_view(self.approve_request_view),
                name="catalog_placeownershiprequest_approve",
            ),
            path(
                "<int:request_id>/reject/",
                self.admin_site.admin_view(self.reject_request_view),
                name="catalog_placeownershiprequest_reject",
            ),
        ]
        return custom_urls + super().get_urls()

    @admin.display(description=_("Статус"))
    def status_badge(self, obj):
        palette = {
            PlaceOwnershipRequest.STATUS_PENDING: "warn",
            PlaceOwnershipRequest.STATUS_APPROVED: "good",
            PlaceOwnershipRequest.STATUS_REJECTED: "danger",
        }
        tone = palette.get(obj.status, "muted")
        return format_html(
            '<div class="km-admin-badges"><span class="km-admin-badge km-admin-badge--{}">{}</span></div>',
            tone,
            obj.get_status_display(),
        )

    def _build_request_form_summary(self, obj) -> dict:
        if not obj or not obj.pk:
            return {}
        
        palette = {
            PlaceOwnershipRequest.STATUS_PENDING: "warn",
            PlaceOwnershipRequest.STATUS_APPROVED: "good",
            PlaceOwnershipRequest.STATUS_REJECTED: "danger",
        }
        status_tone = palette.get(obj.status, "muted")

        return {
            "is_pending": obj.is_pending,
            "status_label": obj.get_status_display(),
            "status_tone": status_tone,
            "place_name": obj.place.name_ru or obj.place.name,
            "place_url": reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name),
            "applicant": obj.applicant.get_full_name() or obj.applicant.email or obj.applicant.username,
        }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:
            context["km_request_form_summary"] = self._build_request_form_summary(obj)
            context["km_action_approve_url"] = reverse("admin:catalog_placeownershiprequest_approve", args=[obj.pk], current_app=self.admin_site.name)
            context["km_action_reject_url"] = reverse("admin:catalog_placeownershiprequest_reject", args=[obj.pk], current_app=self.admin_site.name)
        return super().render_change_form(request, context, add, change, form_url, obj)

    @admin.display(description=_("Дата решения"))
    def moderated_at_display(self, obj):
        return obj.moderated_at or "-"

    @admin.display(description=_("Кто проверил"))
    def moderated_by_display(self, obj):
        return obj.moderated_by or "-"

    @staticmethod
    def _place_text_value(value):
        return (value or "").strip()

    @staticmethod
    def _format_place_number_pair(first_value, second_value, *, unit: str = "", separator: str = "–"):
        if first_value is not None and second_value is not None:
            return f"{first_value}{separator}{second_value}{unit}"
        if first_value is not None:
            return f"{first_value}+{unit}"
        if second_value is not None:
            return f"до {second_value}{unit}"
        return ""

    def _render_place_completion_badge(self, *, is_filled: bool):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            "good" if is_filled else "warn",
            _("Заполнено") if is_filled else _("Не заполнено"),
        )

    def _place_completion_rows(self, place: Place):
        gallery_count = len(place.gallery.all())
        coordinates_value = (
            _("lat %(lat)s, lng %(lng)s") % {"lat": round(place.lat, 6), "lng": round(place.lng, 6)}
            if place.has_coordinates
            else ""
        )
        price_value = ", ".join(f"{label}: {value}" for label, value in place.pricing_options)

        return (
            (_("Название RU"), bool(self._place_text_value(place.name_ru or place.name)), self._place_text_value(place.name_ru or place.name)),
            (_("Название AZ"), bool(self._place_text_value(place.name_az)), self._place_text_value(place.name_az)),
            (_("Название EN"), bool(self._place_text_value(place.name_en)), self._place_text_value(place.name_en)),
            (_("Описание RU"), bool(self._place_text_value(place.description_ru)), self._place_text_value(place.description_ru)),
            (_("Описание AZ"), bool(self._place_text_value(place.description_az)), self._place_text_value(place.description_az)),
            (_("Описание EN"), bool(self._place_text_value(place.description_en)), self._place_text_value(place.description_en)),
            (_("Категория"), bool(self._place_text_value(place.category)), place.get_category_display()),
            (_("Подкатегория"), bool(self._place_text_value(place.subcategory)), self._place_text_value(place.subcategory)),
            (_("Возраст"), bool(place.age_display), place.age_display),
            (_("Цены"), bool(place.pricing_options), price_value),
            (_("Длительность урока"), place.lesson_duration_minutes is not None, place.lesson_duration_display),
            (_("Регион / район"), bool(self._place_text_value(place.district)), get_location_translation(place.district) if place.district else ""),
            (_("Метро"), bool(self._place_text_value(place.metro)), self._place_text_value(place.metro)),
            (_("Адрес"), bool(self._place_text_value(place.address)), self._place_text_value(place.address)),
            (_("Координаты"), place.has_coordinates, coordinates_value),
            (_("Телефон"), bool(self._place_text_value(place.phone1)), self._place_text_value(place.phone1)),
            (_("Instagram"), bool(self._place_text_value(place.instagram)), self._place_text_value(place.instagram_url())),
            (_("Сайт"), bool(self._place_text_value(place.website)), self._place_text_value(place.website_url())),
            (_("Расписание"), bool(self._place_text_value(place.schedule)), self._place_text_value(place.schedule)),
            (_("Дополнительные условия"), bool(self._place_text_value(place.extra_conditions)), self._place_text_value(place.extra_conditions)),
            (_("Дополнительная информация"), bool(self._place_text_value(place.additional_info)), self._place_text_value(place.additional_info)),
            (_("Фото для шапки"), bool(place.cover_photo and getattr(place.cover_photo, "name", "")), getattr(place.cover_photo, "name", "")),
            (_("Главное фото"), bool(place.photo and getattr(place.photo, "name", "")), getattr(place.photo, "name", "")),
            (
                _("Галерея"),
                gallery_count > 0,
                ngettext("%(count)s фото", "%(count)s фото", gallery_count) % {"count": gallery_count} if gallery_count else "",
            ),
            (_("Публикация"), place.is_active and not place.is_deleted, _("Опубликовано") if place.is_active and not place.is_deleted else _("Не опубликовано")),
            (_("Проверка"), place.is_verified, _("Проверено") if place.is_verified else _("Без проверки")),
            (_("Готовность к карте"), place.is_map_ready, _("Готово для карты") if place.is_map_ready else _("Не готово для карты")),
        )

    @admin.display(description=_("Что заполнено в карточке"))
    def place_completion_summary(self, obj):
        if not obj or not obj.place_id:
            return "-"

        rows = self._place_completion_rows(obj.place)
        filled_count = sum(1 for _, is_filled, _ in rows if is_filled)
        total_count = len(rows)

        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">{} <span class="km-admin-meta">{}</span></div>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:8px;">'
            '{}'
            '</div>'
            '</div>',
            format_html(
                '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
                "good" if filled_count == total_count else "warn",
                _("%(filled)s из %(total)s заполнено") % {"filled": filled_count, "total": total_count},
            ),
            _("Показывается текущее состояние связанной карточки."),
            format_html_join(
                "",
                '<div class="km-admin-stack" style="padding:10px 12px;border:1px solid #2f2f2f;border-radius:14px;background:#1a1a1a;">'
                '<div class="km-admin-badges">{} <span class="km-admin-title">{}</span></div>'
                '<span class="km-admin-meta">{}</span>'
                '</div>',
                (
                    (
                        self._render_place_completion_badge(is_filled=is_filled),
                        title,
                        value or _("Пусто"),
                    )
                    for title, is_filled, value in rows
                ),
            ),
        )

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        if not obj or not obj.pk:
            return "-"
            
        change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        primary_action = render_primary_action(change_url, _("Открыть"))

        menu_actions = []
        if obj.is_pending:
            approve_url = reverse("admin:catalog_placeownershiprequest_approve", args=[obj.pk])
            reject_url = reverse("admin:catalog_placeownershiprequest_reject", args=[obj.pk])
            menu_actions.append((approve_url, _("Принять"), "km-admin-action-menu__link--good"))
            menu_actions.append((reject_url, _("Отклонить"), "km-admin-action-menu__link--danger"))
        else:
            menu_actions.append((None, _("Заявка уже обработана"), "km-admin-action-menu__hint"))
        
        menu_html = render_action_menu(menu_actions)

        return render_row_actions_container(primary_action, menu_html)

    def _build_request_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
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

    def _request_quick_filters(self, request):
        current_status = request.GET.get("status__exact")
        keys = ("status__exact",)
        
        counts = {
            "all": PlaceOwnershipRequest.objects.count(),
            "pending": PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count(),
            "approved": PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_APPROVED).count(),
            "rejected": PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_REJECTED).count(),
        }
        
        return (
            {"label": _("Все заявки"), "url": self._build_request_changelist_query_string(request, clear=keys), "active": not current_status, "count": counts["all"]},
            {"label": _("Ожидают решения"), "url": self._build_request_changelist_query_string(request, clear=keys, status__exact=PlaceOwnershipRequest.STATUS_PENDING), "active": current_status == PlaceOwnershipRequest.STATUS_PENDING, "count": counts["pending"]},
            {"label": _("Одобрены"), "url": self._build_request_changelist_query_string(request, clear=keys, status__exact=PlaceOwnershipRequest.STATUS_APPROVED), "active": current_status == PlaceOwnershipRequest.STATUS_APPROVED, "count": counts["approved"]},
            {"label": _("Отклонены"), "url": self._build_request_changelist_query_string(request, clear=keys, status__exact=PlaceOwnershipRequest.STATUS_REJECTED), "active": current_status == PlaceOwnershipRequest.STATUS_REJECTED, "count": counts["rejected"]},
        )

    def _request_bulk_actions(self):
        return (
            {"name": "approve_requests", "label": _("Одобрить"), "tone": "good", "description": _("Одобрить выбранные заявки.")},
            {"name": "reject_requests", "label": _("Отклонить"), "tone": "danger", "description": _("Отклонить выбранные заявки.")},
        )

    def changelist_view(self, request, extra_context=None):
        pending_count = PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
        if pending_count:
            self.message_user(
                request,
                _("Ожидают проверки заявок на владение: %(count)s") % {"count": pending_count},
                level=messages.WARNING,
            )
            
        extra_context = {
            "km_primary_quick_filters": self._request_quick_filters(request),
            "km_secondary_quick_filters": [],
            "request_bulk_actions": self._request_bulk_actions(),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def _moderate_single(self, *, request, request_id: int, new_status: str):
        item = (
            self.get_queryset(request)
            .select_related("place", "applicant")
            .filter(pk=request_id)
            .first()
        )
        if item is None:
            self.message_user(request, _("Заявка не найдена."), level=messages.ERROR)
            return redirect(reverse("admin:catalog_placeownershiprequest_changelist"))

        if request.method != "POST":
            action_label = _("Принять") if new_status == PlaceOwnershipRequest.STATUS_APPROVED else _("Отклонить")
            context = {
                **self.admin_site.each_context(request),
                "opts": self.model._meta,
                "title": _("Подтверждение модерации"),
                "request_item": item,
                "action_label": action_label,
                "action_url": request.path,
                "back_url": reverse("admin:catalog_placeownershiprequest_change", args=[item.pk]),
            }
            return TemplateResponse(
                request,
                "admin/catalog/place_ownership_request_moderate_confirm.html",
                context,
            )

        if not item.is_pending:
            self.message_user(
                request,
                _("Заявка уже обработана."),
                level=messages.WARNING,
            )
            return redirect(reverse("admin:catalog_placeownershiprequest_change", args=[item.pk]))

        note = _("Одобрено через админку") if new_status == PlaceOwnershipRequest.STATUS_APPROVED else _("Отклонено через админку")
        item.apply_moderation(
            moderator=request.user,
            new_status=new_status,
            note=note,
        )
        self.message_user(
            request,
            _("Заявка успешно обработана."),
            level=messages.SUCCESS,
        )
        return redirect(reverse("admin:catalog_placeownershiprequest_change", args=[item.pk]))

    def approve_request_view(self, request, request_id: int):
        return self._moderate_single(
            request=request,
            request_id=request_id,
            new_status=PlaceOwnershipRequest.STATUS_APPROVED,
        )

    def reject_request_view(self, request, request_id: int):
        return self._moderate_single(
            request=request,
            request_id=request_id,
            new_status=PlaceOwnershipRequest.STATUS_REJECTED,
        )

    @admin.action(description=_("Одобрить выбранные заявки"))
    def approve_requests(self, request, queryset):
        approved = 0
        skipped = 0
        for item in queryset.select_related("place", "applicant"):
            if not item.is_pending:
                skipped += 1
                continue
            item.apply_moderation(
                moderator=request.user,
                new_status=PlaceOwnershipRequest.STATUS_APPROVED,
                note=_("Одобрено через админку"),
            )
            approved += 1

        if approved:
            self.message_user(
                request,
                _("Одобрено заявок: %(count)s") % {"count": approved},
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                _("Пропущено заявок (уже обработаны): %(count)s") % {"count": skipped},
                level=messages.WARNING,
            )

    @admin.action(description=_("Отклонить выбранные заявки"))
    def reject_requests(self, request, queryset):
        rejected = 0
        skipped = 0
        for item in queryset.select_related("place", "applicant"):
            if not item.is_pending:
                skipped += 1
                continue
            item.apply_moderation(
                moderator=request.user,
                new_status=PlaceOwnershipRequest.STATUS_REJECTED,
                note=_("Отклонено через админку"),
            )
            rejected += 1

        if rejected:
            self.message_user(
                request,
                _("Отклонено заявок: %(count)s") % {"count": rejected},
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                _("Пропущено заявок (уже обработаны): %(count)s") % {"count": skipped},
                level=messages.WARNING,
            )


@admin.register(PlaceOwnershipRequestAudit)
class PlaceOwnershipRequestAuditAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    list_display = ("ownership_request", "action", "actor", "from_status", "to_status", "created_at")
    list_filter = ("action", "created_at")
    search_fields = (
        "ownership_request__place__name_ru",
        "ownership_request__place__name_en",
        "ownership_request__place__name_az",
        "ownership_request__applicant__username",
        "actor__username",
        "note",
    )
    readonly_fields = ("ownership_request", "actor", "action", "from_status", "to_status", "note", "created_at")
    raw_id_fields = ("ownership_request",)
    autocomplete_fields = ("actor",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
