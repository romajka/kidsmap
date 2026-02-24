from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Place, PlacePhoto


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
    extra = 0
    fields = ("image", "caption", "order")
    ordering = ("order", "id")


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
        }


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    form = PlaceAdminForm
    list_display = (
        "display_name",
        "category",
        "district",
        "metro",
        "likes_count",
        "is_active",
        "is_verified",
        "updated_at",
    )
    list_filter = ("category", "district", "metro", "is_active", "is_verified", "age_from", "age_to")
    search_fields = ("name_ru", "name_en", "name", "address", "instagram", "phone1")
    list_editable = ("is_active", "is_verified", "likes_count")
    readonly_fields = ("slug", "created_at", "updated_at")
    ordering = ("-updated_at",)
    list_per_page = 30
    save_on_top = True
    actions = ("mark_active", "mark_inactive", "mark_verified", "mark_unverified")
    inlines = [PlacePhotoInline]
    fieldsets = (
        (_("Основное"), {"fields": ("name", "slug", "category", "subcategory", "is_active", "is_verified", "likes_count")}),
        (_("Названия и описания (i18n)"), {"classes": ("collapse",), "fields": ("name_ru", "name_az", "name_en", "description_ru", "description_az", "description_en")}),
        (_("Возраст и цена"), {"fields": ("age_from", "age_to", "price_from", "price_to")}),
        (_("Локация"), {"fields": ("district", "metro", "address", "lat", "lng")}),
        (_("Контакты"), {"fields": ("phone1", "instagram", "website", "schedule")}),
        (_("Фото"), {"fields": ("cover_photo", "photo")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        return obj.name_ru or obj.name

    @admin.action(description=_("Сделать активными"))
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description=_("Сделать неактивными"))
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description=_("Отметить как проверенные"))
    def mark_verified(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description=_("Снять отметку проверки"))
    def mark_unverified(self, request, queryset):
        queryset.update(is_verified=False)
