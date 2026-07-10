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
from django.urls import NoReverseMatch, path, reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _, ngettext

from catalog.models import *
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.content_quality import place_quality_check, review_quality_check
from catalog.services.geocoding import PlaceGeocodingService

# Clarify similar names in admin navigation.
SiteReview._meta.verbose_name = _("Отзыв о сайте")
SiteReview._meta.verbose_name_plural = _("Отзывы о сайте")
PlaceChangeAudit._meta.verbose_name_plural = _("История изменений карточек")

_original_get_app_list = admin.site.get_app_list
_original_each_context = admin.site.each_context


def _build_admin_language_switch_items(request, current_language: str):
    lang_codes = [str(code).split("-")[0] for code, _label in settings.LANGUAGES]
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
        next_path = base_path if code == default_lang else f"/{code}{base_path}"
        items.append(
            {
                "code": code,
                "url": request.build_absolute_uri(next_path),
                "active": code == current_language,
            }
        )
    return items


def _kidsmap_get_app_list(self, request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    ownership_pending_count = PlaceOwnershipRequest.objects.filter(
        status=PlaceOwnershipRequest.STATUS_PENDING
    ).count()
    review_pending_count = PlaceReview.objects.filter(status=PlaceReview.STATUS_PENDING).count()
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
            "event": 8,
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
            if object_name == "placeownershiprequest" and ownership_pending_count:
                model["name"] = _("%(name)s (на рассмотрении: %(count)s)") % {
                    "name": model["name"],
                    "count": ownership_pending_count,
                }
            if object_name == "placereview" and review_pending_count:
                model["name"] = _("%(name)s (на проверке: %(count)s)") % {
                    "name": model["name"],
                    "count": review_pending_count,
                }
        app["models"].sort(
            key=lambda model: (
                priority.get(model.get("object_name", "").lower(), 999),
                model.get("name", ""),
            )
        )
    return app_list


def _admin_role_label(user) -> str:
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return str(_("Администратор"))
    return str(_("Пользователь"))


def _normalize_admin_path(path_value: str) -> str:
    base = str(path_value or "").split("?", 1)[0].rstrip("/")
    return f"{base}/" if base else "/"


def _path_matches_any_prefix(request_path: str, prefixes: list[str]) -> bool:
    current_path = _normalize_admin_path(request_path)
    return any(current_path.startswith(_normalize_admin_path(prefix)) for prefix in prefixes if prefix)


def _build_sidebar_item(
    request,
    *,
    model=None,
    label,
    icon,
    badge_count: int = 0,
    url_name: str | None = None,
    active_models: tuple | list | None = None,
    query_params: str | None = None,
):
    model_admin = admin.site._registry.get(model) if model is not None else None
    if model_admin is not None and not model_admin.has_view_or_change_permission(request):
        return None

    if model is not None:
        resolved_url_name = url_name or f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
    else:
        resolved_url_name = url_name

    if not resolved_url_name:
        return None

    try:
        url = reverse(resolved_url_name)
        if query_params:
            url = f"{url}?{query_params}"
    except NoReverseMatch:
        return None

    prefixes = [url.split("?", 1)[0]]
    for active_model in active_models or (() if model is None else (model,)):
        try:
            prefixes.append(
                reverse(
                    f"admin:{active_model._meta.app_label}_{active_model._meta.model_name}_changelist"
                )
            )
        except NoReverseMatch:
            continue

    is_active_path = _path_matches_any_prefix(request.path, prefixes)
    if query_params:
        from urllib.parse import parse_qsl
        expected_params = dict(parse_qsl(query_params))
        active = is_active_path and all(request.GET.get(k) == v for k, v in expected_params.items())
    else:
        active = is_active_path and not (request.GET.get("deleted_state") == "deleted" or request.GET.get("deleted_at__isnull") == "False")

    return {
        "label": str(label),
        "url": url,
        "icon": icon,
        "active": active,
        "badge_count": max(int(badge_count or 0), 0),
    }


def _build_sidebar_sections(request, *, ownership_pending_count: int, review_pending_count: int, deleted_count: int) -> list[dict]:
    if not request.user.is_authenticated or not request.user.is_staff:
        return []

    raw_sections = [
        {
            "key": "catalog",
            "label": _("Каталог"),
            "icon": "far fa-folder-open",
            "items": [
                _build_sidebar_item(request, model=Place, label=_("Места"), icon="fas fa-map-marker-alt"),
                _build_sidebar_item(request, model=Category, label=_("Категории"), icon="far fa-copy"),
                _build_sidebar_item(
                    request,
                    model=PlaceReview,
                    label=_("Отзывы о местах"),
                    icon="far fa-comment-alt",
                    badge_count=review_pending_count,
                ),
                _build_sidebar_item(request, model=PlaceReviewsByClub, label=_("Рейтинги"), icon="far fa-star"),
                _build_sidebar_item(
                    request,
                    model=Place,
                    label=_("Корзина"),
                    icon="fas fa-trash-alt",
                    query_params="deleted_state=deleted",
                    badge_count=deleted_count,
                ),
            ],
        },
        {
            "key": "moderation",
            "label": _("Модерация"),
            "icon": "far fa-shield-alt",
            "items": [
                _build_sidebar_item(
                    request,
                    model=PlaceOwnershipRequest,
                    label=_("Заявки на владение"),
                    icon="far fa-clipboard",
                    badge_count=ownership_pending_count,
                ),
                _build_sidebar_item(
                    request,
                    model=PlaceReview,
                    label=_("Отзывы на проверке"),
                    icon="fas fa-star-half-alt",
                    query_params="status__exact=pending",
                    badge_count=review_pending_count,
                ),
                _build_sidebar_item(request, model=SiteReview, label=_("Отзывы о сайте"), icon="far fa-comment-dots"),
                _build_sidebar_item(
                    request,
                    model=UserEmailVerification,
                    label=_("Подтверждения email"),
                    icon="far fa-envelope",
                ),
            ],
        },
        {
            "key": "users",
            "label": _("Пользователи"),
            "icon": "far fa-user",
            "items": [
                _build_sidebar_item(request, model=SiteRegisteredUser, label=_("Пользователи сайта"), icon="far fa-user"),
                _build_sidebar_item(
                    request,
                    model=StaffAccessUser,
                    label=_("Сотрудники админки"),
                    icon="fas fa-user-shield",
                ),
                _build_sidebar_item(
                    request,
                    model=OwnerTeamMembership,
                    label=_("Команды владельцев"),
                    icon="fas fa-users",
                    active_models=(OwnerTeamMembership, OwnerTeamInvitation),
                ),
            ],
        },
        {
            "key": "content",
            "label": _("Контент сайта"),
            "icon": "far fa-images",
            "items": [
                _build_sidebar_item(request, model=SiteGalleryImage, label=_("Фото и баннеры"), icon="far fa-image"),
                _build_sidebar_item(
                    request,
                    model=SiteSettings,
                    label=_("Настройки сайта"),
                    icon="fas fa-cog",
                    active_models=(
                        SiteSettings,
                        SiteBrandingSettings,
                        SiteAboutSettings,
                        SiteContactsSettings,
                        SiteFooterSettings,
                        SiteEmptyStateSettings,
                        CatalogContentSettings,
                    ),
                ),
            ],
        },
        {
            "key": "analytics",
            "label": _("Аналитика"),
            "icon": "fas fa-chart-line",
            "items": [
                _build_sidebar_item(request, model=SiteAnalytics, label=_("Статистика"), icon="far fa-chart-bar"),
                _build_sidebar_item(
                    request,
                    model=PlaceChangeAudit,
                    label=_("История изменений"),
                    icon="far fa-clock",
                    active_models=(PlaceChangeAudit, PlaceOwnershipRequestAudit),
                ),
            ],
        },
    ]

    sections: list[dict] = []
    for section in raw_sections:
        items = [item for item in section["items"] if item]
        if not items:
            continue
        sections.append(
            {
                "key": section["key"],
                "label": str(section["label"]),
                "icon": section["icon"],
                "items": items,
                "active": any(item["active"] for item in items),
            }
        )
    return sections


def _kidsmap_each_context(self, request):
    context = _original_each_context(request)
    if request.user.is_authenticated and request.user.is_staff:
        ownership_pending_count = PlaceOwnershipRequest.objects.filter(
            status=PlaceOwnershipRequest.STATUS_PENDING
        ).count()
        review_pending_count = PlaceReview.objects.filter(status=PlaceReview.STATUS_PENDING).count()
        deleted_count = Place.objects.filter(deleted_at__isnull=False).count()
    else:
        ownership_pending_count = 0
        review_pending_count = 0
        deleted_count = 0
    context["ownership_pending_count"] = ownership_pending_count
    context["review_pending_count"] = review_pending_count

    current_language = (get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    context["admin_current_language"] = current_language
    context["admin_language_switch_items"] = _build_admin_language_switch_items(request, current_language)
    context["kidsmap_sidebar_sections"] = _build_sidebar_sections(
        request,
        ownership_pending_count=ownership_pending_count,
        review_pending_count=review_pending_count,
        deleted_count=deleted_count,
    )
    context["kidsmap_admin_role_label"] = _admin_role_label(request.user)
    return context


admin.site.get_app_list = _kidsmap_get_app_list.__get__(admin.site, type(admin.site))
admin.site.each_context = _kidsmap_each_context.__get__(admin.site, type(admin.site))

from .user import *
from .review import *
from .owner import *
from .site import *
from .category import *
from .place import *
