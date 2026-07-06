import os

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from catalog.forms import PlaceScheduleEditorFormMixin, SubcategorySelect
from catalog.models import Place, PlacePhoto, PlaceChangeAudit, Event, PlaceReviewsByClub, Category, Subcategory
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.content_quality import place_quality_check
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.place_schedule import build_schedule_summary, serialize_place_schedule
from .review import PlaceReviewInline
from .ui_utils import render_primary_action, render_action_menu, render_row_actions_container


ADMIN_DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
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


class PlaceAdminForm(PlaceScheduleEditorFormMixin, forms.ModelForm):
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT

    region = forms.ChoiceField(
        label=_("Город / регион"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-region": ""}),
    )
    district = forms.ChoiceField(
        label=_("Район города"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-district": ""}),
    )

    class Meta:
        model = Place
        fields = "__all__"
        widgets = {
            "temporary_start": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "900"},
                format=ADMIN_DATETIME_LOCAL_FORMAT,
            ),
            "temporary_end": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "900"},
                format=ADMIN_DATETIME_LOCAL_FORMAT,
            ),
        }
        labels = {
            "slug": _("URL-слаг"),
            "name_ru": _("Название (Русский)"),
            "name_az": _("Название (Азербайджанский)"),
            "name_en": _("Название (English)"),
            "description_ru": _("Описание (Русский)"),
            "description_az": _("Описание (Азербайджанский)"),
            "description_en": _("Описание (English)"),
            "photo": _("Главное фото"),
            "cover_photo": _("Резервное фото"),
            "phone1": _("Телефон"),
            "likes_count": _("Количество лайков"),
            "rating_avg": _("Средний рейтинг"),
            "rating_count": _("Количество отзывов"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "lesson_duration_minutes": _("Длительность урока (мин)"),
        }

    def clean(self):
        cleaned = super().clean()
        cleaned = self._clean_schedule_editor(cleaned)
        from catalog.services.locations import clean_location_fields
        self.draft_save_only = False
        cleaned = clean_location_fields(self, cleaned)
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from catalog.services.locations import init_location_fields, configure_location_choices
        init_location_fields(self, self.instance)
        configure_location_choices(self)

        if "category" in self.fields:
            self.fields["category"].queryset = Category.objects.order_by("order", "name_ru", "name")
            self.fields["category"].label_from_instance = lambda obj: obj.name_i18n()
        if "subcategory" in self.fields:
            self.fields["subcategory"].queryset = Subcategory.objects.select_related("category").order_by(
                "category__order",
                "order",
                "name_ru",
                "name",
            )
            self.fields["subcategory"].label_from_instance = lambda obj: obj.name_i18n()
            self.fields["subcategory"].widget = SubcategorySelect(attrs=self.fields["subcategory"].widget.attrs)
        self.fields["photo"].help_text = _("Используется в каталоге, на карте и первым на странице места.")
        self.fields["cover_photo"].help_text = _("Резервное изображение. Используется только если главное фото отсутствует.")
        for field_name in ("temporary_start", "temporary_end"):
            if field_name in self.fields:
                self.fields[field_name].input_formats = [
                    self.DATETIME_LOCAL_FORMAT,
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                ]
                value = getattr(self.instance, field_name, None)
                if value:
                    localized_value = timezone.localtime(value) if timezone.is_aware(value) else value
                    self.initial[field_name] = localized_value.strftime(self.DATETIME_LOCAL_FORMAT)
        # Placeholders for location & contacts fields
        _placeholders = {
            "lat": _("Напр., 40.409264"),
            "lng": _("Напр., 49.867092"),
            "phone1": _("Напр., +994 50 123-45-67"),
            "instagram": _("Напр., @kidsmap"),
            "website": _("Напр., https://example.com"),
            "schedule": _("Напр., Пн–Пт 10:00–20:00, Сб–Вс 11:00–19:00"),
            "extra_conditions": _("Напр., Предварительная запись, наличие сертификата и т.п."),
            "additional_info": _("Напр., Описание места, особенности, важные детали и т.п."),
            "address": _("Напр., ул. Низами 10, Баку"),
        }
        for field_name, placeholder in _placeholders.items():
            if field_name in self.fields and hasattr(self.fields[field_name].widget, "attrs"):
                self.fields[field_name].widget.attrs.setdefault("placeholder", str(placeholder))
        self._init_schedule_editor()


class EventAdminForm(forms.ModelForm):
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT

    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            "start_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "900"},
                format=ADMIN_DATETIME_LOCAL_FORMAT,
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "900"},
                format=ADMIN_DATETIME_LOCAL_FORMAT,
            ),
            "published_at": forms.DateTimeInput(
                attrs={"type": "datetime-local", "step": "900"},
                format=ADMIN_DATETIME_LOCAL_FORMAT,
            ),
        }
        labels = {
            "slug": _("URL-слаг"),
            "name_ru": _("Название (Русский)"),
            "name_az": _("Название (Азербайджанский)"),
            "name_en": _("Название (English)"),
            "description_ru": _("Описание (Русский)"),
            "description_az": _("Описание (Азербайджанский)"),
            "description_en": _("Описание (English)"),
            "price_text": _("Стоимость и условия"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("start_datetime", "end_datetime", "published_at"):
            if field_name in self.fields:
                self.fields[field_name].input_formats = [
                    self.DATETIME_LOCAL_FORMAT,
                    "%Y-%m-%d %H:%M",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S",
                ]
                value = getattr(self.instance, field_name, None)
                if value:
                    localized_value = timezone.localtime(value) if timezone.is_aware(value) else value
                    self.initial[field_name] = localized_value.strftime(self.DATETIME_LOCAL_FORMAT)
        self.fields["photo"].help_text = _(
            "Основное изображение мероприятия для списка и детальной страницы."
        )
        self.fields["start_datetime"].help_text = _(
            "Дата и время старта. Без этого поле мероприятие нельзя опубликовать."
        )
        self.fields["end_datetime"].help_text = _(
            "Дата и время окончания. Используется для определения актуальности и завершения."
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
    form = EventAdminForm
    actions = ("mark_published", "mark_draft", "mark_pending")
    list_display = (
        "display_name",
        "category",
        "start_datetime",
        "end_datetime",
        "owner",
        "lifecycle_status_display",
        "updated_at",
        "row_actions",
    )
    list_filter = ("status", "category", "start_datetime", "owner")
    search_fields = ("name", "name_az", "name_ru", "name_en", "address", "phone", "owner__username", "owner__email")
    readonly_fields = ("slug", "created_at", "updated_at")
    list_select_related = ("owner", "related_place")
    list_per_page = 15
    change_form_template = "admin/catalog/event/change_form.html"
    EVENT_FORM_PRIMARY_SECTIONS = (
        {
            "id": "basics",
            "step": "01",
            "title": _("Основное"),
            "description": _("Название события, категория, владелец и связанное место."),
            "fieldset_indexes": (0,),
        },
        {
            "id": "copy",
            "step": "02",
            "title": _("Названия и описания"),
            "description": _("Тексты мероприятия на языках сайта. Минимум один качественный язык обязателен."),
            "fieldset_indexes": (1,),
        },
        {
            "id": "schedule",
            "step": "03",
            "title": _("Дата и формат"),
            "description": _("Время проведения, возраст, цена и формат участия."),
            "fieldset_indexes": (2,),
        },
        {
            "id": "location",
            "step": "04",
            "title": _("Локация и контакты"),
            "description": _("Адрес, телефон, Instagram и комментарии для модерации."),
            "fieldset_indexes": (3,),
        },
        {
            "id": "media",
            "step": "05",
            "title": _("Фото и публикация"),
            "description": _("Основное изображение, видимость на сайте и текущий статус публикации."),
            "fieldset_indexes": (4,),
        },
    )
    EVENT_FORM_SECONDARY_SECTIONS = (
        {
            "id": "system",
            "title": _("Системные поля"),
            "description": _("Служебные статусы, причины отклонения и временные метки."),
            "fieldset_indexes": (5,),
        },
    )
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    ("name", "category"),
                    ("owner", "related_place"),
                    "slug",
                )
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                )
            },
        ),
        (
            _("Дата и формат"),
            {
                "fields": (
                    ("start_datetime", "end_datetime"),
                    ("age_from", "age_to"),
                    "price_text",
                )
            },
        ),
        (
            _("Локация и контакты"),
            {
                "fields": (
                    "address",
                    ("phone", "instagram"),
                    "moderation_note",
                )
            },
        ),
        (
            _("Фото и публикация"),
            {
                "fields": (
                    ("photo", "status"),
                    "published_at",
                ),
            },
        ),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": ("rejection_reason", ("deleted_at", "created_at", "updated_at")),
            },
        ),
    )
    add_fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    ("name", "category"),
                    ("owner", "related_place"),
                    "slug",
                ),
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                ),
            },
        ),
        (
            _("Дата и формат"),
            {
                "fields": (
                    ("start_datetime", "end_datetime"),
                    ("age_from", "age_to"),
                    "price_text",
                ),
            },
        ),
        (
            _("Локация и контакты"),
            {
                "fields": (
                    "address",
                    ("phone", "instagram"),
                    "moderation_note",
                ),
            },
        ),
        (
            _("Фото и публикация"),
            {
                "fields": (
                    ("photo", "status"),
                ),
            },
        ),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": ("rejection_reason",),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("status", Event.STATUS_DRAFT)
        return initial

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        adminform = context.get("adminform")
        if adminform is not None:
            context["km_event_form_sections"] = self._build_event_form_sections(adminform)
            context["km_event_secondary_sections"] = self._build_event_secondary_sections(adminform)
            context["km_event_form_summary"] = self._build_event_form_summary(
                form=adminform.form,
                obj=obj,
                add=add,
            )
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def _fieldset_list(self, adminform):
        return list(adminform) if adminform is not None else []

    def _build_event_form_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.EVENT_FORM_PRIMARY_SECTIONS:
            section_fieldsets = [
                fieldsets[index]
                for index in section["fieldset_indexes"]
                if index < len(fieldsets)
            ]
            if not section_fieldsets:
                continue
            sections.append(
                {
                    "id": section["id"],
                    "step": section["step"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _build_event_secondary_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.EVENT_FORM_SECONDARY_SECTIONS:
            section_fieldsets = [
                fieldsets[index]
                for index in section["fieldset_indexes"]
                if index < len(fieldsets)
            ]
            if not section_fieldsets:
                continue
            sections.append(
                {
                    "id": section["id"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _field_has_value(self, form, field_name: str, *, obj=None) -> bool:
        if field_name in form.files and form.files.get(field_name):
            return True

        if form.is_bound:
            raw_value = form.data.get(form.add_prefix(field_name))
        else:
            raw_value = form.initial.get(field_name, getattr(getattr(form, "instance", None), field_name, None))

        if raw_value in (None, "", [], (), {}):
            if obj is not None:
                current_value = getattr(obj, field_name, None)
                if current_value not in (None, "", [], (), {}):
                    return True
            return False

        return True

    def _event_visibility_state(self, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return {
                "label": str(_("Черновик")),
                "tone": "muted",
                "hint": str(_("Мероприятие ещё не опубликовано на сайте.")),
                "is_public": False,
            }
        if obj.deleted_at:
            return {
                "label": str(_("В удалённых")),
                "tone": "muted",
                "hint": str(_("Карточка удалена и не показывается на сайте.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_PENDING:
            return {
                "label": str(_("На модерации")),
                "tone": "warn",
                "hint": str(_("Мероприятие сохранено, но ещё не доступно на сайте.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_REJECTED:
            return {
                "label": str(_("Отклонено")),
                "tone": "danger",
                "hint": str(_("Нужно исправить карточку перед следующей публикацией.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_CANCELLED:
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "warn",
                "hint": str(_("Мероприятие сохранено, но вручную снято с публикации.")),
                "is_public": False,
            }
        if obj.is_public:
            return {
                "label": str(_("Опубликовано")),
                "tone": "good",
                "hint": str(_("Событие видно на сайте и участвует в афише мероприятий.")),
                "is_public": True,
            }
        if obj.effective_status == Event.STATUS_EXPIRED:
            return {
                "label": str(_("Завершено")),
                "tone": "muted",
                "hint": str(_("Дата события уже прошла, поэтому оно не показывается как актуальное.")),
                "is_public": False,
            }
        return {
            "label": str(_("Черновик")),
            "tone": "muted",
            "hint": str(_("Событие пока не опубликовано на сайте.")),
            "is_public": False,
        }

    def _event_publish_missing_fields(self, *, form, obj=None):
        required = (
            ("name", _("Название")),
            ("category", _("Категория")),
            ("description_az", _("Описание (AZ)")),
            ("start_datetime", _("Дата начала")),
            ("end_datetime", _("Дата окончания")),
        )
        missing = []
        for field_name, label in required:
            if not self._field_has_value(form, field_name, obj=obj):
                missing.append(str(label))
        return missing

    def _build_event_form_summary(self, *, form, obj=None, add=False):
        checklist = (
            ("name", _("Название")),
            ("category", _("Категория")),
            ("description_az", _("Описание (AZ)")),
            ("start_datetime", _("Дата начала")),
            ("end_datetime", _("Дата окончания")),
            ("address", _("Адрес")),
            ("phone", _("Телефон")),
            ("photo", _("Фото")),
        )
        completed = 0
        missing = []
        missing_fields = set()
        for field_name, label in checklist:
            if self._field_has_value(form, field_name, obj=obj):
                completed += 1
            else:
                missing.append(str(label))
                missing_fields.add(field_name)

        total = len(checklist)
        completion_pct = round(completed / total * 100) if total else 0
        error_count = len(form.errors)
        visibility = self._event_visibility_state(obj)
        title = str(_("Новое мероприятие"))
        state_badges = [{"label": visibility["label"], "tone": visibility["tone"]}]
        meta_items = []

        if obj is not None and obj.pk:
            title = obj.name_ru or obj.name or title
            state_badges.append(
                {
                    "label": str(obj.get_status_display()),
                    "tone": "good" if obj.status == obj.STATUS_PUBLISHED else "muted",
                }
            )
            if obj.start_datetime:
                meta_items.append(
                    {
                        "label": str(_("Старт")),
                        "value": timezone.localtime(obj.start_datetime).strftime("%d.%m.%Y %H:%M"),
                    }
                )
            if obj.end_datetime:
                meta_items.append(
                    {
                        "label": str(_("Завершение")),
                        "value": timezone.localtime(obj.end_datetime).strftime("%d.%m.%Y %H:%M"),
                    }
                )
            meta_items.append(
                {
                    "label": str(_("Владелец")),
                    "value": obj.owner.username if obj.owner_id and obj.owner else str(_("Не назначен")),
                }
            )
            if obj.related_place_id and obj.related_place:
                meta_items.append(
                    {
                        "label": str(_("Связанное место")),
                        "value": obj.related_place.name_ru or obj.related_place.name or str(obj.related_place),
                    }
                )
        else:
            state_badges.append({"label": str(_("Черновой режим")), "tone": "muted"})

        meta_items.insert(
            0,
            {
                "label": str(_("Режим")),
                "value": str(_("Создание новой карточки")) if add else str(_("Редактирование карточки")),
            },
        )

        return {
            "title": title,
            "completion_pct": completion_pct,
            "completed": completed,
            "total": total,
            "error_count": error_count,
            "visibility": visibility,
            "checklist_items": [
                {
                    "field_name": field_name,
                    "input_id": f"id_{field_name}",
                    "label": str(label),
                    "initial": field_name not in missing_fields,
                }
                for field_name, label in checklist
            ],
            "missing": missing[:5],
            "readiness_label": str(_("Готово к публикации")) if not missing else str(_("Нужна доработка")),
            "readiness_tone": "good" if not missing else "warn",
            "state_badges": state_badges,
            "meta_items": meta_items,
        }

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_i18n()
        meta = [f"ID {obj.pk}"]
        if obj.deleted_at:
            meta.append(str(_("Удалено")))
        preview = ""
        if obj.photo and getattr(obj.photo, "name", ""):
            preview = format_html('<img src="{}" alt="" class="km-admin-thumb" loading="lazy">', obj.photo.url)
        else:
            preview = mark_safe('<span class="km-admin-thumb km-admin-thumb--placeholder" aria-hidden="true">•</span>')
        return format_html(
            '<div class="km-admin-entry">{}<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div></div>',
            preview,
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((item,) for item in meta)),
        )

    @admin.display(description=_("Статус"))
    def lifecycle_status_display(self, obj):
        from django.utils.html import format_html
        if obj.deleted_at:
            tone, label = "danger", _("В удаленных")
        elif obj.status == Event.STATUS_PUBLISHED:
            tone, label = "good", _("Опубликовано")
        elif obj.status == Event.STATUS_PENDING:
            tone, label = "warn", _("На модерации")
        elif obj.status == Event.STATUS_REJECTED:
            tone, label = "danger", _("Отклонено")
        elif obj.status == Event.STATUS_EXPIRED:
            tone, label = "muted", _("Завершено")
        else:
            tone, label = "muted", dict(Event.STATUS_CHOICES).get(obj.status, obj.status)

        return format_html(
            '<div class="km-admin-badges"><span class="km-admin-badge km-admin-badge--{}">{}</span></div>',
            tone,
            label,
        )

    @admin.display(description="")
    def row_actions(self, obj):
        from django.urls import reverse
        edit_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        primary_action = render_primary_action(edit_url, _("Редактировать"))
        
        menu_actions = []
        if obj.is_public:
            menu_actions.append((obj.get_absolute_url(), _("Открыть"), ""))
            
        menu_html = render_action_menu(menu_actions)
        return render_row_actions_container(primary_action, menu_html)

    def save_model(self, request, obj, form, change):
        if "_save_draft" in request.POST:
            obj.status = Event.STATUS_DRAFT
            obj.published_at = None
            obj.rejection_reason = ""
        if "_unpublish_event" in request.POST:
            obj.status = Event.STATUS_CANCELLED
            obj.published_at = None
        if obj.status == Event.STATUS_PUBLISHED and not obj.published_at:
            obj.published_at = timezone.now()
        if obj.status != Event.STATUS_REJECTED:
            obj.rejection_reason = obj.rejection_reason if obj.status == Event.STATUS_PUBLISHED else obj.rejection_reason
        super().save_model(request, obj, form, change)

    def response_add(self, request, obj, post_url_continue=None):
        if "_save_draft" in request.POST:
            return self._handle_event_save_draft_submit(
                request,
                obj,
                message=_("Черновик мероприятия сохранён. Можно продолжить позже."),
            )
        if "_publish_event" in request.POST:
            return self._handle_publish_event_submit(request, obj)
        if "_unpublish_event" in request.POST:
            return self._handle_unpublish_event_submit(request, obj)
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if "_save_draft" in request.POST:
            return self._handle_event_save_draft_submit(
                request,
                obj,
                message=_("Изменения сохранены как черновик. Можно вернуться к мероприятию позже."),
            )
        if "_publish_event" in request.POST:
            return self._handle_publish_event_submit(request, obj)
        if "_unpublish_event" in request.POST:
            return self._handle_unpublish_event_submit(request, obj)
        return super().response_change(request, obj)

    def _event_change_url(self, obj: Event) -> str:
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_change",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

    def _handle_event_save_draft_submit(self, request, obj, *, message: str):
        self.message_user(request, message, level=messages.SUCCESS)
        return HttpResponseRedirect(self._event_change_url(obj))

    def _handle_publish_event_submit(self, request, obj: Event):
        missing_labels = []
        for field_name, label in (
            ("name", _("Название")),
            ("category", _("Категория")),
            ("description_az", _("Описание (AZ)")),
            ("start_datetime", _("Дата начала")),
            ("end_datetime", _("Дата окончания")),
        ):
            value = getattr(obj, field_name, None)
            if value in (None, ""):
                missing_labels.append(str(label))

        if obj.end_datetime and obj.start_datetime and obj.end_datetime <= obj.start_datetime:
            missing_labels.append(str(_("Корректный диапазон дат")))

        if missing_labels:
            obj.status = Event.STATUS_DRAFT
            obj.published_at = None
            obj.save(update_fields=["status", "published_at", "updated_at"])
            self.message_user(
                request,
                _("Мероприятие сохранено, но не опубликовано. Заполните: %(fields)s.")
                % {"fields": ", ".join(missing_labels[:5])},
                level=messages.WARNING,
            )
            return HttpResponseRedirect(self._event_change_url(obj))

        update_fields = ["status", "rejection_reason", "updated_at"]
        obj.status = Event.STATUS_PUBLISHED
        obj.rejection_reason = ""
        if obj.published_at is None:
            obj.published_at = timezone.now()
            update_fields.append("published_at")
        obj.save(update_fields=update_fields)
        self.message_user(
            request,
            _("Мероприятие опубликовано и теперь может показываться на сайте."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._event_change_url(obj))

    def _handle_unpublish_event_submit(self, request, obj: Event):
        obj.status = Event.STATUS_CANCELLED
        obj.published_at = None
        obj.save(update_fields=["status", "published_at", "updated_at"])
        self.message_user(
            request,
            _("Мероприятие снято с публикации и скрыто с сайта."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._event_change_url(obj))

    change_list_template = "admin/catalog/event/change_list.html"
    km_primary_filters = ("category", "status", "start_datetime")

    def _event_dashboard_counts(self):
        return Event.objects.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__gt=timezone.now()) | Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__isnull=True)),
            pending=Count("id", filter=Q(status=Event.STATUS_PENDING, deleted_at__isnull=True)),
            expired=Count("id", filter=Q(status=Event.STATUS_EXPIRED) | Q(end_datetime__lte=timezone.now())),
            deleted=Count("id", filter=Q(deleted_at__isnull=False)),
        )

    def _event_dashboard_stats(self, request, counts: dict):
        return (
            {
                "label": _("Всего мероприятий"),
                "count": counts["total"],
                "url": "?",
                "tone": "info",
            },
            {
                "label": _("Опубликовано (Актуальные)"),
                "count": counts["published"],
                "url": "?status__exact=published",
                "tone": "good",
            },
            {
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": "?status__exact=pending",
                "tone": "warn",
            },
            {
                "label": _("Завершенные"),
                "count": counts["expired"],
                "url": "?status__exact=expired",
                "tone": "muted",
            },
            {
                "label": _("Удалённые"),
                "count": counts["deleted"],
                "url": "?deleted_at__isnull=False",
                "tone": "danger",
            },
        )

    def _event_quick_filters(self, request, counts: dict):
        current_status = request.GET.get("status__exact")
        current_deleted = request.GET.get("deleted_at__isnull")

        return [
            {
                "key": "all",
                "label": _("Все карточки"),
                "count": counts["total"],
                "url": "?",
                "active": not current_status and not current_deleted,
            },
            {
                "key": "published",
                "label": _("Опубликовано"),
                "count": counts["published"],
                "url": "?status__exact=published",
                "active": current_status == "published",
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": "?status__exact=pending",
                "active": current_status == "pending",
            },
            {
                "key": "deleted",
                "label": _("Удалённые"),
                "count": counts["deleted"],
                "url": "?deleted_at__isnull=False",
                "active": current_deleted == "False",
            },
        ]

    def _event_bulk_actions(self):
        return [
            {
                "name": "mark_published",
                "label": _("Опубликовать"),
                "tone": "good",
                "description": _("Опубликовать выбранные мероприятия."),
            },
            {
                "name": "mark_draft",
                "label": _("В черновик"),
                "tone": "muted",
                "description": _("Снять выбранные мероприятия с публикации и вернуть в черновики."),
            },
            {
                "name": "mark_pending",
                "label": _("На модерацию"),
                "tone": "warn",
                "description": _("Отправить выбранные мероприятия на модерацию."),
            },
        ]

    @admin.action(description=_("Опубликовать выбранные мероприятия"))
    def mark_published(self, request, queryset):
        now = timezone.now()
        updated_count = 0
        for event in queryset.iterator(chunk_size=100):
            update_fields = ["status", "rejection_reason", "updated_at"]
            event.status = Event.STATUS_PUBLISHED
            event.rejection_reason = ""
            if event.published_at is None:
                event.published_at = now
                update_fields.append("published_at")
            event.save(update_fields=update_fields)
            updated_count += 1
        self.message_user(
            request,
            ngettext(
                "Опубликовано %(count)d мероприятие.",
                "Опубликовано %(count)d мероприятия.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Вернуть мероприятия в черновик"))
    def mark_draft(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_DRAFT,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d мероприятие переведено в черновик.",
                "%(count)d мероприятия переведены в черновик.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отправить мероприятия на модерацию"))
    def mark_pending(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_PENDING,
            rejection_reason="",
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d мероприятие отправлено на модерацию.",
                "%(count)d мероприятия отправлены на модерацию.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    def changelist_view(self, request, extra_context=None):
        counts = self._event_dashboard_counts()
        quick_filters = self._event_quick_filters(request, counts=counts)
        extra_context = {
            "event_dashboard_stats": self._event_dashboard_stats(request, counts=counts),
            "km_primary_quick_filters": quick_filters,
            "km_secondary_quick_filters": [],
            "event_bulk_actions": self._event_bulk_actions(),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


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
    km_primary_filters = ("category", "district", "status")
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
        "last_verified_at_display",
        "published_at_display",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_per_page = 15
    save_on_top = True

    PLACE_FORM_PRIMARY_SECTIONS = (
        {
            "id": "basics",
            "step": "01",
            "title": _("Основное"),
            "description": _("Базовая информация о карточке: название, категория, подкатегория, URL-слаг и тип размещения."),
            "fieldset_indexes": (0,),
        },
        {
            "id": "copy",
            "step": "02",
            "title": _("Названия и описания"),
            "description": _("Тексты карточки на основных языках сайта. Минимум один качественный язык обязателен."),
            "fieldset_indexes": (1,),
        },
        {
            "id": "pricing",
            "step": "03",
            "title": _("Возраст и цена"),
            "description": _("Возрастные рамки, стоимость и длительность занятий."),
            "fieldset_indexes": (2,),
        },
        {
            "id": "location",
            "step": "04",
            "title": _("Локация и контакты"),
            "description": _("Район, метро, адрес, координаты и контакты для связи."),
            "fieldset_indexes": (3, 4),
        },
        {
            "id": "media",
            "step": "05",
            "title": _("Фотографии"),
            "description": _("Добавьте главное изображение и дополнительные фотографии места."),
            "fieldset_indexes": (5,),
        },
    )

    PLACE_FORM_SECONDARY_SECTIONS = (
        {
            "id": "system",
            "title": _("Системные поля"),
            "description": _("Служебные и административные поля, которые не нужны в основном сценарии заполнения."),
            "fieldset_indexes": (6, 7),
        },
    )

    ADD_FIELDSETS = (
        (
            _("Основное"),
            {
                "fields": (
                    "name",
                    ("category", "subcategory"),
                    "slug",
                    ("is_temporary",),
                    ("temporary_start", "temporary_end"),
                )
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                )
            },
        ),
        (
            _("Возраст и цена"),
            {
                "fields": (
                    ("age_from", "age_to", "lesson_duration_minutes"),
                    ("price_from", "price_to", "price_per_lesson"),
                    ("price_per_month", "price_per_8_lessons"),
                )
            },
        ),
        (
            _("Локация"),
            {
                "fields": (
                    ("district", "metro"),
                    "address",
                    ("lat", "lng"),
                    ("coordinates_status_display", "map_ready_status_display"),
                )
            },
        ),
        (
            _("Контакты"),
            {
                "fields": (
                    ("phone1", "instagram", "website"),
                    "schedule",
                    "extra_conditions",
                    "additional_info",
                )
            },
        ),
        (_("Фотографии"), {"fields": ("photo",)}),
        (
            _("Системные поля"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cover_photo",
                    "is_active",
                    "is_verified",
                    "status",
                    "rejection_reason",
                    "owner",
                    "last_verified_at_display",
                    "published_at_display",
                    "lifecycle_status_display",
                    "quality_status_display",
                ),
            },
        ),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("cover_photo", "created_at", "updated_at")}),
    )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        adminform = context.get("adminform")
        if adminform is not None:
            inline_admin_formsets = context.get("inline_admin_formsets", [])
            context["km_place_gallery_inline"] = next(
                (
                    inline_admin_formset
                    for inline_admin_formset in inline_admin_formsets
                    if inline_admin_formset.opts.model.__name__ == "PlacePhoto"
                ),
                None,
            )
            context["km_place_form_sections"] = self._build_place_form_sections(adminform)
            context["km_place_secondary_sections"] = self._build_place_secondary_sections(adminform)
            context["km_place_inline_sections"] = self._build_place_inline_sections(inline_admin_formsets)
            context["km_place_form_summary"] = self._build_place_form_summary(
                form=adminform.form,
                obj=obj,
                add=add,
            )
            context["km_place_map_alert"] = self._build_place_map_alert(
                form=adminform.form,
                obj=obj,
                has_google_maps_api_key=bool(context["google_maps_api_key"]),
            )
            context["km_place_public_link"] = self._build_public_place_link(request, obj=obj)
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def _fieldset_list(self, adminform):
        return list(adminform) if adminform is not None else []

    def _build_place_form_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.PLACE_FORM_PRIMARY_SECTIONS:
            section_fieldsets = [
                fieldsets[index]
                for index in section["fieldset_indexes"]
                if index < len(fieldsets)
            ]
            if not section_fieldsets:
                continue
            sections.append(
                {
                    "id": section["id"],
                    "step": section["step"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _build_place_secondary_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.PLACE_FORM_SECONDARY_SECTIONS:
            section_fieldsets = [
                fieldsets[index]
                for index in section["fieldset_indexes"]
                if index < len(fieldsets)
            ]
            if not section_fieldsets:
                continue
            sections.append(
                {
                    "id": section["id"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _build_place_inline_sections(self, inline_admin_formsets):
        sections = []
        for inline_admin_formset in inline_admin_formsets or []:
            model_name = inline_admin_formset.opts.model.__name__
            if model_name == "PlacePhoto":
                continue
            elif model_name == "PlaceReview":
                sections.append(
                    {
                        "id": "reviews",
                        "title": _("Отзывы по кружкам"),
                        "description": _("Связанные отзывы и их текущее состояние."),
                        "items": [inline_admin_formset],
                    }
                )
            elif model_name == "PlaceChangeAudit":
                sections.append(
                    {
                        "id": "audit",
                        "title": _("История изменений карточек"),
                        "description": _("Аудит изменений по ключевым полям карточки."),
                        "items": [inline_admin_formset],
                    }
                )
            else:
                sections.append(
                    {
                        "id": f"inline-{model_name.lower()}",
                        "title": inline_admin_formset.opts.verbose_name_plural,
                        "description": "",
                        "items": [inline_admin_formset],
                    }
                )
        return sections

    def _field_has_value(self, form, field_name: str, *, obj=None) -> bool:
        if field_name in form.files and form.files.get(field_name):
            return True

        if form.is_bound:
            raw_value = form.data.get(form.add_prefix(field_name))
        else:
            raw_value = form.initial.get(field_name, getattr(getattr(form, "instance", None), field_name, None))

        if not raw_value and raw_value != 0:
            if obj is not None:
                current_value = getattr(obj, field_name, None)
                if current_value or current_value == 0:
                    return True
            return False

        return True

    def _place_visibility_state(self, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return {
                "label": str(_("Черновик")),
                "tone": "muted",
                "hint": str(_("Карточка ещё не опубликована на сайте.")),
                "is_public": False,
            }
        if obj.is_deleted:
            return {
                "label": str(_("В удалённых")),
                "tone": "muted",
                "hint": str(_("Карточка скрыта с сайта и перемещена в удалённые.")),
                "is_public": False,
            }
        if obj.is_active and obj.status == obj.STATUS_PUBLISHED:
            return {
                "label": str(_("Опубликовано")),
                "tone": "good",
                "hint": str(_("Карточка видна на сайте при текущих правилах качества каталога.")),
                "is_public": True,
            }
        if obj.status == obj.STATUS_PENDING:
            return {
                "label": str(_("На модерации")),
                "tone": "warn",
                "hint": str(_("Карточка сохранена, но ещё не показывается на сайте.")),
                "is_public": False,
            }
        if obj.status == obj.STATUS_REJECTED:
            return {
                "label": str(_("Отклонено")),
                "tone": "danger",
                "hint": str(_("Карточка отклонена и не показывается на сайте.")),
                "is_public": False,
            }
        if not obj.is_active:
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "warn",
                "hint": str(_("Карточка сохранена, но снята с публикации.")),
                "is_public": False,
            }
        return {
            "label": str(_("Черновик")),
            "tone": "muted",
            "hint": str(_("Карточка пока не опубликована на сайте.")),
            "is_public": False,
        }

    def _build_place_map_alert(self, *, form, obj=None, has_google_maps_api_key: bool):
        address_present = self._field_has_value(form, "address", obj=obj)
        lat_present = self._field_has_value(form, "lat", obj=obj)
        lng_present = self._field_has_value(form, "lng", obj=obj)
        should_show_provider_warning = not has_google_maps_api_key and (
            address_present or lat_present or lng_present or (obj is not None and obj.pk)
        )
        if should_show_provider_warning:
            return {
                "tone": "warning",
                "title": str(_("Карта пока не активна")),
                "message": str(
                    _("Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY, чтобы рассчитывать координаты прямо из формы.")
                ),
            }

        if obj is not None and obj.pk and not obj.is_map_ready:
            if obj.is_deleted:
                message = _("Карточка удалена и не может отображаться на карте, пока не будет восстановлена.")
            elif not obj.has_coordinates:
                message = _("Для публикации на карте нужно заполнить адрес или рассчитать координаты.")
            elif not obj.is_active or obj.status != obj.STATUS_PUBLISHED:
                message = _("Координаты есть, но карточка станет доступна на карте только после публикации.")
            else:
                message = _("Карта пока не готова для этой карточки.")
            return {
                "tone": "warning",
                "title": str(_("Проверьте готовность карты")),
                "message": str(message),
            }

        return None

    def _resolve_public_site_host(self, request) -> str:
        current_host = request.get_host()
        current_hostname, separator, port = current_host.partition(":")
        admin_host = (getattr(settings, "ADMIN_HOST", "") or "").strip().lower()

        if admin_host and current_hostname.lower() == admin_host and admin_host.startswith("admin."):
            public_hostname = admin_host[len("admin."):]
            return f"{public_hostname}{separator}{port}" if separator else public_hostname

        return current_host

    def _build_public_place_link(self, request, *, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return None

        visibility = self._place_visibility_state(obj)
        relative_url = obj.get_absolute_url()
        public_host = self._resolve_public_site_host(request)
        absolute_url = f"{'https' if request.is_secure() else request.scheme}://{public_host}{relative_url}"

        return {
            "url": absolute_url,
            "path": relative_url,
            "is_public": visibility["is_public"],
            "label": str(_("Открыть карточку на сайте")),
            "hint": (
                str(_("Карточка опубликована. Ссылка откроет её публичную страницу в новой вкладке."))
                if visibility["is_public"]
                else str(_("Карточка сейчас не видна пользователям. Кнопка появится после публикации."))
            ),
        }

    def _build_place_form_summary(self, *, form, obj=None, add=False):
        checklist = (
            ("name", _("Название")),
            ("category", _("Категория")),
            ("description_az", _("Описание (AZ)")),
            ("age_from", _("Возраст от")),
            ("age_to", _("Возраст до")),
            ("address", _("Адрес")),
            ("phone1", _("Телефон")),
            ("photo", _("Главное фото")),
        )

        completed = 0
        missing = []
        missing_fields = set()
        for field_name, label in checklist:
            if self._field_has_value(form, field_name, obj=obj):
                completed += 1
            else:
                missing.append(str(label))
                missing_fields.add(field_name)

        total = len(checklist)
        completion_pct = round(completed / total * 100) if total else 0

        title = str(_("Новое место"))
        state_badges = []
        meta_items = []
        error_count = len(form.errors)
        visibility = self._place_visibility_state(obj)

        if obj is not None and obj.pk:
            title = obj.name_ru or obj.name or title
            quality = place_quality_check(obj)
            state_badges.append(
                {
                    "label": visibility["label"],
                    "tone": visibility["tone"],
                }
            )
            state_badges.append(
                {
                    "label": str(dict(obj.STATUS_CHOICES).get(obj.status, obj.status)),
                    "tone": "good" if obj.status == obj.STATUS_PUBLISHED else "muted",
                }
            )
            state_badges.append(
                {
                    "label": str(_("Есть координаты")) if obj.has_coordinates else str(_("Нужны координаты")),
                    "tone": "good" if obj.has_coordinates else "warn",
                }
            )
            meta_items.append(
                {
                    "label": str(_("Качество")),
                    "value": f"{quality.score} / 100",
                }
            )
            if obj.published_at:
                meta_items.append(
                    {
                        "label": str(_("Опубликовано")),
                        "value": timezone.localtime(obj.published_at).strftime("%d.%m.%Y %H:%M"),
                    }
                )
            meta_items.append(
                {
                    "label": str(_("Владелец")),
                    "value": obj.owner.username if obj.owner_id and obj.owner else str(_("Не назначен")),
                }
            )
        else:
            state_badges.append(
                {
                    "label": str(_("Черновой режим")),
                    "tone": "muted",
                }
            )

        if add:
            meta_items.insert(
                0,
                {
                    "label": str(_("Режим")),
                    "value": str(_("Создание новой карточки")),
                }
            )
        else:
            meta_items.insert(
                0,
                {
                    "label": str(_("Режим")),
                    "value": str(_("Редактирование карточки")),
                }
            )

        return {
            "title": title,
            "completion_pct": completion_pct,
            "completed": completed,
            "total": total,
            "error_count": error_count,
            "visibility": visibility,
            "checklist_items": [
                {
                    "field_name": field_name,
                    "input_id": f"id_{field_name}",
                    "label": str(label),
                    "initial": field_name not in missing_fields,
                }
                for field_name, label in checklist
            ],
            "missing": missing[:5],
            "readiness_label": str(_("Готово к публикации")) if not missing else str(_("Нужна доработка")),
            "readiness_tone": "good" if not missing else "warn",
            "state_badges": state_badges,
            "meta_items": meta_items,
        }

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
                    ("category", "subcategory"),
                    "slug",
                    ("is_temporary", "is_active", "is_verified"),
                    ("temporary_start", "temporary_end"),
                    ("status", "rejection_reason"),
                    "owner",
                    "likes_count",
                    "rating_avg",
                    "rating_count",
                    "lifecycle_status_display",
                    "quality_status_display",
                )
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                ),
            },
        ),
        (
            _("Возраст и цена"),
            {
                "fields": (
                    ("age_from", "age_to", "lesson_duration_minutes"),
                    ("price_from", "price_to", "price_per_lesson"),
                    ("price_per_month", "price_per_8_lessons"),
                )
            },
        ),
        (_("Локация"), {"fields": (("district", "metro"), "address", ("lat", "lng"), ("coordinates_status_display", "map_ready_status_display"))}),
        (_("Контакты"), {"fields": (("phone1", "instagram", "website"), "schedule", "extra_conditions", "additional_info")}),
        (_("Фотографии"), {"fields": ("photo",)}),
        (_("Удаление"), {"classes": ("collapse",), "fields": ("deleted_at", "deleted_by")}),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cover_photo",
                    "last_verified_at_display",
                    "published_at_display",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.ADD_FIELDSETS
        return super().get_fieldsets(request, obj)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("status", Place.STATUS_DRAFT)
        initial.setdefault("is_active", False)
        return initial

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        if obj is None:
            return [inline for inline in inline_instances if isinstance(inline, PlacePhotoInline)]
        return inline_instances

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_ru or obj.name
        meta: list[str] = [f"ID {obj.pk}"]
        if obj.is_deleted:
            meta.append(str(_("Сейчас скрыта в разделе удалённых")))
        preview = ""
        image_field = obj.photo or obj.cover_photo
        if image_field and getattr(image_field, "name", ""):
            try:
                preview = format_html(
                    '<img src="{}" alt="" class="km-admin-thumb" loading="lazy">',
                    image_field.url,
                )
            except Exception:
                preview = ""
        if not preview:
            preview = mark_safe('<span class="km-admin-thumb km-admin-thumb--placeholder" aria-hidden="true">•</span>')
        return format_html(
            '<div class="km-admin-entry">'
            '{}'
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">{}</span>'
            '{}'
            "</div>"
            "</div>",
            preview,
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

    @admin.display(description=_("Проверено модератором"))
    def last_verified_at_display(self, obj):
        if not obj or not obj.last_verified_at:
            return _("Ещё не отмечено")
        return timezone.localtime(obj.last_verified_at).strftime("%d.%m.%Y %H:%M")

    @admin.display(description=_("Дата публикации"))
    def published_at_display(self, obj):
        if not obj or not obj.published_at:
            return _("Ещё не опубликовано")
        return timezone.localtime(obj.published_at).strftime("%d.%m.%Y %H:%M")

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
        ]
        
        if obj.is_deleted:
            badges.append(self._render_place_state_badge(label=_("В удаленных"), tone="muted"))
        elif not obj.is_active:
            badges.append(self._render_place_state_badge(label=_("Неактивно"), tone="warn"))

        badges.append(
            self._render_place_state_badge(
                label=_("Проверено") if obj.is_verified else _("Без проверки"),
                tone="good" if obj.is_verified else "warn",
            )
        )
        meta_bits: list[str] = []
        if obj.is_temporary:
            meta_bits.append(str(_("Временное")))
        if obj.rejection_reason and obj.status == obj.STATUS_REJECTED:
            meta_bits.append(str(_("Есть причина отклонения")))
            
        badges_html = mark_safe(" ".join(badges))
        return format_html(
            '<div class="km-admin-stack"><div class="km-admin-badges">{}</div>{}</div>',
            badges_html,
            format_html(
                '<span class="km-admin-meta">{}</span>',
                " · ".join(meta_bits),
            ) if meta_bits else "",
        )

    @admin.display(description=_("Карта"))
    def map_status_summary(self, obj):
        coords_line = _("lat %(lat)s, lng %(lng)s") % {"lat": round(obj.lat, 5), "lng": round(obj.lng, 5)} if obj.has_coordinates else _("Координаты не заполнены")
        
        if not obj.has_coordinates:
            map_badge = self._render_place_state_badge(label=_("Нужны координаты"), tone="warn")
        elif obj.is_map_ready:
            map_badge = self._render_place_state_badge(label=_("Готово для карты"), tone="good")
        else:
            map_badge = self._render_place_state_badge(label=_("Не готово для карты"), tone="muted")

        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">{}</div>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            map_badge,
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

    def _place_quick_filters(self, request, *, counts: dict[str, int] | None = None):
        counts = counts or self._place_dashboard_counts()
        status_keys = ("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")
        current_deleted = request.GET.get("deleted_state")
        current_active = request.GET.get("is_active__exact")
        current_coordinates = request.GET.get("coordinates_status")
        current_map_ready = request.GET.get("map_ready_status")
        current_status = request.GET.get("status__exact")
        return (
            {
                "key": "all",
                "label": _("Все карточки"),
                "count": int(counts["quick_all"]),
                "url": self._build_changelist_query_string(request, clear=status_keys),
                "active": not any((current_deleted, current_active, current_coordinates, current_map_ready, current_status)),
            },
            {
                "key": "published",
                "label": _("Опубликованы"),
                "count": int(counts["quick_published"]),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="1",
                ),
                "active": current_deleted == "active" and current_active == "1" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "inactive",
                "label": _("Неактивные"),
                "count": int(counts["quick_inactive"]),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="0",
                ),
                "active": current_deleted == "active" and current_active == "0" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "draft",
                "label": _("Черновики"),
                "count": int(counts["quick_draft"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_DRAFT),
                "active": current_status == Place.STATUS_DRAFT and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": int(counts["quick_pending"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_PENDING),
                "active": current_status == Place.STATUS_PENDING and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "rejected",
                "label": _("Отклонены"),
                "count": int(counts["quick_rejected"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_REJECTED),
                "active": current_status == Place.STATUS_REJECTED and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "deleted",
                "label": _("В удалённых"),
                "count": int(counts["quick_deleted"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, deleted_state="deleted"),
                "active": current_deleted == "deleted" and not current_active and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "without_coordinates",
                "label": _("Без координат"),
                "count": int(counts["quick_without_coordinates"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, coordinates_status="no"),
                "active": current_coordinates == "no" and not current_deleted and not current_active and not current_map_ready and not current_status,
            },
            {
                "key": "not_ready_for_map",
                "label": _("Не готовы для карты"),
                "count": int(counts["quick_not_ready_for_map"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, map_ready_status="no"),
                "active": current_map_ready == "no" and not current_deleted and not current_active and not current_coordinates and not current_status,
            },
        )

    def _place_dashboard_counts(self) -> dict[str, int]:
        counts = Place.objects.aggregate(
            quick_all=Count("pk"),
            quick_published=Count("pk", filter=Q(deleted_at__isnull=True, is_active=True)),
            quick_inactive=Count("pk", filter=Q(deleted_at__isnull=True, is_active=False)),
            quick_draft=Count("pk", filter=Q(status=Place.STATUS_DRAFT)),
            quick_pending=Count("pk", filter=Q(status=Place.STATUS_PENDING)),
            quick_rejected=Count("pk", filter=Q(status=Place.STATUS_REJECTED)),
            quick_deleted=Count("pk", filter=Q(deleted_at__isnull=False)),
            quick_without_coordinates=Count("pk", filter=Q(lat__isnull=True) | Q(lng__isnull=True)),
            quick_not_ready_for_map=Count("pk", filter=Q(is_active=False) | Q(lat__isnull=True) | Q(lng__isnull=True)),
            stat_total=Count("pk"),
            stat_published=Count("pk", filter=Q(deleted_at__isnull=True, is_active=True)),
            stat_pending=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_PENDING)),
            stat_inactive=Count("pk", filter=Q(deleted_at__isnull=True, is_active=False)),
            stat_without_coordinates=Count(
                "pk",
                filter=Q(deleted_at__isnull=True) & (Q(lat__isnull=True) | Q(lng__isnull=True)),
            ),
        )
        return {key: int(value or 0) for key, value in counts.items()}

    def _place_dashboard_stats(self, request, *, counts: dict[str, int] | None = None):
        counts = counts or self._place_dashboard_counts()
        return (
            {
                "label": _("Всего"),
                "count": counts["stat_total"],
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")),
                "tone": "neutral",
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
            },
            {
                "label": _("Опубликовано"),
                "count": counts["stat_published"],
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", is_active__exact="1"),
                "tone": "good",
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            },
            {
                "label": _("На модерации"),
                "count": counts["stat_pending"],
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), status__exact=Place.STATUS_PENDING),
                "tone": "warn",
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            },
            {
                "label": _("Неактивные"),
                "count": counts["stat_inactive"],
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", is_active__exact="0"),
                "tone": "muted",
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/></svg>',
            },
            {
                "label": _("Без координат"),
                "count": counts["stat_without_coordinates"],
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), coordinates_status="no"),
                "tone": "info",
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
            },
        )

    def _place_bulk_actions(self):
        return (
            {
                "name": "mark_published",
                "label": _("Опубликовать"),
                "tone": "good",
                "description": _("Опубликовать выбранные карточки с проверкой качества."),
            },
            {
                "name": "mark_inactive",
                "label": _("Снять с публикации"),
                "tone": "muted",
                "description": _("Оставить карточки в базе, но скрыть их с сайта."),
            },
            {
                "name": "mark_draft",
                "label": _("Вернуть в черновик"),
                "tone": "muted",
                "description": _("Снять выбранные карточки с сайта и перевести в черновики."),
            },
            {
                "name": "mark_pending",
                "label": _("На модерацию"),
                "tone": "warn",
                "description": _("Отправить выбранные карточки на повторную модерацию."),
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

    def _handle_publish_submit(self, request, obj: Place):
        quality = place_quality_check(obj)
        if not quality.is_ready:
            obj.status = Place.STATUS_DRAFT
            obj.is_active = False
            obj.save(update_fields=["status", "is_active", "updated_at"])
            self.message_user(
                request,
                _("Карточка сохранена, но не опубликована: сначала заполните обязательные поля и фото."),
                level=messages.WARNING,
            )
            return HttpResponseRedirect(self._place_change_url(obj))

        update_fields = ["status", "is_active", "rejection_reason", "updated_at"]
        obj.status = Place.STATUS_PUBLISHED
        obj.is_active = True
        obj.rejection_reason = ""
        if obj.published_at is None:
            obj.published_at = timezone.now()
            update_fields.append("published_at")
        obj.save(update_fields=update_fields)
        self.message_user(
            request,
            _("Карточка опубликована и теперь может показываться на сайте."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._place_change_url(obj))

    def _handle_unpublish_submit(self, request, obj: Place):
        obj.is_active = False
        if obj.status == Place.STATUS_PUBLISHED:
            obj.status = Place.STATUS_DRAFT
            obj.save(update_fields=["is_active", "status", "updated_at"])
        else:
            obj.save(update_fields=["is_active", "updated_at"])
        self.message_user(
            request,
            _("Карточка снята с публикации и скрыта с сайта."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._place_change_url(obj))

    def get_urls(self):
        custom_urls = [
            path(
                "search-suggestions/",
                self.admin_site.admin_view(self.search_suggestions_view),
                name="catalog_place_search_suggestions",
            ),
            path(
                "<path:object_id>/restore/",
                self.admin_site.admin_view(self.restore_view),
                name="catalog_place_restore",
            ),
        ]
        return custom_urls + super().get_urls()

    def search_suggestions_view(self, request):
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        queryset = self.get_queryset(request)
        queryset, _ = self.get_search_results(request, queryset, term)
        queryset = queryset.select_related("owner").distinct()[:8]

        results = []
        for place in queryset:
            title = (place.name_i18n(language_code) or place.name or "").strip()
            if not title:
                continue

            meta_parts = []
            if place.district:
                from catalog.services.locations import get_location_translation
                meta_parts.append(get_location_translation(place.district, language_code))
            if place.address:
                meta_parts.append(str(place.address))
            if place.phone1:
                meta_parts.append(str(place.phone1))
            if getattr(place, "owner", None):
                owner_label = place.owner.get_username() or getattr(place.owner, "email", "")
                if owner_label:
                    meta_parts.append(str(owner_label))

            results.append(
                {
                    "value": title,
                    "label": title,
                    "meta": " • ".join(part for part in meta_parts if part)[:180],
                }
            )

        return JsonResponse({"results": results})

    def changelist_view(self, request, extra_context=None):
        dashboard_counts = self._place_dashboard_counts()
        quick_filters = self._place_quick_filters(request, counts=dashboard_counts)
        primary_filter_keys = {"all", "published", "pending", "inactive", "without_coordinates", "deleted"}
        extra_context = {
            "place_dashboard_stats": self._place_dashboard_stats(request, counts=dashboard_counts),
            "km_primary_quick_filters": [item for item in quick_filters if item.get("key") in primary_filter_keys],
            "km_secondary_quick_filters": [item for item in quick_filters if item.get("key") not in primary_filter_keys],
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
        now = timezone.now()
        updated_count = queryset.update(is_verified=True, updated_at=now)
        queryset.filter(last_verified_at__isnull=True).update(last_verified_at=now)
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
        for place in queryset.prefetch_related("gallery").iterator(chunk_size=100):
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
        old_schedule_value = ""
        if change and obj.pk:
            old_obj = Place.objects.filter(pk=obj.pk).first()
            if old_obj:
                for field in self.AUDIT_TRACKED_FIELDS:
                    old_values[field] = getattr(old_obj, field)
                if old_obj.has_structured_schedule:
                    old_schedule_value = build_schedule_summary(serialize_place_schedule(old_obj))
                else:
                    old_schedule_value = (old_obj.schedule or "").strip()

        if "_save_draft" in request.POST:
            obj.status = Place.STATUS_DRAFT
            obj.is_active = False

        if obj.is_verified and obj.last_verified_at is None:
            obj.last_verified_at = timezone.now()

        super().save_model(request, obj, form, change)
        if hasattr(form, "save_schedule"):
            form.save_schedule(obj)
        new_schedule_value = build_schedule_summary(serialize_place_schedule(obj)) if obj.has_structured_schedule else (obj.schedule or "").strip()

        if change and old_values:
            audit_entries = []
            for field_name in self.AUDIT_TRACKED_FIELDS:
                old_value = old_values.get(field_name)
                new_value = getattr(obj, field_name)
                if field_name == "schedule":
                    old_value = old_schedule_value
                    new_value = new_schedule_value
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
        if "_save_draft" in request.POST:
            return self._handle_save_draft_submit(
                request,
                obj,
                message=_("Черновик сохранён. Можно вернуться и продолжить заполнение позже."),
            )
        if "_publish_place" in request.POST:
            return self._handle_publish_submit(request, obj)
        if "_unpublish_place" in request.POST:
            return self._handle_unpublish_submit(request, obj)
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Карточка сохранена."),
            )
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if "_save_draft" in request.POST:
            return self._handle_save_draft_submit(
                request,
                obj,
                message=_("Изменения сохранены как черновик. Можно продолжить редактирование позже."),
            )
        if "_publish_place" in request.POST:
            return self._handle_publish_submit(request, obj)
        if "_unpublish_place" in request.POST:
            return self._handle_unpublish_submit(request, obj)
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Изменения сохранены."),
            )
        return super().response_change(request, obj)

    def _handle_save_draft_submit(self, request, obj, *, message: str):
        self.message_user(request, message, level=messages.SUCCESS)
        return HttpResponseRedirect(self._place_change_url(obj))

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = self._place_change_url(obj)
        primary_action = render_primary_action(edit_url, _("Редактировать"))
        
        menu_actions = []
        if obj.is_deleted:
            menu_actions.append((self._place_restore_url(obj), _("Восстановить"), "km-admin-action-menu__link--good"))
            menu_actions.append((None, _("Карточка скрыта из каталога"), "km-admin-action-menu__hint"))
        else:
            menu_actions.append((obj.get_absolute_url(), _("Открыть"), ""))
            menu_actions.append((self._place_delete_url(obj), _("В удалённые"), "km-admin-action-menu__link--danger"))
            
        menu_html = render_action_menu(menu_actions)
        return render_row_actions_container(primary_action, menu_html)


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


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    fields = ("name_ru", "name_az", "name_en", "order")


def save_uploaded_category_icon(uploaded_file, category_code="category-icon"):
    ext = (uploaded_file.name.rsplit(".", 1)[-1] if "." in uploaded_file.name else "").lower()
    if f".{ext}" not in [".svg", ".png", ".jpg", ".jpeg", ".webp"]:
        raise forms.ValidationError(_("Поддерживаются только SVG, PNG, JPG, JPEG и WEBP."))

    storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
    safe_code = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in (category_code or "category-icon")).strip("-")
    safe_code = safe_code or "category-icon"
    filename = storage.get_available_name(f"cat_icons/{safe_code}.{ext}")
    saved_name = storage.save(filename, uploaded_file)
    return storage.url(saved_name)


class CategoryAdminForm(forms.ModelForm):
    name = forms.CharField(widget=forms.HiddenInput(), required=False)
    name_az = forms.CharField(label=_("Название (AZ)"), required=True)
    icon_upload = forms.FileField(
        label=_("Файл иконки"),
        required=False,
        help_text=_("Загрузите SVG, PNG, JPG, JPEG или WEBP. Это поле сохраняет файл отдельно, а текстовое поле ниже остаётся запасным вариантом для пути или CSS-класса."),
    )

    class Meta:
        model = Category
        fields = "__all__"
        widgets = {
            "code": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: education")}),
            "order": forms.NumberInput(attrs={"min": 0, "step": 1, "inputmode": "numeric"}),
            "name_ru": forms.TextInput(attrs={"placeholder": _("Например: Образование")}),
            "name_en": forms.TextInput(attrs={"placeholder": _("Например: Education")}),
            "icon": forms.TextInput(attrs={"autocomplete": "off", "placeholder": _("Например: icons/categories/sports.svg")}),
            "color_bg": forms.TextInput(attrs={"type": "color"}),
            "color_text": forms.TextInput(attrs={"type": "color"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name_az = cleaned_data.get("name_az")
        if name_az:
            cleaned_data["name"] = name_az
        return cleaned_data

    def clean_icon_upload(self):
        uploaded_file = self.cleaned_data.get("icon_upload")
        if not uploaded_file:
            return uploaded_file
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in [".svg", ".png", ".jpg", ".jpeg", ".webp"]:
            raise forms.ValidationError(_("Поддерживаются только SVG, PNG, JPG, JPEG и WEBP."))
        return uploaded_file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name_az"].widget.attrs.setdefault("placeholder", _("Например: Təhsil"))
        self.fields["icon"].label = _("Путь или CSS-класс")
        self.fields["icon"].help_text = _(
            "Можно указать относительный путь к иконке или CSS-класс. Например: icons/categories/sports.svg или fas fa-futbol."
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.cleaned_data.get("icon_upload")
        if uploaded_file:
            instance.icon = save_uploaded_category_icon(uploaded_file, self.cleaned_data.get("code") or instance.code)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    change_form_template = "admin/catalog/category/change_form.html"
    list_display = ("code", "name_ru", "name_az", "name_en")
    search_fields = ("code", "name_ru", "name_az", "name_en")
    ordering = ("name_ru",)
    inlines = [SubcategoryInline]

    fieldsets = (
        (None, {
            "fields": (
                ("code", "name_az"),
                ("name_ru", "name_en"),
                "icon",
                ("color_bg", "color_text"),
                "name",
            )
        }),
    )

    def get_inlines(self, request, obj=None):
        if not obj or request.GET.get("_popup"):
            return []
        return self.inlines

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('upload-icon/', self.admin_site.admin_view(self.upload_icon_view), name='catalog_category_upload_icon'),
            path('toggle-active/', self.admin_site.admin_view(self.toggle_active_view), name='catalog_taxonomy_toggle_active'),
        ]
        return custom_urls + urls

    def toggle_active_view(self, request):
        from django.http import JsonResponse
        from catalog.models.category import Category, Subcategory
        
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
            
        if not self.has_change_permission(request):
            return JsonResponse({"error": "Permission denied"}, status=403)
            
        obj_type = request.POST.get('obj_type')
        obj_id = request.POST.get('obj_id')
        
        if obj_type == 'category':
            obj = Category.objects.filter(pk=obj_id).first()
        elif obj_type == 'subcategory':
            obj = Subcategory.objects.filter(pk=obj_id).first()
        else:
            return JsonResponse({"error": "Invalid obj_type"}, status=400)
            
        if not obj:
            return JsonResponse({"error": "Object not found"}, status=404)
            
        obj.is_active = not obj.is_active
        obj.save(update_fields=['is_active'])
        
        return JsonResponse({"status": "success", "is_active": obj.is_active})

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Prefetch, Count, Q
        from catalog.models.category import Category, Subcategory
        from django.template.response import TemplateResponse
        from django.utils.translation import gettext as _

        search_query = request.GET.get('q', '').strip()
        
        categories = Category.objects.all()
        subcategories = Subcategory.objects.all()

        if search_query:
            sub_matches = subcategories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query)
            )
            cat_ids_from_subs = sub_matches.values_list('category_id', flat=True)
            
            categories = categories.filter(
                Q(code__icontains=search_query) |
                Q(name_ru__icontains=search_query) |
                Q(name_az__icontains=search_query) |
                Q(name_en__icontains=search_query) |
                Q(code__in=cat_ids_from_subs)
            )

        # Annotate counts and optimize queries
        categories = categories.annotate(
            places_count=Count('place', distinct=True),
            sub_count=Count('subcategories', distinct=True)
        ).order_by('name_ru')

        sub_qs = Subcategory.objects.annotate(
            places_count=Count('place')
        ).order_by('name_ru')

        categories = categories.prefetch_related(
            Prefetch('subcategories', queryset=sub_qs)
        )

        context = {
            **self.admin_site.each_context(request),
            'title': _('Категории и подкатегории'),
            'categories': categories,
            'search_query': search_query,
            'opts': self.model._meta,
            'has_add_permission': self.has_add_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'app_label': self.model._meta.app_label,
        }
        context.update(extra_context or {})
        return TemplateResponse(request, "admin/catalog/category/change_list.html", context)

    def upload_icon_view(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "Method not allowed"}, status=405)

        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            media_url = save_uploaded_category_icon(uploaded_file, request.POST.get("code") or "category-icon")
        except forms.ValidationError as exc:
            return JsonResponse({"error": exc.messages[0]}, status=400)
        except Exception as exc:
            return JsonResponse({"error": f"Failed to save file: {str(exc)}"}, status=500)

        return JsonResponse({"success": True, "url": media_url, "path": media_url})



@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ("name_ru", "category", "name_az", "name_en")
    list_filter = ("category",)
    search_fields = ("name_ru", "name_az", "name_en")
    ordering = ("category", "name_ru")
    exclude = ("code", "order")

    def has_module_permission(self, request):
        # Скрываем подкатегории из бокового меню, так как они управляются из Категорий
        return False
