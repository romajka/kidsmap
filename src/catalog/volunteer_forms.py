import json

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from catalog.forms import PlaceScheduleEditorFormMixin, SubcategorySelect, _validate_azerbaijan_phone
from catalog.models import Place, Subcategory
from catalog.services.image_uploads import normalize_uploaded_image
from catalog.services.pricing_plans import normalize_pricing_plans
from catalog.services.place_schedule import validate_schedule_payload, dump_schedule_payload, WEEKDAY_ORDER


# Everything else (owner, creator, publication, verification, SEO, ratings,
# recommendation flags, deletion) is server-owned and never mass-assigned.
CONTENT_FIELDS = (
    "name_az", "name_ru", "name_en", "category", "subcategory",
    "description_az", "description_ru", "description_en",
    "age_from", "age_to", "age_open_ended", "offers_adult_classes",
    "district", "metro", "address", "lat", "lng",
    "phone1", "phone2", "phone3", "instagram", "website",
    "photo", "cover_photo", "schedule", "schedule_mode",
    "schedule_note_az", "schedule_note_ru", "schedule_note_en",
    "price_mode", "lesson_duration_minutes", "lesson_format",
    "lessons_per_week", "lessons_per_month",
    "extra_conditions_az", "extra_conditions_ru", "extra_conditions_en",
    "additional_info_az", "additional_info_ru", "additional_info_en",
    "custom_price_badge_az", "custom_price_badge_ru", "custom_price_badge_en",
)


class VolunteerPlaceForm(PlaceScheduleEditorFormMixin, forms.ModelForm):
    revision_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    base_token = forms.CharField(widget=forms.HiddenInput)
    pricing_plans = forms.CharField(required=False, widget=forms.HiddenInput(attrs={"data-tariff-input": ""}))

    class Meta:
        model = Place
        fields = CONTENT_FIELDS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.invalid_schedule = False
        if self.is_bound and self.data.get("structured_schedule"):
            # The shared editor initializer expects normalized day objects.
            # Validate hostile/malformed payloads before giving it display data.
            try:
                raw = json.loads(self.data["structured_schedule"])
                if not isinstance(raw, list) or any(
                    not isinstance(day, dict) or day.get("weekday") not in WEEKDAY_ORDER
                    or not isinstance(day.get("intervals", []), list)
                    or any(not isinstance(interval, dict) for interval in day.get("intervals", []))
                    for day in raw
                ):
                    raise ValueError
                validation = validate_schedule_payload(raw)
                self.invalid_schedule = bool(validation.errors)
                normalized = validation.days
            except (ValueError, TypeError, KeyError, AttributeError):
                self.invalid_schedule = True
                normalized = []
            self.data = self.data.copy()
            self.data["structured_schedule"] = dump_schedule_payload(normalized)
        self._init_schedule_editor()
        self.fields["price_mode"].widget = forms.HiddenInput()
        self.fields["price_mode"].required = False
        self.fields["photo"].widget = forms.FileInput()
        self.fields["cover_photo"].widget = forms.FileInput()
        self.fields["photo"].widget.attrs["accept"] = "image/jpeg,image/png,image/webp,image/heic"
        self.fields["cover_photo"].widget.attrs["accept"] = "image/jpeg,image/png,image/webp,image/heic"
        for field in self.fields.values():
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3
        if not self.is_bound:
            self.initial["pricing_plans"] = json.dumps(self.instance.pricing_plans, ensure_ascii=False)
        self.fields["subcategory"].widget = SubcategorySelect()
        self.fields["subcategory"].queryset = Subcategory.objects.select_related("category").all()

    def clean(self):
        cleaned = super().clean()
        category, subcategory = cleaned.get("category"), cleaned.get("subcategory")
        if subcategory and category and subcategory.category_id != category.pk:
            self.add_error("subcategory", _("Подкатегория должна относиться к выбранной категории."))
        if self.invalid_schedule:
            self.add_error("structured_schedule", _("Проверьте расписание работы."))
        if not any((cleaned.get(f"name_{lang}") or "").strip() for lang in ("az", "ru", "en")):
            self.add_error("name_az", _("Укажите название места."))
        self.instance.name = next(((cleaned.get(f"name_{lang}") or "").strip() for lang in ("az", "ru", "en") if (cleaned.get(f"name_{lang}") or "").strip()), "")
        if cleaned.get("age_open_ended"):
            cleaned["age_to"] = None
            cleaned["age_from"] = cleaned.get("age_from") or 0
        cleaned["price_mode"] = cleaned.get("price_mode") or Place.PRICE_MODE_TARIFFS
        try:
            cleaned["pricing_plans"] = normalize_pricing_plans(cleaned.get("pricing_plans") or "[]", allow_verified=False)
        except ValidationError as exc:
            self.add_error("pricing_plans", exc)
        raw = cleaned.get("structured_schedule") or self.data.get("structured_schedule")
        if raw:
            try:
                if not isinstance(json.loads(raw), list):
                    raise ValueError
            except (ValueError, TypeError):
                self.add_error("structured_schedule", _("Проверьте расписание работы."))
        return self._clean_schedule_editor(cleaned)

    def clean_photo(self):
        value = self.cleaned_data.get("photo")
        return normalize_uploaded_image(value) if "photo" in self.files else value

    def clean_cover_photo(self):
        value = self.cleaned_data.get("cover_photo")
        return normalize_uploaded_image(value) if "cover_photo" in self.files else value

    def clean_phone1(self):
        value = self.cleaned_data.get("phone1") or ""
        return _validate_azerbaijan_phone(value) if value else ""

    def clean_phone2(self):
        value = self.cleaned_data.get("phone2") or ""
        return _validate_azerbaijan_phone(value) if value else ""

    def clean_phone3(self):
        value = self.cleaned_data.get("phone3") or ""
        return _validate_azerbaijan_phone(value) if value else ""

    @property
    def publication_rules(self):
        # Owner browser validation differs from canonical moderation readiness.
        # Volunteer mode shows server readiness; it never claims owner-rule readiness.
        return {}

    @property
    def wizard_steps(self):
        from catalog.services.permanent_place_wizard import build_steps
        steps = build_steps(self)
        steps[5]["fields"] = [self["photo"], self["cover_photo"]]
        extra = [name for name in CONTENT_FIELDS if name.startswith("custom_price_badge_")]
        steps[2]["optional"] = [self[name] for name in extra]
        return steps

    @property
    def wizard_copy(self):
        from catalog.services.permanent_place_wizard import ui_copy
        from catalog.services.permanent_place_rules import copy as t
        ui = ui_copy()
        ui.update(intro=t("Заполните карточку и отправьте её администратору. Публикация — только после проверки.", "Kartı doldurub administratora göndərin. Yayımlamaq üçün yoxlama tələb olunur.", "Complete the place and send it to the administrator. Publication requires approval."),
                  submit=_("Отправить на проверку"), browser_saved=t("Есть несохранённые изменения. Сохраните черновик перед выходом.", "Saxlanmamış dəyişikliklər var. Çıxmazdan əvvəl qaralamanı saxlayın.", "You have unsaved changes. Save a draft before leaving."),
                  ready=t("После сохранения готовность будет пересчитана сервером.", "Saxladıqdan sonra hazırlıq yenidən hesablanacaq.", "Readiness will be recalculated after you save."))
        return ui

    def sections(self):
        groups = (
            (_("Основное"), ("name_az", "category", "subcategory", "description_az"), False),
            (_("Переводы (необязательно)"), ("name_ru", "name_en", "description_ru", "description_en"), True),
            (_("Возраст"), CONTENT_FIELDS[8:12], False),
            (_("Адрес и контакты"), CONTENT_FIELDS[12:22], False),
            (_("Фотографии"), ("photo", "cover_photo"), False),
            (_("Дополнительно"), CONTENT_FIELDS[30:40], True),
        )
        return [(title, [self[name] for name in names if not self[name].is_hidden], optional) for title, names, optional in groups]
