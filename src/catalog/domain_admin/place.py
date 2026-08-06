from django.conf import settings
import json
import logging
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Max, Prefetch, Q
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _, ngettext
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from urllib.parse import urlparse
import re

from catalog.content_data import BAKU_METRO_STATIONS
from catalog.forms import PlaceScheduleEditorFormMixin, SubcategorySelect
from catalog.forms import _format_azerbaijan_phone_for_input, _validate_azerbaijan_phone
from catalog.models import (
    Place,
    PlacePhoto,
    PlaceChangeAudit,
    PlaceOwnershipRequest,
    Event,
    EventPhoto,
    PlaceReviewsByClub,
    Category,
    Subcategory,
    CatalogContentSettings,
)
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.content_quality import place_quality_check, public_place_queryset
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.options import sort_translated_values
from catalog.services.image_uploads import normalize_uploaded_image
from catalog.services.pricing_plans import normalize_pricing_plans, pricing_audit_summary
from catalog.services.place_schedule import FULL_DAY_LABELS, build_schedule_summary, serialize_place_schedule
from .review import PlaceReviewInline
from .ui_utils import render_primary_action, render_action_menu, render_row_actions_container


ADMIN_DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"
DRAFT_PLACEHOLDER_NAME = "Черновик без названия"
logger = logging.getLogger(__name__)

PLACE_QUALITY_ERROR_LABELS = {
    "missing_name": _("не указано название"),
    "missing_category": _("не указана категория"),
    "description_too_short": _("слишком короткое описание"),
    "test_content": _("обнаружены тестовые данные"),
    "missing_contact": _("не указан контакт"),
    "missing_address": _("не указан адрес"),
    "missing_age": _("не указан возраст"),
    "missing_price": _("не указана цена"),
    "missing_schedule": _("не указано расписание"),
    "missing_photo": _("не добавлено фото"),
}


def _normalized_phone(value) -> str:
    return "".join(re.findall(r"\d", value or ""))


def _normalized_url(value) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.netloc.removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def _normalized_text(value) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", (value or "").lower()).split())


def place_quality_error_labels(errors) -> str:
    return ", ".join(str(PLACE_QUALITY_ERROR_LABELS.get(error, error)) for error in errors)


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
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


class PlaceAdminForm(PlaceScheduleEditorFormMixin, forms.ModelForm):
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT
    name = forms.CharField(required=False, widget=forms.HiddenInput())
    pricing_plans = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-tariff-input": ""}),
    )

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
    metro = forms.ChoiceField(
        label=_("Метро"),
        required=False,
        choices=(),
        widget=forms.Select(attrs={"class": "field"}),
    )

    class Meta:
        model = Place
        fields = "__all__"
        exclude = (
            "pricing_plans_legacy", "price_from", "price_to", "price_per_lesson",
            "price_per_month", "price_per_8_lessons",
        )
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
            "offers_adult_classes": _("Также есть занятия для взрослых"),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("age_open_ended"):
            cleaned["age_to"] = None
            self.instance.age_to = None
            if cleaned.get("age_from") is None:
                cleaned["age_from"] = 0
                self.instance.age_from = 0
        if cleaned.get("home_recommended_order") is None:
            cleaned["home_recommended_order"] = 0
        cleaned = self._clean_schedule_editor(cleaned)
        is_save_draft = bool(self.data and "_save_draft" in self.data)
        skips_publish_validation = bool(
            self.data
            and any(
                action in self.data
                for action in ("_save_draft", "_refresh_coordinates_from_address", "_unpublish_place")
            )
        )
        self.draft_save_only = is_save_draft
        try:
            cleaned["pricing_plans"] = normalize_pricing_plans(cleaned.get("pricing_plans") or "[]", allow_verified=True)
            self.instance.pricing_plans = cleaned["pricing_plans"]
        except ValidationError as exc:
            self.add_error("pricing_plans", exc)
            cleaned["pricing_plans"] = []
        from catalog.services.locations import clean_location_fields

        primary_name = (
            (cleaned.get("name_az") or "").strip()
            or (cleaned.get("name_ru") or "").strip()
            or (cleaned.get("name_en") or "").strip()
            or (cleaned.get("name") or "").strip()
        )
        if primary_name:
            cleaned["name"] = primary_name
        elif is_save_draft:
            cleaned["name"] = (getattr(self.instance, "name", "") or "").strip() or DRAFT_PLACEHOLDER_NAME
        else:
            self.add_error("name_az", _("Заполните хотя бы одно название, лучше азербайджанское как основное."))

        cleaned = clean_location_fields(self, cleaned)
        is_active = cleaned.get("is_active")
        if is_active is None:
            is_active = getattr(self.instance, "is_active", False)
        status = cleaned.get("status")
        if status is None:
            status = getattr(self.instance, "status", "")
        # Use getattr to safely access STATUS_PUBLISHED from instance or just string
        status_published = getattr(self.instance, "STATUS_PUBLISHED", "published")
        if (is_active or status == status_published) and not skips_publish_validation:
            checklist = [
                ("name", _("Название")),
                ("category", _("Категория")),
                ("description_az", _("Описание (AZ)")),
                ("age_from", _("Возраст от")),
                ("age_to", _("Возраст до")),
                ("address", _("Адрес")),
                ("phone1", _("Телефон")),
                ("photo", _("Главное фото")),
            ]
            if cleaned.get("age_open_ended"):
                checklist = [item for item in checklist if item[0] != "age_to"]
            missing = []
            for field_name, label in checklist:
                val = cleaned.get(field_name)
                if not val and val != 0:
                    if self.instance and self.instance.pk:
                        val = getattr(self.instance, field_name, None)
                        if hasattr(val, "name") and not val.name:
                            val = None
                if not val and val != 0:
                    missing.append(str(label))
            if missing:
                self.add_error(None, _("Нельзя опубликовать карточку. Обязательны для заполнения: {}").format(", ".join(missing)))

        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The order only matters for places selected for the home page. Keep
        # ordinary draft and catalog saves from requiring a meaningless value.
        self.fields["home_recommended_order"].required = False
        self.fields["age_open_ended"].help_text = _(
            "Отметьте для 3+; для всех возрастов укажите «Возраст от» = 0."
        )
        self.draft_save_only = bool(self.data and "_save_draft" in self.data)
        if self.draft_save_only:
            for field in self.fields.values():
                field.required = False
        if not self.is_bound and self.instance is not None:
            self.initial["pricing_plans"] = json.dumps(self.instance.pricing_plans or [], ensure_ascii=False)
        from catalog.services.locations import init_location_fields, configure_location_choices
        init_location_fields(self, self.instance)
        configure_location_choices(self)
        self._configure_metro_choices()

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
            subcategory_widget = SubcategorySelect(attrs=self.fields["subcategory"].widget.attrs)
            subcategory_widget.choices = self.fields["subcategory"].choices
            self.fields["subcategory"].widget = subcategory_widget
        self.fields["photo"].help_text = _("Используется в каталоге, на карте и первым на странице места.")
        self.fields["cover_photo"].help_text = _("Резервное изображение. Используется только если главное фото отсутствует.")
        self.fields["offers_adult_classes"].help_text = _(
            "Отметьте, если кроме детских программ у места есть отдельные занятия для взрослых."
        )
        for field_name in ("phone1", "phone2", "phone3"):
            if field_name not in self.fields:
                continue
            self.fields[field_name].widget.attrs.update(
                {
                    "autocomplete": "tel",
                    "inputmode": "tel",
                    "placeholder": "+994 50 123 45 67",
                    "data-km-az-phone": "1",
                    "maxlength": "17",
                }
            )
            phone_value = self.initial.get(field_name) or getattr(self.instance, field_name, "") or ""
            if phone_value:
                self.initial[field_name] = _format_azerbaijan_phone_for_input(phone_value)
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
            "phone2": _("Напр., +994 55 123-45-67"),
            "phone3": _("Напр., +994 70 123-45-67"),
            "instagram": _("Напр., @kidsmap"),
            "website": _("Напр., https://example.com"),
            "schedule": _("Напр., Пн–Пт 10:00–20:00, Сб–Вс 11:00–19:00"),
            "extra_conditions": _("Напр., Предварительная запись, наличие сертификата и т.п."),
            "additional_info": _("Напр., Описание места, особенности, важные детали и т.п."),
            "extra_conditions_az": _("Şərtləri azərbaycanca yazın."),
            "extra_conditions_ru": _("Укажите условия по-русски."),
            "extra_conditions_en": _("Add conditions in English."),
            "additional_info_az": _("Əlavə məlumatı azərbaycanca yazın."),
            "additional_info_ru": _("Укажите дополнительную информацию по-русски."),
            "additional_info_en": _("Add additional information in English."),
            "address": _("Напр., ул. Низами 10, Баку"),
        }
        for field_name, placeholder in _placeholders.items():
            if field_name in self.fields and hasattr(self.fields[field_name].widget, "attrs"):
                self.fields[field_name].widget.attrs.setdefault("placeholder", str(placeholder))
        self._init_schedule_editor()

    def clean_phone1(self):
        value = self.cleaned_data.get("phone1") or ""
        if not value:
            return ""
        return _validate_azerbaijan_phone(value)

    def clean_phone2(self):
        value = self.cleaned_data.get("phone2") or ""
        return _validate_azerbaijan_phone(value) if value else ""

    def clean_phone3(self):
        value = self.cleaned_data.get("phone3") or ""
        return _validate_azerbaijan_phone(value) if value else ""

    def _configure_metro_choices(self):
        metro_options = sort_translated_values(BAKU_METRO_STATIONS)
        try:
            content_settings = CatalogContentSettings.get_solo()
            metro_options = sort_translated_values(content_settings.metro_stations())
        except Exception:
            pass

        metro_current = (self.initial.get("metro") or getattr(self.instance, "metro", "") or "").strip()
        choices = [("", _("Выберите метро"))]
        seen = set()

        for raw in metro_options or []:
            value = str(raw or "").strip()
            if not value or value in seen:
                continue
            seen.add(value)
            choices.append((value, _(value)))

        if metro_current and metro_current not in seen:
            choices.insert(1, (metro_current, _(metro_current)))

        self.fields["metro"].choices = choices
        self.fields["metro"].help_text = _("Если район не выбран, укажите ближайшую станцию метро.")
        self.fields["metro"].error_messages.update({"invalid_choice": _("Выберите станцию метро из списка.")})


class EventAdminForm(forms.ModelForm):
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT
    PICKER_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
    require_location_region = False

    # The custom admin template renders one text input per date. Declaring the
    # fields prevents ModelAdmin from replacing them with SplitDateTimeField,
    # which expects a two-item POST value and rejects the browser payload.
    start_datetime = forms.DateTimeField(
        label=_("Начало мероприятия"), required=False,
        widget=forms.TextInput(attrs={"class": "field", "data-kidsmap-datetime-picker": "1", "data-event-datetime": "start", "data-allow-input": "1"}),
    )
    end_datetime = forms.DateTimeField(
        label=_("Окончание мероприятия"), required=False,
        widget=forms.TextInput(attrs={"class": "field", "data-kidsmap-datetime-picker": "1", "data-event-datetime": "end", "data-allow-input": "1"}),
    )
    published_at = forms.DateTimeField(
        label=_("Дата публикации"), required=False,
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "step": "900"},
            format=ADMIN_DATETIME_LOCAL_FORMAT,
        ),
    )

    region = forms.ChoiceField(
        label=_("Город / регион"), required=False, choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-region": ""}),
    )
    district = forms.ChoiceField(
        label=_("Район города"), required=False, choices=(),
        widget=forms.Select(attrs={"class": "field", "data-km-location-district": ""}),
    )
    metro = forms.ChoiceField(
        label=_("Метро"), required=False, choices=(), widget=forms.Select(attrs={"class": "field"}),
    )

    class Meta:
        model = Event
        fields = "__all__"
        widgets = {
            "start_datetime": forms.TextInput(attrs={"class": "field", "data-kidsmap-datetime-picker": "1", "data-event-datetime": "start", "data-allow-input": "1"}),
            "end_datetime": forms.TextInput(attrs={"class": "field", "data-kidsmap-datetime-picker": "1", "data-event-datetime": "end", "data-allow-input": "1"}),
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
            "website": _("Сайт"),
            "lat": _("Широта"),
            "lng": _("Долгота"),
        }

    def clean(self):
        cleaned = super().clean()
        from catalog.services.locations import clean_location_fields
        cleaned = clean_location_fields(self, cleaned)
        start_datetime = cleaned.get("start_datetime")
        end_datetime = cleaned.get("end_datetime")
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error("end_datetime", _("Окончание мероприятия должно быть позже начала."))
        is_save_draft = bool(self.data and "_save_draft" in self.data)
        skips_publish_validation = bool(
            self.data and any(action in self.data for action in ("_save_draft", "_unpublish_event"))
        )
        is_active = cleaned.get("is_active")
        if is_active is None:
            is_active = getattr(self.instance, "is_active", False)
        status = cleaned.get("status")
        if status is None:
            status = getattr(self.instance, "status", "")
        status_published = getattr(self.instance, "STATUS_PUBLISHED", "published")
        if (is_active or status == status_published) and not skips_publish_validation:
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
            missing = []
            for field_name, label in checklist:
                val = cleaned.get(field_name)
                if not val and val != 0:
                    if self.instance and self.instance.pk:
                        val = getattr(self.instance, field_name, None)
                        if hasattr(val, "name") and not val.name:
                            val = None
                if not val and val != 0:
                    missing.append(str(label))
            if missing:
                self.add_error(None, _("Нельзя опубликовать мероприятие. Обязательны для заполнения: {}").format(", ".join(missing)))
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from catalog.services.locations import configure_location_choices, init_location_fields
        init_location_fields(self, self.instance)
        configure_location_choices(self)
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
                    display_format = self.PICKER_DATETIME_FORMAT if field_name in {"start_datetime", "end_datetime"} else self.DATETIME_LOCAL_FORMAT
                    self.initial[field_name] = localized_value.strftime(display_format)
        self.fields["photo"].help_text = _(
            "Основное изображение мероприятия для списка и детальной страницы."
        )
        self.fields["start_datetime"].help_text = _(
            "Дата и время старта. Без этого поле мероприятие нельзя опубликовать."
        )
        self.fields["end_datetime"].help_text = _(
            "Дата и время окончания. Используется для определения актуальности и завершения."
        )
        self.fields["address"].widget.attrs.setdefault("placeholder", _("Напр., ул. Низами 10, Баку"))
        self.fields["phone"].widget.attrs.setdefault("placeholder", _("Напр., +994 50 123 45 67"))
        self.fields["instagram"].widget.attrs.setdefault("placeholder", _("Напр., @kidsmap"))
        self.fields["website"].widget.attrs.setdefault("placeholder", _("Напр., https://example.com"))
        self.fields["lat"].widget.attrs.setdefault("placeholder", _("Напр., 40.409264"))
        self.fields["lng"].widget.attrs.setdefault("placeholder", _("Напр., 49.867092"))


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
        queryset = model_admin.get_queryset(request)
        user_ids = (
            queryset
            .exclude(created_by_id__isnull=True)
            .order_by()
            .values_list("created_by_id", flat=True)
            .distinct()
        )
        users = get_user_model().objects.filter(pk__in=user_ids).order_by("username", "email")
        lookups = [(str(user.pk), model_admin._user_label(user)) for user in users]
        if queryset.filter(created_by_id__isnull=True).exists():
            lookups.append(("__unknown__", _("Не указан — старые карточки")))
        return tuple(lookups)

    def queryset(self, request, queryset):
        value = self.value()
        if value == "__unknown__":
            return queryset.filter(created_by_id__isnull=True)
        if value and value.isdigit():
            return queryset.filter(created_by_id=int(value))
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


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventAdminForm
    inlines = [EventPhotoInline]
    actions = ("mark_published", "mark_draft", "mark_pending", "mark_rejected")
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
    list_filter = (EventDeletedFilter, "status", "category", "start_datetime", "owner")
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
            "title": _("Служебное"),
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
                    ("region", "district", "metro"),
                    "address",
                    ("lat", "lng"),
                    ("phone", "instagram"),
                    "website",
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
                    ("region", "district", "metro"),
                    "address",
                    ("lat", "lng"),
                    ("phone", "instagram"),
                    "website",
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
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        adminform = context.get("adminform")
        if adminform is not None:
            inline_admin_formsets = context.get("inline_admin_formsets", [])
            context["km_event_gallery_inline"] = next(
                (
                    inline_admin_formset
                    for inline_admin_formset in inline_admin_formsets
                    if inline_admin_formset.opts.model is EventPhoto
                ),
                None,
            )
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
        if field_name == "name":
            return (
                self._field_has_value(form, "name_az", obj=obj)
                or self._field_has_value(form, "name_ru", obj=obj)
                or self._field_has_value(form, "name_en", obj=obj)
                or bool(form.is_bound and form.data.get(form.add_prefix("name")))
                or bool(form.initial.get("name"))
                or bool(obj and getattr(obj, "name", None))
            )

        if field_name in form.files and form.files.get(field_name):
            return True

        if form.is_bound:
            if hasattr(form, "cleaned_data") and field_name in form.cleaned_data:
                raw_value = form.cleaned_data.get(field_name)
            else:
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
            is_open_ended_age = field_name == "age_to" and self._field_has_value(form, "age_open_ended", obj=obj)
            if is_open_ended_age or self._field_has_value(form, field_name, obj=obj):
                completed += 1
            else:
                field_id = "id_name_az" if field_name == "name" else f"id_{field_name}"
                missing.append({
                    "label": str(label),
                    "field_id": field_id
                })
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
                    "input_id": "id_name_az" if field_name == "name" else f"id_{field_name}",
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
            total=Count("id", filter=Q(deleted_at__isnull=True)),
            published=Count("id", filter=Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__gt=timezone.now()) | Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__isnull=True)),
            pending=Count("id", filter=Q(status=Event.STATUS_PENDING, deleted_at__isnull=True)),
            expired=Count("id", filter=Q(deleted_at__isnull=True) & (Q(status=Event.STATUS_EXPIRED) | Q(end_datetime__lte=timezone.now()))),
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

    @admin.action(description=_("Отклонить выбранные мероприятия"))
    def mark_rejected(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_REJECTED,
            rejection_reason=_("Мероприятие требует доработки перед публикацией."),
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("Отклонено %(count)d мероприятие.", "Отклонено %(count)d мероприятия.", updated_count)
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
        "age_open_ended",
        "offers_adult_classes",
        "district",
        "metro",
        "address",
        "phone1",
        "phone2",
        "phone3",
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
        "is_home_recommended",
        "home_recommended_order",
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
    km_primary_filters = ("category", "district", "status", "created_by")
    delete_selected_confirmation_template = "admin/catalog/place_delete_selected_confirmation.html"
    list_select_related = ("owner", "created_by", "category", "subcategory")
    list_display = (
        "display_name",
        "category_summary",
        "location_summary",
        "publication_status",
        "home_recommendation_status",
        "map_status_summary",
        "owner_display",
        "engagement_summary",
        "updated_summary",
        "row_actions",
    )
    trash_list_display = (
        "display_name",
        "deleted_at_display",
        "deleted_by_display",
        "updated_at",
        "row_actions",
    )
    list_filter = (
        PlaceDeletedFilter,
        PlaceCoordinatesFilter,
        PlaceMapReadyFilter,
        PlaceCreatedByFilter,
        "category",
        "is_temporary",
        "district",
        "metro",
        "owner",
        "is_active",
        "is_home_recommended",
        "is_verified",
        "status",
        "age_from",
        "age_to",
        "offers_adult_classes",
    )
    search_fields = (
        "name_az",
        "name_ru",
        "name_en",
        "name",
        "slug",
        "address",
        "instagram",
        "phone1",
        "phone2",
        "phone3",
        "owner__username",
        "owner__email",
    )
    search_help_text = _("Ищет по названию места на AZ, RU или EN. Можно также искать по адресу, телефону или владельцу.")
    readonly_fields = (
        "slug",
        "likes_count",
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
            "description": _("Сначала название и описание карточки, затем категория и подкатегория."),
            "fieldset_indexes": (1, 0),
        },
        {
            "id": "pricing",
            "step": "02",
            "title": _("Цена и возраст"),
            "description": _("Возрастные рамки, стоимость и длительность занятий."),
            "fieldset_indexes": (2,),
        },
        {
            "id": "location",
            "step": "03",
            "title": _("Локация"),
            "description": _("Район, метро, адрес, координаты и контакты для связи."),
            "fieldset_indexes": (3, 4),
        },
        {
            "id": "media",
            "step": "04",
            "title": _("Фото"),
            "description": _("Добавьте главное изображение и дополнительные фотографии места."),
            "fieldset_indexes": (5,),
        },
    )

    PLACE_FORM_SECONDARY_SECTIONS = (
        {
            "id": "system",
            "title": _("Служебное"),
            "description": _("Служебные и административные поля, которые не нужны в основном сценарии заполнения."),
            "fieldset_indexes": (7, 8),
        },
    )

    ADD_FIELDSETS = (
        (
            _("Основное"),
            {
                "fields": (
                    ("category", "subcategory"),
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
            _("Цена и возраст"),
            {
                "fields": (
                ("age_from", "age_to", "age_open_ended", "lesson_duration_minutes"),
                    "offers_adult_classes",
                    "pricing_plans",
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
                    ("phone1", "phone2", "phone3"),
                    ("instagram", "website"),
                    "schedule",
                    ("extra_conditions_az", "extra_conditions_ru", "extra_conditions_en"),
                    ("additional_info_az", "additional_info_ru", "additional_info_en"),
                )
            },
        ),
        (_("Фотографии"), {"fields": ("photo",)}),
        (
            _("Управление карточкой"),
            {
                "fields": (
                    "is_active",
                    "is_verified",
                    ("is_home_recommended", "home_recommended_order"),
                    "status",
                    "rejection_reason",
                    "owner",
                ),
            },
        ),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cover_photo",
                    "last_verified_at_display",
                    "published_at_display",
                    "lifecycle_status_display",
                    "quality_status_display",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        context["km_place_draft_save_failed"] = "_save_draft" in request.POST and bool(context.get("errors"))
        fallback_url = reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
            current_app=self.admin_site.name,
        )
        referer = request.META.get("HTTP_REFERER", "")
        if referer and url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            referer_path = referer.split("?", 1)[0].split("#", 1)[0]
            if referer_path != request.path:
                context["km_admin_back_url"] = referer
            else:
                context["km_admin_back_url"] = fallback_url
        else:
            context["km_admin_back_url"] = fallback_url
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
            context["km_place_form_errors"] = self._build_place_form_errors(
                adminform.form,
                inline_admin_formsets=inline_admin_formsets,
            )
            context["km_place_taxonomy_picker"] = self._build_taxonomy_picker_config(adminform.form)
            context["km_place_map_alert"] = self._build_place_map_alert(
                form=adminform.form,
                obj=obj,
                has_google_maps_api_key=bool(context["google_maps_api_key"]),
            )
            context["km_place_public_link"] = self._build_public_place_link(request, obj=obj)
            context["km_place_duplicates_url"] = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_duplicate_candidates"
            )
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def add_view(self, request, form_url='', extra_context=None):
        if not request.GET.get("type"):
            from django.shortcuts import redirect
            return redirect("admin_add_choice")
        return super().add_view(request, form_url=form_url, extra_context=extra_context)


    def _fieldset_list(self, adminform):
        return list(adminform) if adminform is not None else []

    def _build_place_form_errors(self, form, *, inline_admin_formsets=()):
        """Return actionable errors with anchors to the matching form section."""
        section_by_field = {
            "category": "#basics",
            "subcategory": "#basics",
            "name": "#basics",
            "name_az": "#basics",
            "name_ru": "#basics",
            "name_en": "#basics",
            "description_az": "#basics",
            "description_ru": "#basics",
            "description_en": "#basics",
            "age_from": "#pricing",
            "age_to": "#pricing",
            "offers_adult_classes": "#pricing",
            "price_from": "#pricing",
            "price_to": "#pricing",
            "pricing_plans": "#pricing",
            "district": "#location",
            "metro": "#location",
            "address": "#location",
            "phone1": "#location",
            "structured_schedule": "#admin-place-schedule",
            "photo": "#media",
        }
        errors = []

        for weekday, messages_for_day in getattr(form, "schedule_editor_errors", {}).items():
            day_label = FULL_DAY_LABELS.get(weekday, weekday)
            for message in messages_for_day:
                errors.append(
                    {
                        "label": str(_("Расписание: %(day)s") % {"day": day_label}),
                        "message": str(message),
                        "target": f"#admin-place-schedule-row-{weekday}",
                    }
                )

        for field_name, messages_for_field in form.errors.items():
            if field_name == "structured_schedule" and getattr(form, "schedule_editor_errors", None):
                # The detailed day errors above are more useful than the generic field error.
                continue
            if field_name == "__all__":
                label = str(_("Карточка"))
                target = "#verification"
            else:
                field = form.fields.get(field_name)
                label = str(field.label) if field is not None else field_name
                target = section_by_field.get(field_name, f"#id_{field_name}")
            for message in messages_for_field:
                errors.append({"label": label, "message": str(message), "target": target})

        # Django puts inline-form errors (for example, gallery photos) into the
        # top-level ``errors`` object, not into the main form. Surface them here
        # as actionable messages instead of showing the vague fallback alert.
        for inline_admin_formset in inline_admin_formsets:
            formset = inline_admin_formset.formset
            inline_label = str(inline_admin_formset.opts.verbose_name)
            target = "#media" if inline_admin_formset.opts.model.__name__ == "PlacePhoto" else "#verification"
            for message in formset.non_form_errors():
                errors.append({"label": inline_label, "message": str(message), "target": target})
            for inline_form in formset.forms:
                for field_name, messages_for_field in inline_form.errors.items():
                    field = inline_form.fields.get(field_name)
                    label = str(field.label) if field is not None else inline_label
                    for message in messages_for_field:
                        errors.append({"label": label, "message": str(message), "target": target})

        return errors

    def _build_taxonomy_picker_config(self, form):
        category_field = form.fields.get("category")
        subcategory_field = form.fields.get("subcategory")
        if category_field is None or subcategory_field is None:
            return {"categories": [], "subcategories": []}

        categories = []
        category_queryset = category_field.queryset.order_by("order", "name_ru", "name")
        subcategory_counts = {
            item["category_id"]: item["total"]
            for item in Subcategory.objects.filter(category__in=category_queryset)
            .values("category_id")
            .annotate(total=Count("pk"))
        }
        for category in category_queryset:
            categories.append(
                {
                    "code": category.pk,
                    "label": str(category.name_i18n()),
                    "icon": category.icon_file_url,
                    "icon_class": category.icon_name if category.icon_is_font_class else "",
                    "color_bg": category.resolved_color_bg,
                    "color_text": category.resolved_color_text,
                    "subcategory_count": int(subcategory_counts.get(category.pk, 0) or 0),
                }
            )

        subcategories = []
        for subcategory in subcategory_field.queryset.order_by("category__order", "order", "name_ru", "name"):
            subcategories.append(
                {
                    "id": str(subcategory.pk),
                    "code": subcategory.code or "",
                    "category": subcategory.category_id,
                    "label": str(subcategory.name_i18n()),
                }
            )

        return {
            "categories": categories,
            "subcategories": subcategories,
        }

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
        quality = place_quality_check(obj)
        if obj.status == obj.STATUS_PUBLISHED and obj.is_active and not quality.is_ready:
            reasons = place_quality_error_labels(quality.errors)
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "danger",
                "hint": str(_("Карточка имеет статус публикации, но не проходит проверку качества каталога: %(reasons)s.") % {"reasons": reasons}),
                "is_public": False,
            }
        if obj.is_public:
            return {
                "label": str(_("Опубликовано")),
                "tone": "good",
                "hint": str(_("Карточка видна на сайте при текущих правилах качества каталога.")),
                "is_public": True,
            }
        if obj.status == obj.STATUS_PUBLISHED and not obj.is_active:
            return {
                "label": str(_("Снято с публикации")),
                "tone": "warn",
                "hint": str(_("Карточка была выведена из публичного каталога и сейчас не видна пользователям.")),
                "is_public": False,
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
            is_open_ended_age = field_name == "age_to" and self._field_has_value(
                form, "age_open_ended", obj=obj
            )
            if is_open_ended_age or self._field_has_value(form, field_name, obj=obj):
                completed += 1
            else:
                field_id = "id_name_az" if field_name == "name" else f"id_{field_name}"
                missing.append({
                    "label": str(label),
                    "field_id": field_id
                })
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
                    "label": (
                        str(_("Статус: %(status)s") % {"status": dict(obj.STATUS_CHOICES).get(obj.status, obj.status)})
                        if obj.status == obj.STATUS_PUBLISHED and not visibility["is_public"]
                        else str(dict(obj.STATUS_CHOICES).get(obj.status, obj.status))
                    ),
                    "tone": "good" if obj.status == obj.STATUS_PUBLISHED and visibility["is_public"] else "muted",
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
            if not visibility["is_public"]:
                meta_items.append(
                    {
                        "label": str(_("Почему скрыто")),
                        "value": visibility["hint"],
                    }
                )
            if obj.published_at:
                meta_items.append(
                    {
                        "label": str(_("Опубликовано")),
                        "value": timezone.localtime(obj.published_at).strftime("%d.%m.%Y %H:%M"),
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
                    "input_id": "id_name_az" if field_name == "name" else f"id_{field_name}",
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
        "mark_home_recommended",
        "unmark_home_recommended",
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
                    ("category", "subcategory"),
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
            _("Цена и возраст"),
            {
                "fields": (
                ("age_from", "age_to", "age_open_ended", "lesson_duration_minutes"),
                    "offers_adult_classes",
                    "pricing_plans",
                )
            },
        ),
        (_("Локация"), {"fields": (("district", "metro"), "address", ("lat", "lng"), ("coordinates_status_display", "map_ready_status_display"))}),
        (
            _("Контакты"),
            {
                "fields": (
                    ("phone1", "phone2", "phone3"),
                    ("instagram", "website"),
                    "schedule",
                    "extra_conditions",
                    "additional_info",
                )
            },
        ),
        (_("Фотографии"), {"fields": ("photo",)}),
        (
            _("Управление карточкой"),
            {
                "fields": (
                    "is_active",
                    "is_verified",
                    ("is_home_recommended", "home_recommended_order"),
                    "status",
                    "rejection_reason",
                    "owner",
                ),
            },
        ),
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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            Prefetch(
                "ownership_requests",
                queryset=PlaceOwnershipRequest.objects.select_related("applicant").order_by("created_at"),
                to_attr="km_prefetched_ownership_requests",
            ),
            Prefetch(
                "change_audits",
                queryset=PlaceChangeAudit.objects.select_related("changed_by").order_by("-created_at"),
                to_attr="km_prefetched_change_audits",
            ),
        )

    def _is_trash_changelist(self, request) -> bool:
        return request.GET.get("deleted_state") == "deleted"

    def get_list_display(self, request):
        if self._is_trash_changelist(request):
            return self.trash_list_display
        return super().get_list_display(request)

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        if obj is None:
            return [inline for inline in inline_instances if isinstance(inline, PlacePhotoInline)]
        return inline_instances

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_az or obj.name_ru or obj.name_en or obj.name
        meta: list[str] = [f"ID {obj.pk}"]
        if obj.is_deleted:
            meta.append(str(_("В удаленных")))
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
        visibility = self._place_visibility_state(obj)
        if obj.status == obj.STATUS_PUBLISHED and obj.is_active:
            return self._render_place_state_badge(label=visibility["label"], tone=visibility["tone"])
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
        details = place_quality_error_labels(check.errors[:4]) if check.errors else _("Критичных замечаний нет")
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

    def _user_label(self, user) -> str:
        if not user:
            return ""
        return user.get_full_name() or user.get_username() or user.email or str(user.pk)

    def _latest_place_audit(self, obj):
        audits = getattr(obj, "km_prefetched_change_audits", None)
        if audits is not None:
            return audits[0] if audits else None
        return obj.change_audits.select_related("changed_by").order_by("-created_at").first()

    def _first_ownership_request(self, obj):
        requests = getattr(obj, "km_prefetched_ownership_requests", None)
        if requests is not None:
            return requests[0] if requests else None
        return obj.ownership_requests.select_related("applicant").order_by("created_at").first()

    @admin.display(description=_("Категория"))
    def category_summary(self, obj):
        category = obj.category
        label = category.name_i18n() if category else obj.get_category_display()
        icon = (getattr(category, "icon", "") or "").strip() if category else ""
        if icon:
            icon_src = icon if icon.startswith(("http://", "https://", "/")) else f"{settings.STATIC_URL}{icon}"
            icon_html = format_html('<img src="{}" alt="" class="km-admin-category-icon" loading="lazy">', icon_src)
        else:
            icon_html = mark_safe('<span class="km-admin-category-icon km-admin-category-icon--fallback" aria-hidden="true">#</span>')
        subcategory = obj.subcategory.name_i18n() if getattr(obj, "subcategory_id", None) and obj.subcategory else ""
        return format_html(
            '<div class="km-admin-category-cell">{}<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div></div>',
            icon_html,
            label,
            format_html('<span class="km-admin-meta">{}</span>', subcategory) if subcategory else "",
        )

    @admin.display(description=_("Локация"))
    def location_summary(self, obj):
        address = (obj.address or "").strip()
        if address:
            return format_html(
                '<span class="km-admin-address" title="{}">{}</span>',
                address,
                address,
            )
        fallback = " / ".join(part for part in (obj.district, obj.metro) if part)
        if fallback:
            return format_html('<span class="km-admin-address km-admin-address--muted">{}</span>', fallback)
        return format_html(
            '<span class="km-admin-address km-admin-address--empty">{}</span>',
            _("Адрес не заполнен"),
        )

    @admin.display(description=_("Публикация"))
    def publication_status(self, obj):
        visibility = self._place_visibility_state(obj)
        badges = [
            self._render_place_state_badge(label=visibility["label"], tone=visibility["tone"]),
        ]

        if obj.status != obj.STATUS_PUBLISHED or not visibility["is_public"]:
            status_tone = {
                obj.STATUS_DRAFT: "muted",
                obj.STATUS_PENDING: "warn",
                obj.STATUS_PUBLISHED: "muted",
                obj.STATUS_REJECTED: "danger",
            }.get(obj.status, "muted")
            status_label = (
                _("Статус: %(status)s") % {"status": obj.get_status_display()}
                if obj.status == obj.STATUS_PUBLISHED and not visibility["is_public"]
                else obj.get_status_display()
            )
            badges.append(self._render_place_state_badge(label=status_label, tone=status_tone))

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
            '<div class="km-admin-status-line">{}</div>{}',
            badges_html,
            format_html(
                '<span class="km-admin-meta km-admin-status-note">{}</span>',
                " · ".join(meta_bits),
            ) if meta_bits else "",
        )

    @admin.display(boolean=True, description=_("На главной"))
    def home_recommendation_status(self, obj):
        return obj.is_home_recommended

    @admin.display(description=_("Карта"))
    def map_status_summary(self, obj):
        visibility = self._place_visibility_state(obj)
        if visibility["is_public"] and obj.has_coordinates:
            label = _("Готово для карты")
            return format_html('<span class="km-admin-map-state km-admin-map-state--good" title="{}" aria-label="{}"><i class="fas fa-check"></i></span>', label, label)
        if not visibility["is_public"]:
            label = _("Скрыто с сайта")
        else:
            label = _("Нужны координаты") if not obj.has_coordinates else _("Не готово для карты")
        return format_html('<span class="km-admin-map-state km-admin-map-state--bad" title="{}" aria-label="{}"><i class="fas fa-times"></i></span>', label, label)

    @admin.display(description=_("Добавил"))
    def owner_display(self, obj):
        if obj.created_by_id:
            return format_html(
                '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
                self._user_label(obj.created_by),
                _("сотрудник"),
            )
        audit = self._latest_place_audit(obj)
        if audit and audit.changed_by_id:
            return format_html(
                '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
                self._user_label(audit.changed_by),
                audit.get_source_display(),
            )
        return format_html('<span class="km-admin-meta">{}</span>', _("Не указан"))

    @admin.display(description=_("Статистика"))
    def engagement_summary(self, obj):
        likes_value = int(obj.likes_count or 0)
        rating_value = f"{float(obj.rating_avg or 0):.1f}"
        reviews_value = int(obj.rating_count or 0)
        return format_html(
            '<div class="km-admin-stats" aria-label="{}">'
            '<span title="{}"><i class="far fa-comment-dots"></i>{}</span>'
            '<span title="{}"><i class="fas fa-star"></i>{}</span>'
            '<span title="{}"><i class="far fa-heart"></i>{}</span>'
            "</div>",
            _("Статистика карточки"),
            _("Отзывы"),
            reviews_value,
            _("Средний рейтинг"),
            rating_value,
            _("Лайки"),
            likes_value,
        )

    @admin.display(description=_("Обновлено"), ordering="updated_at")
    def updated_summary(self, obj):
        audit = self._latest_place_audit(obj)
        if audit:
            actor = self._user_label(audit.changed_by) or _("Система")
            source = audit.get_source_display()
            dt = timezone.localtime(audit.created_at)
            return format_html(
                '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{} · {}</span></div>',
                dt.strftime("%d.%m.%Y %H:%M"),
                actor,
                source,
            )
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
            timezone.localtime(obj.updated_at).strftime("%d.%m.%Y %H:%M"),
            _("без истории изменений"),
        )

    @admin.display(description=_("Удалено"))
    def deleted_at_display(self, obj):
        if not obj.deleted_at:
            return format_html('<span class="km-admin-meta">{}</span>', _("Нет данных"))
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
            timezone.localtime(obj.deleted_at).strftime("%d.%m.%Y"),
            timezone.localtime(obj.deleted_at).strftime("%H:%M"),
        )

    @admin.display(description=_("Удалил"))
    def deleted_by_display(self, obj):
        if not obj.deleted_by:
            return format_html('<span class="km-admin-meta">{}</span>', _("Не указано"))
        label = obj.deleted_by.get_username() or obj.deleted_by.email or str(obj.deleted_by_id)
        return format_html('<span class="km-admin-title">{}</span>', label)

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
                    status__exact=Place.STATUS_PUBLISHED,
                ),
                "active": current_deleted == "active" and current_active == "1" and current_status == Place.STATUS_PUBLISHED and not current_coordinates and not current_map_ready,
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
            quick_all=Count("pk", filter=Q(deleted_at__isnull=True)),
            quick_published=Count("pk", filter=Q(deleted_at__isnull=True, is_active=True, status=Place.STATUS_PUBLISHED)),
            quick_inactive=Count("pk", filter=Q(deleted_at__isnull=True, is_active=False)),
            quick_draft=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_DRAFT)),
            quick_pending=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_PENDING)),
            quick_rejected=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_REJECTED)),
            quick_deleted=Count("pk", filter=Q(deleted_at__isnull=False)),
            quick_without_coordinates=Count("pk", filter=Q(deleted_at__isnull=True) & (Q(lat__isnull=True) | Q(lng__isnull=True))),
            quick_not_ready_for_map=Count(
                "pk",
                filter=Q(deleted_at__isnull=True) & (~Q(is_active=True, status=Place.STATUS_PUBLISHED) | Q(lat__isnull=True) | Q(lng__isnull=True)),
            ),
            stat_total=Count("pk", filter=Q(deleted_at__isnull=True)),
            stat_published=Count("pk", filter=Q(deleted_at__isnull=True, is_active=True, status=Place.STATUS_PUBLISHED)),
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
                "url": self._build_changelist_query_string(request, clear=("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", is_active__exact="1", status__exact=Place.STATUS_PUBLISHED),
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
                "icon": "fas fa-bullhorn",
                "description": _("Опубликовать выбранные карточки с проверкой качества."),
            },
            {
                "name": "mark_inactive",
                "label": _("Снять с публикации"),
                "tone": "muted",
                "icon": "fas fa-eye-slash",
                "description": _("Оставить карточки в базе, но скрыть их с сайта."),
            },
            {
                "name": "mark_draft",
                "label": _("Вернуть в черновик"),
                "tone": "muted",
                "icon": "far fa-file-alt",
                "description": _("Снять выбранные карточки с сайта и перевести в черновики."),
            },
            {
                "name": "mark_pending",
                "label": _("На модерацию"),
                "tone": "warn",
                "icon": "fas fa-hourglass-half",
                "description": _("Отправить выбранные карточки на повторную модерацию."),
            },
            {
                "name": "refresh_coordinates",
                "label": _("Обновить координаты"),
                "tone": "info",
                "icon": "fas fa-location-arrow",
                "description": _("Повторно рассчитать координаты по адресу."),
            },
            {
                "name": "restore_selected",
                "label": _("Восстановить"),
                "tone": "good",
                "icon": "fas fa-undo",
                "confirm": _("Вы собираетесь восстановить {count} выбранных карточек из удалённых.\n\nПосле восстановления карточки останутся неактивными, их можно будет отдельно опубликовать.\n\nПродолжить?"),
                "description": _("Вернуть карточки из удалённых в базовый список."),
            },
            {
                "name": "move_selected_to_deleted",
                "label": _("В удалённые"),
                "tone": "danger",
                "icon": "far fa-trash-alt",
                "confirm": _("Вы собираетесь переместить в удалённые {count} выбранных карточек.\n\nКарточки исчезнут с сайта, но останутся в базе и их можно будет восстановить.\n\nПродолжить?"),
                "description": _("Безопасное мягкое удаление с возможностью восстановления."),
            },
        )

    def _place_trash_bulk_actions(self):
        return (
            {
                "name": "restore_selected",
                "label": _("Восстановить"),
                "tone": "good",
                "icon": "fas fa-undo",
                "confirm": _("Вы собираетесь восстановить {count} выбранных карточек из удалённых.\n\nПосле восстановления карточки останутся неактивными, их можно будет отдельно опубликовать.\n\nПродолжить?"),
                "description": _("Вернуть карточки из удалённых в базовый список."),
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
            path("pricing/import/validate/", self.admin_site.admin_view(self.validate_pricing_import_view), name="catalog_place_pricing_import_validate"),
            path("<int:object_id>/export-json/", self.admin_site.admin_view(self.export_place_json_view), name="catalog_place_export_json"),
            path(
                "duplicate-candidates/",
                self.admin_site.admin_view(self.duplicate_candidates_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_duplicate_candidates",
            ),
            path(
                "home-recommendations/candidates/",
                self.admin_site.admin_view(self.home_recommendation_candidates_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_home_recommendation_candidates",
            ),
            path(
                "home-recommendations/save/",
                self.admin_site.admin_view(self.save_home_recommendations_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_home_recommendations_save",
            ),
            path(
                "search-suggestions/",
                self.admin_site.admin_view(self.search_suggestions_view),
                name="catalog_place_search_suggestions",
            ),
            path(
                "<int:object_id>/toggle-publication/",
                self.admin_site.admin_view(self.toggle_publication_view),
                name="catalog_place_toggle_publication",
            ),
            path(
                "<path:object_id>/restore/",
                self.admin_site.admin_view(self.restore_view),
                name="catalog_place_restore",
            ),
        ]
        return custom_urls + super().get_urls()

    def validate_pricing_import_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": str(_("Разрешён только POST."))}, status=405)
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": str(_("Некорректный JSON."))}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({"ok": False, "error": str(_("Нужен один объект карточки."))}, status=400)
        warnings = []
        raw_plans = payload.get("pricing_plans")
        if raw_plans is None:
            raw_plans = payload.get("tariffs")
        if raw_plans is None:
            raw_plans = []
            legacy_specs = (
                ("price_per_lesson", {"product_type": "lesson", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "lesson"}),
                ("price_per_month", {"product_type": "membership", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1}),
                ("price_per_8_lessons", {"product_type": "lesson", "billing_mode": "one_time", "quantity": 8, "quantity_unit": "lesson"}),
            )
            for key, base in legacy_specs:
                if payload.get(key) is not None:
                    amount = payload[key]
                    raw_plans.append({**base, "price_kind": "free" if str(amount) in {"0", "0.0", "0.00"} else "exact", "price": amount})
            if payload.get("price_from") is not None or payload.get("price_to") is not None:
                warnings.append(str(_("price_from/price_to не создают тариф: неизвестен продаваемый продукт.")))
        try:
            plans = normalize_pricing_plans(raw_plans, allow_verified=request.user.is_staff)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "error": exc.messages[0]}, status=400)
        return JsonResponse({"ok": True, "pricing_plans": plans, "warnings": warnings})

    def export_place_json_view(self, request, object_id):
        obj = Place.objects.filter(pk=object_id).first()
        if obj is None or not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        from catalog.services.pricing_plans import serialize_pricing_plans
        payload = {
            "name_az": obj.name_az, "name_ru": obj.name_ru, "name_en": obj.name_en,
            "description_az": obj.description_az, "description_ru": obj.description_ru, "description_en": obj.description_en,
            "category": obj.category_id, "subcategory": obj.subcategory_id,
            "age_from": obj.age_from, "age_to": obj.age_to, "address": obj.address,
            "district": obj.district, "metro": obj.metro, "phone1": obj.phone1,
            "instagram": obj.instagram, "website": obj.website,
            "pricing_plans": serialize_pricing_plans(obj.pricing_plan_records.all()),
        }
        response = HttpResponse(json.dumps(payload, ensure_ascii=False, indent=2, default=str), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="place-{obj.pk}.json"'
        return response

    def duplicate_candidates_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied

        values = {
            "phone": _normalized_phone(request.GET.get("phone")),
            "website": _normalized_url(request.GET.get("website")),
            "instagram": _normalized_text((request.GET.get("instagram") or "").lstrip("@")),
            "address": _normalized_text(request.GET.get("address")),
        }
        object_id = request.GET.get("exclude")
        if not any(values.values()):
            return JsonResponse({"results": []})

        queryset = Place.objects.filter(deleted_at__isnull=True).only(
            "id", "name", "name_az", "name_ru", "name_en", "address", "phone1", "phone2", "phone3", "website", "instagram"
        )
        if object_id and object_id.isdigit():
            queryset = queryset.exclude(pk=int(object_id))

        results = []
        for place in queryset.iterator():
            matched = []
            if values["phone"] and values["phone"] in {
                _normalized_phone(place.phone1),
                _normalized_phone(place.phone2),
                _normalized_phone(place.phone3),
            }:
                matched.append(str(_("телефон")))
            if values["website"] and values["website"] == _normalized_url(place.website):
                matched.append(str(_("сайт")))
            if values["instagram"] and values["instagram"] == _normalized_text((place.instagram or "").lstrip("@")):
                matched.append("Instagram")
            if values["address"] and values["address"] == _normalized_text(place.address):
                matched.append(str(_("адрес")))
            if matched:
                results.append(
                    {
                        "id": place.pk,
                        "title": place.name_i18n(getattr(request, "LANGUAGE_CODE", None)) or place.name,
                        "address": place.address,
                        "matched": matched,
                        "url": reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_change", args=[place.pk]),
                    }
                )
        return JsonResponse({"results": results[:8]})

    def _home_recommendation_queryset(self):
        return public_place_queryset(
            Place.objects.select_related("category", "subcategory")
        )

    def _serialize_home_recommendation(self, place, *, language_code=None):
        image_url = ""
        image_field = place.photo or place.cover_photo
        if image_field and getattr(image_field, "name", ""):
            try:
                image_url = image_field.url
            except Exception:
                image_url = ""

        location = place.district_i18n(language_code)
        if place.metro:
            metro_label = place.metro_i18n(language_code)
            location = " · ".join(part for part in (location, metro_label) if part)

        return {
            "id": place.pk,
            "title": place.name_i18n(language_code) or place.name,
            "category": place.get_category_display(),
            "location": location,
            "image_url": image_url,
            "change_url": reverse("admin:catalog_place_change", args=[place.pk]),
        }

    def home_recommendation_candidates_view(self, request):
        if request.method != "GET" or not self.has_change_permission(request):
            raise PermissionDenied

        term = (request.GET.get("q") or "").strip()
        queryset = self._home_recommendation_queryset()
        if term:
            queryset = queryset.filter(
                Q(name__icontains=term)
                | Q(name_az__icontains=term)
                | Q(name_ru__icontains=term)
                | Q(name_en__icontains=term)
                | Q(district__icontains=term)
                | Q(address__icontains=term)
            )
        queryset = queryset.order_by("-is_home_recommended", "home_recommended_order", "-updated_at")[:24]
        language_code = getattr(request, "LANGUAGE_CODE", None)
        return JsonResponse(
            {
                "results": [
                    self._serialize_home_recommendation(place, language_code=language_code)
                    for place in queryset
                ]
            }
        )

    def save_home_recommendations_view(self, request):
        if request.method != "POST" or not self.has_change_permission(request):
            raise PermissionDenied

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "error": str(_("Некорректные данные."))}, status=400)

        raw_ids = payload.get("place_ids")
        if not isinstance(raw_ids, list):
            return JsonResponse({"ok": False, "error": str(_("Передайте список мест."))}, status=400)

        try:
            place_ids = [int(value) for value in raw_ids]
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": str(_("Некорректный идентификатор места."))}, status=400)

        if len(place_ids) != len(set(place_ids)):
            return JsonResponse({"ok": False, "error": str(_("Одно место нельзя добавить дважды."))}, status=400)
        if len(place_ids) > 4:
            return JsonResponse({"ok": False, "error": str(_("На главной можно показать максимум четыре места."))}, status=400)

        available_places = {
            place.pk: place
            for place in self._home_recommendation_queryset().filter(pk__in=place_ids)
        }
        if len(available_places) != len(place_ids):
            return JsonResponse(
                {"ok": False, "error": str(_("Одно из мест недоступно для публикации. Обновите список."))},
                status=400,
            )

        now = timezone.now()
        with transaction.atomic():
            Place.objects.filter(is_home_recommended=True).exclude(pk__in=place_ids).update(
                is_home_recommended=False,
                updated_at=now,
            )
            for index, place_id in enumerate(place_ids, start=1):
                Place.objects.filter(pk=place_id).update(
                    is_home_recommended=True,
                    home_recommended_order=index * 10,
                    updated_at=now,
                )

        language_code = getattr(request, "LANGUAGE_CODE", None)
        return JsonResponse(
            {
                "ok": True,
                "results": [
                    self._serialize_home_recommendation(
                        available_places[place_id],
                        language_code=language_code,
                    )
                    for place_id in place_ids
                ],
            }
        )

    def toggle_publication_view(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied

        if not self.has_change_permission(request):
            raise PermissionDenied
        place = Place.objects.filter(pk=object_id, deleted_at__isnull=True).first()
        if place is None:
            raise PermissionDenied

        if place.status == Place.STATUS_PUBLISHED and place.is_active:
            place.status = Place.STATUS_DRAFT
            place.is_active = False
            place.save(update_fields=["status", "is_active", "updated_at"])
            self.message_user(request, _("Карточка снята с публикации и скрыта с сайта."), messages.SUCCESS)
        else:
            quality = place_quality_check(place)
            if not quality.is_ready:
                self.message_user(
                    request,
                    _("Карточка не опубликована: сначала заполните обязательные поля и фото."),
                    messages.WARNING,
                )
            else:
                place.status = Place.STATUS_PUBLISHED
                place.is_active = True
                place.rejection_reason = ""
                update_fields = ["status", "is_active", "rejection_reason", "updated_at"]
                if place.published_at is None:
                    place.published_at = timezone.now()
                    update_fields.append("published_at")
                place.save(update_fields=update_fields)
                self.message_user(request, _("Карточка опубликована и теперь может показываться на сайте."), messages.SUCCESS)

        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))

    def search_suggestions_view(self, request):
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        # Suggestions must not inherit changelist-only filters or annotations
        # from ModelAdmin.get_queryset(); search the canonical active table.
        queryset = Place.objects.filter(deleted_at__isnull=True).filter(
            Q(name__icontains=term)
            | Q(name_az__icontains=term)
            | Q(name_ru__icontains=term)
            | Q(name_en__icontains=term)
            | Q(slug__icontains=term)
            | Q(address__icontains=term)
            | Q(phone1__icontains=term)
            | Q(phone2__icontains=term)
            | Q(phone3__icontains=term)
            | Q(owner__username__icontains=term)
            | Q(owner__email__icontains=term)
        )
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
        is_trash = self._is_trash_changelist(request)
        primary_filter_keys = {"all", "published", "draft", "pending", "inactive", "without_coordinates", "deleted"}
        if is_trash:
            primary_filter_keys = {"all", "deleted"}
        extra_context = {
            "place_dashboard_stats": self._place_dashboard_stats(request, counts=dashboard_counts),
            "km_primary_quick_filters": [item for item in quick_filters if item.get("key") in primary_filter_keys],
            "km_secondary_quick_filters": [item for item in quick_filters if item.get("key") not in primary_filter_keys],
            "place_bulk_actions": self._place_trash_bulk_actions() if is_trash else self._place_bulk_actions(),
            "km_is_trash_changelist": is_trash,
            "km_changelist_reset_url": "?deleted_state=deleted" if is_trash else "?",
            "home_recommendation_editor": (
                {
                    "cards": [
                        self._serialize_home_recommendation(
                            place,
                            language_code=getattr(request, "LANGUAGE_CODE", None),
                        )
                        for place in self._home_recommendation_queryset()
                        .filter(is_home_recommended=True)
                        .order_by("home_recommended_order", "-updated_at")[:4]
                    ],
                    "save_url": reverse("admin:catalog_place_home_recommendations_save"),
                    "candidates_url": reverse("admin:catalog_place_home_recommendation_candidates"),
                    "max_items": 4,
                }
                if not is_trash and self.has_change_permission(request)
                else None
            ),
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
        updated_count = queryset.update(
            is_active=False,
            status=Place.STATUS_DRAFT,
            updated_at=timezone.now(),
        )
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

    @admin.action(description=_("Добавить в рекомендации на главной"))
    def mark_home_recommended(self, request, queryset):
        updated_count = queryset.update(
            is_home_recommended=True,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d карточка добавлена в рекомендации.",
                "%(count)d карточки добавлены в рекомендации.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Убрать из рекомендаций на главной"))
    def unmark_home_recommended(self, request, queryset):
        updated_count = queryset.update(
            is_home_recommended=False,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d карточка убрана из рекомендаций.",
                "%(count)d карточки убраны из рекомендаций.",
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
        updated_count = queryset.update(
            status=Place.STATUS_PENDING,
            is_active=False,
            rejection_reason="",
            updated_at=timezone.now(),
        )
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
        for place in queryset.iterator(chunk_size=100):
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
            for place in queryset.iterator(chunk_size=100):
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
        selected_ids = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        if selected_ids:
            queryset = Place.objects.filter(pk__in=selected_ids, deleted_at__isnull=False)

        restored_count = 0
        for place in queryset.iterator(chunk_size=100):
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

        for place in queryset.iterator(chunk_size=100):
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
        for place in queryset.iterator(chunk_size=100):
            self._soft_delete_place(place=place, user=request.user)

    def _stringify_audit_value(self, value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def save_model(self, request, obj, form, change):
        old_values = {}
        old_pricing_value = "0 tariffs"
        old_schedule_value = ""
        old_status = None
        if change and obj.pk:
            old_obj = Place.objects.filter(pk=obj.pk).first()
            if old_obj:
                old_pricing_value = pricing_audit_summary(old_obj)
                old_status = old_obj.status
                for field in self.AUDIT_TRACKED_FIELDS:
                    old_values[field] = getattr(old_obj, field)
                if old_obj.has_structured_schedule:
                    old_schedule_value = build_schedule_summary(serialize_place_schedule(old_obj))
                else:
                    old_schedule_value = (old_obj.schedule or "").strip()

        if "_save_draft" in request.POST:
            if not (obj.name or "").strip():
                obj.name = DRAFT_PLACEHOLDER_NAME
            if not obj.category_id:
                obj.category = Category.objects.order_by("order", "name", "code").first()
            obj.status = Place.STATUS_DRAFT
            obj.is_active = False
        elif "_publish_place" not in request.POST:
            if obj.status != Place.STATUS_PUBLISHED:
                obj.is_active = False
            elif not obj.is_active or old_status != Place.STATUS_PUBLISHED:
                obj.status = Place.STATUS_DRAFT
                obj.is_active = False
                setattr(request, "_km_place_publish_requires_explicit_action", True)

        if obj.is_verified and obj.last_verified_at is None:
            obj.last_verified_at = timezone.now()

        if not change and not obj.created_by_id:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)
        new_pricing_value = pricing_audit_summary(obj)
        if not change:
            self.place_audit_repository.create_entries(
                place=obj,
                changed_by=request.user,
                source=PlaceChangeAudit.SOURCE_ADMIN,
                changes={"created": ("", "1"), "pricing_plans": ("0 tariffs", new_pricing_value)},
            )
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
            if old_pricing_value != new_pricing_value:
                audit_entries.append(
                    PlaceChangeAudit(
                        place=obj,
                        changed_by=request.user,
                        source=PlaceChangeAudit.SOURCE_ADMIN,
                        field_name="pricing_plans",
                        old_value=old_pricing_value,
                        new_value=new_pricing_value,
                    )
                )
            if audit_entries:
                PlaceChangeAudit.objects.bulk_create(audit_entries)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self._save_filepond_gallery_uploads(request, form.instance)

    def _save_filepond_gallery_uploads(self, request, obj):
        if not obj or not obj.pk or not hasattr(request, "FILES"):
            return

        uploads = request.FILES.getlist("gallery_uploads")
        if not uploads:
            return

        current_count = PlacePhoto.objects.filter(place=obj).count()
        available_slots = max(10 - current_count, 0)
        if available_slots <= 0:
            messages.warning(request, _("Лимит галереи — 10 фотографий. Новые файлы не добавлены."))
            return

        max_order = PlacePhoto.objects.filter(place=obj).aggregate(max_order=Max("order"))["max_order"] or 0
        created_count = 0
        failed_count = 0
        for offset, uploaded_file in enumerate(uploads[:available_slots], start=1):
            try:
                normalized = normalize_uploaded_image(uploaded_file)
                PlacePhoto.objects.create(
                    place=obj,
                    image=normalized,
                    order=max_order + offset,
                )
            except ValidationError as exc:
                failed_count += 1
                messages.error(
                    request,
                    _("%(name)s — ошибка: %(reason)s")
                    % {"name": uploaded_file.name, "reason": "; ".join(exc.messages)},
                )
            except Exception:
                failed_count += 1
                logger.exception(
                    "Admin gallery image persistence failed: place_id=%s name=%s size=%s mime=%s",
                    obj.pk,
                    uploaded_file.name,
                    getattr(uploaded_file, "size", 0),
                    getattr(uploaded_file, "content_type", ""),
                )
                messages.error(
                    request,
                    _("%(name)s — ошибка сохранения в хранилище.")
                    % {"name": uploaded_file.name},
                )
            else:
                created_count += 1
                messages.success(
                    request,
                    _("%(name)s — загружено.") % {"name": uploaded_file.name},
                )

        skipped_count = len(uploads) - created_count - failed_count
        if skipped_count > 0:
            messages.warning(
                request,
                ngettext(
                    "%(count)d фото не добавлено: лимит галереи — 10 фотографий.",
                    "%(count)d фото не добавлены: лимит галереи — 10 фотографий.",
                    skipped_count,
                )
                % {"count": skipped_count},
            )

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
        if getattr(request, "_km_place_publish_requires_explicit_action", False):
            self.message_user(
                request,
                _("Обычное сохранение не публикует карточку. Для публикации используйте кнопку “Опубликовать”."),
                level=messages.WARNING,
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
        if getattr(request, "_km_place_publish_requires_explicit_action", False):
            self.message_user(
                request,
                _("Обычное сохранение не публикует карточку. Для публикации используйте кнопку “Опубликовать”."),
                level=messages.WARNING,
            )
        return super().response_change(request, obj)

    def _handle_save_draft_submit(self, request, obj, *, message: str):
        self.message_user(request, message, level=messages.SUCCESS)
        return HttpResponseRedirect(self._place_change_url(obj))

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = self._place_change_url(obj)
        actions = [
            format_html(
                '<a class="km-admin-icon-action km-admin-icon-action--edit" href="{}" title="{}" aria-label="{}"><i class="fas fa-pen"></i></a>',
                edit_url,
                _("Редактировать"),
                _("Редактировать"),
            )
        ]
        if obj.is_deleted:
            actions.append(
                format_html(
                    '<a class="km-admin-icon-action km-admin-icon-action--restore" href="{}" title="{}" aria-label="{}"><i class="fas fa-undo"></i></a>',
                    self._place_restore_url(obj),
                    _("Восстановить"),
                    _("Восстановить"),
                )
            )
        else:
            is_published = obj.status == Place.STATUS_PUBLISHED and obj.is_active
            visibility_label = _("Снять с публикации") if is_published else _("Опубликовать")
            visibility_icon = "fas fa-eye-slash" if is_published else "fas fa-bullhorn"
            visibility_tone = "unpublish" if is_published else "publish"
            actions.extend(
                [
                    format_html(
                        '<button type="button" class="km-admin-icon-action km-admin-icon-action--{}" data-place-visibility-url="{}" title="{}" aria-label="{}"><i class="{}"></i></button>',
                        visibility_tone,
                        reverse("admin:catalog_place_toggle_publication", args=[obj.pk]),
                        visibility_label,
                        visibility_label,
                        visibility_icon,
                    ),
                    format_html(
                        '<a class="km-admin-icon-action km-admin-icon-action--open" href="{}" title="{}" aria-label="{}" target="_blank" rel="noopener"><i class="fas fa-eye"></i></a>',
                        obj.get_absolute_url(),
                        _("Открыть"),
                        _("Открыть"),
                    ),
                    format_html(
                        '<a class="km-admin-icon-action km-admin-icon-action--delete km-admin-action-menu__link--danger" href="{}" title="{}" aria-label="{}"><i class="far fa-trash-alt"></i></a>',
                        self._place_delete_url(obj),
                        _("В удалённые"),
                        _("В удалённые"),
                    ),
                ]
            )

        return format_html(
            '<div class="km-place-row-actions km-place-row-actions--icons">{}</div>',
            format_html_join("", "{}", ((action,) for action in actions)),
        )


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
