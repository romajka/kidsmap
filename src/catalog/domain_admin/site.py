from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse, path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.template.response import TemplateResponse
from django.http import JsonResponse

from catalog.models import (
    SiteSettings,
    SiteBrandingSettings,
    SiteAboutSettings,
    SiteContactsSettings,
    SiteFooterSettings,
    SiteEmptyStateSettings,
    SiteVisibilitySettings,
    SiteAnalytics,
    SiteGalleryImage,
    CatalogContentSettings
)
from catalog.services.admin_analytics import build_statistics_context
from catalog.services.images import validate_uploaded_image
from .user import _HiddenFromAdminIndexMixin


class SiteRasterImageForm(forms.ModelForm):
    class Meta:
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        for field_name, upload in self.files.items():
            if field_name == "logo":
                continue
            validate_uploaded_image(upload)
        return cleaned


class _BaseSiteSettingsSectionAdmin(admin.ModelAdmin):
    form = SiteRasterImageForm
    change_form_template = "admin/catalog/shared_settings_change_form.html"
    list_display = ("brand_name", "updated_at")
    readonly_fields = (
        "updated_at",
        "logo_preview",
        "site_background_image_preview",
        "home_hero_image_preview",
        "empty_results_image_preview",
        "catalog_hero_image_preview",
        "about_hero_image_preview",
        "reviews_hero_image_preview",
        "for_business_hero_image_preview",
        "dashboard_hero_image_preview",
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

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["km_settings_title"] = self.model._meta.verbose_name.capitalize()
        context["km_settings_subtitle"] = _("Заполните настройки для этого раздела сайта.")
        context["km_settings_hub_url"] = reverse("admin:catalog_sitesettings_changelist")
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

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

    @admin.display(description=_("Текущий баннер каталога"))
    def catalog_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "catalog_hero_image")

    @admin.display(description=_("Текущий баннер страницы 'О проекте'"))
    def about_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "about_hero_image")

    @admin.display(description=_("Текущий баннер отзывов"))
    def reviews_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "reviews_hero_image")

    @admin.display(description=_("Текущий баннер владельцам"))
    def for_business_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "for_business_hero_image")

    @admin.display(description=_("Текущий баннер личного кабинета"))
    def dashboard_hero_image_preview(self, obj):
        return self._render_image_preview(obj, "dashboard_hero_image")


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
                "key": "branding",
                "icon": "fas fa-paint-brush",
                "title": _("Лого и бренд"),
                "description": _("Название проекта и логотип в шапке."),
                "url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "complete": branding_ok,
            },
            {
                "key": "about",
                "icon": "fas fa-info-circle",
                "title": _("О проекте"),
                "description": _("Текст страницы «О проекте»."),
                "url": reverse("admin:catalog_siteaboutsettings_changelist"),
                "complete": about_ok,
            },
            {
                "key": "contacts",
                "icon": "fas fa-address-book",
                "title": _("Контакты"),
                "description": _("Контакты для страницы «Контакты»."),
                "url": reverse("admin:catalog_sitecontactssettings_changelist"),
                "complete": contacts_ok,
            },
            {
                "key": "footer",
                "icon": "fas fa-share-alt",
                "title": _("Футер и соцсети"),
                "description": _("Телефон, email, соцсети и мессенджеры в футере."),
                "url": reverse("admin:catalog_sitefootersettings_changelist"),
                "complete": footer_ok,
            },
            {
                "key": "empty",
                "icon": "far fa-window-minimize",
                "title": _("Пустой результат"),
                "description": _("Картинка и текст, если в каталоге ничего не найдено."),
                "url": reverse("admin:catalog_siteemptystatesettings_changelist"),
                "complete": empty_ok,
            },
            {
                "key": "visibility",
                "icon": "fas fa-eye",
                "title": _("Разделы сайта"),
                "description": _("Включение и скрытие публичных разделов сайта."),
                "url": reverse("admin:catalog_sitevisibilitysettings_changelist"),
                "complete": True,
            },
            {
                "key": "analytics",
                "icon": "fas fa-chart-line",
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
            {
                "fields": (
                    "site_background_image",
                    "site_background_image_preview",
                    "home_hero_image",
                    "home_hero_image_preview",
                    "catalog_hero_image",
                    "catalog_hero_image_preview",
                    "reviews_hero_image",
                    "reviews_hero_image_preview",
                    "for_business_hero_image",
                    "for_business_hero_image_preview",
                    "dashboard_hero_image",
                    "dashboard_hero_image_preview",
                )
            },
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
        (_("Баннер страницы"), {"fields": ("about_hero_image", "about_hero_image_preview")}),
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


@admin.register(SiteVisibilitySettings)
class SiteVisibilitySettingsAdmin(_BaseSiteSettingsSectionAdmin):
    fieldsets = (
        (
            _("Раздел «Педагоги и специалисты»"),
            {
                "fields": ("specialists_section_enabled",),
                "description": _("Выключите, чтобы скрыть раздел из меню и owner-интерфейса. Публичные ссылки будут перенаправляться в каталог, а данные и админка останутся доступными."),
            },
        ),
        (
            _("Раздел «Временные мероприятия»"),
            {
                "fields": ("events_section_enabled",),
                "description": _("Выключите, чтобы скрыть афишу, временные карточки, ссылки в навигации и owner-интерфейсе. Публичные ссылки станут недоступны, а данные и админка останутся доступными."),
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
        try:
            period_days = int(request.GET.get("period", 30))
        except (ValueError, TypeError):
            period_days = 30

        context = {
            **self.admin_site.each_context(request),
            "title": _("Статистика"),
            "opts": self.model._meta,
            **build_statistics_context(period_days),
        }
        return TemplateResponse(request, "admin/catalog/site_analytics.html", context)


@admin.register(SiteGalleryImage)
class SiteGalleryImageAdmin(admin.ModelAdmin):
    form = SiteRasterImageForm
    MAIN_IMAGE_FIELDS = {
        "logo",
        "site_background_image",
        "home_hero_image",
        "empty_results_image",
        "catalog_hero_image",
        "about_hero_image",
        "reviews_hero_image",
        "for_business_hero_image",
        "dashboard_hero_image",
    }

    change_form_template = "admin/catalog/shared_settings_change_form.html"
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
        if request.GET.get("placement__exact"):
            return super().changelist_view(request, extra_context)

        from django.template.defaultfilters import filesizeformat
        import os

        def get_file_info(file_field, fallback_static_path=None):
            if not file_field:
                if fallback_static_path:
                    from django.templatetags.static import static
                    return {
                        "url": static(fallback_static_path),
                        "name": fallback_static_path.split("/")[-1],
                        "size": "По умолчанию",
                        "is_fallback": True
                    }
                return None
            try:
                size = filesizeformat(file_field.size)
                name = os.path.basename(file_field.name)
                url = file_field.url
                return {"url": url, "name": name, "size": size, "is_fallback": False}
            except Exception:
                # Fallback if file is missing on disk
                return {
                    "url": getattr(file_field, "url", ""),
                    "name": os.path.basename(getattr(file_field, "name", "")) if getattr(file_field, "name", "") else "",
                    "size": "N/A",
                    "is_fallback": False
                }

        site = SiteSettings.get_solo()
        
        # Oдиночные фото
        main_images = [
            {
                "title": "Логотип сайта",
                "field_name": "logo",
                "location": "Отображается в шапке сайта (header) слева на всех страницах",
                "size_hint": "SVG или PNG, 256×256 px (минимум 128×128), до 500 KB",
                "file": get_file_info(site.logo, "img/logo.svg"),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("home"),
            },
            {
                "title": "Фон сайта",
                "field_name": "site_background_image",
                "location": "Декоративный фон всего сайта",
                "size_hint": "JPG/WebP, 1920×1080 px, до 2 MB",
                "file": get_file_info(site.site_background_image),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("home"),
            },
            {
                "title": "Фон hero-баннера",
                "field_name": "home_hero_image",
                "location": "Фоновое изображение главной страницы (большой баннер)",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.home_hero_image),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("home"),
            },
            {
                "title": "Баннер каталога",
                "field_name": "catalog_hero_image",
                "location": "Фоновое изображение вверху страницы каталога кружков",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.catalog_hero_image, "img/banners/catalog-hero.webp"),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("place_list"),
            },
            {
                "title": "Баннер страницы 'О проекте'",
                "field_name": "about_hero_image",
                "location": "Фоновое изображение вверху страницы «О проекте»",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.about_hero_image, "img/banners/about-hero.webp"),
                "edit_url": reverse("admin:catalog_siteaboutsettings_changelist"),
                "preview_url": reverse("about"),
            },
            {
                "title": "Баннер страницы отзывов",
                "field_name": "reviews_hero_image",
                "location": "Фоновое изображение вверху страницы отзывов о проекте",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.reviews_hero_image, "img/banners/reviews-hero.webp"),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("site_reviews"),
            },
            {
                "title": "Баннер страницы владельцам",
                "field_name": "for_business_hero_image",
                "location": "Фоновое изображение вверху страницы «Для бизнеса»",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.for_business_hero_image, "img/banners/for-business-hero.webp"),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("for_business"),
            },
            {
                "title": "Баннер личного кабинета",
                "field_name": "dashboard_hero_image",
                "location": "Фоновое изображение в шапке личного кабинета (дашборда)",
                "size_hint": "JPG/WebP, 1600×500 px, до 1 MB",
                "file": get_file_info(site.dashboard_hero_image, "img/banners/owner-dashboard-hero.webp"),
                "edit_url": reverse("admin:catalog_sitebrandingsettings_changelist"),
                "preview_url": reverse("account_profile"),
            },
            {
                "title": "Картинка пустого результата",
                "field_name": "empty_results_image",
                "location": "Отображается, когда ничего не найдено по поиску/фильтру",
                "size_hint": "PNG/WebP, 600×400 px, до 500 KB",
                "file": get_file_info(site.empty_results_image, "img/banners/listing-placeholder.webp"),
                "edit_url": reverse("admin:catalog_siteemptystatesettings_changelist"),
                "preview_url": reverse("place_list"),
            },
        ]

        # Галереи
        galleries_qs = list(SiteGalleryImage.objects.all().order_by("placement", "order", "id"))
        
        # Группируем
        hero_gallery = []
        partners_gallery = []
        for img in galleries_qs:
            info = {
                "id": img.id,
                "title": img.title_i18n(),
                "file": get_file_info(img.image),
                "edit_url": reverse("admin:catalog_sitegalleryimage_change", args=[img.id]),
                "delete_url": reverse("admin:catalog_sitegalleryimage_delete", args=[img.id]),
            }
            if img.placement == SiteGalleryImage.PLACEMENT_HOME_HERO:
                hero_gallery.append(info)
            elif img.placement == SiteGalleryImage.PLACEMENT_HOME_PARTNERS:
                partners_gallery.append(info)

        galleries = []
        if hero_gallery or not partners_gallery: # Показываем hero по умолчанию, даже если пусто
            galleries.append({
                "title": "Hero-слайдер",
                "placement": SiteGalleryImage.PLACEMENT_HOME_HERO,
                "add_url": reverse("admin:catalog_sitegalleryimage_add") + f"?placement={SiteGalleryImage.PLACEMENT_HOME_HERO}",
                "images": hero_gallery,
                "size_hint": "JPG, PNG или WebP до 2 MB",
            })
        if partners_gallery:
            galleries.append({
                "title": "Партнёры",
                "placement": SiteGalleryImage.PLACEMENT_HOME_PARTNERS,
                "add_url": reverse("admin:catalog_sitegalleryimage_add") + f"?placement={SiteGalleryImage.PLACEMENT_HOME_PARTNERS}",
                "images": partners_gallery,
                "size_hint": "PNG или SVG с прозрачным фоном, до 500 KB",
            })

        context = {
            **self.admin_site.each_context(request),
            "title": "Фото для блоков сайта",
            "opts": self.model._meta,
            "main_images": main_images,
            "galleries": galleries,
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

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["km_settings_title"] = _("Фото для галереи")
        context["km_settings_subtitle"] = _("Изображение для слайдеров или партнеров.")
        context["km_gallery_hub_url"] = reverse("admin:catalog_sitegalleryimage_changelist")
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "ajax-upload/",
                self.admin_site.admin_view(self.ajax_upload),
                name="catalog_sitegalleryimage_ajax_upload",
            ),
            path(
                "ajax-delete-main-image/",
                self.admin_site.admin_view(self.ajax_delete_main_image),
                name="catalog_sitegalleryimage_ajax_delete_main_image",
            ),
        ]
        return custom_urls + urls

    def ajax_upload(self, request):
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Only POST requests are allowed"}, status=400)
        
        image_file = request.FILES.get("image")
        placement = request.POST.get("placement")
        field_name = request.POST.get("field")
        
        if not image_file:
            return JsonResponse({"success": False, "error": "Missing image file"}, status=400)

        try:
            validate_uploaded_image(image_file)
        except ValidationError as exc:
            validation_messages = exc.messages
            return JsonResponse(
                {"success": False, "error": validation_messages[0]},
                status=400,
            )
            
        try:
            from django.template.defaultfilters import filesizeformat
            import os
            
            if field_name:
                if field_name not in self.MAIN_IMAGE_FIELDS:
                    return JsonResponse({"success": False, "error": "Invalid field name"}, status=400)
                
                site = SiteSettings.get_solo()
                setattr(site, field_name, image_file)
                site.save()
                
                # Clear singleton cache
                from catalog.models.site import clear_singleton_caches
                clear_singleton_caches()
                
                updated_field = getattr(site, field_name)
                size = filesizeformat(updated_field.size)
                name = os.path.basename(updated_field.name)
                
                return JsonResponse({
                    "success": True,
                    "field": field_name,
                    "file": {
                        "url": updated_field.url,
                        "name": name,
                        "size": size
                    }
                })
                
            if not placement:
                return JsonResponse({"success": False, "error": "Missing placement or field parameter"}, status=400)
                
            from django.db.models import Max
            
            max_order = SiteGalleryImage.objects.filter(placement=placement).aggregate(Max('order'))['order__max']
            next_order = (max_order or 0) + 1
            
            title = os.path.splitext(image_file.name)[0]
            
            instance = SiteGalleryImage.objects.create(
                placement=placement,
                image=image_file,
                order=next_order,
                is_active=True,
                title_ru=title,
            )
            
            size = filesizeformat(instance.image.size)
            
            edit_url = reverse("admin:catalog_sitegalleryimage_change", args=[instance.id])
            delete_url = reverse("admin:catalog_sitegalleryimage_delete", args=[instance.id])
            
            return JsonResponse({
                "success": True,
                "id": instance.id,
                "title": instance.title_ru,
                "file": {
                    "url": instance.image.url,
                    "name": os.path.basename(instance.image.name),
                    "size": size
                },
                "edit_url": edit_url,
                "delete_url": delete_url,
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    def ajax_delete_main_image(self, request):
        if request.method != "POST":
            return JsonResponse({"success": False, "error": "Only POST requests are allowed"}, status=400)

        field_name = request.POST.get("field")
        if field_name not in self.MAIN_IMAGE_FIELDS:
            return JsonResponse({"success": False, "error": "Invalid field name"}, status=400)

        try:
            site = SiteSettings.get_solo()
            image_field = getattr(site, field_name)
            if not image_field:
                return JsonResponse({"success": True, "field": field_name, "deleted": False})

            image_field.delete(save=False)
            setattr(site, field_name, None)
            site.save(update_fields=[field_name, "updated_at"])

            from catalog.models.site import clear_singleton_caches
            clear_singleton_caches()

            return JsonResponse({"success": True, "field": field_name, "deleted": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


@admin.register(CatalogContentSettings)
class CatalogContentSettingsAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    change_form_template = "admin/catalog/shared_settings_change_form.html"
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

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["km_settings_title"] = _("Контент и SEO")
        context["km_settings_subtitle"] = _("Настройки фильтров и SEO-данных каталога (JSON).")
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)
