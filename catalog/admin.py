from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from .models import (
    CatalogContentSettings,
    Place,
    PlacePhoto,
    PlaceReview,
    PlaceReviewsByClub,
    SiteReview,
    SiteSettings,
    SiteBrandingSettings,
    SiteAboutSettings,
    SiteContactsSettings,
    SiteFooterSettings,
    SiteEmptyStateSettings,
)

# Keep "Настройка сайта" as the first item in CATALOG app menu.
_original_get_app_list = admin.site.get_app_list


def _kidsmap_get_app_list(self, request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    for app in app_list:
        if app.get("app_label") != "catalog":
            continue
        priority = {
            "sitesettings": 0,
            "place": 10,
        }
        app["models"].sort(key=lambda m: (priority.get(m.get("object_name", "").lower(), 999), m.get("name", "")))
    return app_list


admin.site.get_app_list = _kidsmap_get_app_list.__get__(admin.site, type(admin.site))


class PlacePhotoInline(admin.TabularInline):
    model = PlacePhoto
    extra = 0
    fields = ("image", "caption", "order")
    ordering = ("order", "id")


class PlaceReviewInline(admin.TabularInline):
    model = PlaceReview
    extra = 0
    fields = ("author_name", "is_anonymous", "rating", "text", "is_approved", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


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
        "rating_avg",
        "rating_count",
        "is_active",
        "is_verified",
        "updated_at",
    )
    list_filter = ("category", "district", "metro", "is_active", "is_verified", "age_from", "age_to")
    search_fields = ("name_ru", "name_en", "name", "address", "instagram", "phone1")
    list_editable = ("is_active", "is_verified", "likes_count")
    readonly_fields = ("slug", "rating_avg", "rating_count", "created_at", "updated_at")
    ordering = ("-updated_at",)
    list_per_page = 30
    save_on_top = True
    actions = ("mark_active", "mark_inactive", "mark_verified", "mark_unverified")
    inlines = [PlacePhotoInline, PlaceReviewInline]
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "subcategory",
                    "is_active",
                    "is_verified",
                    "likes_count",
                    "rating_avg",
                    "rating_count",
                )
            },
        ),
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


class _BaseSiteSettingsSectionAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "updated_at")
    readonly_fields = (
        "updated_at",
        "logo_preview",
        "site_background_image_preview",
        "home_hero_image_preview",
        "empty_results_image_preview",
    )

    def get_model_perms(self, request):
        # Hide subsection models from the left sidebar; open via "Настройка сайта" hub.
        return {}

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = SiteSettings.get_solo()
        opts = self.model._meta
        url = reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])
        return redirect(url)

    def _render_image_preview(self, obj, field_name):
        if not obj:
            return "-"
        file_field = getattr(obj, field_name, None)
        if not file_field:
            return "-"
        try:
            url = file_field.url
        except Exception:
            return "-"
        name = file_field.name.split("/")[-1] if getattr(file_field, "name", "") else ""
        return format_html(
            '<div style="display:flex;align-items:center;gap:10px;">'
            '<a href="{0}" target="_blank" rel="noopener">'
            '<img src="{0}" alt="{1}" style="max-width:220px;max-height:120px;border:1px solid #cdd6df;border-radius:8px;background:#fff;" />'
            "</a>"
            '<span style="font-family:monospace;">{2}</span>'
            "</div>",
            url,
            name,
            name,
        )

    @admin.display(description=_("Текущее лого"))
    def logo_preview(self, obj):
        return self._render_image_preview(obj, "logo")

    @admin.display(description=_("Текущий фон сайта"))
    def site_background_image_preview(self, obj):
        return self._render_image_preview(obj, "site_background_image")

    @admin.display(description=_("Текущий фон баннера"))
    def home_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "home_hero_image")

    @admin.display(description=_("Текущая картинка пустого результата"))
    def empty_results_image_preview(self, obj):
        return self._render_image_preview(obj, "empty_results_image")


@admin.register(SiteSettings)
class SiteSettingsCompatAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def _is_section_complete(self, obj, fields):
        for field in fields:
            value = getattr(obj, field, None)
            if value in (None, "", []):
                return False
        return True

    def _sections(self):
        obj = SiteSettings.get_solo()
        branding_ok = self._is_section_complete(obj, ["brand_name"])
        about_ok = self._is_section_complete(obj, ["about_text_ru"])
        contacts_ok = self._is_section_complete(obj, ["contacts_text_ru"])
        footer_ok = self._is_section_complete(obj, ["footer_phone", "footer_email"])
        empty_ok = self._is_section_complete(obj, ["empty_results_text_ru"])
        return [
            {
                "title": _("Лого и бренд"),
                "description": _("Название проекта и логотип в шапке."),
                "url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "complete": branding_ok,
            },
            {
                "title": _("О проекте"),
                "description": _("Текст страницы «О проекте»."),
                "url": reverse("admin:catalog_siteaboutsettings_changelist"),
                "complete": about_ok,
            },
            {
                "title": _("Контакты"),
                "description": _("Контакты для страницы «Контакты»."),
                "url": reverse("admin:catalog_sitecontactssettings_changelist"),
                "complete": contacts_ok,
            },
            {
                "title": _("Футер и соцсети"),
                "description": _("Телефон, email, Instagram и WhatsApp в футере."),
                "url": reverse("admin:catalog_sitefootersettings_changelist"),
                "complete": footer_ok,
            },
            {
                "title": _("Пустой результат"),
                "description": _("Картинка и текст, если в каталоге ничего не найдено."),
                "url": reverse("admin:catalog_siteemptystatesettings_changelist"),
                "complete": empty_ok,
            },
        ]

    def changelist_view(self, request, extra_context=None):
        context = {
            **self.admin_site.each_context(request),
            "title": _("Настройка сайта"),
            "opts": self.model._meta,
            "sections": self._sections(),
        }
        return TemplateResponse(request, "admin/catalog/site_settings_hub.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return redirect(reverse("admin:catalog_sitesettings_changelist"))


@admin.register(SiteBrandingSettings)
class SiteBrandingSettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (_("Лого и бренд"), {"fields": ("brand_name", "logo", "logo_preview")}),
        (
            _("Дизайн-картинки"),
            {"fields": ("site_background_image", "site_background_image_preview", "home_hero_image", "home_hero_image_preview")},
        ),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )


@admin.register(SiteAboutSettings)
class SiteAboutSettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (_("О проекте (i18n)"), {"fields": ("about_text_ru", "about_text_az", "about_text_en")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )


@admin.register(SiteContactsSettings)
class SiteContactsSettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (_("Контакты страницы (i18n)"), {"fields": ("contacts_text_ru", "contacts_text_az", "contacts_text_en")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )


@admin.register(SiteFooterSettings)
class SiteFooterSettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (_("Футер и соцсети"), {"fields": ("footer_phone", "footer_email", "footer_instagram", "footer_whatsapp")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )


@admin.register(SiteEmptyStateSettings)
class SiteEmptyStateSettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (
            _("Пустой результат каталога"),
            {
                "fields": (
                    "empty_results_text_ru",
                    "empty_results_text_az",
                    "empty_results_text_en",
                    "empty_results_image",
                    "empty_results_image_preview",
                )
            },
        ),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )


@admin.register(PlaceReview)
class PlaceReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "display_author", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved", "is_anonymous", "created_at")
    search_fields = ("place__name_ru", "place__name_en", "place__name_az", "author_name", "text")
    actions = ("approve_reviews", "hide_reviews")
    readonly_fields = ("created_at", "updated_at", "session_key")

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

    @admin.action(description=_("Одобрить выбранные отзывы"))
    def approve_reviews(self, request, queryset):
        places = set(queryset.values_list("place_id", flat=True))
        queryset.update(is_approved=True)
        for place in Place.objects.filter(id__in=places):
            place.refresh_rating_stats()

    @admin.action(description=_("Скрыть выбранные отзывы"))
    def hide_reviews(self, request, queryset):
        places = set(queryset.values_list("place_id", flat=True))
        queryset.update(is_approved=False)
        for place in Place.objects.filter(id__in=places):
            place.refresh_rating_stats()


@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = ("display_author", "rating", "is_approved", "created_at")
    list_filter = ("rating", "is_approved", "is_anonymous", "created_at")
    search_fields = ("author_name", "text")
    actions = ("approve_reviews", "hide_reviews")
    readonly_fields = ("created_at", "updated_at", "session_key")

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

    @admin.action(description=_("Одобрить выбранные отзывы"))
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description=_("Скрыть выбранные отзывы"))
    def hide_reviews(self, request, queryset):
        queryset.update(is_approved=False)


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


@admin.register(CatalogContentSettings)
class CatalogContentSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        (
            _("Контент фильтров"),
            {
                "fields": (
                    "districts_json",
                    "metro_stations_json",
                )
            },
        ),
        (
            _("Контент SEO-страниц"),
            {
                "fields": ("seo_pages_json",),
                "description": _("JSON-структура SEO страниц. Если оставить пусто, используются значения по умолчанию из кода."),
            },
        ),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("updated_at",)}),
    )

    def has_add_permission(self, request):
        return not CatalogContentSettings.objects.exists()
