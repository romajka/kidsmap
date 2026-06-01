from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse

from catalog.models import (
    SiteSettings,
    SiteBrandingSettings,
    SiteAboutSettings,
    SiteContactsSettings,
    SiteFooterSettings,
    SiteEmptyStateSettings,
    SiteAnalytics,
    SiteGalleryImage,
    CatalogContentSettings
)
from catalog.services.admin_analytics import build_site_analytics_context
from .user import _HiddenFromAdminIndexMixin


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
                "description": _("Телефон, email, соцсети и мессенджеры в футере."),
                "url": reverse("admin:catalog_sitefootersettings_changelist"),
                "complete": footer_ok,
            },
            {
                "title": _("Пустой результат"),
                "description": _("Картинка и текст, если в каталоге ничего не найдено."),
                "url": reverse("admin:catalog_siteemptystatesettings_changelist"),
                "complete": empty_ok,
            },
            {
                "title": _("Статистика"),
                "description": _("Сводные показатели по кружкам, лайкам и отзывам."),
                "url": reverse("admin:catalog_siteanalytics_changelist"),
                "complete": True,
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
        (
            _("Hero главной страницы (i18n)"),
            {
                "fields": (
                    "home_hero_show_decor",
                    "home_title_ru",
                    "home_title_az",
                    "home_title_en",
                    "home_subtitle_ru",
                    "home_subtitle_az",
                    "home_subtitle_en",
                    "home_search_label_ru",
                    "home_search_label_az",
                    "home_search_label_en",
                    "home_search_placeholder_ru",
                    "home_search_placeholder_az",
                    "home_search_placeholder_en",
                    "home_cta_text_ru",
                    "home_cta_text_az",
                    "home_cta_text_en",
                )
            },
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
        (
            _("Футер и соцсети"),
            {
                "fields": (
                    "footer_phone",
                    "footer_email",
                    "footer_instagram",
                    "footer_telegram",
                    "footer_youtube",
                    "footer_tiktok",
                    "footer_facebook",
                    "footer_linkedin",
                    "footer_whatsapp",
                )
            },
        ),
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


@admin.register(SiteAnalytics)
class SiteAnalyticsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        context = {
            **self.admin_site.each_context(request),
            "title": _("Статистика"),
            "opts": self.model._meta,
            **build_site_analytics_context(),
        }
        return TemplateResponse(request, "admin/catalog/site_analytics.html", context)


@admin.register(SiteGalleryImage)
class SiteGalleryImageAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/sitegalleryimage/change_list.html"
    list_display = (
        "image_preview",
        "placement",
        "category",
        "title_ru",
        "order",
        "is_active",
        "updated_at",
    )
    list_filter = ("placement", "category", "is_active")
    search_fields = ("title_ru", "title_az", "title_en", "image")
    list_editable = ("category", "order", "is_active")
    readonly_fields = ("image_preview", "created_at", "updated_at")
    ordering = ("placement", "order", "id")
    fieldsets = (
        (
            _("Где показывать"),
            {
                "fields": (
                    "placement",
                    "category",
                    "order",
                    "is_active",
                )
            },
        ),
        (
            _("Изображение и подписи"),
            {
                "fields": (
                    "image",
                    "image_preview",
                    "title_ru",
                    "title_az",
                    "title_en",
                )
            },
        ),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def changelist_view(self, request, extra_context=None):
        from django.db.models import Count

        site = SiteSettings.get_solo()
        gallery_counts = dict(
            SiteGalleryImage.objects
            .values("placement")
            .annotate(cnt=Count("id"))
            .values_list("placement", "cnt")
        )

        # Describe each photo slot on the site
        photo_slots = [
            {
                "group": "Одиночные фото сайта",
                "slots": [
                    {
                        "title": "Логотип сайта",
                        "location": "Шапка сайта (header) — слева",
                        "size_hint": "SVG или PNG, 256×256 px, мин. 128×128 px, до 500 KB",
                        "count_label": "1 файл",
                        "image_url": site.logo.url if site.logo else None,
                        "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                        "field": "logo",
                    },
                    {
                        "title": "Фон сайта",
                        "location": "Декоративный фон всего сайта",
                        "size_hint": "JPG/WebP, 1920×1080 px, до 2 MB",
                        "count_label": "1 файл",
                        "image_url": site.site_background_image.url if site.site_background_image else None,
                        "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                        "field": "site_background_image",
                    },
                    {
                        "title": "Фон hero-баннера",
                        "location": "Главная страница — большой баннер с поиском",
                        "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                        "count_label": "1 файл",
                        "image_url": site.home_hero_image.url if site.home_hero_image else None,
                        "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                        "field": "home_hero_image",
                    },
                    {
                        "title": "Картинка пустого результата",
                        "location": "Каталог — когда ничего не найдено по поиску/фильтру",
                        "size_hint": "PNG/WebP, 600×400 px, до 500 KB",
                        "count_label": "1 файл",
                        "image_url": site.empty_results_image.url if site.empty_results_image else None,
                        "edit_url": reverse("admin:catalog_siteemptystatesettings_changelist"),
                        "field": "empty_results_image",
                    },
                ],
            },
            {
                "group": "Галерея блоков (несколько фото)",
                "slots": [
                    {
                        "title": "Hero-слайдер",
                        "location": "Главная страница — фото-карточки с категориями рядом с баннером",
                        "size_hint": "JPG/WebP/PNG, рекомендуется 1200×900 или 900×1200 px, до 2 MB",
                        "count_label": f"{gallery_counts.get(SiteGalleryImage.PLACEMENT_HOME_HERO, 0)} фото",
                        "count": gallery_counts.get(SiteGalleryImage.PLACEMENT_HOME_HERO, 0),
                        "image_url": None,
                        "add_url": reverse("admin:catalog_sitegalleryimage_add") + f"?placement={SiteGalleryImage.PLACEMENT_HOME_HERO}",
                        "list_url": reverse("admin:catalog_sitegalleryimage_changelist") + f"?placement__exact={SiteGalleryImage.PLACEMENT_HOME_HERO}",
                        "is_gallery": True,
                    },
                    {
                        "title": "Блок «Партнёры»",
                        "location": "Главная страница — горизонтальный ряд логотипов партнёров",
                        "size_hint": "PNG/SVG с прозрачным фоном, 300×150 px, до 500 KB",
                        "count_label": f"{gallery_counts.get(SiteGalleryImage.PLACEMENT_HOME_PARTNERS, 0)} фото",
                        "count": gallery_counts.get(SiteGalleryImage.PLACEMENT_HOME_PARTNERS, 0),
                        "image_url": None,
                        "add_url": reverse("admin:catalog_sitegalleryimage_add") + f"?placement={SiteGalleryImage.PLACEMENT_HOME_PARTNERS}",
                        "list_url": reverse("admin:catalog_sitegalleryimage_changelist") + f"?placement__exact={SiteGalleryImage.PLACEMENT_HOME_PARTNERS}",
                        "is_gallery": True,
                    },
                ],
            },
        ]

        context = {
            **self.admin_site.each_context(request),
            "title": "Фото для блоков сайта",
            "opts": self.model._meta,
            "photo_slots": photo_slots,
        }
        return TemplateResponse(request, "admin/catalog/sitegalleryimage/change_list.html", context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        placement = (request.GET.get("placement") or "").strip()
        if placement in {value for value, _ in SiteGalleryImage.PLACEMENT_CHOICES}:
            initial["placement"] = placement
        return initial

    @admin.display(description=_("Превью"))
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "-"
        try:
            image_url = obj.image.url
        except Exception:
            return "-"
        return format_html(
            '<a href="{0}" target="_blank" rel="noopener">'
            '<img src="{0}" alt="" style="display:block;width:120px;height:78px;object-fit:cover;border:1px solid #cdd6df;border-radius:12px;background:#fff;" />'
            "</a>",
            image_url,
        )


@admin.register(CatalogContentSettings)
class CatalogContentSettingsAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
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
        return False

    def has_delete_permission(self, request, obj=None):
        return False
