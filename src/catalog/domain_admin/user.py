from django.contrib import admin, messages
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse

from catalog.models import (
    UserProfile,
    SiteRegisteredUser,
    StaffAccessUser,
    UserEmailVerification,
    PlaceOwnershipRequestAudit,
)
from .ui_utils import render_primary_action, render_action_menu, render_row_actions_container, build_admin_query_string

User = get_user_model()

ADMIN_ROLE_SUPERADMIN = "superadmin"
ADMIN_ROLE_MODERATOR = "moderator"
ADMIN_ROLE_CONTENT_MANAGER = "content_manager"

ADMIN_ROLE_CHOICES = (
    (ADMIN_ROLE_MODERATOR, _("Модератор")),
    (ADMIN_ROLE_CONTENT_MANAGER, _("Контент-менеджер")),
    (ADMIN_ROLE_SUPERADMIN, _("Суперадмин")),
)

ADMIN_ROLE_PERMISSION_PRESETS = {
    ADMIN_ROLE_MODERATOR: {
        "view_place",
        "view_event",
        "view_placereview",
        "change_placereview",
        "view_sitereview",
        "change_sitereview",
        "view_placeownershiprequest",
        "change_placeownershiprequest",
    },
    ADMIN_ROLE_CONTENT_MANAGER: {
        "view_place",
        "add_place",
        "change_place",
        "view_event",
        "add_event",
        "change_event",
        "view_category",
        "add_category",
        "change_category",
        "view_subcategory",
        "add_subcategory",
        "change_subcategory",
        "view_placephoto",
        "add_placephoto",
        "change_placephoto",
        "delete_placephoto",
        "view_sitegalleryimage",
        "add_sitegalleryimage",
        "change_sitegalleryimage",
        "delete_sitegalleryimage",
        "view_sitesettings",
        "change_sitesettings",
        "view_sitebrandingsettings",
        "change_sitebrandingsettings",
        "view_siteaboutsettings",
        "change_siteaboutsettings",
        "view_sitecontactssettings",
        "change_sitecontactssettings",
        "view_sitefootersettings",
        "change_sitefootersettings",
        "view_siteemptystatesettings",
        "change_siteemptystatesettings",
    },
}


class StaffAccessUserCreationForm(AdminUserCreationForm):
    admin_role = forms.ChoiceField(
        label=_("Роль"),
        choices=ADMIN_ROLE_CHOICES,
        initial=ADMIN_ROLE_MODERATOR,
        widget=forms.RadioSelect,
    )

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
    fields = (
        "avatar_preview",
        "avatar",
        "phone",
        "gender",
        "created_at",
        "updated_at",
    )
    readonly_fields = ("avatar_preview", "created_at", "updated_at")

    def get_extra(self, request, obj=None, **kwargs):
        if obj is None or not hasattr(obj, "profile"):
            return 1
        return 0

    @admin.display(description=_("Текущее фото"))
    def avatar_preview(self, obj):
        if not obj or not obj.avatar:
            return format_html(
                '<div class="km-user-avatar-preview km-user-avatar-preview--empty">'
                '<i class="fas fa-user" aria-hidden="true"></i>'
                '<span>{}</span>'
                "</div>",
                _("Фото не загружено"),
            )
        return format_html(
            '<div class="km-user-avatar-preview">'
            '<img src="{}" alt="{}">'
            "</div>",
            obj.avatar.url,
            _("Фото профиля"),
        )


class _BaseKidsMapUserAdmin(UserAdmin):
    change_form_template = "admin/catalog/user/change_form.html"
    filter_horizontal = ()
    search_fields = ("username", "email", "first_name", "last_name", "profile__phone")
    ordering = ("username",)
    inlines = (UserProfileInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("profile")

    def get_deleted_objects(self, objs, request):
        deleted_objects, model_count, perms_needed, protected = super().get_deleted_objects(objs, request)
        # User deletion can cascade through ownership requests into their audit trail.
        # Audit rows are read-only in admin, but they must not block deleting the parent user.
        perms_needed = {
            perm
            for perm in perms_needed
            if perm != str(PlaceOwnershipRequestAudit._meta.verbose_name)
        }
        return deleted_objects, model_count, perms_needed, protected

    def has_add_permission(self, request):
        return bool(request.user and request.user.is_superuser)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        UserProfile.get_or_create_for_user(form.instance)

    def get_urls(self):
        from django.urls import path
        from django.contrib.admin import ModelAdmin
        return [
            path(
                "<id>/password/",
                self.admin_site.admin_view(self.user_change_password),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_password_change",
            ),
            *ModelAdmin.get_urls(self),
        ]

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
        email_verification = getattr(obj, "email_verification", None)
        title = obj.username or "-"
        details: list[str] = []
        avatar_html = self._avatar_html(obj, size=38)

        full_name = " ".join(part for part in (obj.first_name, obj.last_name) if part).strip()
        if obj.email:
            email_status = "✅" if email_verification and email_verification.is_verified else "⏳"
            details.append(f"{email_status} {obj.email}")
        if full_name:
            details.append(full_name)
            
        badges = []
        if obj.is_superuser:
            badges.append('<span class="km-badge km-badge--danger" style="margin-right:4px;">Суперадмин</span>')
        elif obj.is_staff:
            badges.append('<span class="km-badge km-badge--info" style="margin-right:4px;">Админ</span>')

        if not obj.is_active:
            badges.append('<span class="km-badge km-badge--neutral" style="margin-right:4px;">Неактивен</span>')

        badge_html = f'<div style="margin-top:6px;">{"".join(badges)}</div>' if badges else ""

        if not details and not badges:
            return format_html(
                '<div class="km-user-identity">{}<div class="km-admin-stack">'
                '<span class="km-admin-title">{}</span></div></div>',
                avatar_html,
                title,
            )

        return format_html(
            '<div class="km-user-identity">{}<div class="km-admin-stack">'
            '<span class="km-admin-title" style="margin-bottom:2px;">{}</span>{}{}'
            "</div></div>",
            avatar_html,
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((detail,) for detail in details)),
            mark_safe(badge_html)
        )

    def _avatar_html(self, obj, *, size=56):
        profile = getattr(obj, "profile", None)
        if profile and profile.avatar:
            return format_html(
                '<span class="km-user-avatar" style="width:{0}px;height:{0}px;">'
                '<img src="{1}" alt="{2}"></span>',
                size,
                profile.avatar.url,
                obj.get_username(),
            )
        initials = (obj.get_full_name() or obj.get_username() or "?").strip()[:1].upper()
        return format_html(
            '<span class="km-user-avatar km-user-avatar--empty" style="width:{0}px;height:{0}px;">{1}</span>',
            size,
            initials or "?",
        )

    @admin.display(description=_("Пароль"))
    def password_summary(self, obj):
        if not obj or not obj.pk:
            return _("Пароль задаётся при создании пользователя.")

        password_url = reverse(
            f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_password_change",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )
        return format_html(
            '<div class="km-admin-stack">'
            '<span class="km-admin-meta">{}</span>'
            '<a class="km-admin-link-inline" href="{}">{}</a>'
            "</div>",
            _("Пароль скрыт. При необходимости откройте отдельную форму смены пароля."),
            password_url,
            _("Сменить пароль"),
        )

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["km_password_change_url"] = ""
        if obj and obj.pk:
            context["km_password_change_url"] = reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_password_change",
                args=[obj.pk],
                current_app=self.admin_site.name,
            )
            
            from catalog.models.owner import PlaceOwnershipRequest
            profile = getattr(obj, "profile", None)
            email_verification = getattr(obj, "email_verification", None)
            
            pending_requests = PlaceOwnershipRequest.objects.filter(applicant=obj, status=PlaceOwnershipRequest.STATUS_PENDING).count()
            total_requests = PlaceOwnershipRequest.objects.filter(applicant=obj).count()
            
            owner_workflow = {
                "has_requests": total_requests > 0,
                "pending_requests_count": pending_requests,
                "changelist_url": f"{reverse('admin:catalog_placeownershiprequest_changelist')}?applicant__id__exact={obj.pk}" if total_requests > 0 else ""
            }
            
            context["km_user_form_summary"] = {
                "full_name": " ".join(part for part in (obj.first_name, obj.last_name) if part).strip() or obj.username,
                "email": obj.email,
                "email_verified": email_verification.is_verified if email_verification else False,
                "phone": profile.phone if profile else "",
                "avatar_url": profile.avatar.url if profile and profile.avatar else "",
                "avatar_initial": (obj.get_full_name() or obj.get_username() or "?").strip()[:1].upper(),
                "is_active": obj.is_active,
                "is_staff": obj.is_staff,
                "is_superuser": obj.is_superuser,
                "last_login": obj.last_login,
                "date_joined": obj.date_joined,
                "owner_workflow": owner_workflow,
            }
            
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)


@admin.register(User)
class HiddenBaseUserAdmin(_HiddenFromAdminIndexMixin, _BaseKidsMapUserAdmin):
    """
    Hidden base registration to keep default auth user admin URLs alive.
    """

    fieldsets = (
        (_("Аккаунт"), {"fields": ("username", "email", "first_name", "last_name", "password_summary")}),
        (_("Права доступа"), {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
        (_("Важные даты"), {"classes": ("collapse",), "fields": ("last_login", "date_joined")}),
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
    readonly_fields = ("password_summary", "last_login", "date_joined")
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active", "last_login", "date_joined")
    filter_horizontal = ("user_permissions",)


@admin.register(SiteRegisteredUser)
class SiteRegisteredUserAdmin(_BaseKidsMapUserAdmin):
    change_list_template = "admin/catalog/siteregistereduser/change_list.html"
    km_primary_filters = ("is_active", "date_joined")
    list_per_page = 15
    fieldsets = (
        (_("Аккаунт"), {"fields": ("username", "email", "first_name", "last_name", "is_active", "password_summary")}),
        (_("Важные даты"), {"classes": ("collapse",), "fields": ("last_login", "date_joined")}),
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
    readonly_fields = ("password_summary", "last_login", "date_joined")
    list_display = ("identity_summary", "site_phone", "site_gender", "is_active", "date_joined", "last_login", "row_actions")
    list_filter = ("is_active", "date_joined", "last_login", "profile__gender")

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False, is_superuser=False)

    @admin.display(description="")
    def row_actions(self, obj):
        change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        primary_action = render_primary_action(change_url, _("Редактировать"))
        
        password_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_password_change", args=[obj.pk])
        delete_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete", args=[obj.pk])
        
        menu_actions = [
            (password_url, _("Сменить пароль"), ""),
            (delete_url, _("Удалить"), "km-admin-action-menu__link--danger"),
        ]
        menu_html = render_action_menu(menu_actions)
        return render_row_actions_container(primary_action, menu_html)

    def _build_user_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
        return build_admin_query_string(request, clear=clear, **updates)

    def _user_quick_filters(self, request):
        # Registered accounts are a single category: managing a listing is a
        # relation to that listing, not a kind of account. So these tabs split
        # on account activity, which is the one distinction that still exists.
        current = request.GET.get("is_active__exact")
        keys = ("is_active__exact",)
        base = SiteRegisteredUser.objects.filter(is_staff=False, is_superuser=False)

        return (
            {
                "label": _("Все пользователи"),
                "url": self._build_user_changelist_query_string(request, clear=keys),
                "active": current not in {"0", "1"},
                "count": base.count(),
            },
            {
                "label": _("Активные"),
                "url": self._build_user_changelist_query_string(request, clear=keys, is_active__exact="1"),
                "active": current == "1",
                "count": base.filter(is_active=True).count(),
            },
            {
                "label": _("Неактивные"),
                "url": self._build_user_changelist_query_string(request, clear=keys, is_active__exact="0"),
                "active": current == "0",
                "count": base.filter(is_active=False).count(),
            },
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "km_primary_quick_filters": self._user_quick_filters(request),
            "km_secondary_quick_filters": [],
            "title": _("Пользователи сайта"),
            "subtitle": _("Управление зарегистрированными пользователями сайта."),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


class StaffAccessRoleFilter(admin.SimpleListFilter):
    title = _("Роль")
    parameter_name = "role"

    def lookups(self, request, model_admin):
        return (
            (ADMIN_ROLE_SUPERADMIN, _("Суперадмины")),
            ("admin", _("Админы")),
        )

    def queryset(self, request, queryset):
        if self.value() == ADMIN_ROLE_SUPERADMIN:
            return queryset.filter(is_superuser=True)
        if self.value() == "admin":
            return queryset.filter(is_staff=True, is_superuser=False)
        return queryset


@admin.register(StaffAccessUser)
class StaffAccessUserAdmin(_BaseKidsMapUserAdmin):
    add_form_template = "admin/catalog/user/change_form.html"
    add_form = StaffAccessUserCreationForm
    change_list_template = "admin/catalog/staffaccessuser/change_list.html"
    list_per_page = 15
    fieldsets = (
        (_("Аккаунт"), {"fields": ("username", "email", "first_name", "last_name", "password_summary")}),
        (_("Права доступа"), {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
        (_("Важные даты"), {"classes": ("collapse",), "fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "admin_role"),
            },
        ),
    )
    readonly_fields = ("password_summary", "last_login", "date_joined")
    list_display = ("identity_summary", "email", "staff_role", "places_count", "activity_status", "last_login", "row_actions")
    list_filter = (StaffAccessRoleFilter,)
    filter_horizontal = ("user_permissions",)
    actions = None

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(Q(is_staff=True) | Q(is_superuser=True))
        return queryset.annotate(
            places_count=Count(
                "managed_places",
                filter=Q(managed_places__deleted_at__isnull=True),
                distinct=True,
            )
        )

    @admin.display(description=_("Роль"))
    def staff_role(self, obj):
        if obj.is_superuser:
            return format_html('<span class="km-staff-role km-staff-role--super">{}</span>', _("Суперадмин"))
        return format_html('<span class="km-staff-role km-staff-role--admin">{}</span>', _("Админ"))

    @admin.display(description=_("Добавленные места"), ordering="places_count")
    def places_count(self, obj):
        return getattr(obj, "places_count", 0)

    @admin.display(description=_("Активность"), boolean=True, ordering="is_active")
    def activity_status(self, obj):
        return obj.is_active

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        actions = [(change_url, _("Открыть"), "")]
        if getattr(obj, "km_can_delete", False):
            delete_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete", args=[obj.pk])
            actions.append((delete_url, _("Удалить"), "km-staff-action--danger"))
        return render_action_menu(actions)

    def _is_protected_from_deletion(self, *, request, obj) -> bool:
        if obj.pk == request.user.pk:
            return True
        return obj.is_superuser and not StaffAccessUser.objects.filter(is_superuser=True).exclude(pk=obj.pk).exists()

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        if obj is None:
            return True
        return not self._is_protected_from_deletion(request=request, obj=obj)

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, object_id)
        if obj is None:
            return super().delete_view(request, object_id, extra_context=extra_context)
        if not request.user.is_superuser:
            raise PermissionDenied
        if self._is_protected_from_deletion(request=request, obj=obj):
            message = (
                _("Нельзя удалить собственный профиль.")
                if obj.pk == request.user.pk
                else _("Нельзя удалить последнего суперadmin.")
            )
            self.message_user(request, message, level=messages.ERROR)
            return redirect(f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist")
        return super().delete_view(request, object_id, extra_context=extra_context)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("is_active", True)
        initial.setdefault("is_staff", True)
        return initial

    def save_model(self, request, obj, form, change):
        selected_role = form.cleaned_data.get("admin_role") if not change else ""
        obj.is_staff = True
        obj.is_active = True
        if not change and selected_role:
            obj.is_superuser = selected_role == ADMIN_ROLE_SUPERADMIN
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if change:
            return
        selected_role = form.cleaned_data.get("admin_role") or ADMIN_ROLE_MODERATOR
        if selected_role == ADMIN_ROLE_SUPERADMIN:
            form.instance.user_permissions.clear()
            return
        permissions = Permission.objects.filter(
            content_type__app_label="catalog",
            codename__in=ADMIN_ROLE_PERMISSION_PRESETS.get(selected_role, set()),
        )
        form.instance.user_permissions.set(permissions)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if not hasattr(response, "context_data"):
            return response
        superadmin_count = StaffAccessUser.objects.filter(is_superuser=True).count()
        for staff_user in response.context_data["cl"].result_list:
            staff_user.km_can_delete = bool(
                request.user.is_superuser
                and staff_user.pk != request.user.pk
                and (not staff_user.is_superuser or superadmin_count > 1)
            )
        extra_context = {
            "title": _("Сотрудники админки"),
            "subtitle": _("Управление сотрудниками, имеющими доступ к панели управления."),
            **(extra_context or {}),
        }
        response.context_data.update(extra_context)
        return response


class UserProfileAccessLevelFilter(admin.SimpleListFilter):
    title = _("Уровень доступа")
    parameter_name = "access_level"

    def lookups(self, request, model_admin):
        return (
            ("superadmin", _("Суперадмин")),
            ("admin", _("Админ")),
            ("user", _("Пользователь")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "superadmin":
            return queryset.filter(user__is_superuser=True)
        if value == "admin":
            return queryset.filter(user__is_staff=True, user__is_superuser=False)
        if value == "user":
            return queryset.filter(user__is_staff=False, user__is_superuser=False)
        return queryset


@admin.register(UserProfile)
class UserProfileAdmin(_HiddenFromAdminIndexMixin, admin.ModelAdmin):
    list_display = (
        "user",
        "access_level",
        "phone",
        "gender",
        "created_at",
        "updated_at",
    )
    list_filter = (UserProfileAccessLevelFilter, "gender", "created_at")
    search_fields = ("user__username", "user__email", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (_("Пользователь"), {"fields": ("user", "phone", "gender")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Уровень доступа"))
    def access_level(self, obj):
        if obj.user.is_superuser:
            return _("Суперадмин")
        if obj.user.is_staff:
            return _("Админ")
        return _("Пользователь")


@admin.register(UserEmailVerification)
class UserEmailVerificationAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "is_verified", "attempts_left", "expires_at", "resend_available_at", "updated_at")
    list_filter = ("is_verified",)
    search_fields = ("user__username", "user__email", "email")
    readonly_fields = ("created_at", "updated_at", "verified_at")
