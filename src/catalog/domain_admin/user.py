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
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateformat import format as date_format

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


class UserPhoneFilter(admin.SimpleListFilter):
    title = _("Телефон")
    parameter_name = "has_phone"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("С телефоном")),
            ("no", _("Без телефона")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(profile__phone__gt="")
        if self.value() == "no":
            return queryset.filter(Q(profile__isnull=True) | Q(profile__phone=""))
        return queryset


class UserPlacesFilter(admin.SimpleListFilter):
    title = _("Связанные места")
    parameter_name = "has_places"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Есть места")),
            ("no", _("Нет мест")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(managed_places__isnull=False).distinct()
        if self.value() == "no":
            return queryset.filter(managed_places__isnull=True)
        return queryset


class UserLastLoginFilter(admin.SimpleListFilter):
    title = _("Последний вход")
    parameter_name = "has_login"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Входил на сайт")),
            ("never", _("Не входил")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(last_login__isnull=False)
        if self.value() == "never":
            return queryset.filter(last_login__isnull=True)
        return queryset


@admin.register(SiteRegisteredUser)
class SiteRegisteredUserAdmin(_BaseKidsMapUserAdmin):
    change_list_template = "admin/catalog/siteregistereduser/change_list.html"
    km_primary_filters = ("is_active", "date_joined")
    list_per_page = 20
    actions = ["activate_users", "deactivate_users"]
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
    list_display = (
        "user_profile_card",
        "user_phone",
        "user_gender",
        "user_status",
        "user_date_joined",
        "user_last_login",
        "user_activity",
        "user_actions",
    )
    list_filter = (
        "is_active",
        UserPhoneFilter,
        UserPlacesFilter,
        UserLastLoginFilter,
        "profile__gender",
        "date_joined",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .filter(is_staff=False, is_superuser=False)
            .select_related("profile", "email_verification")
            .annotate(
                managed_places_count=Count("managed_places", distinct=True),
                ownership_requests_count=Count("ownership_requests", distinct=True),
                reviews_count=Count("place_reviews", distinct=True),
            )
        )

    def get_urls(self):
        from django.urls import path
        custom_urls = [
            path(
                "<id>/toggle-active/",
                self.admin_site.admin_view(self.user_toggle_active),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_toggle_active",
            ),
        ]
        return custom_urls + super().get_urls()

    def user_toggle_active(self, request, id):
        if not self.has_change_permission(request):
            raise PermissionDenied
        user = self.get_object(request, id)
        if not user:
            messages.error(request, _("Пользователь не найден."))
            return redirect("admin:catalog_siteregistereduser_changelist")
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])

        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.GET.get("format") == "json":
            return JsonResponse({
                "success": True,
                "is_active": user.is_active,
                "status_label": str(_("Активен")) if user.is_active else str(_("Неактивен")),
                "message": str(_("Пользователь активирован.")) if user.is_active else str(_("Пользователь деактивирован.")),
            })

        msg = _("Пользователь %(name)s успешно активирован.") if user.is_active else _("Пользователь %(name)s успешно деактивирован.")
        self.message_user(request, msg % {"name": user.get_full_name() or user.username}, messages.SUCCESS)

        referer = request.META.get("HTTP_REFERER")
        return redirect(referer or "admin:catalog_siteregistereduser_changelist")

    @admin.action(description=_("Активировать выбранных пользователей"))
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            _("Успешно активировано пользователей: %(count)d.") % {"count": count},
            messages.SUCCESS,
        )

    @admin.action(description=_("Деактивировать выбранных пользователей"))
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            _("Успешно деактивировано пользователей: %(count)d.") % {"count": count},
            messages.WARNING,
        )

    @admin.display(description=_("Пользователь"), ordering="first_name")
    def user_profile_card(self, obj):
        profile = getattr(obj, "profile", None)
        email_verification = getattr(obj, "email_verification", None)

        full_name = " ".join(part for part in (obj.first_name, obj.last_name) if part).strip()
        change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])

        if profile and profile.avatar:
            avatar_html = format_html(
                '<a href="{}" class="km-u-avatar km-u-avatar--img" tabindex="-1">'
                '<img src="{}" alt="{}">'
                '</a>',
                change_url,
                profile.avatar.url,
                obj.username,
            )
        else:
            initial = (full_name or obj.username or "?")[:1].upper()
            color_num = (ord(initial) % 6) + 1
            avatar_html = format_html(
                '<a href="{}" class="km-u-avatar km-u-avatar--initials km-u-avatar--c{}" tabindex="-1">'
                '<span>{}</span>'
                '</a>',
                change_url,
                color_num,
                initial,
            )

        if full_name:
            primary_text = full_name
            secondary_text = obj.email or ""
            tertiary_text = f"@{obj.username}"
        elif obj.email:
            primary_text = obj.email.split("@")[0]
            secondary_text = obj.email
            tertiary_text = f"@{obj.username}" if obj.username != obj.email else ""
        else:
            primary_text = obj.username
            secondary_text = ""
            tertiary_text = ""

        verified_badge = ""
        if obj.email and email_verification and email_verification.is_verified:
            verified_badge = format_html(
                '<span class="km-u-verified" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-check_circle"></use></svg>'
                '</span>',
                _("Email подтверждён"),
            )

        email_row = ""
        if secondary_text:
            email_row = format_html(
                '<span class="km-u-meta km-u-meta--email"><span>{}</span>{}</span>',
                secondary_text,
                verified_badge,
            )

        username_row = ""
        if tertiary_text:
            username_row = format_html(
                '<span class="km-u-meta km-u-meta--username">{}</span>',
                tertiary_text,
            )

        return format_html(
            '<div class="km-u-cell-profile">'
            '{}'
            '<div class="km-u-profile-info">'
            '<a href="{}" class="km-u-name">{}</a>'
            '{}'
            '{}'
            '</div>'
            '</div>',
            avatar_html,
            change_url,
            primary_text,
            email_row,
            username_row,
        )

    # Aliases for backward compatibility
    identity_summary = user_profile_card

    @admin.display(description=_("Телефон"), ordering="profile__phone")
    def user_phone(self, obj):
        profile = getattr(obj, "profile", None)
        phone = profile.phone.strip() if (profile and profile.phone) else ""
        if not phone:
            return mark_safe('<span class="km-u-empty">—</span>')
        return format_html(
            '<a href="tel:{}" class="km-u-phone">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-call"></use></svg>'
            '<span>{}</span>'
            '</a>',
            phone,
            phone,
        )

    site_phone = user_phone

    @admin.display(description=_("Пол"), ordering="profile__gender")
    def user_gender(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile or profile.gender not in ("M", "F"):
            return mark_safe('<span class="km-u-empty">—</span>')
        gender_cls = "km-u-gender--m" if profile.gender == "M" else "km-u-gender--f"
        return format_html(
            '<span class="km-u-gender {}">{}</span>',
            gender_cls,
            profile.get_gender_display(),
        )

    site_gender = user_gender

    @admin.display(description=_("Статус"), ordering="is_active")
    def user_status(self, obj):
        if obj.is_active:
            return format_html(
                '<span class="km-u-status km-u-status--active">'
                '<span class="km-u-status-dot" aria-hidden="true"></span>'
                '<span>{}</span>'
                '</span>',
                _("Активен"),
            )
        return format_html(
            '<span class="km-u-status km-u-status--inactive">'
            '<span class="km-u-status-dot" aria-hidden="true"></span>'
            '<span>{}</span>'
            '</span>',
            _("Неактивен"),
        )

    @admin.display(description=_("Регистрация"), ordering="date_joined")
    def user_date_joined(self, obj):
        if not obj.date_joined:
            return mark_safe('<span class="km-u-empty">—</span>')
        d_str = date_format(obj.date_joined, "d.m.Y")
        t_str = date_format(obj.date_joined, "H:i")
        return format_html(
            '<div class="km-u-datetime">'
            '<span class="km-u-date">{}</span>'
            '<span class="km-u-time">{}</span>'
            '</div>',
            d_str,
            t_str,
        )

    @admin.display(description=_("Последний вход"), ordering="last_login")
    def user_last_login(self, obj):
        if not obj.last_login:
            return format_html('<span class="km-u-never">{}</span>', _("Не входил"))
        d_str = date_format(obj.last_login, "d.m.Y")
        t_str = date_format(obj.last_login, "H:i")
        return format_html(
            '<div class="km-u-datetime">'
            '<span class="km-u-date">{}</span>'
            '<span class="km-u-time">{}</span>'
            '</div>',
            d_str,
            t_str,
        )

    @admin.display(description=_("Активность"), ordering="managed_places_count")
    def user_activity(self, obj):
        places_cnt = getattr(obj, "managed_places_count", 0)
        reqs_cnt = getattr(obj, "ownership_requests_count", 0)
        revs_cnt = getattr(obj, "reviews_count", 0)

        pills = []
        if places_cnt:
            url = f"{reverse('admin:catalog_place_changelist')}?owner__id__exact={obj.pk}"
            pills.append(format_html(
                '<a href="{}" class="km-u-act-pill km-u-act-pill--place" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-place"></use></svg>'
                '<span>{}</span>'
                '</a>',
                url,
                _("Управление карточками мест"),
                _("%(count)d мест") % {"count": places_cnt},
            ))
        if reqs_cnt:
            url = f"{reverse('admin:catalog_placeownershiprequest_changelist')}?applicant__id__exact={obj.pk}"
            pills.append(format_html(
                '<a href="{}" class="km-u-act-pill km-u-act-pill--request" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-assignment"></use></svg>'
                '<span>{}</span>'
                '</a>',
                url,
                _("Заявки на владение"),
                _("%(count)d заяв.") % {"count": reqs_cnt},
            ))
        if revs_cnt:
            url = f"{reverse('admin:catalog_placereview_changelist')}?user__id__exact={obj.pk}"
            pills.append(format_html(
                '<a href="{}" class="km-u-act-pill km-u-act-pill--review" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-chat_bubble"></use></svg>'
                '<span>{}</span>'
                '</a>',
                url,
                _("Отзывы на сайте"),
                _("%(count)d отз.") % {"count": revs_cnt},
            ))

        if pills:
            return format_html('<div class="km-u-activity-list">{}</div>', mark_safe("".join(pills)))
        return mark_safe('<span class="km-u-empty">—</span>')

    @admin.display(description="")
    def user_actions(self, obj):
        change_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        password_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_password_change", args=[obj.pk])
        delete_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete", args=[obj.pk])
        toggle_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_toggle_active", args=[obj.pk])

        places_cnt = getattr(obj, "managed_places_count", 0)
        reqs_cnt = getattr(obj, "ownership_requests_count", 0)
        revs_cnt = getattr(obj, "reviews_count", 0)

        places_item = ""
        if places_cnt:
            places_url = f"{reverse('admin:catalog_place_changelist')}?owner__id__exact={obj.pk}"
            places_item = format_html(
                '<a href="{}" class="km-u-dropdown-item">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-place"></use></svg>'
                '<span>{} ({})</span>'
                '</a>',
                places_url,
                _("Связанные места"),
                places_cnt,
            )

        reqs_item = ""
        if reqs_cnt:
            reqs_url = f"{reverse('admin:catalog_placeownershiprequest_changelist')}?applicant__id__exact={obj.pk}"
            reqs_item = format_html(
                '<a href="{}" class="km-u-dropdown-item">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-assignment"></use></svg>'
                '<span>{} ({})</span>'
                '</a>',
                reqs_url,
                _("Заявки на владение"),
                reqs_cnt,
            )

        revs_item = ""
        if revs_cnt:
            revs_url = f"{reverse('admin:catalog_placereview_changelist')}?user__id__exact={obj.pk}"
            revs_item = format_html(
                '<a href="{}" class="km-u-dropdown-item">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-chat_bubble"></use></svg>'
                '<span>{} ({})</span>'
                '</a>',
                revs_url,
                _("Отзывы"),
                revs_cnt,
            )

        toggle_icon = "kmi-block" if obj.is_active else "kmi-check_circle"
        toggle_label = _("Деактивировать") if obj.is_active else _("Активировать")
        toggle_class = "km-u-dropdown-item js-km-toggle-active is-deactivate" if obj.is_active else "km-u-dropdown-item js-km-toggle-active is-activate"

        return format_html(
            '<div class="km-u-actions-wrap">'
            '<a href="{}" class="km-u-action-btn km-u-action-btn--edit" title="{}" aria-label="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-edit"></use></svg>'
            '</a>'
            '<details class="km-u-dropdown-wrap">'
            '<summary class="km-u-action-btn km-u-action-btn--more" title="{}" aria-label="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-more_vert"></use></svg>'
            '</summary>'
            '<div class="km-u-dropdown-menu">'
            '<a href="{}" class="km-u-dropdown-item">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-person"></use></svg>'
            '<span>{}</span>'
            '</a>'
            '<a href="{}" class="km-u-dropdown-item">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-key"></use></svg>'
            '<span>{}</span>'
            '</a>'
            '<a href="{}" class="{}" data-user-id="{}" data-user-name="{}" data-active="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#{}"></use></svg>'
            '<span>{}</span>'
            '</a>'
            '{}{}{}'
            '<div class="km-u-dropdown-divider"></div>'
            '<a href="{}" class="km-u-dropdown-item km-u-dropdown-item--danger">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-delete"></use></svg>'
            '<span>{}</span>'
            '</a>'
            '</div>'
            '</details>'
            '</div>',
            change_url,
            _("Редактировать"),
            _("Редактировать"),
            _("Действия"),
            _("Действия"),
            change_url,
            _("Открыть профиль"),
            password_url,
            _("Сменить пароль"),
            toggle_url,
            toggle_class,
            obj.pk,
            obj.get_full_name() or obj.username,
            "1" if obj.is_active else "0",
            toggle_icon,
            toggle_label,
            places_item,
            reqs_item,
            revs_item,
            delete_url,
            _("Удалить"),
        )

    row_actions = user_actions

    def _build_user_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
        return build_admin_query_string(request, clear=clear, **updates)

    def _user_quick_filters(self, request):
        current = request.GET.get("is_active__exact")
        keys = ("is_active__exact",)
        base = SiteRegisteredUser.objects.filter(is_staff=False, is_superuser=False)

        return (
            {
                "id": "all",
                "label": _("Все пользователи"),
                "url": self._build_user_changelist_query_string(request, clear=keys),
                "active": current not in {"0", "1"},
                "count": base.count(),
            },
            {
                "id": "active",
                "label": _("Активные"),
                "url": self._build_user_changelist_query_string(request, clear=keys, is_active__exact="1"),
                "active": current == "1",
                "count": base.filter(is_active=True).count(),
            },
            {
                "id": "inactive",
                "label": _("Неактивные"),
                "url": self._build_user_changelist_query_string(request, clear=keys, is_active__exact="0"),
                "active": current == "0",
                "count": base.filter(is_active=False).count(),
            },
        )

    def changelist_view(self, request, extra_context=None):
        can_add = self.has_add_permission(request)
        add_url = reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_add") if can_add else ""

        applied_filters = []
        if request.GET.get("q"):
            q_val = request.GET.get("q")
            applied_filters.append({
                "name": "q",
                "label": _("Поиск: «%(q)s»") % {"q": q_val},
                "clear_url": self._build_user_changelist_query_string(request, clear=("q",)),
            })
        if request.GET.get("has_phone"):
            p_val = request.GET.get("has_phone")
            lbl = _("С телефоном") if p_val == "yes" else _("Без телефона")
            applied_filters.append({
                "name": "has_phone",
                "label": lbl,
                "clear_url": self._build_user_changelist_query_string(request, clear=("has_phone",)),
            })
        if request.GET.get("has_places"):
            pl_val = request.GET.get("has_places")
            lbl = _("Есть места") if pl_val == "yes" else _("Нет мест")
            applied_filters.append({
                "name": "has_places",
                "label": lbl,
                "clear_url": self._build_user_changelist_query_string(request, clear=("has_places",)),
            })
        if request.GET.get("has_login"):
            l_val = request.GET.get("has_login")
            lbl = _("Входил на сайт") if l_val == "yes" else _("Не входил")
            applied_filters.append({
                "name": "has_login",
                "label": lbl,
                "clear_url": self._build_user_changelist_query_string(request, clear=("has_login",)),
            })
        if request.GET.get("profile__gender__exact"):
            g_val = request.GET.get("profile__gender__exact")
            g_map = {"M": _("Мужской"), "F": _("Женский"), "U": _("Пол не указан")}
            applied_filters.append({
                "name": "profile__gender__exact",
                "label": g_map.get(g_val, g_val),
                "clear_url": self._build_user_changelist_query_string(request, clear=("profile__gender__exact",)),
            })

        curr_o = request.GET.get("o", "-5")
        sort_choices = [
            {"val": "-5", "label": _("Последний вход (новые)"), "url": self._build_user_changelist_query_string(request, o="-5"), "active": curr_o == "-5"},
            {"val": "5", "label": _("Последний вход (старые)"), "url": self._build_user_changelist_query_string(request, o="5"), "active": curr_o == "5"},
            {"val": "-4", "label": _("Регистрация (новые)"), "url": self._build_user_changelist_query_string(request, o="-4"), "active": curr_o in ("-4", "")},
            {"val": "4", "label": _("Регистрация (старые)"), "url": self._build_user_changelist_query_string(request, o="4"), "active": curr_o == "4"},
            {"val": "0", "label": _("Имя (А-Я)"), "url": self._build_user_changelist_query_string(request, o="0"), "active": curr_o == "0"},
            {"val": "-0", "label": _("Имя (Я-А)"), "url": self._build_user_changelist_query_string(request, o="-0"), "active": curr_o == "-0"},
        ]
        active_sort = next((s for s in sort_choices if s["active"]), sort_choices[0])

        extra = {
            "km_primary_quick_filters": self._user_quick_filters(request),
            "km_secondary_quick_filters": [],
            "title": _("Пользователи сайта"),
            "subtitle": _("Управление зарегистрированными пользователями KidsMap"),
            "can_add_user": can_add,
            "add_user_url": add_url,
            "applied_filters": applied_filters,
            "has_applied_filters": bool(applied_filters),
            "reset_all_filters_url": self._build_user_changelist_query_string(request, clear=("q", "has_phone", "has_places", "has_login", "profile__gender__exact", "is_active__exact")),
            "sort_choices": sort_choices,
            "active_sort": active_sort,
            "current_phone_filter": request.GET.get("has_phone", ""),
            "current_places_filter": request.GET.get("has_places", ""),
            "current_login_filter": request.GET.get("has_login", ""),
            "current_gender_filter": request.GET.get("profile__gender__exact", ""),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra)


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
