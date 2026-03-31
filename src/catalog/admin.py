from django.contrib import admin, messages
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Q
from django import forms
from django.utils.html import format_html
from django.shortcuts import redirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from .models import (
    CatalogContentSettings,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
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
    SiteAnalytics,
    SiteRegisteredUser,
    StaffAccessUser,
    UserEmailVerification,
    UserProfile,
)
from .repositories.django_repositories import DjangoPlaceChangeAuditRepository
from .services.admin_analytics import build_site_analytics_context
from .services.geocoding import PlaceGeocodingService

# Clarify similar names in admin navigation.
SiteReview._meta.verbose_name = _("Отзыв о сайте")
SiteReview._meta.verbose_name_plural = _("Отзывы о сайте")
PlaceChangeAudit._meta.verbose_name_plural = _("История изменений карточек")

# Keep "Настройка сайта" as the first item in CATALOG app menu.
_original_get_app_list = admin.site.get_app_list
_original_each_context = admin.site.each_context


def _kidsmap_get_app_list(self, request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    pending_count = PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
    for app in app_list:
        if app.get("app_label") == "auth":
            app["name"] = _("Пользователи")
        if app.get("app_label") != "catalog":
            continue
        priority = {
            "sitesettings": 0,
            "siteanalytics": 1,
            "siteregistereduser": 2,
            "staffaccessuser": 3,
            "placeownershiprequest": 5,
            "place": 10,
            "placechangeaudit": 20,
            "placereview": 30,
            "sitereview": 40,
            "placereviewsbyclub": 50,
            "userprofile": 60,
            "useremailverification": 70,
        }
        display_name_overrides = {
            "sitereview": _("Отзывы о сайте"),
            "placereview": _("Отзывы по кружкам"),
            "placechangeaudit": _("История изменений карточек"),
        }
        for model in app["models"]:
            object_name = model.get("object_name", "").lower()
            if object_name in display_name_overrides:
                model["name"] = display_name_overrides[object_name]
            if object_name == "placeownershiprequest" and pending_count:
                model["name"] = _("%(name)s (на рассмотрении: %(count)s)") % {
                    "name": model["name"],
                    "count": pending_count,
                }
        app["models"].sort(key=lambda m: (priority.get(m.get("object_name", "").lower(), 999), m.get("name", "")))
    return app_list


def _kidsmap_each_context(self, request):
    context = _original_each_context(request)
    if request.user.is_authenticated and request.user.is_staff:
        context["ownership_pending_count"] = PlaceOwnershipRequest.objects.filter(
            status=PlaceOwnershipRequest.STATUS_PENDING
        ).count()
    else:
        context["ownership_pending_count"] = 0
    return context


admin.site.get_app_list = _kidsmap_get_app_list.__get__(admin.site, type(admin.site))
admin.site.each_context = _kidsmap_each_context.__get__(admin.site, type(admin.site))


User = get_user_model()


try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

try:
    admin.site.unregister(User)
except NotRegistered:
    pass


class _HiddenFromAdminIndexMixin:
    def get_model_perms(self, request):
        return {}


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    fk_name = "user"
    can_delete = False
    extra = 0
    max_num = 1
    fields = ("role", "owner_role", "owner_permissions_override", "phone", "gender", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")


class _BaseKidsMapUserAdmin(UserAdmin):
    filter_horizontal = ()
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    inlines = (UserProfileInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("profile")

    @admin.display(description=_("Статус на сайте"))
    def site_role(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_role_display() if profile else "-"

    @admin.display(description=_("Телефон"))
    def site_phone(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.phone if profile and profile.phone else "-"

    @admin.display(description=_("Пол"))
    def site_gender(self, obj):
        profile = getattr(obj, "profile", None)
        return profile.get_gender_display() if profile else "-"


@admin.register(User)
class HiddenBaseUserAdmin(_HiddenFromAdminIndexMixin, _BaseKidsMapUserAdmin):
    """
    Hidden base registration to keep default auth user admin URLs alive.
    """

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Персональная информация"), {"fields": ("first_name", "last_name", "email")}),
        (_("Права доступа"), {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
        (_("Важные даты"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active", "last_login", "date_joined")
    filter_horizontal = ("user_permissions",)


@admin.register(SiteRegisteredUser)
class SiteRegisteredUserAdmin(_BaseKidsMapUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Персональная информация"), {"fields": ("first_name", "last_name", "email")}),
        (_("Статус аккаунта"), {"fields": ("is_active",)}),
        (_("Важные даты"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_active"),
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "site_role",
        "site_phone",
        "site_gender",
        "is_active",
        "date_joined",
        "last_login",
    )
    list_filter = ("is_active", "date_joined", "last_login", "profile__role", "profile__gender")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)


@admin.register(StaffAccessUser)
class StaffAccessUserAdmin(_BaseKidsMapUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Персональная информация"), {"fields": ("first_name", "last_name", "email")}),
        (_("Права доступа"), {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
        (_("Важные даты"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_superuser",
        "is_active",
        "last_login",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "last_login", "date_joined")
    filter_horizontal = ("user_permissions",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(Q(is_staff=True) | Q(is_superuser=True))


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


class PlaceChangeAuditInline(admin.TabularInline):
    model = PlaceChangeAudit
    extra = 0
    can_delete = False
    fields = ("created_at", "changed_by", "source", "field_name", "old_value", "new_value")
    readonly_fields = fields
    ordering = ("-created_at",)

    def has_add_permission(self, request, obj=None):
        return False


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
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "lesson_duration_minutes": _("Длительность урока (мин)"),
        }


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
    )
    form = PlaceAdminForm
    geocoding_service = PlaceGeocodingService.build_default()
    place_audit_repository = DjangoPlaceChangeAuditRepository()
    list_display = (
        "display_name",
        "category",
        "event_kind",
        "district",
        "metro",
        "coordinates_status",
        "map_ready_status",
        "owner",
        "likes_count",
        "rating_avg",
        "rating_count",
        "is_active",
        "is_verified",
        "updated_at",
    )
    list_filter = (
        PlaceCoordinatesFilter,
        PlaceMapReadyFilter,
        "category",
        "is_temporary",
        "district",
        "metro",
        "owner",
        "is_active",
        "is_verified",
        "age_from",
        "age_to",
    )
    search_fields = ("name_ru", "name_en", "name", "address", "instagram", "phone1", "owner__username", "owner__email")
    list_editable = ("is_active", "is_verified", "likes_count")
    readonly_fields = (
        "slug",
        "rating_avg",
        "rating_count",
        "coordinates_status_display",
        "map_ready_status_display",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_per_page = 30
    save_on_top = True
    actions = ("mark_active", "mark_inactive", "mark_verified", "mark_unverified", "refresh_coordinates")
    inlines = [PlacePhotoInline, PlaceReviewInline, PlaceChangeAuditInline]
    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "name",
                    "slug",
                    "category",
                    "subcategory",
                    "is_temporary",
                    "temporary_start",
                    "temporary_end",
                    "is_active",
                    "is_verified",
                    "owner",
                    "likes_count",
                    "rating_avg",
                    "rating_count",
                )
            },
        ),
        (_("Названия и описания (i18n)"), {"classes": ("collapse",), "fields": ("name_ru", "name_az", "name_en", "description_ru", "description_az", "description_en")}),
        (
            _("Возраст и цена"),
            {
                "fields": (
                    "age_from",
                    "age_to",
                    "price_from",
                    "price_to",
                    "price_per_lesson",
                    "price_per_month",
                    "price_per_8_lessons",
                    "lesson_duration_minutes",
                )
            },
        ),
        (_("Локация"), {"fields": ("district", "metro", "address", "lat", "lng", "coordinates_status_display", "map_ready_status_display")}),
        (_("Контакты"), {"fields": ("phone1", "instagram", "website", "schedule", "extra_conditions", "additional_info")}),
        (_("Фото"), {"fields": ("cover_photo", "photo")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        return obj.name_ru or obj.name

    @admin.display(description=_("Формат"))
    def event_kind(self, obj):
        return _("Временное") if obj.is_temporary else _("Постоянное")

    def _render_place_state_badge(self, *, label: str, positive: bool):
        bg = "#e7f8ed" if positive else "#eef2f7"
        fg = "#17663d" if positive else "#49515a"
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;border-radius:999px;background:{};color:{};font-weight:600;">{}</span>',
            bg,
            fg,
            label,
        )

    @admin.display(description=_("Координаты"))
    def coordinates_status(self, obj):
        return self._render_place_state_badge(
            label=_("Есть координаты") if obj.has_coordinates else _("Нужны координаты"),
            positive=obj.has_coordinates,
        )

    @admin.display(description=_("Координаты"))
    def coordinates_status_display(self, obj):
        return self.coordinates_status(obj)

    @admin.display(description=_("На карте"))
    def map_ready_status(self, obj):
        return self._render_place_state_badge(
            label=_("Готово для карты") if obj.is_map_ready else _("Не готово для карты"),
            positive=obj.is_map_ready,
        )

    @admin.display(description=_("На карте"))
    def map_ready_status_display(self, obj):
        return self.map_ready_status(obj)

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
            previous_coordinates = {"lat": place.lat, "lng": place.lng}
            geocoding_result = self.geocoding_service.geocode_place(place=place, overwrite=True)
            if geocoding_result.updated:
                updated_count += 1
                coordinate_changes: dict[str, tuple[object, object]] = {}
                for field_name in ("lat", "lng"):
                    old_value = previous_coordinates[field_name]
                    new_value = getattr(place, field_name)
                    if old_value != new_value:
                        coordinate_changes[field_name] = (old_value, new_value)
                if coordinate_changes:
                    self.place_audit_repository.create_entries(
                        place=place,
                        changed_by=request.user,
                        source=PlaceChangeAudit.SOURCE_SYSTEM,
                        changes=coordinate_changes,
                    )
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

    def _stringify_audit_value(self, value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def save_model(self, request, obj, form, change):
        old_values = {}
        if change and obj.pk:
            old_obj = Place.objects.filter(pk=obj.pk).first()
            if old_obj:
                for field in self.AUDIT_TRACKED_FIELDS:
                    old_values[field] = getattr(old_obj, field)

        super().save_model(request, obj, form, change)

        if change and old_values:
            audit_entries = []
            for field_name in self.AUDIT_TRACKED_FIELDS:
                old_value = old_values.get(field_name)
                new_value = getattr(obj, field_name)
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


@admin.register(PlaceReview)
class PlaceReviewAdmin(admin.ModelAdmin):
    list_display = ("place", "display_author", "rating", "likes_count", "dislikes_count", "contains_profanity", "created_at")
    list_filter = ("rating", "is_anonymous", "contains_profanity", "created_at")
    search_fields = ("place__name_ru", "place__name_en", "place__name_az", "author_name", "text")
    readonly_fields = ("likes_count", "dislikes_count", "contains_profanity", "created_at", "updated_at", "session_key")
    exclude = ("is_approved",)

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

    def save_model(self, request, obj, form, change):
        obj.is_approved = True
        super().save_model(request, obj, form, change)


@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = ("display_author", "rating", "likes_count", "dislikes_count", "contains_profanity", "created_at")
    list_filter = ("rating", "is_anonymous", "contains_profanity", "created_at")
    search_fields = ("author_name", "text")
    readonly_fields = ("likes_count", "dislikes_count", "contains_profanity", "created_at", "updated_at", "session_key")
    exclude = ("is_approved",)

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

    def save_model(self, request, obj, form, change):
        obj.is_approved = True
        super().save_model(request, obj, form, change)


class UserProfileAccessLevelFilter(admin.SimpleListFilter):
    title = _("Уровень доступа")
    parameter_name = "access_level"

    def lookups(self, request, model_admin):
        return (
            ("superadmin", _("Суперадмин")),
            ("admin", _("Админ")),
            ("owner", _("Владелец")),
            ("user", _("Пользователь")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "superadmin":
            return queryset.filter(user__is_superuser=True)
        if value == "admin":
            return queryset.filter(user__is_staff=True, user__is_superuser=False)
        if value == "owner":
            return queryset.filter(role=UserProfile.ROLE_OWNER, user__is_staff=False, user__is_superuser=False)
        if value == "user":
            return queryset.filter(role=UserProfile.ROLE_USER, user__is_staff=False, user__is_superuser=False)
        return queryset


class UserProfileOwnerRoleFilter(admin.SimpleListFilter):
    title = _("Роль владельца")
    parameter_name = "owner_role_localized"

    ROLE_LABELS = {
        UserProfile.OWNER_ROLE_MANAGER: _("Менеджер владельца"),
        UserProfile.OWNER_ROLE_MODERATOR: _("Модератор владельца"),
        UserProfile.OWNER_ROLE_EDITOR: _("Редактор владельца"),
    }

    def lookups(self, request, model_admin):
        return tuple((value, label) for value, label in self.ROLE_LABELS.items())

    def queryset(self, request, queryset):
        value = self.value()
        if value in self.ROLE_LABELS:
            return queryset.filter(owner_role=value)
        return queryset


@admin.register(UserProfile)
class UserProfileAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "access_level",
        "phone",
        "gender",
        "role",
        "owner_role_display",
        "owner_permissions_preview",
        "created_at",
        "updated_at",
    )
    list_filter = (UserProfileAccessLevelFilter, UserProfileOwnerRoleFilter, "gender", "role", "created_at")
    search_fields = ("user__username", "user__email", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Пользователь"), {"fields": ("user", "phone", "gender")}),
        (_("Роли"), {"fields": ("role", "owner_role")}),
        (_("Гранулярные права владельца"), {"fields": ("owner_permissions_override",)}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Уровень доступа"))
    def access_level(self, obj):
        if obj.user.is_superuser:
            return _("Суперадмин")
        if obj.user.is_staff:
            return _("Админ")
        if obj.role == UserProfile.ROLE_OWNER:
            return _("Владелец")
        return _("Пользователь")

    @admin.display(description=_("Роль владельца"))
    def owner_role_display(self, obj):
        if obj.role != UserProfile.ROLE_OWNER:
            return "-"
        labels = {
            UserProfile.OWNER_ROLE_MANAGER: _("Менеджер владельца"),
            UserProfile.OWNER_ROLE_MODERATOR: _("Модератор владельца"),
            UserProfile.OWNER_ROLE_EDITOR: _("Редактор владельца"),
        }
        return labels.get(obj.owner_role, obj.get_owner_role_display())

    @admin.display(description=_("Права владельца"))
    def owner_permissions_preview(self, obj):
        labels_by_code = {code: label for code, label in UserProfile.OWNER_PERMISSION_CHOICES}
        permissions = sorted(str(labels_by_code.get(code, code)) for code in obj.get_owner_permissions())
        if not permissions:
            return "-"
        return ", ".join(permissions)


@admin.register(UserEmailVerification)
class UserEmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "is_verified", "attempts_left", "expires_at", "resend_available_at", "updated_at")
    list_filter = ("is_verified",)
    search_fields = ("user__username", "user__email", "email")
    readonly_fields = ("created_at", "updated_at", "verified_at")


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


@admin.register(PlaceChangeAudit)
class PlaceChangeAuditAdmin(admin.ModelAdmin):
    list_display = ("place", "field_name", "changed_by", "source", "created_at")
    list_filter = ("source", "field_name", "created_at")
    search_fields = ("place__name_ru", "place__name_en", "place__name_az", "changed_by__username", "field_name", "old_value", "new_value")
    readonly_fields = ("place", "changed_by", "source", "field_name", "old_value", "new_value", "created_at")
    autocomplete_fields = ("place", "changed_by")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
    list_display = (
        "id",
        "place",
        "applicant",
        "status_badge",
        "created_at",
        "moderated_at_display",
        "moderated_by_display",
        "moderation_actions",
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
    readonly_fields = ("status", "note", "moderation_actions", "created_at", "updated_at", "moderated_at", "moderated_by")
    autocomplete_fields = ("place", "applicant", "moderated_by")
    actions = ("approve_requests", "reject_requests")
    inlines = (PlaceOwnershipRequestAuditInline,)
    fieldsets = (
        (_("Заявка"), {"fields": ("place", "applicant", "status", "note")}),
        (_("Модерация"), {"fields": ("moderation_note", "moderation_actions", "moderated_by", "moderated_at")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

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
            PlaceOwnershipRequest.STATUS_PENDING: ("#ffefcc", "#8a5a00"),
            PlaceOwnershipRequest.STATUS_APPROVED: ("#e7f8ed", "#17663d"),
            PlaceOwnershipRequest.STATUS_REJECTED: ("#fde8e8", "#9b1c1c"),
        }
        bg, fg = palette.get(obj.status, ("#eef2f7", "#243447"))
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;border-radius:999px;background:{};color:{};font-weight:600;">{}</span>',
            bg,
            fg,
            obj.get_status_display(),
        )

    @admin.display(description=_("Дата решения"))
    def moderated_at_display(self, obj):
        return obj.moderated_at or "-"

    @admin.display(description=_("Кто проверил"))
    def moderated_by_display(self, obj):
        return obj.moderated_by or "-"

    @admin.display(description=_("Действия"))
    def moderation_actions(self, obj):
        if not obj or not obj.pk:
            return "-"
        if not obj.is_pending:
            return _("Заявка уже обработана")
        approve_url = reverse("admin:catalog_placeownershiprequest_approve", args=[obj.pk])
        reject_url = reverse("admin:catalog_placeownershiprequest_reject", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}">{}</a>&nbsp;'
            '<a class="button" href="{}" style="background:#ba2121;color:#fff;">{}</a>',
            approve_url,
            _("Принять"),
            reject_url,
            _("Отклонить"),
        )

    def changelist_view(self, request, extra_context=None):
        pending_count = PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
        if pending_count:
            self.message_user(
                request,
                _("Ожидают проверки заявок на владение: %(count)s") % {"count": pending_count},
                level=messages.WARNING,
            )
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
    autocomplete_fields = ("ownership_request", "actor")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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

    def changelist_view(self, request, extra_context=None):
        obj = CatalogContentSettings.get_solo()
        opts = self.model._meta
        return redirect(reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk]))
