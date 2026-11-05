"""Admin forms for places and events."""

import json
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from zoneinfo import ZoneInfo

from catalog.content_data import BAKU_METRO_STATIONS
from catalog.forms import PlaceScheduleEditorFormMixin, SubcategorySelect
from catalog.services.phone_forms import ContactPhoneFormMixin
from catalog.models import (
    Place,
    PlacePhoto,
    Event,
    Category,
    Subcategory,
    CatalogContentSettings,
)
from catalog.services.options import sort_translated_values
from catalog.services.place_readiness import (
    evaluate_form_readiness,
    publication_blocked_message,
)
from catalog.services.pricing_plans import normalize_pricing_plans
from catalog.services.place_public_links import PublicLinksFormMixin
from .common import ADMIN_DATETIME_LOCAL_FORMAT, DRAFT_PLACEHOLDER_NAME


class CandidatePlacePhotoFormSet(forms.BaseInlineFormSet):
    """Edit server-stored candidate files as extra forms; never invent live IDs."""
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        from catalog.models import VolunteerPlaceRevision
        from catalog.services.publication_forms import gallery_for_edit
        self.candidate_rows = None
        if instance and instance.pk and VolunteerPlaceRevision.objects.filter(
                place_id=instance.pk, status__in=['draft', 'pending', 'rejected']).exists():
            self.candidate_rows = gallery_for_edit(instance)
            kwargs['queryset'] = PlacePhoto.objects.none()
        super().__init__(*args, **kwargs)
        if self.candidate_rows is not None:
            self.extra = len(self.candidate_rows)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if self.candidate_rows is not None and index is not None and index < len(self.candidate_rows):
            row = self.candidate_rows[index]
            kwargs['instance'] = PlacePhoto(place=self.instance, image=row['image'],
                caption=row.get('caption', ''), order=row['order'])
        return kwargs

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if self.candidate_rows is not None and index is not None and index < len(self.candidate_rows):
            form.candidate_gallery_row = self.candidate_rows[index]
            from catalog.services.photo_gallery import gallery_key
            form.candidate_gallery_key = gallery_key(self.candidate_rows[index])

    def clean(self):
        super().clean()
        if self.candidate_rows is not None and self.is_bound:
            if self.initial_form_count() != 0 or self.total_form_count() < len(self.candidate_rows):
                raise ValidationError(_('Галерея изменилась. Обновите страницу.'))
            if any(form.cleaned_data.get('id') for form in self.forms):
                raise ValidationError(_('Галерея изменилась. Обновите страницу.'))

class PlaceAdminForm(PublicLinksFormMixin, ContactPhoneFormMixin, PlaceScheduleEditorFormMixin, forms.ModelForm):
    compact_contact_fields = True

    @property
    def pricing_editor_contract(self):
        from catalog.services.pricing_editor_contract import build_pricing_editor_contract
        return build_pricing_editor_contract()

    @property
    def offering_choices(self):
        from catalog.services.pricing_plans import offering_editor_choices
        return offering_editor_choices(self.instance)

    @property
    def wizard_copy(self):
        from catalog.services.permanent_place_wizard import ui_copy
        return ui_copy()

    location_override_reason = forms.CharField(
        label=_("Причина ручного исправления района"), required=False, max_length=1000,
        help_text=_("Только для исключений: причина сохранится в истории. При переносе точки исправление нужно подтвердить заново."),
        widget=forms.Textarea(attrs={"rows": 2, "data-location-override": ""}),
    )
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT
    name = forms.CharField(required=False, widget=forms.HiddenInput())
    # These controls are rendered inside pricing_editor.html rather than by a
    # regular admin fieldset. Declare them explicitly so ModelAdmin.get_form()
    # does not drop them when it restricts the form to fieldset fields.
    custom_price_badge_az = forms.CharField(
        label=_("Текст плашки (AZ)"), required=False, max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Pulsuz · 120 ₼-dən"}),
    )
    custom_price_badge_ru = forms.CharField(
        label=_("Текст плашки (RU)"), required=False, max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Бесплатно · от 120 ₼"}),
    )
    custom_price_badge_en = forms.CharField(
        label=_("Текст плашки (EN)"), required=False, max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Free · from 120 ₼"}),
    )
    pricing_plans = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"data-tariff-input": ""}),
    )
    nested_pricing = forms.CharField(required=False, widget=forms.HiddenInput())
    price_mode = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={"id": "id_price_mode"}),
        initial=Place.PRICE_MODE_TARIFFS,
    )

    create_as_distinct_branch = forms.BooleanField(required=False)

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

    def clean_price_mode(self):
        if self.is_bound and "price_mode" not in self.data and self.instance.pk:
            return Place.objects.only("price_mode").get(pk=self.instance.pk).price_mode
        val = (self.cleaned_data.get("price_mode") or "").strip()
        if val not in dict(Place.PRICE_MODE_CHOICES):
            val = Place.PRICE_MODE_TARIFFS
        return val

    def clean(self):
        cleaned = super().clean()
        from catalog.services.publication_forms import validate_form_source
        validate_form_source(self)
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
            cleaned["pricing_plans"] = normalize_pricing_plans(cleaned.get("pricing_plans") or "[]", allow_verified=True, legacy_place=self.instance)
            if self.instance.pk:
                from catalog.services.pricing_plans import validate_target_plan_ids
                validate_target_plan_ids(self.instance, cleaned["pricing_plans"])
            # A legacy scalar-only card has nothing to replace. Scheduling an
            # empty replacement would erase its prices on an unrelated edit.
            # Actual tariff edits/removals still synchronize the projections.
            if cleaned["pricing_plans"] or not self.instance.pk or self.instance.pricing_plan_records.exists():
                self.instance.pricing_plans = cleaned["pricing_plans"]
        except ValidationError as exc:
            self.add_error("pricing_plans", exc)
            cleaned["pricing_plans"] = []
        if cleaned.get("nested_pricing"):
            try:
                from catalog.services.pricing_plans import validate_nested_pricing
                nested = json.loads(cleaned["nested_pricing"])
                if not self.instance.pk:
                    raise ValidationError(_("Вложенные тарифы требуют существующую карточку."))
                cleaned["nested_pricing"] = validate_nested_pricing(self.instance, nested, allow_verified=True)
            except (ValueError, ValidationError) as exc:
                self.add_error("nested_pricing", exc)
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
        # One readiness verdict for the whole product: the same service drives
        # the progress bar, the "Проверка" block and this gate, so the form can
        # never show 100% while the save is refused. Compute it before any
        # ``add_error`` call: an error drops its field from ``cleaned_data``,
        # and a later re-read would fall back to the stored value and show a
        # missing item as filled.
        readiness = evaluate_form_readiness(self, self.instance)
        self.place_readiness = readiness
        # A card that is already live keeps its place on the site while its
        # legacy data is migrated: refusing the save would freeze every stored
        # card at once. ``self.instance`` still holds the stored values here —
        # ``construct_instance`` runs later, in ``_post_clean``.
        self.place_readiness_compatibility = False
        was_published = (
            bool(getattr(self.instance, "pk", None))
            and getattr(self.instance, "status", "") == status_published
            and bool(getattr(self.instance, "is_active", False))
        )
        if (is_active or status == status_published) and not skips_publish_validation:
            if not readiness.is_ready:
                if was_published and not any(issue.code == 'coordinates' for issue in readiness.issues):
                    # Compatibility never applies to a new card, a draft or a
                    # card that was taken off the site: those need a full 12/12.
                    self.place_readiness_compatibility = True
                else:
                    self.add_error(None, ValidationError(publication_blocked_message(readiness),code='publication_incomplete'))
                    for issue in readiness.issues:
                        if issue.field in self.fields and issue.field not in self.errors:
                            self.add_error(issue.field, issue.message)

        return cleaned

    def __init__(self, *args, **kwargs):
        if not args and kwargs.get("data") is None and kwargs.get("instance") is not None:
            from catalog.services.publication_forms import candidate_for_edit
            kwargs["instance"]=candidate_for_edit(kwargs["instance"])
        if kwargs.get("instance") is not None and (kwargs.get("data") is not None or (args and args[0] is not None)) and kwargs["instance"].pk:
            from catalog.services.publication_forms import candidate_for_edit
            candidate = candidate_for_edit(kwargs["instance"])
            contact_names = ("phone1", "phone2", "phone3", "phone_country", "whatsapp_mode", "whatsapp_number")
            kwargs["initial"] = {**{name: getattr(candidate, name) for name in contact_names}, **(kwargs.get("initial") or {})}
        super().__init__(*args, **kwargs)
        if self.is_bound and self.instance.pk:
            from catalog.services.publication_forms import candidate_for_edit
            candidate = candidate_for_edit(self.instance)
            # No upload means keep the saved candidate, not the live file.
            # ClearableFileInput still handles explicit removal and replacement.
            for name in ("photo", "cover_photo"):
                value = getattr(candidate, name)
                self.initial[name] = value
                # An empty saved candidate must also replace the live value:
                # FileField.save_form_data(None) otherwise leaves it unchanged.
                setattr(self.instance, name, value)
        from catalog.services.publication_forms import init_version_field
        init_version_field(self)
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
            if getattr(self.instance, "pending_nested_pricing", None) is not None:
                self.initial["nested_pricing"] = json.dumps(self.instance.pending_nested_pricing, ensure_ascii=False)
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
        for name, field in self.fields.items():
            if name.startswith(("extra_conditions", "additional_info")):
                field.widget.attrs["rows"] = 4
        self._init_schedule_editor()

    def save(self, commit=True):
        instance = super().save(commit=False)
        for field_name in (
            "custom_price_badge_az",
            "custom_price_badge_ru",
            "custom_price_badge_en",
        ):
            if field_name in self.cleaned_data:
                setattr(instance, field_name, self.cleaned_data[field_name])
        if commit:
            instance.save()
            self._save_m2m()
        return instance

    def _configure_metro_choices(self):
        metro_options = sort_translated_values(BAKU_METRO_STATIONS)
        try:
            content_settings = CatalogContentSettings.objects.order_by('pk').first() or CatalogContentSettings()
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

class BakuEventDateTimeField(forms.DateTimeField):
    def to_python(self, value):
        with timezone.override(ZoneInfo("Asia/Baku")):
            return super().to_python(value)

class EventAdminForm(forms.ModelForm):
    expected_updated_at = forms.CharField(required=False, widget=forms.HiddenInput())
    DATETIME_LOCAL_FORMAT = ADMIN_DATETIME_LOCAL_FORMAT
    PICKER_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
    require_location_region = False

    name = forms.CharField(required=False, widget=forms.HiddenInput())

    # The custom admin template renders one text input per date. Declaring the
    # fields prevents ModelAdmin from replacing them with SplitDateTimeField,
    # which expects a two-item POST value and rejects the browser payload.
    start_datetime = BakuEventDateTimeField(
        label=_("Начало мероприятия"), required=False,
        widget=forms.TextInput(attrs={"class": "field", "data-kidsmap-datetime-picker": "1", "data-event-datetime": "start", "data-allow-input": "1"}),
    )
    end_datetime = BakuEventDateTimeField(
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
        if self.instance.pk and self.check_version:
            # ModelAdmin change POST is atomic; retain the lock through parent,
            # inline and publication writes instead of checking after save_model.
            locked = Event.objects.select_for_update().get(pk=self.instance.pk)
            if self.data.get('expected_updated_at', '') != locked.updated_at.isoformat():
                raise forms.ValidationError(_('Запись изменилась. Обновите страницу.'), code='stale_version')
        from catalog.services.locations import clean_location_fields
        cleaned = clean_location_fields(self, cleaned)
        # The widgets display minutes. An unchanged displayed value must retain
        # the stored seconds, rather than masquerade as an occurrence change.
        if self.instance.pk:
            for name in ("start_datetime", "end_datetime", "published_at"):
                original = getattr(self.instance, name)
                raw = self.data.get(name)
                if name in cleaned and original and timezone.is_aware(original) and isinstance(raw, str):
                    local = timezone.localtime(original, ZoneInfo("Asia/Baku"))
                    displayed = {local.strftime(self.PICKER_DATETIME_FORMAT), local.strftime(self.DATETIME_LOCAL_FORMAT)}
                    if raw.strip() in displayed:
                        cleaned[name] = original
        start_datetime = cleaned.get("start_datetime")
        end_datetime = cleaned.get("end_datetime")
        if start_datetime and end_datetime and end_datetime <= start_datetime:
            self.add_error("end_datetime", _("Окончание мероприятия должно быть позже начала."))
        related = cleaned.get("related_place")
        if cleaned.get("event_format") == Event.FORMAT_ONLINE:
            cleaned.update(related_place=None, address="", district="", metro="", lat=None, lng=None)
        elif related:
            for field in ("address", "district", "metro", "lat", "lng"):
                if cleaned.get(field) in (None, ""):
                    value = getattr(related, field)
                    if field in {"lat", "lng"} and value is not None:
                        from decimal import Decimal
                        value = Decimal(str(value)).quantize(Decimal("0.000001"))
                    cleaned[field] = value
        return cleaned


    def _post_clean(self):
        super()._post_clean()
        if self.errors:
            return
        from catalog.services.event_domain import _validate
        from catalog.models.event_domain import validate_event_domain
        try:
            original = Event.objects.filter(pk=self.instance.pk).first() if self.instance.pk else None
            validate_event_domain(self.instance, original)
            publication = ("_publish_event" in self.data or (
                self.instance.status == Event.STATUS_PUBLISHED and (not original or original.status != Event.STATUS_PUBLISHED)
            )) and not any(action in self.data for action in ("_save_draft", "_unpublish_event"))
            if original and original.status == Event.STATUS_PUBLISHED and not publication and not any(action in self.data for action in ("_save_draft", "_unpublish_event")):
                from catalog.services.event_readiness import publication_errors
                before = publication_errors(original)
                introduced = {name: message for name, message in publication_errors(self.instance).items() if name not in before}
                if introduced:
                    self.add_error(None, list(introduced.values()))
                    return
            if self.instance.organizer_resolution == Event.ORGANIZER_RESOLVED or not self.instance.pk:
                _validate(self.instance, publication=publication)
            elif publication:
                raise ValidationError(_("Выберите организатора перед публикацией."))
        except (ValidationError, PermissionDenied) as exc:
            if isinstance(exc, ValidationError) and hasattr(exc, "error_dict"):
                for name, errors in exc.error_dict.items():
                    self.add_error(name if name in self.fields else None, errors)
            else:
                self.add_error(None, ValidationError(str(exc)))

    def __init__(self, *args, check_version=True, **kwargs):
        self.check_version = check_version
        # Old callers do not send fields introduced by the additive schema.
        # Preserve persisted choices instead of treating absence as a new choice.
        data = args[0] if args else kwargs.get("data")
        if data is not None:
            data = data.copy()
            instance = kwargs.get("instance")
            for name in ("price_mode", "price_currency", "registration_method"):
                if name not in data:
                    data[name] = getattr(instance, name, None) or Event._meta.get_field(name).get_default()
            if args:
                args = (data,) + args[1:]
            else:
                kwargs["data"] = data
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['expected_updated_at'] = self.instance.updated_at.isoformat()
        from catalog.services.locations import configure_location_choices, init_location_fields
        init_location_fields(self, self.instance)
        configure_location_choices(self)
        from django.utils.translation import get_language
        if "organizer_organization" in self.fields:
            self.fields["organizer_organization"].label = _("Организация")
            self.fields["organizer_organization"].label_from_instance = lambda org: (
                getattr(org, "name_" + (get_language() or "az").split("-")[0], "") or org.name_az
            )
        if "organizer_specialist" in self.fields:
            self.fields["organizer_specialist"].label = _("Специалист")
            self.fields["organizer_specialist"].label_from_instance = lambda person: person.name
        if "event_format" in self.fields:
            self.fields["event_format"].label = _("Формат")
        for name, label in (("age_from", _("Возраст от")), ("age_to", _("Возраст до"))):
            if name in self.fields:
                self.fields[name].widget.attrs["aria-label"] = label
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
                    localized_value = timezone.localtime(value, ZoneInfo("Asia/Baku")) if timezone.is_aware(value) else value
                    display_format = self.PICKER_DATETIME_FORMAT if field_name in {"start_datetime", "end_datetime"} else self.DATETIME_LOCAL_FORMAT
                    self.initial[field_name] = localized_value.strftime(display_format)
        for name in ("registration_url", "website"):
            if name in self.fields:
                self.fields[name].widget = forms.URLInput(attrs={"class": "field", "placeholder": "https://"})
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
