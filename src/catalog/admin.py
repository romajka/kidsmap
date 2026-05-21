from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django import forms
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils.formats import date_format
from django.utils.html import format_html, format_html_join
from django.utils.dateparse import parse_datetime
from django.shortcuts import redirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _, ngettext
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
    SiteGalleryImage,
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
from .services.content_quality import place_quality_check, review_quality_check
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
    pending_count = (
        Place.objects.filter(status=Place.STATUS_PENDING, deleted_at__isnull=True).count()
        + PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
    )
    for app in app_list:
        if app.get("app_label") == "auth":
            app["name"] = _("Пользователи")
        if app.get("app_label") != "catalog":
            continue
        priority = {
            "sitesettings": 0,
            "siteanalytics": 1,
            "sitegalleryimage": 2,
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
        context["ownership_pending_count"] = (
            Place.objects.filter(status=Place.STATUS_PENDING, deleted_at__isnull=True).count()
            + PlaceOwnershipRequest.objects.filter(status=PlaceOwnershipRequest.STATUS_PENDING).count()
        )
    else:
        context["ownership_pending_count"] = 0
    context["admin_current_language"] = (get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    context["admin_language_switch_items"] = _build_admin_language_switch_items(request, context["admin_current_language"])
    return context


def _build_admin_language_switch_items(request, current_language: str):
    lang_codes = [code for code, _label in settings.LANGUAGES]
    default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
    path = request.path
    stripped = path.lstrip("/")
    first_segment, sep, remainder = stripped.partition("/")
    if first_segment in lang_codes:
        base_path = f"/{remainder}" if sep else "/"
    else:
        base_path = path if path.startswith("/") else f"/{path}"

    if not base_path:
        base_path = "/"

    items = []
    for code in lang_codes:
        url = request.build_absolute_uri(base_path if code == default_lang else f"/{code}{base_path}")
        items.append({"code": code, "url": url, "active": code == current_language})
    return items


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
    search_fields = ("username", "email", "first_name", "last_name", "profile__phone")
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

    @admin.display(description=_("Профиль"))
    def identity_summary(self, obj):
        profile = getattr(obj, "profile", None)
        title = obj.username or "-"
        details: list[str] = []

        full_name = " ".join(part for part in (obj.first_name, obj.last_name) if part).strip()
        if obj.email:
            details.append(obj.email)
        if full_name:
            details.append(full_name)

        if not details:
            return format_html('<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>', title)

        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div>',
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((detail,) for detail in details)),
        )


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
    list_display = ("identity_summary", "site_role", "site_phone", "site_gender", "is_active", "date_joined", "last_login")
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
        "identity_summary",
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


class ReviewModerationStatusFilter(admin.SimpleListFilter):
    title = _("Статус модерации")
    parameter_name = "review_status"

    def lookups(self, request, model_admin):
        return (
            ("published", _("Опубликован")),
            ("hidden", _("Скрыт")),
            ("suspicious", _("Требует проверки")),
            ("only_rating", _("Только оценка")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "published":
            return queryset.filter(is_approved=True, contains_profanity=False)
        if value == "hidden":
            return queryset.filter(is_approved=False)
        if value == "suspicious":
            return queryset.filter(Q(contains_profanity=True) | Q(is_approved=False, dislikes_count__gt=0))
        if value == "only_rating":
            return queryset.filter(Q(text__isnull=True) | Q(text__exact=""))
        return queryset


class ReviewTextPresenceFilter(admin.SimpleListFilter):
    title = _("Текст")
    parameter_name = "text_presence"

    def lookups(self, request, model_admin):
        return (
            ("with_text", _("Есть текст")),
            ("only_rating", _("Только оценка")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "with_text":
            return queryset.exclude(text__isnull=True).exclude(text__exact="")
        if value == "only_rating":
            return queryset.filter(Q(text__isnull=True) | Q(text__exact=""))
        return queryset


class ReviewRiskFilter(admin.SimpleListFilter):
    title = _("Сигналы риска")
    parameter_name = "risk_signal"

    def lookups(self, request, model_admin):
        return (
            ("profanity", _("Есть скрытая лексика")),
            ("anonymous", _("Анонимный")),
            ("low_rating", _("Низкая оценка")),
            ("many_dislikes", _("Много дизлайков")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "profanity":
            return queryset.filter(contains_profanity=True)
        if value == "anonymous":
            return queryset.filter(is_anonymous=True)
        if value == "low_rating":
            return queryset.filter(rating__lte=2)
        if value == "many_dislikes":
            return queryset.filter(dislikes_count__gt=0)
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
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_per_page = 30
    save_on_top = True
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
                    "slug",
                    "category",
                    "subcategory",
                    "is_temporary",
                    "temporary_start",
                    "temporary_end",
                    "is_active",
                    "is_verified",
                    "status",
                    "rejection_reason",
                    "last_verified_at",
                    "published_at",
                    "owner",
                    "likes_count",
                    "rating_avg",
                    "rating_count",
                    "lifecycle_status_display",
                    "quality_status_display",
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
        (_("Удаление"), {"classes": ("collapse",), "fields": ("deleted_at", "deleted_by")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_ru or obj.name
        meta: list[str] = []
        if obj.slug:
            meta.append(f"ID {obj.pk} · /{obj.slug}/")
        else:
            meta.append(f"ID {obj.pk}")
        if obj.is_deleted:
            meta.append(str(_("Сейчас скрыта в разделе удалённых")))
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div>',
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
            self.lifecycle_status(obj),
        ]
        badges.append(
            self._render_place_state_badge(
                label=_("Проверено") if obj.is_verified else _("Без проверки"),
                tone="good" if obj.is_verified else "warn",
            )
        )
        badges.append(
            self._render_place_state_badge(
                label=_("Временное") if obj.is_temporary else _("Постоянное"),
                tone="info" if obj.is_temporary else "muted",
            )
        )
        return format_html(
            '<div class="km-admin-stack"><div class="km-admin-badges">{} {} {} {}</div></div>',
            badges[0],
            badges[1],
            badges[2],
            badges[3],
        )

    @admin.display(description=_("Карта"))
    def map_status_summary(self, obj):
        coords_line = _("lat %(lat)s, lng %(lng)s") % {"lat": round(obj.lat, 5), "lng": round(obj.lng, 5)} if obj.has_coordinates else _("Координаты не заполнены")
        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">{} {}</div>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            self.coordinates_status(obj),
            self.map_ready_status(obj),
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

    def _place_quick_filters(self, request):
        status_keys = ("deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")
        current_deleted = request.GET.get("deleted_state")
        current_active = request.GET.get("is_active__exact")
        current_coordinates = request.GET.get("coordinates_status")
        current_map_ready = request.GET.get("map_ready_status")
        current_status = request.GET.get("status__exact")
        return (
            {
                "label": _("Все карточки"),
                "url": self._build_changelist_query_string(request, clear=status_keys),
                "active": not any((current_deleted, current_active, current_coordinates, current_map_ready, current_status)),
            },
            {
                "label": _("Опубликованы"),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="1",
                ),
                "active": current_deleted == "active" and current_active == "1" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Неактивные"),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="0",
                ),
                "active": current_deleted == "active" and current_active == "0" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Черновики"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_DRAFT),
                "active": current_status == Place.STATUS_DRAFT and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("На модерации"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_PENDING),
                "active": current_status == Place.STATUS_PENDING and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("Отклонены"),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_REJECTED),
                "active": current_status == Place.STATUS_REJECTED and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "label": _("В удалённых"),
                "url": self._build_changelist_query_string(request, clear=status_keys, deleted_state="deleted"),
                "active": current_deleted == "deleted" and not current_active and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "label": _("Без координат"),
                "url": self._build_changelist_query_string(request, clear=status_keys, coordinates_status="no"),
                "active": current_coordinates == "no" and not current_deleted and not current_active and not current_map_ready and not current_status,
            },
            {
                "label": _("Не готовы для карты"),
                "url": self._build_changelist_query_string(request, clear=status_keys, map_ready_status="no"),
                "active": current_map_ready == "no" and not current_deleted and not current_active and not current_coordinates and not current_status,
            },
        )

    def _place_bulk_actions(self):
        return (
            {
                "name": "mark_active",
                "label": _("Опубликовать"),
                "tone": "good",
                "description": _("Сделать выбранные карточки активными и вернуть их в каталог."),
            },
            {
                "name": "mark_inactive",
                "label": _("Снять с публикации"),
                "tone": "muted",
                "description": _("Оставить карточки в базе, но скрыть их с сайта."),
            },
            {
                "name": "mark_verified",
                "label": _("Отметить проверенными"),
                "tone": "info",
                "description": _("Показать, что карточки прошли проверку."),
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

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/restore/",
                self.admin_site.admin_view(self.restore_view),
                name="catalog_place_restore",
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "place_quick_filters": self._place_quick_filters(request),
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
        updated_count = queryset.update(is_verified=True, updated_at=timezone.now())
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
        for place in queryset.prefetch_related("gallery").iterator():
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

    def response_add(self, request, obj, post_url_continue=None):
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Карточка сохранена."),
            )
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Изменения сохранены."),
            )
        return super().response_change(request, obj)

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = self._place_change_url(obj)
        action_links = [
            format_html(
                '<a class="km-admin-action km-admin-action--primary" href="{}">{}</a>',
                edit_url,
                _("Редактировать"),
            )
        ]
        if obj.is_deleted:
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--good" href="{}">{}</a>',
                    self._place_restore_url(obj),
                    _("Восстановить"),
                )
            )
            action_links.append(
                format_html('<span class="km-admin-action km-admin-action--muted">{}</span>', _("В каталоге скрыта"))
            )
        else:
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--secondary" href="{}" target="_blank" rel="noopener">{}</a>',
                    obj.get_absolute_url(),
                    _("Открыть"),
                )
            )
            action_links.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--danger" href="{}">{}</a>',
                    self._place_delete_url(obj),
                    _("В удалённые"),
                )
            )
        return format_html('<div class="km-place-row-actions">{}</div>', format_html_join("", "{}", ((link,) for link in action_links)))


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
    list_filter = ("category", "is_active")
    search_fields = ("title_ru", "title_az", "title_en", "image")
    list_editable = ("placement", "category", "order", "is_active")
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
        return super().changelist_view(request, extra_context=extra_context)

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


@admin.register(PlaceReview)
class PlaceReviewAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placereview/change_list.html"
    change_form_template = "admin/catalog/placereview/change_form.html"
    list_select_related = ("place", "user")
    list_display = (
        "review_summary",
        "author_summary",
        "rating_summary",
        "moderation_status_summary",
        "risk_flags_summary",
        "engagement_summary",
        "created_at_display",
        "row_actions",
    )
    list_filter = (
        ReviewModerationStatusFilter,
        ReviewTextPresenceFilter,
        ReviewRiskFilter,
        "rating",
        "is_anonymous",
        "contains_profanity",
        "is_approved",
        "status",
        "place",
        "created_at",
    )
    search_fields = ("place__name_ru", "place__name_en", "place__name_az", "author_name", "user__username", "user__email", "text")
    readonly_fields = (
        "moderation_status_summary",
        "likes_count",
        "dislikes_count",
        "contains_profanity",
        "popularity_score_display",
        "created_at",
        "updated_at",
        "session_key",
    )
    actions = ("approve_selected", "hide_selected", "reject_selected", "delete_selected")
    fieldsets = (
        (_("Отзыв"), {"fields": ("place", "user", "author_name", "is_anonymous", "rating", "text")}),
        (_("Модерация"), {"fields": ("status", "is_approved", "rejection_reason", "contains_profanity", "moderation_status_summary")}),
        (_("Реакции"), {"fields": ("likes_count", "dislikes_count", "popularity_score_display")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("session_key", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("place", "user")

    def _review_has_text(self, obj) -> bool:
        return bool((obj.text or "").strip())

    def _render_review_badge(self, *, label: str, tone: str = "muted"):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            tone,
            label,
        )

    def _place_admin_change_url(self, obj) -> str:
        return reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name)

    def _review_change_url(self, obj) -> str:
        return reverse("admin:catalog_placereview_change", args=[obj.pk], current_app=self.admin_site.name)

    def _review_delete_url(self, obj) -> str:
        return reverse("admin:catalog_placereview_delete", args=[obj.pk], current_app=self.admin_site.name)

    def _review_action_url(self, obj, action: str) -> str:
        return reverse(f"admin:catalog_placereview_{action}", args=[obj.pk], current_app=self.admin_site.name)

    def _review_preview_text(self, obj) -> str:
        text = (obj.text or "").strip()
        if not text:
            return str(_("Только оценка без комментария"))
        if len(text) <= 180:
            return text
        return f"{text[:177].rstrip()}..."

    def _review_status(self, obj) -> tuple[str, str]:
        if obj.status == obj.STATUS_REJECTED:
            return str(_("Отклонен")), "danger"
        if obj.status == obj.STATUS_PENDING:
            return str(_("На модерации")), "warn"
        if not obj.is_approved:
            return str(_("Скрыт")), "muted"
        if obj.contains_profanity:
            return str(_("Требует проверки")), "warn"
        return str(_("Опубликован")), "good"

    @admin.display(description=_("Отзыв"))
    def review_summary(self, obj):
        place_name = obj.place.name_ru or obj.place.name
        preview = self._review_preview_text(obj)
        return format_html(
            '<div class="km-admin-stack">'
            '<a class="km-review-place-link" href="{}">{}</a>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            self._place_admin_change_url(obj),
            place_name,
            preview,
        )

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

    @admin.display(description=_("Автор"))
    def author_summary(self, obj):
        badges = []
        if obj.is_anonymous:
            badges.append(self._render_review_badge(label=_("Анонимный"), tone="muted"))
        if obj.user_id:
            badges.append(self._render_review_badge(label=_("Есть аккаунт"), tone="info"))
        name = self.display_author(obj)
        meta = obj.user.email if obj.user_id and obj.user.email else (obj.user.username if obj.user_id else _("Гость"))
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span><div class="km-admin-badges">{}</div></div>',
            name,
            meta,
            format_html_join("", "{}", ((badge,) for badge in badges)),
        )

    @admin.display(description=_("Рейтинг"))
    def rating_summary(self, obj):
        tone = "warn" if obj.rating <= 2 else "info" if obj.rating == 3 else "good"
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-badge km-admin-badge--{}">★ {}</span>{}</div>',
            tone,
            obj.rating,
            format_html(
                '<span class="km-admin-meta">{}</span>',
                _("Только оценка") if not self._review_has_text(obj) else _("Есть комментарий"),
            ),
        )

    @admin.display(description=_("Статус"))
    def moderation_status_summary(self, obj):
        label, tone = self._review_status(obj)
        help_text = _("Виден на сайте") if obj.is_approved else _("На сайте скрыт")
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-badge km-admin-badge--{}">{}</span><span class="km-admin-meta">{}</span></div>',
            tone,
            label,
            help_text,
        )

    @admin.display(description=_("Риски"))
    def risk_flags_summary(self, obj):
        flags = []
        quality = review_quality_check(obj)
        if obj.contains_profanity:
            flags.append(self._render_review_badge(label=_("Есть скрытая лексика"), tone="warn"))
        if not quality.is_ready:
            flags.append(self._render_review_badge(label=_("Низкое качество"), tone="warn"))
        if obj.is_anonymous:
            flags.append(self._render_review_badge(label=_("Анонимный"), tone="muted"))
        if not self._review_has_text(obj):
            flags.append(self._render_review_badge(label=_("Только оценка"), tone="info"))
        if obj.rating <= 2:
            flags.append(self._render_review_badge(label=_("Низкая оценка"), tone="warn"))
        if obj.dislikes_count > obj.likes_count:
            flags.append(self._render_review_badge(label=_("Много дизлайков"), tone="warn"))
        if not flags:
            flags.append(self._render_review_badge(label=_("Без сигналов риска"), tone="good"))
        return format_html('<div class="km-admin-badges">{}</div>', format_html_join("", "{}", ((flag,) for flag in flags)))

    @admin.display(description=_("Реакции"))
    def engagement_summary(self, obj):
        balance_value = f"{int(obj.popularity_score or 0):+d}"
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">👍 {} · 👎 {}</span><span class="km-admin-meta">{} {}</span></div>',
            int(obj.likes_count or 0),
            int(obj.dislikes_count or 0),
            _("Баланс:"),
            balance_value,
        )

    @admin.display(description=_("Создан"))
    def created_at_display(self, obj):
        return obj.created_at

    @admin.display(description=_("Баланс реакций"))
    def popularity_score_display(self, obj):
        return obj.popularity_score

    def _build_review_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
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

    def _review_quick_filters(self, request):
        keys = ("review_status", "risk_signal", "text_presence", "rating__exact")
        current_status = request.GET.get("review_status")
        current_risk = request.GET.get("risk_signal")
        current_text = request.GET.get("text_presence")
        current_rating = request.GET.get("rating__exact")
        return (
            {"label": _("Все отзывы"), "url": self._build_review_changelist_query_string(request, clear=keys), "active": not any((current_status, current_risk, current_text, current_rating))},
            {"label": _("Опубликованы"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="published"), "active": current_status == "published"},
            {"label": _("Скрытые"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="hidden"), "active": current_status == "hidden"},
            {"label": _("Требуют проверки"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="suspicious"), "active": current_status == "suspicious"},
            {"label": _("Только оценка"), "url": self._build_review_changelist_query_string(request, clear=keys, text_presence="only_rating"), "active": current_text == "only_rating"},
            {"label": _("Низкая оценка"), "url": self._build_review_changelist_query_string(request, clear=keys, risk_signal="low_rating"), "active": current_risk == "low_rating"},
        )

    def _review_bulk_actions(self):
        return (
            {"name": "approve_selected", "label": _("Опубликовать"), "tone": "good", "description": _("Сделать выбранные отзывы видимыми на сайте.")},
            {"name": "hide_selected", "label": _("Скрыть"), "tone": "muted", "confirm": _("Вы собираетесь скрыть {count} выбранных отзывов.\n\nОтзывы останутся в базе и их можно будет снова опубликовать.\n\nПродолжить?"), "description": _("Скрыть отзывы с сайта без удаления.")},
            {"name": "reject_selected", "label": _("Отклонить"), "tone": "warn", "confirm": _("Вы собираетесь отклонить {count} выбранных отзывов.\n\nОтзывы останутся в базе как скрытые, их можно будет позже опубликовать вручную.\n\nПродолжить?"), "description": _("Скрыть отзывы как отклонённые после модерации.")},
            {"name": "delete_selected", "label": _("Удалить"), "tone": "danger", "confirm": _("Вы собираетесь удалить {count} выбранных отзывов.\n\nЭто действие удалит отзывы из базы после стандартного экрана подтверждения Django admin.\n\nПродолжить?"), "description": _("Полное удаление отзывов из базы.")},
        )

    def get_urls(self):
        custom_urls = [
            path("<path:object_id>/approve/", self.admin_site.admin_view(self.approve_view), name="catalog_placereview_approve"),
            path("<path:object_id>/hide/", self.admin_site.admin_view(self.hide_view), name="catalog_placereview_hide"),
            path("<path:object_id>/reject/", self.admin_site.admin_view(self.reject_view), name="catalog_placereview_reject"),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "review_quick_filters": self._review_quick_filters(request),
            "review_bulk_actions": self._review_bulk_actions(),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def _message_for_single_review_action(self, *, request, obj, action_key: str):
        messages_map = {
            "approve": _("Отзыв опубликован и виден на сайте."),
            "hide": _("Отзыв скрыт. Его можно снова опубликовать позже."),
            "reject": _("Отзыв отклонён и скрыт. При необходимости его можно снова опубликовать."),
        }
        self.message_user(request, messages_map[action_key], level=messages.SUCCESS)

    def _toggle_review_visibility(self, *, obj, is_approved: bool, rejected: bool = False):
        target_status = obj.STATUS_APPROVED if is_approved else (obj.STATUS_REJECTED if rejected else obj.STATUS_PENDING)
        if obj.is_approved == is_approved and obj.status == target_status:
            return False
        obj.status = target_status
        obj.is_approved = is_approved
        obj.save(update_fields=["status", "is_approved", "updated_at"])
        return True

    def approve_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=True)
            self._message_for_single_review_action(request=request, obj=obj, action_key="approve")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Опубликовать отзыв"),
            "action_label": _("Опубликовать"),
            "action_key": "approve",
            "description": _("Отзыв станет снова виден на сайте."),
            "object": obj,
            "opts": self.opts,
        })

    def hide_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=False)
            self._message_for_single_review_action(request=request, obj=obj, action_key="hide")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Скрыть отзыв"),
            "action_label": _("Скрыть"),
            "action_key": "hide",
            "description": _("Отзыв исчезнет с сайта, но останется в базе и его можно будет снова опубликовать."),
            "object": obj,
            "opts": self.opts,
        })

    def reject_view(self, request, object_id):
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=False, rejected=True)
            self._message_for_single_review_action(request=request, obj=obj, action_key="reject")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Отклонить отзыв"),
            "action_label": _("Отклонить"),
            "action_key": "reject",
            "description": _("Отзыв останется в базе как скрытый. Это решение можно будет изменить позже."),
            "object": obj,
            "opts": self.opts,
        })

    @admin.action(description=_("Опубликовать выбранные отзывы"))
    def approve_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=True, status=PlaceReview.STATUS_APPROVED).update(is_approved=True, status=PlaceReview.STATUS_APPROVED, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Опубликован %(count)d отзыв.", "Опубликовано %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Скрыть выбранные отзывы"))
    def hide_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=False, status=PlaceReview.STATUS_PENDING).update(is_approved=False, status=PlaceReview.STATUS_PENDING, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Скрыт %(count)d отзыв.", "Скрыто %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить выбранные отзывы"))
    def reject_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=False, status=PlaceReview.STATUS_REJECTED).update(is_approved=False, status=PlaceReview.STATUS_REJECTED, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Отклонён %(count)d отзыв.", "Отклонено %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        actions = [
            format_html('<a class="km-admin-action km-admin-action--primary" href="{}">{}</a>', self._review_change_url(obj), _("Открыть")),
            format_html('<a class="km-admin-action km-admin-action--secondary" href="{}">{}</a>', self._place_admin_change_url(obj), _("К кружку")),
        ]
        if obj.is_approved:
            actions.append(format_html('<a class="km-admin-action km-admin-action--muted" href="{}">{}</a>', self._review_action_url(obj, "hide"), _("Скрыть")))
        else:
            actions.append(format_html('<a class="km-admin-action km-admin-action--good" href="{}">{}</a>', self._review_action_url(obj, "approve"), _("Опубликовать")))
            actions.append(format_html('<a class="km-admin-action km-admin-action--warn" href="{}">{}</a>', self._review_action_url(obj, "reject"), _("Отклонить")))
        actions.append(format_html('<a class="km-admin-action km-admin-action--danger" href="{}">{}</a>', self._review_delete_url(obj), _("Удалить")))
        return format_html('<div class="km-place-row-actions">{}</div>', format_html_join("", "{}", ((action,) for action in actions)))


@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = ("display_author", "rating", "status", "is_approved", "likes_count", "dislikes_count", "contains_profanity", "created_at")
    list_filter = ("status", "is_approved", "rating", "is_anonymous", "contains_profanity", "created_at")
    search_fields = ("author_name", "text")
    readonly_fields = ("likes_count", "dislikes_count", "contains_profanity", "created_at", "updated_at", "session_key")
    fieldsets = (
        (_("Отзыв"), {"fields": ("user", "author_name", "is_anonymous", "rating", "text")}),
        (_("Модерация"), {"fields": ("status", "is_approved", "rejection_reason", "contains_profanity")}),
        (_("Реакции"), {"fields": ("likes_count", "dislikes_count")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("session_key", "created_at", "updated_at")}),
    )

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        if obj.is_anonymous:
            return _("Аноним")
        return obj.author_name or _("Без имени")

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


class PlaceChangeTypeFilter(admin.SimpleListFilter):
    title = _("Тип изменения")
    parameter_name = "change_kind"

    GROUPS = {
        "delete": (_("Удаление / восстановление"), {"deleted_at", "deleted_by_id"}),
        "publication": (_("Публикация"), {"is_active"}),
        "verification": (_("Проверка"), {"is_verified"}),
        "location": (_("Локация"), {"lat", "lng", "district", "metro", "address"}),
        "contacts": (_("Контакты"), {"phone1", "instagram", "website", "schedule"}),
        "photos": (_("Фото"), {"cover_photo", "photo"}),
        "owner": (_("Владелец"), {"owner_id"}),
        "content": (
            _("Данные карточки"),
            {
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
                "price_from",
                "price_to",
                "price_per_lesson",
                "price_per_month",
                "price_per_8_lessons",
                "lesson_duration_minutes",
                "extra_conditions",
                "additional_info",
                "is_temporary",
                "temporary_start",
                "temporary_end",
            },
        ),
    }

    def lookups(self, request, model_admin):
        return tuple((key, label) for key, (label, _field_names) in self.GROUPS.items())

    def queryset(self, request, queryset):
        value = self.value()
        if not value:
            return queryset
        group = self.GROUPS.get(value)
        if not group:
            return queryset
        _label, field_names = group
        return queryset.filter(field_name__in=field_names)


@admin.register(PlaceChangeAudit)
class PlaceChangeAuditAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placechangeaudit/change_list.html"
    list_select_related = ("place", "changed_by")
    date_hierarchy = "created_at"
    list_display = ("place_summary", "change_summary", "changed_by_summary", "source_badge", "created_at_display", "row_actions")
    list_display_links = None
    list_filter = (PlaceChangeTypeFilter, "source", "changed_by", "place", "created_at")
    search_fields = (
        "place__name_ru",
        "place__name_en",
        "place__name_az",
        "place__slug",
        "changed_by__username",
        "changed_by__email",
        "field_name",
        "old_value",
        "new_value",
    )
    readonly_fields = ("place", "changed_by", "source", "field_name", "old_value", "new_value", "created_at")
    autocomplete_fields = ("place", "changed_by")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def _truthy_audit_value(value) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on", "да", "y"}

    @staticmethod
    def _audit_display_value(value) -> str:
        if value is None:
            return "—"
        text = str(value).strip()
        if not text:
            return "—"
        parsed_dt = parse_datetime(text)
        if parsed_dt is not None:
            if timezone.is_naive(parsed_dt):
                return date_format(parsed_dt, "d.m.Y H:i")
            return date_format(timezone.localtime(parsed_dt), "d.m.Y H:i")
        if text in {"0", "1"}:
            return _("Да") if text == "1" else _("Нет")
        return text

    @staticmethod
    def _audit_user_value(value) -> str:
        text = str(value).strip()
        if not text:
            return "—"
        try:
            user_id = int(text)
        except (TypeError, ValueError):
            return text
        user = User.objects.filter(pk=user_id).only("username", "email").first()
        if not user:
            return text
        if user.email and user.username:
            return f"{user.username} · {user.email}"
        return user.email or user.username or text

    @staticmethod
    def _audit_field_label(field_name: str) -> str:
        labels = {
            "deleted_at": _("Удаление"),
            "deleted_by_id": _("Кто удалил"),
            "is_active": _("Публикация"),
            "is_verified": _("Проверка"),
            "owner_id": _("Владелец"),
            "lat": _("Координаты"),
            "lng": _("Координаты"),
            "district": _("Регион / район"),
            "metro": _("Метро"),
            "address": _("Адрес"),
            "phone1": _("Телефон"),
            "instagram": _("Instagram"),
            "website": _("Сайт"),
            "schedule": _("Расписание"),
            "lesson_duration_minutes": _("Длительность урока"),
            "is_temporary": _("Тип события"),
            "temporary_start": _("Начало события"),
            "temporary_end": _("Окончание события"),
            "price_from": _("Цена от"),
            "price_to": _("Цена до"),
            "price_per_lesson": _("Цена за 1 урок"),
            "price_per_month": _("Цена за месяц"),
            "price_per_8_lessons": _("Цена за 8 уроков"),
            "extra_conditions": _("Дополнительные условия"),
            "additional_info": _("Дополнительная информация"),
            "cover_photo": _("Фото для шапки"),
            "photo": _("Главное фото"),
            "name": _("Название"),
            "name_ru": _("Название (RU)"),
            "name_az": _("Название (AZ)"),
            "name_en": _("Название (EN)"),
            "description_ru": _("Описание (RU)"),
            "description_az": _("Описание (AZ)"),
            "description_en": _("Описание (EN)"),
            "category": _("Категория"),
            "subcategory": _("Подкатегория"),
            "age_from": _("Возраст от"),
            "age_to": _("Возраст до"),
        }
        return labels.get(field_name, field_name)

    def _audit_event_metadata(self, obj):
        field_name = obj.field_name
        old_value = obj.old_value
        new_value = obj.new_value

        if field_name in {"deleted_at", "deleted_by_id"}:
            is_restore = not bool(str(new_value).strip())
            return (
                "restore" if is_restore else "delete",
                "good" if is_restore else "warn",
                _("Карточка восстановлена") if is_restore else _("Карточка перемещена в удалённые"),
            )

        if field_name == "is_active":
            became_active = self._truthy_audit_value(new_value)
            return (
                "publication",
                "good" if became_active else "warn",
                _("Карточка опубликована") if became_active else _("Карточка снята с публикации"),
            )

        if field_name == "is_verified":
            became_verified = self._truthy_audit_value(new_value)
            return (
                "verification",
                "info" if became_verified else "muted",
                _("Карточка помечена как проверенная") if became_verified else _("Снята отметка проверки"),
            )

        if field_name in {"lat", "lng"}:
            return ("coordinates", "info", _("Координаты обновлены"))

        if field_name in {"district", "metro", "address"}:
            return ("location", "info", _("Локация карточки обновлена"))

        if field_name in {"phone1", "instagram", "website", "schedule"}:
            return ("contacts", "muted", _("Контакты карточки обновлены"))

        if field_name in {"cover_photo", "photo"}:
            return ("photos", "muted", _("Фото карточки обновлены"))

        if field_name in {
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
            "price_from",
            "price_to",
            "price_per_lesson",
            "price_per_month",
            "price_per_8_lessons",
            "lesson_duration_minutes",
            "extra_conditions",
            "additional_info",
        }:
            return ("content", "muted", _("Изменены данные карточки"))

        if field_name == "owner_id":
            return ("owner", "info", _("Изменён владелец карточки"))

        return ("other", "muted", _("Изменено поле карточки"))

    def _audit_value_pair(self, obj) -> str:
        field_label = self._audit_field_label(obj.field_name)
        old_value = self._audit_display_value(obj.old_value)
        new_value = self._audit_display_value(obj.new_value)
        if obj.field_name == "deleted_at":
            if self._truthy_audit_value(obj.new_value):
                return _("Служебное поле удаления: %(value)s") % {"value": new_value}
            return _("Служебное поле удаления очищено")
        if obj.field_name == "deleted_by_id":
            old_value = self._audit_user_value(obj.old_value)
            new_value = self._audit_user_value(obj.new_value)
            if self._truthy_audit_value(obj.new_value):
                return _("Удалил: %(value)s") % {"value": new_value}
            return _("Удаливший пользователь очищен")
        if obj.field_name == "owner_id":
            old_value = self._audit_user_value(obj.old_value)
            new_value = self._audit_user_value(obj.new_value)
        if old_value == new_value:
            return _("Значение не изменилось")
        return _("%(field)s: %(old)s → %(new)s") % {
            "field": field_label,
            "old": old_value,
            "new": new_value,
        }

    @admin.display(description=_("Карточка"))
    def place_summary(self, obj):
        if not obj.place_id:
            return "-"
        edit_url = reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name)
        meta_bits = [obj.place.get_category_display()]
        if obj.place.district:
            meta_bits.append(obj.place.district)
        meta = " · ".join(bit for bit in meta_bits if bit)
        return format_html(
            '<div class="km-admin-stack">'
            '<a class="km-audit-place-link" href="{}">{}</a>'
            '{}'
            "</div>",
            edit_url,
            obj.place,
            format_html('<span class="km-admin-meta">{}</span>', meta) if meta else "",
        )

    @admin.display(description=_("Изменение"))
    def change_summary(self, obj):
        _kind, tone, label = self._audit_event_metadata(obj)
        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">'
            '<span class="km-admin-badge km-audit-kind km-audit-kind--{}">{}</span>'
            "</div>"
            '<span class="km-admin-title">{}</span>'
            '<span class="km-admin-meta">{}</span>'
            "</div>",
            tone,
            label,
            self._audit_field_label(obj.field_name),
            self._audit_value_pair(obj),
        )

    @admin.display(description=_("Кто изменил"))
    def changed_by_summary(self, obj):
        if not obj.changed_by_id:
            return format_html('<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>', _("Система"))
        meta = obj.changed_by.email or obj.changed_by.get_full_name() or ""
        return format_html(
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">{}</span>'
            '{}'
            "</div>",
            obj.changed_by.get_username(),
            format_html('<span class="km-admin-meta">{}</span>', meta) if meta else "",
        )

    @admin.display(description=_("Источник"))
    def source_badge(self, obj):
        source_label = obj.get_source_display()
        tone = {
            PlaceChangeAudit.SOURCE_OWNER_PANEL: "good",
            PlaceChangeAudit.SOURCE_ADMIN: "info",
            PlaceChangeAudit.SOURCE_SYSTEM: "muted",
        }.get(obj.source, "muted")
        return format_html(
            '<span class="km-admin-badge km-audit-source km-audit-source--{}">{}</span>',
            tone,
            source_label,
        )

    @admin.display(description=_("Когда"))
    def created_at_display(self, obj):
        return date_format(timezone.localtime(obj.created_at), "d F Y, H:i")

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name)
        actions = [
            format_html('<a class="button km-audit-action" href="{}">{}</a>', edit_url, _("Редактировать")),
        ]
        if obj.place.is_deleted:
            actions.append(format_html('<span class="km-admin-meta">{}</span>', _("В каталоге скрыта")))
        else:
            actions.append(
                format_html(
                    '<a class="button km-audit-action km-audit-action--secondary" href="{}" target="_blank" rel="noopener">{}</a>',
                    obj.place.get_absolute_url(),
                    _("Открыть"),
                )
            )
        return format_html('<div class="km-audit-actions">{}</div>', format_html_join("", "{}", ((action,) for action in actions)))


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
    readonly_fields = (
        "status",
        "note",
        "place_completion_summary",
        "moderation_actions",
        "created_at",
        "updated_at",
        "moderated_at",
        "moderated_by",
    )
    autocomplete_fields = ("place", "applicant", "moderated_by")
    actions = ("approve_requests", "reject_requests")
    inlines = (PlaceOwnershipRequestAuditInline,)
    fieldsets = (
        (_("Заявка"), {"fields": ("place", "applicant", "status", "note")}),
        (_("Заполненность карточки"), {"fields": ("place_completion_summary",)}),
        (_("Модерация"), {"fields": ("moderation_note", "moderation_actions", "moderated_by", "moderated_at")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("place", "applicant", "moderated_by").prefetch_related("place__gallery")

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

    @staticmethod
    def _place_text_value(value):
        return (value or "").strip()

    @staticmethod
    def _format_place_number_pair(first_value, second_value, *, unit: str = "", separator: str = "–"):
        if first_value is not None and second_value is not None:
            return f"{first_value}{separator}{second_value}{unit}"
        if first_value is not None:
            return f"{first_value}+{unit}"
        if second_value is not None:
            return f"до {second_value}{unit}"
        return ""

    def _render_place_completion_badge(self, *, is_filled: bool):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            "good" if is_filled else "warn",
            _("Заполнено") if is_filled else _("Не заполнено"),
        )

    def _place_completion_rows(self, place: Place):
        gallery_count = len(place.gallery.all())
        coordinates_value = (
            _("lat %(lat)s, lng %(lng)s") % {"lat": round(place.lat, 6), "lng": round(place.lng, 6)}
            if place.has_coordinates
            else ""
        )
        price_value = ", ".join(f"{label}: {value}" for label, value in place.pricing_options)

        return (
            (_("Название RU"), bool(self._place_text_value(place.name_ru or place.name)), self._place_text_value(place.name_ru or place.name)),
            (_("Название AZ"), bool(self._place_text_value(place.name_az)), self._place_text_value(place.name_az)),
            (_("Название EN"), bool(self._place_text_value(place.name_en)), self._place_text_value(place.name_en)),
            (_("Описание RU"), bool(self._place_text_value(place.description_ru)), self._place_text_value(place.description_ru)),
            (_("Описание AZ"), bool(self._place_text_value(place.description_az)), self._place_text_value(place.description_az)),
            (_("Описание EN"), bool(self._place_text_value(place.description_en)), self._place_text_value(place.description_en)),
            (_("Категория"), bool(self._place_text_value(place.category)), place.get_category_display()),
            (_("Подкатегория"), bool(self._place_text_value(place.subcategory)), self._place_text_value(place.subcategory)),
            (_("Возраст"), bool(place.age_display), place.age_display),
            (_("Цены"), bool(place.pricing_options), price_value),
            (_("Длительность урока"), place.lesson_duration_minutes is not None, place.lesson_duration_display),
            (_("Регион / район"), bool(self._place_text_value(place.district)), self._place_text_value(place.district)),
            (_("Метро"), bool(self._place_text_value(place.metro)), self._place_text_value(place.metro)),
            (_("Адрес"), bool(self._place_text_value(place.address)), self._place_text_value(place.address)),
            (_("Координаты"), place.has_coordinates, coordinates_value),
            (_("Телефон"), bool(self._place_text_value(place.phone1)), self._place_text_value(place.phone1)),
            (_("Instagram"), bool(self._place_text_value(place.instagram)), self._place_text_value(place.instagram_url())),
            (_("Сайт"), bool(self._place_text_value(place.website)), self._place_text_value(place.website_url())),
            (_("Расписание"), bool(self._place_text_value(place.schedule)), self._place_text_value(place.schedule)),
            (_("Дополнительные условия"), bool(self._place_text_value(place.extra_conditions)), self._place_text_value(place.extra_conditions)),
            (_("Дополнительная информация"), bool(self._place_text_value(place.additional_info)), self._place_text_value(place.additional_info)),
            (_("Фото для шапки"), bool(place.cover_photo and getattr(place.cover_photo, "name", "")), getattr(place.cover_photo, "name", "")),
            (_("Главное фото"), bool(place.photo and getattr(place.photo, "name", "")), getattr(place.photo, "name", "")),
            (
                _("Галерея"),
                gallery_count > 0,
                ngettext("%(count)s фото", "%(count)s фото", gallery_count) % {"count": gallery_count} if gallery_count else "",
            ),
            (_("Публикация"), place.is_active and not place.is_deleted, _("Опубликовано") if place.is_active and not place.is_deleted else _("Не опубликовано")),
            (_("Проверка"), place.is_verified, _("Проверено") if place.is_verified else _("Без проверки")),
            (_("Готовность к карте"), place.is_map_ready, _("Готово для карты") if place.is_map_ready else _("Не готово для карты")),
        )

    @admin.display(description=_("Что заполнено в карточке"))
    def place_completion_summary(self, obj):
        if not obj or not obj.place_id:
            return "-"

        rows = self._place_completion_rows(obj.place)
        filled_count = sum(1 for _, is_filled, _ in rows if is_filled)
        total_count = len(rows)

        return format_html(
            '<div class="km-admin-stack">'
            '<div class="km-admin-badges">{} <span class="km-admin-meta">{}</span></div>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:8px;">'
            '{}'
            '</div>'
            '</div>',
            format_html(
                '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
                "good" if filled_count == total_count else "warn",
                _("%(filled)s из %(total)s заполнено") % {"filled": filled_count, "total": total_count},
            ),
            _("Показывается текущее состояние связанной карточки."),
            format_html_join(
                "",
                '<div class="km-admin-stack" style="padding:10px 12px;border:1px solid #2f2f2f;border-radius:14px;background:#1a1a1a;">'
                '<div class="km-admin-badges">{} <span class="km-admin-title">{}</span></div>'
                '<span class="km-admin-meta">{}</span>'
                '</div>',
                (
                    (
                        self._render_place_completion_badge(is_filled=is_filled),
                        title,
                        value or _("Пусто"),
                    )
                    for title, is_filled, value in rows
                ),
            ),
        )

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
