from django import forms
from django.contrib import admin, messages
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from catalog.models import (
    Region,
    District,
    MetroStation,
    SpecialistSpecialization,
    Specialist,
    SpecialistPracticeLocation,
    SpecialistDocument,
    SpecialistReview
)

class SpecialistAdminForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        consultation_format = cleaned_data.get("consultation_format")
        
        # Enforce that if format is offline or both, at least one location must be provided and active.
        if consultation_format in [Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH]:
            total_forms_raw = self.data.get("practice_locations-TOTAL_FORMS")
            has_location = False
            if total_forms_raw is not None:
                try:
                    total_forms = int(total_forms_raw)
                    for i in range(total_forms):
                        # Skip deleted rows
                        delete_val = self.data.get(f"practice_locations-{i}-DELETE")
                        if delete_val in ["on", "1", "true"]:
                            continue
                        
                        place = self.data.get(f"practice_locations-{i}-place")
                        address = self.data.get(f"practice_locations-{i}-address")
                        region = self.data.get(f"practice_locations-{i}-region")
                        is_active_val = self.data.get(f"practice_locations-{i}-is_active")
                        
                        is_active = (is_active_val not in ["off", "false", "0"])
                        
                        if is_active and (place or address):
                            has_location = True
                            
                            # Validate region is filled for active locations
                            if not region:
                                raise forms.ValidationError(
                                    _("Для очной локации необходимо указать город/регион.")
                                )
                except ValueError:
                    pass
            
            if not has_location:
                raise forms.ValidationError(
                    _("Для очного формата работы (или онлайн и очно) необходимо указать хотя бы одно активное место приема.")
                )
                
        return cleaned_data


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("key", "name_ru", "name_az", "name_en")
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("key", "region", "name_ru", "name_az", "name_en")
    list_filter = ("region",)
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(MetroStation)
class MetroStationAdmin(admin.ModelAdmin):
    list_display = ("key", "name_ru", "name_az", "name_en")
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(SpecialistSpecialization)
class SpecialistSpecializationAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "name_az", "name_en", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("code", "name_ru", "name_az", "name_en")


class SpecialistPracticeLocationInline(admin.TabularInline):
    model = SpecialistPracticeLocation
    extra = 0
    verbose_name = _("Место приёма")
    verbose_name_plural = _("8. Места приёма")
    fields = ("place", "address", "region", "district", "metro", "price_per_session", "phone", "is_primary", "is_active")
    autocomplete_fields = ("place",)


class SpecialistDocumentInline(admin.TabularInline):
    model = SpecialistDocument
    extra = 0
    verbose_name = _("Документ")
    verbose_name_plural = _("10. Документы")
    fields = ("document_type", "name", "file", "download_link", "status", "is_published", "rejection_reason")
    readonly_fields = ("download_link",)

    @admin.display(description=_("Скачать"))
    def download_link(self, obj):
        if obj and obj.pk:
            url = reverse("serve_specialist_document", args=[obj.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, _("Скачать / Просмотреть"))
        return "-"


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    form = SpecialistAdminForm
    change_form_template = "admin/catalog/specialist/change_form.html"
    
    list_display = ("name", "consultation_format", "rating_avg", "rating_count", "is_verified", "status", "is_active", "created_at")
    list_filter = ("status", "is_verified", "is_active", "consultation_format", "specializations")
    search_fields = ("name", "name_alt", "bio_ru", "bio_az", "bio_en")
    readonly_fields = ("rating_avg", "rating_count", "created_at", "updated_at")
    filter_horizontal = ("specializations",)
    inlines = [SpecialistPracticeLocationInline, SpecialistDocumentInline]
    
    fieldsets = (
        (
            _("1. Основная информация"),
            {
                "fields": (
                    "owner",
                    "name",
                    "name_alt",
                    "slug",
                )
            },
        ),
        (
            _("2. Фото и описание"),
            {
                "fields": (
                    "photo",
                    "bio_az",
                    "bio_ru",
                    "bio_en",
                )
            },
        ),
        (
            _("3. Специализации"),
            {
                "fields": (
                    "specializations",
                )
            },
        ),
        (
            _("4. Возраст детей"),
            {
                "fields": (
                    ("age_from", "age_to"),
                )
            },
        ),
        (
            _("5. Языки консультации"),
            {
                "fields": (
                    ("language_az", "language_ru", "language_en"),
                )
            },
        ),
        (
            _("6. Онлайн / очно"),
            {
                "fields": (
                    "consultation_format",
                )
            },
        ),
        (
            _("7. Стоимость и продолжительность"),
            {
                "fields": (
                    ("price_from", "price_to"),
                    "duration_minutes",
                )
            },
        ),
        # 8 = SpecialistPracticeLocationInline
        (
            _("9. Образование и опыт"),
            {
                "fields": (
                    "experience_years",
                    "education_az",
                    "education_ru",
                    "education_en",
                    "experience_info_az",
                    "experience_info_ru",
                    "experience_info_en",
                )
            },
        ),
        # 10 = SpecialistDocumentInline
        (
            _("11. Контакты"),
            {
                "fields": (
                    "phone",
                    "whatsapp",
                    "instagram",
                    "website",
                )
            },
        ),
        (
            _("12. Модерация и публикация"),
            {
                "fields": (
                    "status",
                    "is_active",
                    "is_verified",
                    "rejection_reason",
                    "rating_avg",
                    "rating_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )



@admin.register(SpecialistReview)
class SpecialistReviewAdmin(admin.ModelAdmin):
    list_display = ("specialist", "author_name", "rating", "status", "is_approved", "created_at")
    list_filter = ("status", "is_approved", "rating", "created_at")
    search_fields = ("specialist__name", "author_name", "text")
    readonly_fields = ("created_at",)
    fieldsets = (
        (
            _("Отзыв"),
            {
                "fields": (
                    "specialist",
                    "user",
                    "author_name",
                    "rating",
                    "text",
                )
            },
        ),
        (
            _("Статус и модерация"),
            {
                "fields": (
                    "status",
                    "is_approved",
                    "rejection_reason",
                    "created_at",
                )
            },
        ),
    )
