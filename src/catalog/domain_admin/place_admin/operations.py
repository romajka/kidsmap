"""PlaceAdmin: custom admin views, URLs, bulk actions and soft delete."""

import json
from django.contrib import admin, messages
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext

from catalog.models import (
    Place,
    PlaceChangeAudit,
    SiteSettings,
    VolunteerPlaceRevision,
)
from catalog.services.content_quality import (
    place_quality_check,
    public_place_queryset,
)
from catalog.services.place_identity_copy import identity_copy
from catalog.services.place_readiness import (
    evaluate_saved_place_readiness,
    format_readiness_issues,
)
from catalog.services.pricing_plans import normalize_pricing_plans
from catalog.services.place_card_validation import validate_place_card
from .common import HOME_RECOMMENDATIONS_MAX_ITEMS, HOME_RECOMMENDATIONS_MIN_ITEMS


class PlaceAdminOperationsMixin:
    """Custom admin views, URLs, bulk actions and soft delete."""

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        from catalog.services.staff_roles import is_volunteer
        if is_volunteer(request.user): actions.pop('connect_to_organization',None)
        return actions

    def has_connection_permission(self,request):
        from catalog.services.staff_roles import is_volunteer
        from catalog.services.organization_ownership import _reviewer
        if is_volunteer(request.user) or not self.has_view_permission(request):return False
        if self.has_change_permission(request):return True
        try:_reviewer(request.user)
        except PermissionDenied:return False
        return True

    def connect_to_organization(self,request,queryset):
        from catalog.domain_admin.organization_connections import connect_to_organization
        return connect_to_organization(self,request,queryset)
    connect_to_organization.short_description = _('Подключить к организации')
    connect_to_organization.allowed_permissions = ['connection']

    def organization_connections_view(self,request):
        from catalog.domain_admin.organization_connections import organization_connections_view
        return organization_connections_view(self,request)

    def place_state_rules(self, obj: Place, user) -> dict[str, tuple[str, str]]:
        """One transition matrix for row actions; labels stay visible when disabled."""
        no_rights = str(_("Недостаточно прав для этого действия."))
        deleted = bool(obj.is_deleted)
        can_change = bool(getattr(user, "is_superuser", False) or user.has_perm("catalog.change_place"))
        can_delete = bool(getattr(user, "is_superuser", False) or user.has_perm("catalog.delete_place"))
        published = obj.status == Place.STATUS_PUBLISHED and obj.is_active
        quality = place_quality_check(obj)

        def rule(ok: bool, reason: str = no_rights):
            return ("allowed", "") if ok else ("disabled", reason)

        publish = rule(not deleted and can_change)
        if publish[0] == "allowed" and not published and not evaluate_saved_place_readiness(obj).is_ready:
            publish = ("conditional", format_readiness_issues(evaluate_saved_place_readiness(obj)))
        home = rule(not deleted and can_change)
        if home[0] == "allowed" and not obj.is_home_recommended and (not published or quality.score < 100):
            home = ("conditional", str(_("На главную можно поставить только опубликованную карточку с готовностью 100%.")))
        return {
            "toggle_pub": publish,
            "to_draft": rule(not deleted and can_change and obj.status != Place.STATUS_DRAFT, str(_("Карточка уже в черновике."))),
            "to_pending": rule(not deleted and can_change and obj.status != Place.STATUS_PENDING, str(_("Карточка уже на модерации."))),
            "refresh_coords": rule(not deleted and can_change),
            "toggle_home": home,
            "soft_delete": rule(not deleted and can_delete),
            "restore": rule(deleted and can_change, str(_("Восстановить можно только карточку из удалённых."))),
        }

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
        if geocoding_result.reason == "location_unresolved":
            from catalog.services.location_assignment import UNRESOLVED_MESSAGE
            return str(UNRESOLVED_MESSAGE), messages.WARNING
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

    def _handle_publish_submit(self, request, obj: Place):
        from catalog.services.publication import publish
        try:
            publish(actor=request.user,place_id=obj.pk,expected_version=obj.content_version)
        except ValidationError as exc:
            self.message_user(request,"; ".join(exc.messages),level=messages.WARNING)
            return HttpResponseRedirect(self._place_change_url(obj))
        from catalog.services.place_editor_feedback import queue_editor_result
        queue_editor_result(request, action="publish", message=_("Карточка опубликована — уже видна на сайте"))
        self.message_user(request, _("Карточка опубликована — уже видна на сайте"), level=messages.SUCCESS)
        return HttpResponseRedirect(reverse("admin:catalog_place_change", args=[obj.pk], current_app=self.admin_site.name))

    def _handle_unpublish_submit(self, request, obj: Place):
        from catalog.services.publication import unpublish
        try:
            unpublish(actor=request.user, target_type="place", target_id=obj.pk,
                      expected_version=obj.content_version)
        except ValidationError as exc:
            self.message_user(request, "; ".join(exc.messages), level=messages.ERROR)
        else:
            self.message_user(request, _("Карточка снята с публикации и скрыта с сайта."), level=messages.SUCCESS)
        return HttpResponseRedirect(self._place_change_url(obj))

    def site_preview_view(self, request, object_id):
        from django.shortcuts import get_object_or_404
        from catalog.services.admin_place_preview import build_place_preview
        from catalog.services.admin_site_preview import render_site_preview
        obj = get_object_or_404(self.get_queryset(request), pk=object_id)
        concrete_admin = self.admin_site._registry[Place]
        if not concrete_admin.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        language = request.GET.get("lang", getattr(request, "LANGUAGE_CODE", "ru"))
        language = language if language in ("az", "ru", "en") else "ru"
        back = reverse("admin:catalog_place_change", args=[obj.pk], current_app=self.admin_site.name)
        preview = build_place_preview(obj, language=language)
        return render_site_preview(request, preview, language=language, back_url=back)

    def localized_url_preview_view(self, request):
        from django.shortcuts import get_object_or_404
        from catalog.services.staff_roles import can_use_volunteer_workspace
        from catalog.services.volunteer_places import own_places
        from catalog.services.place_urls import build_place_public_slug, place_paths_by_language, place_slug_for_language
        from catalog.services.public_urls import build_public_absolute_uri

        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
        try:
            payload = json.loads(request.body)
            if not isinstance(payload, dict):
                raise ValueError
            pk = payload.get("pk")
            if pk is not None and (isinstance(pk, bool) or not str(pk).isdigit()):
                raise ValueError
            for language in ("az", "ru", "en"):
                value = payload.get(f"name_{language}", "")
                if not isinstance(value, str) or len(value) > 1000:
                    raise ValueError
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"error": "Invalid preview payload"}, status=400)
        volunteer = can_use_volunteer_workspace(request.user)
        obj = None
        if pk is not None:
            queryset = own_places(request.user) if volunteer else self.get_queryset(request)
            obj = get_object_or_404(queryset, pk=pk)
            if not volunteer and not self.has_view_or_change_permission(request, obj):
                raise PermissionDenied
        elif not volunteer and not self.has_add_permission(request):
            raise PermissionDenied
        urls_fixed = bool(obj and obj.uses_slug_only_urls and obj.public_slug_az)
        pending_publication = obj is None or bool(obj.uses_slug_only_urls and not urls_fixed)
        paths = place_paths_by_language(obj) if obj and not pending_publication else {}
        names = {language: payload.get(f'name_{language}', getattr(obj, f'name_{language}', ''))
                 for language in ('az', 'ru', 'en')}
        fallback = next((value for value in names.values() if value), '')
        urls = {}
        for language in ("az", "ru", "en"):
            if pending_publication:
                slug = build_place_public_slug(names[language] or fallback)
            elif urls_fixed:
                slug = getattr(obj, f'public_slug_{language}')
            else:
                slug = place_slug_for_language(obj, language)
            path = paths.get(language)
            urls[language] = {"slug": slug, "path": path, "url": build_public_absolute_uri(request, path) if path else None}
        return JsonResponse({"urls": urls, "pending_publication": pending_publication,
                             "urls_fixed": urls_fixed,
                             "public": bool(obj and public_place_queryset(Place.objects.all()).filter(pk=obj.pk).exists())})

    def get_urls(self):
        from catalog.controllers.location_resolution import location_resolve
        custom_urls = [
            path("<int:object_id>/site-preview/", self.admin_site.admin_view(require_GET(self.site_preview_view)),
                 name=f"{self.opts.app_label}_{self.opts.model_name}_site_preview"),
            path('organization-connections/',self.admin_site.admin_view(self.organization_connections_view),name=f'{self.opts.app_label}_{self.opts.model_name}_organization_connections'),
            path("location/resolve/", self.admin_site.admin_view(location_resolve), name=f"{self.opts.app_label}_{self.opts.model_name}_location_resolve"),
            path("url-preview/", self.admin_site.admin_view(self.localized_url_preview_view), name=f"{self.opts.app_label}_{self.opts.model_name}_url_preview"),
            path(
                "pricing/import/validate/",
                self.admin_site.admin_view(self.validate_pricing_import_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_pricing_import_validate",
            ),
            path(
                "<int:object_id>/export-json/",
                self.admin_site.admin_view(self.export_place_json_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_export_json",
            ),
            path(
                "<int:object_id>/quality-check/",
                self.admin_site.admin_view(self.place_quality_check_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_quality_check",
            ),
            path(
                "quality-report/",
                self.admin_site.admin_view(self.place_quality_report_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_quality_report",
            ),
            path("duplicate-registry/", self.admin_site.admin_view(self.identity_registry_view),
                 name=f"{self.opts.app_label}_{self.opts.model_name}_identity_registry"),
            path("<int:object_id>/compare-versions/", self.admin_site.admin_view(self.identity_compare_view),
                 name=f"{self.opts.app_label}_{self.opts.model_name}_identity_compare"),
            path(
                "duplicate-candidates/",
                self.admin_site.admin_view(self.duplicate_candidates_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_duplicate_candidates",
            ),
            path(
                "home-recommendations/candidates/",
                self.admin_site.admin_view(self.home_recommendation_candidates_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_home_recommendation_candidates",
            ),
            path(
                "home-recommendations/save/",
                self.admin_site.admin_view(self.save_home_recommendations_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_home_recommendations_save",
            ),
            path(
                "search-suggestions/",
                self.admin_site.admin_view(self.search_suggestions_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_search_suggestions",
            ),
            path(
                "<int:object_id>/toggle-publication/",
                self.admin_site.admin_view(self.toggle_publication_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_toggle_publication",
            ),
            path(
                "<int:object_id>/quick-action/",
                self.admin_site.admin_view(self.quick_action_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_quick_action",
            ),
            path(
                "<path:object_id>/restore/",
                self.admin_site.admin_view(self.restore_view),
                name=f"{self.opts.app_label}_{self.opts.model_name}_restore",
            ),
        ]
        return custom_urls + super().get_urls()

    def place_quality_check_view(self, request, object_id):
        obj = Place.objects.filter(pk=object_id).first()
        if obj is None or not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        if request.method != "POST":
            raise PermissionDenied
        result = validate_place_card(obj)
        context = {
            **self.admin_site.each_context(request),
            "opts": self.opts,
            "original": obj,
            "result": result,
            "change_url": self._place_change_url(obj),
            "title": _("Проверка качества карточки"),
        }
        return TemplateResponse(request, "admin/catalog/place/quality_check.html", context)

    def place_quality_report_view(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        scope = request.GET.get("scope", "all")
        if scope not in {"all", "published"}:
            scope = "all"
        base_places = self.get_queryset(request).filter(is_temporary=False)
        scope_counts = {
            "all": base_places.count(),
            "published": base_places.filter(
                is_active=True,
                status=Place.STATUS_PUBLISHED,
                deleted_at__isnull=True,
            ).count(),
        }
        places = base_places
        if scope == "published":
            places = places.filter(is_active=True, status=Place.STATUS_PUBLISHED, deleted_at__isnull=True)
        places = places.prefetch_related(
            "gallery", "schedule_days__intervals", "pricing_plan_records"
        )
        rows = []
        summary = {"total": 0, "clean": 0, "warnings": 0, "errors": 0}
        for place in places.order_by("pk"):
            result = validate_place_card(place)
            summary["total"] += 1
            if result.errors:
                summary["errors"] += 1
            elif result.warnings:
                summary["warnings"] += 1
            else:
                summary["clean"] += 1
            if result.errors or result.warnings:
                rows.append(
                    {
                        "place": place,
                        "result": result,
                        "change_url": self._place_change_url(place),
                        "public_url": place.get_absolute_url() if place.is_public else "",
                    }
                )
        context = {
            **self.admin_site.each_context(request),
            "opts": self.opts,
            "title": _("Отчёт качества карточек"),
            "summary": summary,
            "scope": scope,
            "scope_counts": scope_counts,
            "rows": rows,
            "changelist_url": reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
                current_app=self.admin_site.name,
            ),
        }
        return TemplateResponse(request, "admin/catalog/place/quality_report.html", context)

    def validate_pricing_import_view(self, request):
        if request.method != "POST":
            return JsonResponse({"ok": False, "error": str(_("Разрешён только POST."))}, status=405)
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": str(_("Некорректный JSON."))}, status=400)
        if not isinstance(payload, dict):
            return JsonResponse({"ok": False, "error": str(_("Нужен один объект карточки."))}, status=400)
        if payload.get("export_scope") in {"duplicate_registry", "identity_comparison"}:
            return JsonResponse({"ok":False,"error":identity_copy()["not_edit_import"]},status=400)
        from catalog.services.publication import SCHEMA_VERSION
        supplied_schema = payload.get("schema_version", SCHEMA_VERSION)
        if isinstance(supplied_schema, bool) or not isinstance(supplied_schema, int) or supplied_schema != SCHEMA_VERSION:
            return JsonResponse({"ok":False,"error":"Publication schema conflict."},status=409)
        current = None
        if payload.get("place_id") is not None:
            place_id = payload["place_id"]
            if isinstance(place_id, bool) or not isinstance(place_id, int) or place_id <= 0:
                return JsonResponse({"ok": False, "error": str(_("place_id должен быть положительным целым числом."))}, status=400)
            current=Place.objects.filter(pk=payload["place_id"]).first()
            if current is None:
                raise PermissionDenied
            if not self.has_change_permission(request, current):
                from catalog.services.staff_roles import is_volunteer
                from catalog.services.volunteer_places import own_places
                if not is_volunteer(request.user) or not own_places(request.user).filter(pk=current.pk).exists():
                    raise PermissionDenied
            supplied_version = payload.get("base_content_version")
            if isinstance(supplied_version, bool) or not isinstance(supplied_version, int) or supplied_version != current.content_version:
                return JsonResponse({"ok":False,"error":"Publication source conflict."},status=409)
            if "candidate_version" in payload:
                revision = VolunteerPlaceRevision.objects.filter(place=current).first()
                supplied_candidate = payload["candidate_version"]
                if (isinstance(supplied_candidate, bool) or not isinstance(supplied_candidate, int)
                        or supplied_candidate != (revision.version if revision else 0)):
                    return JsonResponse({"ok": False, "error": str(_("Рабочая версия карточки изменилась. Получите свежий экспорт."))}, status=409)
        contact_fields = {"phone1", "phone2", "phone3", "phone_country", "whatsapp_mode", "whatsapp_number"}
        try:
            from catalog.services.phone_numbers import normalize_contact_patch
            contacts = {name: payload[name] for name in contact_fields if name in payload}
            # The AI instruction uses null for an unconfirmed WhatsApp mode.
            # Unknown does not claim same/none, and must not overwrite a saved mode.
            if contacts.get('whatsapp_mode') in (None, ''):
                contacts.pop('whatsapp_mode', None)
            if "whatsapp_mode" in contacts and contacts["whatsapp_mode"] not in {"legacy", "same", "separate", "none"}:
                raise ValidationError(_("Проверьте настройку WhatsApp."))
            contacts = normalize_contact_patch(current or Place(), contacts)
        except ValidationError as exc:
            return JsonResponse({"ok": False, "error": exc.messages[0]}, status=400)
        warnings = []
        # Full exports retain historical source data, but importing them must
        # not silently reinterpret or replace excluded legacy model fields.
        if payload.get("pricing_plans_legacy"):
            if current is None or payload["pricing_plans_legacy"] != current.pricing_plans_legacy:
                return JsonResponse({"ok": False, "error": str(_("Старые JSON-тарифы требуют ручной сверки. Используйте свежий экспорт той же карточки."))}, status=400)
            warnings.append(str(_("Старые JSON-тарифы сохранены без преобразования. Тип, единицу и период уточните вручную.")))
        if "pricing_plans" in payload:
            for name in ("price_from", "price_to", "price_per_lesson", "price_per_month", "price_per_8_lessons"):
                if name not in payload:
                    continue
                try:
                    amount = Place._meta.get_field(name).to_python(payload[name])
                except ValidationError:
                    return JsonResponse({"ok": False, "error": str(_("Проверьте старые поля цены."))}, status=400)
                if amount is not None and (current is None or amount != getattr(current, name)):
                    return JsonResponse({"ok": False, "error": str(_("Старые поля цены в полном экспорте доступны для сверки. Изменяйте цену через тарифы."))}, status=400)
        raw_plans = payload.get("pricing_plans")
        if raw_plans is None:
            raw_plans = payload.get("tariffs")
        if raw_plans is None:
            raw_plans = []
            legacy_specs = (
                ("price_per_lesson", {"product_type": "lesson", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "lesson"}),
                ("price_per_month", {"product_type": "membership", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1}),
                ("price_per_8_lessons", {"product_type": "lesson", "billing_mode": "one_time", "quantity": 8, "quantity_unit": "lesson"}),
            )
            for key, base in legacy_specs:
                if payload.get(key) is not None:
                    amount = payload[key]
                    raw_plans.append({**base, "price_kind": "free" if str(amount) in {"0", "0.0", "0.00"} else "exact", "price": amount})
            if payload.get("price_from") is not None or payload.get("price_to") is not None:
                warnings.append(str(_("price_from/price_to не создают тариф: неизвестен продаваемый продукт.")))
        try:
            from catalog.services.staff_roles import is_volunteer
            from catalog.services.pricing_plans import validate_pricing_import_keys, validate_nested_pricing_import_keys
            validate_pricing_import_keys(raw_plans)
            validate_nested_pricing_import_keys(payload.get("nested_pricing"))
            plans = normalize_pricing_plans(raw_plans, allow_verified=request.user.is_staff and not is_volunteer(request.user), legacy_place=current)
            if payload.get("place_id") is not None:
                from catalog.services.pricing_plans import validate_target_plan_ids
                validate_target_plan_ids(current, plans)
            nested = None
            if payload.get("nested_pricing") is not None:
                from catalog.services.pricing_plans import validate_nested_pricing
                if payload.get("place_id") is None:
                    raise ValidationError(_("Вложенные тарифы требуют существующую карточку."))
                nested = validate_nested_pricing(current, payload["nested_pricing"], allow_verified=request.user.is_staff and not is_volunteer(request.user))
        except ValidationError as exc:
            return JsonResponse({"ok": False, "error": exc.messages[0]}, status=400)
        return JsonResponse({"ok": True, "pricing_plans": plans, "nested_pricing": nested, "warnings": warnings, "contacts": contacts})

    def export_place_json_view(self, request, object_id):
        obj = Place.objects.filter(pk=object_id).first()
        if obj is None or not self.has_view_or_change_permission(request, obj):
            raise PermissionDenied
        from catalog.services.pricing_plans import serialize_pricing_plans, serialize_nested_pricing
        from catalog.services.place_schedule import serialize_place_schedule
        revision = VolunteerPlaceRevision.objects.filter(place=obj).first()
        from catalog.services.place_identity import identity_registry
        access = identity_registry(request.user, places=Place.objects.filter(pk=obj.pk),
            can_view=lambda row:self.has_view_or_change_permission(request,row),
            can_edit=lambda row:self.has_change_permission(request,row))
        if not access['records']: raise PermissionDenied
        visible_candidate = any(v['source']=='candidate' for v in access['records'][0]['versions'])
        active_revision = revision if revision and visible_candidate else None
        if active_revision:
            from catalog.services.volunteer_places import candidate_from_payload
            obj = candidate_from_payload(obj, active_revision.payload)
        payload = {
            "schema_version": 1, "place_id": obj.pk, "base_content_version": obj.content_version,
            "candidate_version": revision.version if revision else 0,
            "export_scope": "candidate" if active_revision else "stored",
            "name_az": obj.name_az, "name_ru": obj.name_ru, "name_en": obj.name_en,
            "description_az": obj.description_az, "description_ru": obj.description_ru, "description_en": obj.description_en,
            "category": obj.category_id, "subcategory": obj.subcategory_id,
            "age_from": obj.age_from, "age_to": obj.age_to, "age_open_ended": obj.age_open_ended,
            "age_varies_by_program": obj.age_varies_by_program,
            "offers_adult_classes": obj.offers_adult_classes,
            "address": obj.address, "district": obj.district, "metro": obj.metro,
            "region": "baku" if obj.district.startswith("baku_") else obj.district,
            "lat": obj.lat, "lng": obj.lng,
            "phone1": obj.phone1, "phone2": obj.phone2, "phone3": obj.phone3,
            "phone_country": obj.phone_country, "whatsapp_mode": obj.whatsapp_mode, "whatsapp_number": obj.whatsapp_number,
            "instagram": obj.instagram, "website": obj.website,
            "public_links": obj.public_links,
            "schedule_mode": obj.schedule_mode,
            "schedule_days": serialize_place_schedule(obj),
            "schedule": obj.schedule,
            "schedule_note_az": obj.schedule_note_az,
            "schedule_note_ru": obj.schedule_note_ru,
            "schedule_note_en": obj.schedule_note_en,
            "lesson_duration_minutes": obj.lesson_duration_minutes,
            "lesson_format": obj.lesson_format,
            "lessons_per_week": obj.lessons_per_week,
            "lessons_per_month": obj.lessons_per_month,
            "is_temporary": obj.is_temporary,
            "temporary_start": obj.temporary_start.isoformat() if obj.temporary_start else None,
            "temporary_end": obj.temporary_end.isoformat() if obj.temporary_end else None,
            "price_mode": obj.price_mode,
            "custom_price_badge_az": obj.custom_price_badge_az,
            "custom_price_badge_ru": obj.custom_price_badge_ru,
            "custom_price_badge_en": obj.custom_price_badge_en,
            "extra_conditions_az": obj.extra_conditions_az,
            "extra_conditions_ru": obj.extra_conditions_ru,
            "extra_conditions_en": obj.extra_conditions_en,
            "additional_info_az": obj.additional_info_az,
            "additional_info_ru": obj.additional_info_ru,
            "additional_info_en": obj.additional_info_en,
            "extra_conditions": obj.extra_conditions,
            "additional_info": obj.additional_info,
            "pricing_plans": serialize_pricing_plans(obj.pricing_plan_records.all()),
            "pricing_plans_legacy": obj.pricing_plans_legacy,
        }
        for name in ("price_from", "price_to", "price_per_lesson", "price_per_month", "price_per_8_lessons"):
            payload[name] = getattr(obj, name)
        if active_revision:
            for exported_name, candidate_name in (("pricing_plans", "pricing_plans"), ("schedule_days", "structured_schedule")):
                if candidate_name in active_revision.payload:
                    payload[exported_name] = active_revision.payload[candidate_name]
        if request.GET.get("pricing_schema_version") == "2":
            payload["nested_pricing"] = getattr(obj, "pending_nested_pricing", None) or serialize_nested_pricing(obj)
        response = HttpResponse(json.dumps(payload, ensure_ascii=False, indent=2, default=str), content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="place-{obj.pk}.json"'
        return response

    def identity_registry_view(self, request):
        from ..place_identity import registry_view
        return registry_view(request, self)

    def identity_compare_view(self, request, object_id):
        from ..place_identity import comparison_view
        return comparison_view(request, self, object_id)

    def duplicate_candidates_view(self, request):
        from ..place_identity import matching_view
        return matching_view(request, self)

    def _home_recommendation_queryset(self):
        return public_place_queryset(
            Place.objects.select_related("category", "subcategory")
        ).filter(is_temporary=False)

    @staticmethod
    def _home_recommendations_limit(value) -> int:
        try:
            limit = int(value)
        except (TypeError, ValueError):
            return 4
        return limit if HOME_RECOMMENDATIONS_MIN_ITEMS <= limit <= HOME_RECOMMENDATIONS_MAX_ITEMS else 4

    def _serialize_home_recommendation(self, place, *, language_code=None):
        image_url = ""
        image_field = place.photo or place.cover_photo
        if image_field and getattr(image_field, "name", ""):
            try:
                image_url = image_field.url
            except Exception:
                image_url = ""

        location = place.district_i18n(language_code)
        if place.metro:
            metro_label = place.metro_i18n(language_code)
            location = " · ".join(part for part in (location, metro_label) if part)

        return {
            "id": place.pk,
            "title": place.name_i18n(language_code) or place.name,
            "category": place.get_category_display(),
            "location": location,
            "image_url": image_url,
            "change_url": reverse("admin:catalog_place_change", args=[place.pk]),
        }

    def home_recommendation_candidates_view(self, request):
        if request.method != "GET" or not self.has_change_permission(request):
            raise PermissionDenied

        term = (request.GET.get("q") or "").strip()
        queryset = self._home_recommendation_queryset()
        if term:
            queryset = queryset.filter(
                Q(name__icontains=term)
                | Q(name_az__icontains=term)
                | Q(name_ru__icontains=term)
                | Q(name_en__icontains=term)
                | Q(district__icontains=term)
                | Q(address__icontains=term)
            )
        queryset = queryset.order_by("-is_home_recommended", "home_recommended_order", "-updated_at")[:24]
        language_code = getattr(request, "LANGUAGE_CODE", None)
        return JsonResponse(
            {
                "results": [
                    self._serialize_home_recommendation(place, language_code=language_code)
                    for place in queryset
                ]
            }
        )

    def save_home_recommendations_view(self, request):
        if request.method != "POST" or not self.has_change_permission(request):
            raise PermissionDenied

        try:
            payload = json.loads(request.body.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"ok": False, "error": str(_("Некорректные данные."))}, status=400)

        raw_ids = payload.get("place_ids")
        if not isinstance(raw_ids, list):
            return JsonResponse({"ok": False, "error": str(_("Передайте список мест."))}, status=400)

        site_settings = SiteSettings.get_solo()
        raw_limit = payload.get("limit", site_settings.home_recommendations_limit)
        if isinstance(raw_limit, bool):
            return JsonResponse({"ok": False, "error": str(_("Укажите количество мест от 1 до 24."))}, status=400)
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": str(_("Укажите количество мест от 1 до 24."))}, status=400)
        if not HOME_RECOMMENDATIONS_MIN_ITEMS <= limit <= HOME_RECOMMENDATIONS_MAX_ITEMS:
            return JsonResponse({"ok": False, "error": str(_("Количество мест должно быть от 1 до 24."))}, status=400)

        try:
            place_ids = [int(value) for value in raw_ids]
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": str(_("Некорректный идентификатор места."))}, status=400)

        if len(place_ids) != len(set(place_ids)):
            return JsonResponse({"ok": False, "error": str(_("Одно место нельзя добавить дважды."))}, status=400)
        if len(place_ids) > limit:
            return JsonResponse(
                {"ok": False, "error": str(_("Сначала уберите лишние места из карусели."))},
                status=400,
            )

        available_places = {
            place.pk: place
            for place in self._home_recommendation_queryset().filter(pk__in=place_ids)
        }
        if len(available_places) != len(place_ids):
            return JsonResponse(
                {"ok": False, "error": str(_("Одно из мест недоступно для публикации. Обновите список."))},
                status=400,
            )

        now = timezone.now()
        with transaction.atomic():
            site_settings = SiteSettings.objects.select_for_update().get(pk=site_settings.pk)
            site_settings.home_recommendations_limit = limit
            site_settings.save(update_fields=["home_recommendations_limit", "updated_at"])
            Place.objects.filter(is_home_recommended=True).exclude(pk__in=place_ids).update(
                is_home_recommended=False,
                updated_at=now,
            )
            for index, place_id in enumerate(place_ids, start=1):
                Place.objects.filter(pk=place_id).update(
                    is_home_recommended=True,
                    home_recommended_order=index * 10,
                    updated_at=now,
                )

        language_code = getattr(request, "LANGUAGE_CODE", None)
        return JsonResponse(
            {
                "ok": True,
                "max_items": limit,
                "results": [
                    self._serialize_home_recommendation(
                        available_places[place_id],
                        language_code=language_code,
                    )
                    for place_id in place_ids
                ],
            }
        )

    def toggle_publication_view(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied

        if not self.has_change_permission(request):
            raise PermissionDenied
        place = Place.objects.filter(pk=object_id, deleted_at__isnull=True).first()
        if place is None or not self.has_change_permission(request, place):
            raise PermissionDenied

        intent = request.POST.get("intent")
        currently_published = place.status == Place.STATUS_PUBLISHED and place.is_active
        if intent and (intent not in {"publish", "unpublish"} or
                       (intent == "publish") == currently_published):
            return JsonResponse({"ok": False, "error": "stale_publication_state",
                "message": str(_("Состояние карточки изменилось. Обновите список и повторите действие."))}, status=409)

        publication_rule, publication_reason = self.place_state_rules(place, request.user)["toggle_pub"]
        if publication_rule != "allowed":
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": "transition_not_allowed", "message": publication_reason}, status=400)
            self.message_user(request, publication_reason, messages.WARNING)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))

        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")

        if place.status == Place.STATUS_PUBLISHED and place.is_active:
            place.status = Place.STATUS_DRAFT
            place.is_active = False
            place.save(update_fields=["status", "is_active", "updated_at"])
            msg = _("Карточка снята с публикации — на сайте больше не показывается")
            if is_ajax:
                return JsonResponse({
                    "ok": True,
                    "status": place.status,
                    "is_active": place.is_active,
                    "message": str(msg),
                })
            self.message_user(request, msg, messages.SUCCESS)
        else:
            readiness = evaluate_saved_place_readiness(place)
            if not readiness.is_ready:
                err_text = _("Нельзя опубликовать. Заполнено %(done)s из %(total)s обязательных пунктов. Исправьте: %(reasons)s.") % {
                    "done": readiness.completed_count,
                    "total": readiness.required_count,
                    "reasons": format_readiness_issues(readiness),
                }
                if is_ajax:
                    return JsonResponse({
                        "ok": False,
                        "error": "not_ready",
                        "message": str(err_text),
                    }, status=400)
                self.message_user(request, err_text, messages.WARNING)
            else:
                from catalog.services.publication import publish
                try:
                    publish(actor=request.user,place_id=place.pk,expected_version=place.content_version)
                except ValidationError as exc:
                    return JsonResponse({"ok":False,"error":"conflict","message":"; ".join(exc.messages)},status=409)
                place.refresh_from_db()
                msg = _("Карточка опубликована — уже видна на сайте")
                if is_ajax:
                    return JsonResponse({
                        "ok": True,
                        "status": place.status,
                        "is_active": place.is_active,
                        "message": str(msg),
                    })
                self.message_user(request, msg, messages.SUCCESS)

        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))

    def quick_action_view(self, request, object_id):
        if request.method != "POST":
            raise PermissionDenied
        if not self.has_change_permission(request):
            raise PermissionDenied

        place = Place.objects.filter(pk=object_id).first()
        if place is None:
            raise PermissionDenied

        action = request.POST.get("action")
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest" or "application/json" in request.headers.get("accept", "")

        action_rules = self.place_state_rules(place, request.user)
        if action not in action_rules:
            raise PermissionDenied
        action_rule, action_reason = action_rules[action]
        if action_rule != "allowed":
            if is_ajax:
                return JsonResponse({"ok": False, "error": "transition_not_allowed", "message": action_reason}, status=400)
            self.message_user(request, action_reason, messages.WARNING)
            return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))

        if action == "to_draft":
            place.status = Place.STATUS_DRAFT
            place.is_active = False
            place.save(update_fields=["status", "is_active", "updated_at"])
            msg = _("Карточка возвращена в черновик.")
        elif action == "to_pending":
            place.status = Place.STATUS_PENDING
            place.is_active = False
            place.save(update_fields=["status", "is_active", "updated_at"])
            msg = _("Карточка отправлена на модерацию.")
        elif action == "toggle_home":
            if place.is_home_recommended:
                place.is_home_recommended = False
                place.home_recommended_order = 0
                place.save(update_fields=["is_home_recommended", "home_recommended_order", "updated_at"])
                msg = _("Карточка убрана с главной страницы.")
            else:
                quality = place_quality_check(place)
                if quality.score < 100 or place.status != Place.STATUS_PUBLISHED or not place.is_active:
                    err_msg = _("Слот главной доступен только для опубликованных карточек с готовностью 100%.")
                    if is_ajax:
                        return JsonResponse({"ok": False, "message": str(err_msg)}, status=400)
                    self.message_user(request, err_msg, messages.WARNING)
                    return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))
                place.is_home_recommended = True
                place.save(update_fields=["is_home_recommended", "updated_at"])
                msg = _("Карточка добавлена в рекомендуемые на главной.")
        elif action == "refresh_coords":
            self._refresh_place_coordinates_with_audit(place=place, changed_by=request.user)
            if place.has_coordinates:
                msg = _("Координаты успешно обновлены.")
            else:
                msg = _("Не удалось автоматически определить координаты по адресу.")
        elif action == "soft_delete":
            self._soft_delete_place(place=place, user=request.user)
            msg = _("Карточка перемещена в удалённые.")
        elif action == "restore":
            self._restore_place(place=place, user=request.user, activate=False)
            msg = _("Карточка восстановлена в черновики.")
        else:
            if is_ajax:
                return JsonResponse({"ok": False, "message": "Unknown action"}, status=400)
            raise PermissionDenied

        if is_ajax:
            return JsonResponse({"ok": True, "message": str(msg)})
        self.message_user(request, msg, messages.SUCCESS)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER") or reverse("admin:catalog_place_changelist"))

    def search_suggestions_view(self, request):
        if not self.has_view_or_change_permission(request):
            raise PermissionDenied
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        # Share saved-content search, without inheriting changelist filters.
        queryset, _may_have_duplicates = self.get_search_results(
            request, Place.objects.filter(deleted_at__isnull=True), term)
        queryset = queryset.select_related("owner", "category", "volunteer_revision").distinct()[:8]

        results = []
        for place in queryset:
            revision = getattr(place, "volunteer_revision", None)
            if revision and revision.status in {"draft", "pending", "rejected"} and self.has_change_permission(request, place):
                from catalog.services.publication import authorize
                from catalog.services.volunteer_places import candidate_from_payload
                try:
                    authorize(request.user, place, "place")
                except PermissionDenied:
                    pass
                else:
                    place = candidate_from_payload(place, revision.payload)
            title = (place.name_i18n(language_code) or place.name or "").strip()
            if not title:
                continue

            meta_parts = []
            district_name = ""
            owner_label = ""
            if place.district:
                from catalog.services.locations import get_location_translation
                district_name = get_location_translation(place.district, language_code)
                meta_parts.append(district_name)
            if place.address:
                meta_parts.append(str(place.address))
            if place.phone1:
                meta_parts.append(str(place.phone1))
            if getattr(place, "owner", None):
                owner_label = place.owner.get_username() or getattr(place.owner, "email", "")
                if owner_label:
                    meta_parts.append(str(owner_label))

            from django.urls import reverse
            change_url = reverse("admin:catalog_place_change", args=[place.pk])
            public_url = place.get_absolute_url() if hasattr(place, "get_absolute_url") else ""

            tone = "muted"
            if place.status == Place.STATUS_PUBLISHED and place.is_active:
                tone = "good"
            elif place.status == Place.STATUS_PENDING:
                tone = "warn"
            elif place.status == Place.STATUS_REJECTED:
                tone = "danger"

            results.append(
                {
                    "id": place.pk,
                    "value": title,
                    "label": title,
                    "meta": " • ".join(part for part in meta_parts if part)[:180],
                    "status": place.status,
                    "status_label": place.get_status_display(),
                    "status_tone": tone,
                    "category": place.category.name_i18n(language_code) if place.category else "",
                    "district": district_name,
                    "address": str(place.address or ""),
                    "phone": str(place.phone1 or ""),
                    "owner": owner_label,
                    "change_url": change_url,
                    "public_url": public_url,
                }
            )

        return JsonResponse({"results": results, "labels": {"edit": str(_("Редактировать карточку")), "found": str(_("Найдено"))}})

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
        updated_count = queryset.update(
            is_active=False,
            status=Place.STATUS_DRAFT,
            updated_at=timezone.now(),
        )
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

    @admin.action(description=_("Добавить в рекомендации на главной"))
    def mark_home_recommended(self, request, queryset):
        updated_count = queryset.update(
            is_home_recommended=True,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d карточка добавлена в рекомендации.",
                "%(count)d карточки добавлены в рекомендации.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Убрать из рекомендаций на главной"))
    def unmark_home_recommended(self, request, queryset):
        updated_count = queryset.update(
            is_home_recommended=False,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d карточка убрана из рекомендаций.",
                "%(count)d карточки убраны из рекомендаций.",
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



    @admin.action(description=_("Опубликовать выбранные карточки"))
    def mark_published(self, request, queryset):
        from catalog.services.publication import publish
        published_count = skipped_count = 0
        for place in queryset.iterator(chunk_size=100):
            try:
                publish(actor=request.user, place_id=place.pk, expected_version=place.content_version)
            except ValidationError:
                skipped_count += 1
            else:
                published_count += 1
        self.message_user(request,
            _("Опубликовано карточек: %(published)d. Пропущено из-за качества: %(skipped)d.")
            % {"published": published_count, "skipped": skipped_count},
            level=messages.SUCCESS if published_count else messages.WARNING)

    @admin.action(description=_("Отправить на модерацию"))
    def mark_pending(self, request, queryset):
        from catalog.services import publication
        updated_count = skipped_count = 0
        for place in queryset.iterator(chunk_size=100):
            try:
                revision = VolunteerPlaceRevision.objects.filter(place_id=place.pk).first()
                publication.propose(actor=request.user,target_type='place',target_id=place.pk,
                    patch={},schema_version=publication.SCHEMA_VERSION,
                    expected_version=place.content_version,
                    revision_version=revision.version if revision else 0,
                    submit=True,explicit_save=False)
            except ValidationError:
                skipped_count += 1
            else:
                if not place.is_public:
                    # A new unpublished card may show its queued lifecycle state.
                    Place.objects.filter(pk=place.pk).update(status=Place.STATUS_PENDING,is_active=False)
                updated_count += 1
        self.message_user(request,
            _("Передано на модерацию: %(updated)d. Пропущено: %(skipped)d.")
            % {"updated": updated_count, "skipped": skipped_count},
            level=messages.SUCCESS if updated_count else messages.WARNING)

    @admin.action(description=_("Отклонить карточки"))
    def mark_rejected(self, request, queryset):
        default_reason = _("Məkan admin moderasiyasından keçmədi. Zəhmət olmasa məlumatları yeniləyin.")
        updated_count = 0
        for place in queryset.iterator(chunk_size=100):
            from catalog.models import VolunteerPlaceRevision
            revision=VolunteerPlaceRevision.objects.filter(place=place,status="pending").first()
            if revision:
                from catalog.services.publication import review
                review(actor=request.user,revision_id=revision.pk,version=revision.version,approve=False,note=str(default_reason))
                updated_count += 1
                continue

            place.status = Place.STATUS_REJECTED
            place.is_active = False
            place.moderated_by = request.user
            if not (place.rejection_reason or "").strip():
                place.rejection_reason = default_reason
            place.save(update_fields=["status", "is_active", "rejection_reason", "updated_at", "moderated_by"])
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
            for place in queryset.iterator(chunk_size=100):
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
        selected_ids = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        if selected_ids:
            queryset = Place.objects.filter(pk__in=selected_ids, deleted_at__isnull=False)

        restored_count = 0
        for place in queryset.iterator(chunk_size=100):
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

        for place in queryset.iterator(chunk_size=100):
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
