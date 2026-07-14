from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
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
from catalog.services.features import is_events_section_enabled, is_specialists_section_enabled

# Clarify similar names in admin navigation.
SiteReview._meta.verbose_name = _("Отзыв о сайте")
SiteReview._meta.verbose_name_plural = _("Отзывы о сайте")
PlaceChangeAudit._meta.verbose_name_plural = _("История изменений карточек")

_original_get_app_list = admin.site.get_app_list
_original_each_context = admin.site.each_context


def _get_sidebar_metrics(request) -> dict[str, int]:
    """Build admin sidebar counters once per request with one aggregate per model."""
    cached = getattr(request, "_kidsmap_sidebar_metrics", None)
    if cached is not None:
        return cached

    empty_metrics = {
        "places_total": 0,
        "places_active": 0,
        "places_pending": 0,
        "places_deleted": 0,
        "events_total": 0,
        "events_active": 0,
        "events_pending": 0,
        "specialists_total": 0,
        "specialists_active": 0,
        "specialists_pending": 0,
        "place_reviews_pending": 0,
        "specialist_reviews_pending": 0,
        "ownership_pending": 0,
    }
    if not request.user.is_authenticated or not request.user.is_staff:
        request._kidsmap_sidebar_metrics = empty_metrics
        return empty_metrics

    now = timezone.now()
    place_counts = Place.objects.aggregate(
        total=Count("pk", filter=Q(deleted_at__isnull=True, is_temporary=False)),
        active=Count(
            "pk",
            filter=Q(
                deleted_at__isnull=True,
                is_temporary=False,
                is_active=True,
                status=Place.STATUS_PUBLISHED,
            ),
        ),
        pending=Count(
            "pk",
            filter=Q(
                deleted_at__isnull=True,
                is_temporary=False,
                status=Place.STATUS_PENDING,
            ),
        ),
        deleted=Count("pk", filter=Q(deleted_at__isnull=False)),
    )
    event_counts = Event.objects.aggregate(
        total=Count("pk", filter=Q(deleted_at__isnull=True)),
        active=Count(
            "pk",
            filter=Q(
                deleted_at__isnull=True,
                status=Event.STATUS_PUBLISHED,
                start_datetime__isnull=False,
                end_datetime__gte=now,
            ),
        ),
        pending=Count(
            "pk",
            filter=Q(deleted_at__isnull=True, status=Event.STATUS_PENDING),
        ),
    )
    specialist_counts = Specialist.objects.aggregate(
        total=Count("pk"),
        active=Count(
            "pk",
            filter=Q(status=Specialist.STATUS_PUBLISHED, is_active=True),
        ),
        pending=Count("pk", filter=Q(status=Specialist.STATUS_PENDING)),
    )
    place_review_counts = PlaceReview.objects.aggregate(
        pending=Count("pk", filter=Q(status=PlaceReview.STATUS_PENDING)),
    )
    specialist_review_counts = SpecialistReview.objects.aggregate(
        pending=Count("pk", filter=Q(status=SpecialistReview.STATUS_PENDING)),
    )
    ownership_counts = PlaceOwnershipRequest.objects.aggregate(
        pending=Count("pk", filter=Q(status=PlaceOwnershipRequest.STATUS_PENDING)),
    )
    metrics = {
        "places_total": int(place_counts["total"] or 0),
        "places_active": int(place_counts["active"] or 0),
        "places_pending": int(place_counts["pending"] or 0),
        "places_deleted": int(place_counts["deleted"] or 0),
        "events_total": int(event_counts["total"] or 0),
        "events_active": int(event_counts["active"] or 0),
        "events_pending": int(event_counts["pending"] or 0),
        "specialists_total": int(specialist_counts["total"] or 0),
        "specialists_active": int(specialist_counts["active"] or 0),
        "specialists_pending": int(specialist_counts["pending"] or 0),
        "place_reviews_pending": int(place_review_counts["pending"] or 0),
        "specialist_reviews_pending": int(specialist_review_counts["pending"] or 0),
        "ownership_pending": int(ownership_counts["pending"] or 0),
    }
    request._kidsmap_sidebar_metrics = metrics
    return metrics


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
    sidebar_metrics = _get_sidebar_metrics(request)
    ownership_pending_count = sidebar_metrics["ownership_pending"]
    review_pending_count = sidebar_metrics["place_reviews_pending"]
    specialist_review_pending_count = sidebar_metrics["specialist_reviews_pending"]
    specialist_pending_count = sidebar_metrics["specialists_pending"]

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
            "specialist": 11,
            "specialistspecialization": 12,
            "placechangeaudit": 20,
            "placereview": 30,
            "specialistreview": 31,
            "sitereview": 40,
            "placereviewsbyclub": 50,
            "userprofile": 60,
            "useremailverification": 70,
            "region": 80,
            "district": 81,
            "metrostation": 82,
        }
        display_name_overrides = {
            "sitereview": _("Отзывы о сайте"),
            "placereview": _("Отзывы по кружкам"),
            "specialistreview": _("Отзывы о специалистах"),
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
            if object_name == "specialist" and specialist_pending_count:
                model["name"] = _("%(name)s (модерация: %(count)s)") % {
                    "name": model["name"],
                    "count": specialist_pending_count,
                }
            if object_name == "specialistreview" and specialist_review_pending_count:
                model["name"] = _("%(name)s (проверка: %(count)s)") % {
                    "name": model["name"],
                    "count": specialist_review_pending_count,
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
    show_badge: bool = False,
    badge_label: str = "",
    status_label: str = "",
    url_name: str | None = None,
    active_models: tuple | list | None = None,
    query_params: str | None = None,
    required_permission: str = "view",
):
    model_admin = admin.site._registry.get(model) if model is not None else None
    if model_admin is not None:
        if required_permission == "add":
            is_allowed = model_admin.has_add_permission(request)
        else:
            is_allowed = model_admin.has_view_or_change_permission(request)
        if not is_allowed:
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
    # A custom URL (for example, the "add staff member" form) must only be
    # active for that URL.  Falling back to the model changelist here made the
    # add link active together with the changelist link on every staff page.
    if active_models is None:
        models_for_active_state = () if url_name else (() if model is None else (model,))
    else:
        models_for_active_state = active_models

    for active_model in models_for_active_state:
        try:
            prefixes.append(
                reverse(
                    f"admin:{active_model._meta.app_label}_{active_model._meta.model_name}_changelist"
                )
            )
        except NoReverseMatch:
            continue

    is_active_path = _path_matches_any_prefix(request.path, prefixes)
    # An add form has its own navigation entry when available. Do not also
    # highlight the parent changelist merely because its URL is a prefix.
    is_add_view_without_dedicated_item = request.path.rstrip("/").endswith("/add") and not url_name
    if query_params:
        from urllib.parse import parse_qsl
        expected_params = dict(parse_qsl(query_params))
        active = (
            is_active_path
            and not is_add_view_without_dedicated_item
            and all(request.GET.get(k) == v for k, v in expected_params.items())
        )
    else:
        active = (
            is_active_path
            and not is_add_view_without_dedicated_item
            and not (request.GET.get("deleted_state") == "deleted" or request.GET.get("deleted_at__isnull") == "False")
        )

    return {
        "label": str(label),
        "url": url,
        "icon": icon,
        "active": active,
        "badge_count": max(int(badge_count or 0), 0),
        "show_badge": show_badge,
        "badge_label": str(badge_label or ""),
        "status_label": str(status_label or ""),
    }


def _build_sidebar_sections(request, *, metrics: dict[str, int]) -> list[dict]:
    if not request.user.is_authenticated or not request.user.is_staff:
        return []

    raw_sections = [
        {
            "key": "catalog",
            "label": _("Каталог"),
            "icon": "far fa-folder-open",
            "items": [
                _build_sidebar_item(
                    request,
                    model=Place,
                    label=_("Постоянные места"),
                    icon="fas fa-map-marker-alt",
                    query_params="is_temporary__exact=0",
                    badge_label=str(metrics["places_total"]),
                ),
                _build_sidebar_item(
                    request,
                    model=Event,
                    label=_("Временные мероприятия"),
                    icon="fas fa-calendar-alt",
                    badge_label=str(metrics["events_total"]),
                    status_label=_("Скрыто на сайте") if not is_events_section_enabled() else "",
                ),
                _build_sidebar_item(
                    request,
                    model=Specialist,
                    label=_("Специалисты"),
                    icon="fas fa-user-tie",
                    badge_label=str(metrics["specialists_total"]),
                    status_label=_("Скрыто на сайте") if not is_specialists_section_enabled() else "",
                ),
                _build_sidebar_item(
                    request,
                    model=PlaceReview,
                    label=_("Отзывы"),
                    icon="far fa-star",
                ),
                _build_sidebar_item(
                    request,
                    model=Place,
                    label=_("Корзина"),
                    icon="fas fa-trash-alt",
                    query_params="deleted_state=deleted",
                    badge_count=metrics["places_deleted"],
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
                    model=Place,
                    label=_("Места на проверке"),
                    icon="fas fa-map-marker-alt",
                    url_name="admin:catalog_moderation_moderationplace_changelist",
                    badge_count=metrics["places_pending"],
                    show_badge=True,
                ),
                _build_sidebar_item(
                    request,
                    model=Event,
                    label=_("Мероприятия на проверке"),
                    icon="fas fa-calendar-alt",
                    url_name="admin:catalog_moderation_moderationevent_changelist",
                    badge_count=metrics["events_pending"],
                    show_badge=True,
                ),
                _build_sidebar_item(
                    request,
                    model=Specialist,
                    label=_("Специалисты на проверке"),
                    icon="fas fa-user-tie",
                    url_name="admin:catalog_moderation_moderationspecialist_changelist",
                    badge_count=metrics["specialists_pending"],
                    show_badge=True,
                ),
                _build_sidebar_item(
                    request,
                    model=PlaceReview,
                    label=_("Отзывы на проверке"),
                    icon="fas fa-star-half-alt",
                    url_name="admin:catalog_moderation_moderationreview_changelist",
                    badge_count=metrics["place_reviews_pending"],
                    show_badge=True,
                ),
                _build_sidebar_item(
                    request,
                    model=PlaceOwnershipRequest,
                    label=_("Заявки на владение"),
                    icon="far fa-clipboard",
                    badge_count=metrics["ownership_pending"],
                    show_badge=True,
                ),
            ],
        },
        {
            "key": "directories",
            "label": _("Справочники"),
            "icon": "fas fa-map-marked-alt",
            "items": [
                _build_sidebar_item(request, model=Category, label=_("Категории"), icon="far fa-copy"),
                _build_sidebar_item(request, model=Subcategory, label=_("Подкатегории"), icon="far fa-clone"),
                _build_sidebar_item(request, model=SpecialistSpecialization, label=_("Специализации"), icon="fas fa-graduation-cap"),
                _build_sidebar_item(request, model=Region, label=_("Регионы и города"), icon="fas fa-globe"),
                _build_sidebar_item(request, model=District, label=_("Районы"), icon="fas fa-map-signs"),
                _build_sidebar_item(request, model=MetroStation, label=_("Станции метро"), icon="fas fa-subway"),
            ],
        },
        {
            "key": "users",
            "label": _("Пользователи и доступ"),
            "icon": "far fa-user",
            "items": [
                _build_sidebar_item(request, model=SiteRegisteredUser, label=_("Все пользователи"), icon="far fa-user"),
                _build_sidebar_item(
                    request,
                    model=SiteRegisteredUser,
                    label=_("Владельцы"),
                    icon="fas fa-store",
                    query_params="profile__role__exact=owner",
                ),
                _build_sidebar_item(
                    request,
                    model=StaffAccessUser,
                    label=_("Добавить администратора"),
                    icon="fas fa-user-plus",
                    url_name="admin:catalog_staffaccessuser_add",
                    required_permission="add",
                ),
                _build_sidebar_item(
                    request,
                    model=StaffAccessUser,
                    label=_("Список администраторов"),
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
                _build_sidebar_item(request, model=PlaceReviewsByClub, label=_("Популярный контент"), icon="far fa-star"),
            ],
        },
        {
            "key": "system",
            "label": _("Система"),
            "icon": "fas fa-cogs",
            "items": [
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
    sidebar_metrics = _get_sidebar_metrics(request)
    context["ownership_pending_count"] = sidebar_metrics["ownership_pending"]
    context["review_pending_count"] = sidebar_metrics["place_reviews_pending"]
    context["specialist_review_pending_count"] = sidebar_metrics["specialist_reviews_pending"]
    context["specialist_pending_count"] = sidebar_metrics["specialists_pending"]

    current_language = (get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    context["admin_current_language"] = current_language
    context["admin_language_switch_items"] = _build_admin_language_switch_items(request, current_language)
    context["kidsmap_sidebar_sections"] = _build_sidebar_sections(request, metrics=sidebar_metrics)
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
from .specialist import *
