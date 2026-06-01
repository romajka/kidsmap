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

from catalog.models import *
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.admin_analytics import build_site_analytics_context
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
    pending_count = (
        Place.objects.filter(status=Place.STATUS_PENDING, deleted_at__isnull=True).count()
        + Event.objects.filter(status=Event.STATUS_PENDING, deleted_at__isnull=True).count()
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
            if object_name == "placeownershiprequest" and pending_count:
                model["name"] = _("%(name)s (на рассмотрении: %(count)s)") % {
                    "name": model["name"],
                    "count": pending_count,
                }
        app["models"].sort(
            key=lambda model: (
                priority.get(model.get("object_name", "").lower(), 999),
                model.get("name", ""),
            )
        )
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

    current_language = (get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    context["admin_current_language"] = current_language
    context["admin_language_switch_items"] = _build_admin_language_switch_items(request, current_language)
    return context


admin.site.get_app_list = _kidsmap_get_app_list.__get__(admin.site, type(admin.site))
admin.site.each_context = _kidsmap_each_context.__get__(admin.site, type(admin.site))

from .user import *
from .review import *
from .owner import *
from .site import *
from .place import *
