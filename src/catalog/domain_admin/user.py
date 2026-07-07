from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.db.models import Q
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
        email_verification = getattr(obj, "email_verification", None)
        title = obj.username or "-"
        details: list[str] = []

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
            
        if profile and profile.role == "OWNER":
            badges.append('<span class="km-badge km-badge--primary" style="margin-right:4px;">Владелец</span>')
            
        if not obj.is_active:
            badges.append('<span class="km-badge km-badge--neutral" style="margin-right:4px;">Неактивен</span>')

        badge_html = f'<div style="margin-top:6px;">{"".join(badges)}</div>' if badges else ""

        if not details and not badges:
            return format_html('<div class="km-admin-stack"><span class="km-admin-title">{}</span></div>', title)

        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title" style="margin-bottom:2px;">{}</span>{}{}'
            '</div>',
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((detail,) for detail in details)),
            mark_safe(badge_html)
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
                "role": profile.get_role_display() if profile else "",
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
    km_primary_filters = ("profile__role", "is_active", "date_joined")
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
    list_display = ("identity_summary", "site_role", "site_phone", "site_gender", "is_active", "date_joined", "last_login", "row_actions")
    list_filter = ("is_active", "date_joined", "last_login", "profile__role", "profile__gender")

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
        current_role = request.GET.get("profile__role__exact")
        keys = ("profile__role__exact",)
        
        counts = {
            "all": SiteRegisteredUser.objects.filter(is_staff=False, is_superuser=False).count(),
            "users": SiteRegisteredUser.objects.filter(is_staff=False, is_superuser=False, profile__role="user").count(),
            "owners": SiteRegisteredUser.objects.filter(is_staff=False, is_superuser=False, profile__role="owner").count(),
        }
        
        return (
            {"label": _("Все пользователи"), "url": self._build_user_changelist_query_string(request, clear=keys), "active": not current_role, "count": counts["all"]},
            {"label": _("Владельцы кружков"), "url": self._build_user_changelist_query_string(request, clear=keys, profile__role__exact="owner"), "active": current_role == "owner", "count": counts["owners"]},
            {"label": _("Обычные пользователи"), "url": self._build_user_changelist_query_string(request, clear=keys, profile__role__exact="user"), "active": current_role == "user", "count": counts["users"]},
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "km_primary_quick_filters": self._user_quick_filters(request),
            "km_secondary_quick_filters": [],
            "title": _("Пользователи сайта"),
            "subtitle": _("Управление зарегистрированными пользователями (владельцы кружков и обычные пользователи)."),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(StaffAccessUser)
class StaffAccessUserAdmin(_BaseKidsMapUserAdmin):
    change_list_template = "admin/catalog/siteregistereduser/change_list.html"
    km_primary_filters = ("is_staff", "is_superuser", "is_active", "date_joined")
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
                "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
            },
        ),
    )
    readonly_fields = ("password_summary", "last_login", "date_joined")
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

    def _build_user_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
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

    def _user_quick_filters(self, request):
        is_superuser = request.GET.get("is_superuser__exact")
        keys = ("is_superuser__exact",)
        
        counts = {
            "all": StaffAccessUser.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count(),
            "admins": StaffAccessUser.objects.filter(is_staff=True, is_superuser=False).count(),
            "superusers": StaffAccessUser.objects.filter(is_superuser=True).count(),
        }
        
        return (
            {"label": _("Все сотрудники"), "url": self._build_user_changelist_query_string(request, clear=keys), "active": not is_superuser, "count": counts["all"]},
            {"label": _("Админы"), "url": self._build_user_changelist_query_string(request, clear=keys, is_superuser__exact="0"), "active": is_superuser == "0", "count": counts["admins"]},
            {"label": _("Суперадмины"), "url": self._build_user_changelist_query_string(request, clear=keys, is_superuser__exact="1"), "active": is_superuser == "1", "count": counts["superusers"]},
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "km_primary_quick_filters": self._user_quick_filters(request),
            "km_secondary_quick_filters": [],
            "title": _("Сотрудники админки"),
            "subtitle": _("Управление сотрудниками, имеющими доступ к панели управления."),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


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
