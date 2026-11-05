from django.conf import settings
import json
import logging
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.admin import helpers
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Avg, Case, CharField, Count, Exists, F, Max, OuterRef, Prefetch, Q, When
from django.db.models.fields.json import KeyTextTransform
from django import forms
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict
from django.urls import path, reverse
from django.views.decorators.http import require_GET
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _, ngettext
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.text import smart_split, unescape_string_literal
from urllib.parse import urlparse
import re
from zoneinfo import ZoneInfo

from catalog.content_data import BAKU_METRO_STATIONS
from catalog.forms import PlaceScheduleEditorFormMixin, SubcategorySelect
from catalog.services.phone_forms import ContactPhoneFormMixin
from catalog.models import (
    Place,
    PlacePhoto,
    PlaceChangeAudit,
    PlaceOwnershipRequest,
    Event,
    EventPhoto,
    PlaceReviewsByClub,
    Category,
    Subcategory,
    CatalogContentSettings,
    SiteSettings,
    VolunteerPlaceRevision,
)
from catalog.repositories.django_repositories import DjangoPlaceChangeAuditRepository
from catalog.services.content_quality import (
    _place_has_pricing_plan_price,
    format_place_quality_errors,
    place_catalog_visibility_reasons,
    place_quality_check,
    place_quality_error_labels as get_place_quality_error_labels,
    public_place_queryset,
    public_review_filter,
)
from catalog.services.admin_place_presentation import with_saved_location, saved_presentation, saved_thumbnail_url
from catalog.services.place_identity_copy import identity_copy
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.options import sort_translated_values
from catalog.services.image_uploads import normalize_uploaded_image
from catalog.services.place_readiness import (
    PLACE_READINESS_REQUIREMENTS,
    evaluate_form_readiness,
    evaluate_saved_place_readiness,
    evaluate_place_readiness,
    format_readiness_issues,
    publication_blocked_message,
)
from catalog.services.pricing_plans import normalize_pricing_plans, pricing_audit_summary
from catalog.services.place_schedule import FULL_DAY_LABELS, build_schedule_summary, serialize_place_schedule
from catalog.services.place_card_validation import validate_place_card
from .queue_sorting import QueueSortingAdminMixin, QueueSortParameter
from .review import PlaceReviewInline
from .ui_utils import render_primary_action, render_action_menu, render_row_actions_container
from catalog.services.place_public_links import PublicLinksFormMixin
from .place_admin.changelist import PlaceAdminChangelistMixin
from .place_admin.common import logger
from .place_admin.filters import (
    PlaceCoordinatesFilter,
    PlaceCreatedByFilter,
    PlaceCreatedDateFilter,
    PlaceDeletedFilter,
    PlaceMapReadyFilter,
    PlacePublicationFilter,
    PlaceSortFilter,
)
from .place_admin.forms import PlaceAdminForm
from .place_admin.inlines import PlaceChangeAuditInline, PlacePhotoInline
from .place_admin.layout import PlaceAdminLayoutMixin
from .place_admin.operations import PlaceAdminOperationsMixin

# Re-exported: these names lived in this module before it was split into
# ``place_admin/``; other code (and ``domain_admin/__init__``) imports them from here.
from .place_admin.common import (  # noqa: F401
    ADMIN_DATETIME_LOCAL_FORMAT,
    DRAFT_PLACEHOLDER_NAME,
    HOME_RECOMMENDATIONS_MAX_ITEMS,
    HOME_RECOMMENDATIONS_MIN_ITEMS,
    place_quality_error_labels,
)
from .place_admin.event import (  # noqa: F401
    EventAdmin,
)
from .place_admin.filters import (  # noqa: F401
    EventDeletedFilter,
)
from .place_admin.forms import (  # noqa: F401
    BakuEventDateTimeField,
    CandidatePlacePhotoFormSet,
    EventAdminForm,
)
from .place_admin.inlines import (  # noqa: F401
    EventPhotoInline,
)


@admin.register(Place)
class PlaceAdmin(PlaceAdminLayoutMixin, PlaceAdminChangelistMixin, PlaceAdminOperationsMixin, admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)
        model_admin = self
        class LocationActorForm(form_class):
            location_actor = request.user

            def identity_can_view(self, place):
                return model_admin.has_view_or_change_permission(request,place)

            def identity_can_edit(self, place):
                return model_admin.has_change_permission(request,place)

            def __init__(self, *args, **form_kwargs):
                super().__init__(*args, **form_kwargs)
                from catalog.services.location_assignment import can_override_location
                if not can_override_location(request.user):
                    self.fields.pop('location_override_reason', None)

            def clean(self):
                cleaned = super().clean()
                identity_conflict = getattr(request, '_km_identity_conflict', None)
                if identity_conflict is not None:
                    self.add_error(None,identity_conflict)
                elif not self.instance.pk and not self.errors:
                    from catalog.services.place_identity import guard_new_place, identity_fields
                    values={**identity_fields(self.instance),**cleaned}
                    try:
                        with transaction.atomic():
                            guard_new_place(request.user,values,
                                exclude_draft_id=self.data.get('server_draft_id'),
                                distinct_branch=bool(cleaned.get('create_as_distinct_branch')),
                                can_view=self.identity_can_view,can_edit=self.identity_can_edit)
                    except ValidationError as exc:
                        self.identity_duplicate=getattr(exc,'identity_result',None)
                        self.add_error(None,exc)
                conflict = getattr(request, '_km_candidate_conflict', None)
                if conflict is not None:
                    self.add_error(None, conflict)
                return cleaned
        return LocationActorForm

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
        "age_open_ended",
        "age_varies_by_program",
        "offers_adult_classes",
        "district",
        "metro",
        "address",
        "phone1",
        "phone2",
        "phone3",
        "owner_id",
        "instagram",
        "website",
        "schedule",
        "schedule_mode",
        "schedule_note_az",
        "schedule_note_ru",
        "schedule_note_en",
        "price_mode",
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
        "is_home_recommended",
        "home_recommended_order",
        "is_active",

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
    volunteer_revision_change_form_template = "admin/catalog/place/volunteer_revision_change_form.html"
    delete_confirmation_template = "admin/catalog/place_delete_confirmation.html"
    km_primary_filters = ("category", "district", "status", "created_by")
    delete_selected_confirmation_template = "admin/catalog/place_delete_selected_confirmation.html"
    list_select_related = ("owner", "created_by", "category", "subcategory")
    list_display = (
        "col_place",
        "col_location",
        "col_state",
        "col_marks",
        "col_updated",
        "col_actions",
    )
    trash_list_display = (
        "col_place",
        "col_location",
        "col_state",
        "col_marks",
        "deleted_at_display",
        "col_actions",
    )
    list_filter = (
        PlaceDeletedFilter,
        PlacePublicationFilter,
        PlaceCoordinatesFilter,
        PlaceMapReadyFilter,
        PlaceCreatedByFilter,
        PlaceCreatedDateFilter,
        PlaceSortFilter,
        "category",
        "is_temporary",
        "district",
        "metro",
        "owner",
        "organization",
        "is_active",
        "is_home_recommended",

        "status",
        "age_from",
        "age_to",
        "offers_adult_classes",
    )
    search_fields = (
        "name_az",
        "name_ru",
        "name_en",
        "name",
        "slug",
        "address",
        "instagram",
        "phone1",
        "phone2",
        "phone3",
        "owner__username",
        "owner__email",
    )
    search_help_text = _("Ищет по названию места на AZ, RU или EN. Можно также искать по адресу, телефону или владельцу.")

    def get_search_results(self, request, queryset, search_term):
        results, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if not search_term.strip() or not self.has_change_permission(request):
            return results, may_have_duplicates

        # Editors overlay these saved fields without writing them to Place.
        # Search the same effective values; never scan arbitrary JSON metadata.
        fields = ("name_az", "name_ru", "name_en", "address", "instagram", "phone1", "phone2", "phone3")
        aliases = {field: f"km_saved_search_{field}" for field in fields}
        saved = queryset.filter(volunteer_revision__status__in=("draft", "pending", "rejected")).alias(**{
            aliases[field]: Case(
                When(volunteer_revision__payload__has_key=field,
                     then=KeyTextTransform(field, F("volunteer_revision__payload"))),
                default=F(field), output_field=CharField(),
            ) for field in fields
        })
        for term in smart_split(search_term):
            if term.startswith(('"', "'")) and term[0] == term[-1]:
                term = unescape_string_literal(term)
            matches = Q()
            for field in self.get_search_fields(request):
                matches |= Q(**{f"{aliases.get(field, field)}__icontains": term})
            saved = saved.filter(matches)

        from catalog.services.publication import authorize
        allowed = []
        for place in saved.prefetch_related(None).iterator():
            if not self.has_change_permission(request, place):
                continue
            try:
                authorize(request.user, place, "place")
            except PermissionDenied:
                continue
            allowed.append(place.pk)
        # A private working copy can belong to an existing Place. Its matching
        # target must survive the changelist filter as well as the draft panel.
        from catalog.services.place_editor_drafts import working_draft_rows
        try:
            allowed.extend(row["target_id"] for row in working_draft_rows(
                user=request.user, query=search_term) if row["target_id"] is not None)
        except PermissionDenied:
            pass
        if allowed:
            results = queryset.filter(Q(pk__in=results.values("pk")) | Q(pk__in=allowed))
        return results, may_have_duplicates

    readonly_fields = (
        "slug",
        "likes_count",
        "rating_avg",
        "rating_count",
        "lifecycle_status_display",
        "coordinates_status_display",
        "map_ready_status_display",
        "quality_status_display",

        "published_at_display",
        "deleted_at",
        "deleted_by",
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)
    list_per_page = 15
    save_on_top = True

    def get_ordering(self, request):
        sort_param = request.GET.get("sort")
        if sort_param == "created_desc":
            return ["-created_at", "-id"]
        elif sort_param == "created_asc":
            return ["created_at", "id"]
        elif sort_param == "updated_desc":
            return ["-updated_at", "-id"]
        elif sort_param == "updated_asc":
            return ["updated_at", "id"]
        elif sort_param == "name_asc":
            return ["name_ru", "name_az", "id"]
        elif sort_param == "name_desc":
            return ["-name_ru", "-name_az", "-id"]
        return super().get_ordering(request)


    actions = (
        "connect_to_organization",
        "mark_active",
        "mark_inactive",
        "mark_home_recommended",
        "unmark_home_recommended",
        "mark_draft",


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
                    ("category", "subcategory"),
                )
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                ),
            },
        ),
        (
            _("Цена и возраст"),
            {
                "fields": (
                ("age_from", "age_to", "age_open_ended", "lesson_duration_minutes"),
                    "age_varies_by_program",
                    "offers_adult_classes",
                    "price_mode",
                    "pricing_plans", "nested_pricing",
                    ("lesson_format", "lessons_per_week", "lessons_per_month"),
                    ("custom_price_badge_az", "custom_price_badge_ru", "custom_price_badge_en"),
                )
            },
        ),
        (_("Локация"), {"fields": (("region", "district", "metro"), "address", ("lat", "lng"), ("coordinates_status_display", "map_ready_status_display"))}),
        (
            _("Контакты"),
            {
                "fields": (
                    "phone_country",
                    ("phone1", "phone2", "phone3"),
                    ("whatsapp_mode", "whatsapp_number"),
                    ("instagram", "website"),
                    "public_links",
                    "schedule",
                    "schedule_mode",
                    ("schedule_note_az", "schedule_note_ru", "schedule_note_en"),
                    # The per-language fields are the ones the site renders; the
                    # non-suffixed columns stay in the database as a fallback.
                    "extra_conditions", "additional_info",
                    ("extra_conditions_az", "extra_conditions_ru", "extra_conditions_en"),
                    ("additional_info_az", "additional_info_ru", "additional_info_en"),
                )
            },
        ),
        (_("Фотографии"), {"fields": ("photo",)}),
        (
            _("Управление карточкой"),
            {
                "fields": (
                    "is_active",

                    ("is_home_recommended", "home_recommended_order"),
                    "status",
                    "rejection_reason",
                    "owner",
                ),
            },
        ),
        (_("Удаление"), {"classes": ("collapse",), "fields": ("deleted_at", "deleted_by")}),
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cover_photo",

                    "published_at_display",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = self.ADD_FIELDSETS if obj is None else super().get_fieldsets(request, obj)
        from catalog.services.location_assignment import can_override_location
        if can_override_location(request.user):
            from django.contrib.admin.utils import flatten_fieldsets
            return tuple(
                (title, {**options, "fields": tuple(options["fields"]) + ("location_override_reason",)})
                if "district" in flatten_fieldsets(((title, options),)) else (title, options)
                for title, options in fieldsets
            )
        return fieldsets

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("status", Place.STATUS_DRAFT)
        initial.setdefault("is_active", False)
        return initial

    def get_queryset(self, request):
        queryset = with_saved_location(super().get_queryset(request), request, self)
        public_match = public_place_queryset(Place.objects.filter(pk=OuterRef("pk")))
        return queryset.annotate(km_in_public_catalog=Exists(public_match)).select_related(
            "volunteer_revision", "subcategory__category",
        ).prefetch_related(
            "gallery",
            "schedule_days",
            "pricing_plan_records",
            Prefetch(
                "ownership_requests",
                queryset=PlaceOwnershipRequest.objects.select_related("applicant").order_by("created_at"),
                to_attr="km_prefetched_ownership_requests",
            ),
            Prefetch(
                "change_audits",
                queryset=PlaceChangeAudit.objects.select_related("changed_by").order_by("-created_at"),
                to_attr="km_prefetched_change_audits",
            ),
        )

    def delete_model(self, request, obj):
        self._soft_delete_place(place=obj, user=request.user)

    def delete_queryset(self, request, queryset):
        for place in queryset.iterator(chunk_size=100):
            self._soft_delete_place(place=place, user=request.user)

    def _stringify_audit_value(self, value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return "1" if value else "0"
        return str(value)

    def save_model(self, request, obj, form, change):
        submit = not any(action in request.POST for action in ("_save_draft", "_refresh_coordinates_from_address"))
        from catalog.services.publication_forms import save_form,create_from_form,save_admin_metadata
        if change and obj.pk:
            if "_publish_place" in request.POST:
                # The explicit review may save staff corrections before publish.
                # Remember the signed, validated version the reviewer opened;
                # newer or already stale requests must not join that decision.
                from catalog.services.publication_forms import source_version
                reviewed = source_version(form, Place.objects.get(pk=obj.pk))
                request._km_reviewed_publication_source = (reviewed['source'], reviewed['candidate'])
            save_form(actor=request.user,form=form,submit=submit)
            obj.refresh_from_db()
        else:
            base=create_from_form(actor=request.user,form=form,submit=submit)
            obj.__dict__.update(base.__dict__)
        save_admin_metadata(obj,form.cleaned_data)
        request._km_candidate_saved=True

    def save_related(self, request, form, formsets, change):
        submit = not any(action in request.POST for action in ("_save_draft", "_refresh_coordinates_from_address"))
        if getattr(request,"_km_candidate_saved",False):
            from catalog.services.publication_forms import save_admin_related
            save_admin_related(actor=request.user,place=form.instance,formsets=formsets,
                uploads=request.FILES.getlist("gallery_uploads"),submit=submit)
            for formset in formsets:
                # Django's change-message builder expects these after save_related.
                formset.new_objects = []
                formset.changed_objects = []
                formset.deleted_objects = []
            if "_publish_place" in request.POST:
                from catalog.services.publication import publish, _complete_publication_requests
                publish(actor=request.user,place_id=form.instance.pk,expected_version=form.instance.content_version)
                form.instance.refresh_from_db()
                reviewed = getattr(request, '_km_reviewed_publication_source', None)
                if reviewed:
                    _complete_publication_requests(actor=request.user, place=form.instance,
                        source_version=reviewed[0], candidate_version=reviewed[1])
            return
        super().save_related(request, form, formsets, change)
        self._save_filepond_gallery_uploads(request, form.instance)

    def _save_filepond_gallery_uploads(self, request, obj):
        if not obj or not obj.pk or not hasattr(request, "FILES"):
            return

        uploads = request.FILES.getlist("gallery_uploads")
        if not uploads:
            return

        current_count = PlacePhoto.objects.filter(place=obj).count()
        available_slots = max(10 - current_count, 0)
        if available_slots <= 0:
            messages.warning(request, _("Лимит галереи — 10 фотографий. Новые файлы не добавлены."))
            return

        max_order = PlacePhoto.objects.filter(place=obj).aggregate(max_order=Max("order"))["max_order"] or 0
        created_count = 0
        failed_count = 0
        for offset, uploaded_file in enumerate(uploads[:available_slots], start=1):
            try:
                normalized = normalize_uploaded_image(uploaded_file)
                PlacePhoto.objects.create(
                    place=obj,
                    image=normalized,
                    order=max_order + offset,
                )
            except ValidationError as exc:
                failed_count += 1
                messages.error(
                    request,
                    _("%(name)s — ошибка: %(reason)s")
                    % {"name": uploaded_file.name, "reason": "; ".join(exc.messages)},
                )
            except Exception:
                failed_count += 1
                logger.exception(
                    "Admin gallery image persistence failed: place_id=%s name=%s size=%s mime=%s",
                    obj.pk,
                    uploaded_file.name,
                    getattr(uploaded_file, "size", 0),
                    getattr(uploaded_file, "content_type", ""),
                )
                messages.error(
                    request,
                    _("%(name)s — ошибка сохранения в хранилище.")
                    % {"name": uploaded_file.name},
                )
            else:
                created_count += 1
                messages.success(
                    request,
                    _("%(name)s — загружено.") % {"name": uploaded_file.name},
                )

        skipped_count = len(uploads) - created_count - failed_count
        if skipped_count > 0:
            messages.warning(
                request,
                ngettext(
                    "%(count)d фото не добавлено: лимит галереи — 10 фотографий.",
                    "%(count)d фото не добавлены: лимит галереи — 10 фотографий.",
                    skipped_count,
                )
                % {"count": skipped_count},
            )

    def _close_private_working_draft(self, request, obj, *, change):
        from catalog.services.server_drafts import mark_explicit_save
        if request.POST.get('server_draft_id'):
            mark_explicit_save(user=request.user, draft_id=request.POST['server_draft_id'],
                expected_version=request.POST.get('server_draft_version', ''), place=obj,
                target_id=obj.pk if change else None,
                cutoff=getattr(request, '_km_explicit_save_cutoff', None))

    def _queue_place_save_result(self, request, obj):
        from catalog.services.permanent_place_rules import copy as t
        from catalog.services.place_editor_feedback import queue_editor_result
        from catalog.services.moderation_hub import reviewer_scopes
        revision = VolunteerPlaceRevision.objects.filter(place_id=obj.pk, status__in=["draft", "pending", "rejected"]).first()
        next_url = next_label = ""
        if revision and revision.status == "pending":
            message = t("Изменения сохранены и ожидают модерации. На сайте пока показана опубликованная версия.", "Dəyişikliklər saxlanılıb və moderasiya gözləyir. Saytda hələ dərc edilmiş versiya göstərilir.", "Changes are saved and awaiting review. The website still shows the published version.") if obj.status == Place.STATUS_PUBLISHED else t("Карточка сохранена и ожидает модерации. Она ещё не опубликована.", "Kart saxlanılıb və moderasiya gözləyir. Hələ dərc edilməyib.", "The listing is saved and awaiting review. It is not published yet.")
            try:
                can_review = reviewer_scopes(request.user)[1]
            except PermissionDenied:
                can_review = False
            if can_review:
                next_url = reverse("admin:volunteer_moderation_detail", args=["content", revision.pk])
                next_label = t("Проверить и опубликовать изменения", "Dəyişiklikləri yoxla və dərc et", "Review and publish changes")
            else:
                next_url = self._place_change_url(obj)
                next_label = t("Продолжить редактирование", "Redaktəyə davam et", "Continue editing")
            action = "moderation"
        elif revision:
            message = t("Рабочая версия сохранена. Изменения ещё не опубликованы.", "İş versiyası saxlanıldı. Dəyişikliklər hələ dərc edilməyib.", "The working version is saved. These changes are not published yet.")
            next_url, next_label = self._place_change_url(obj), t("Продолжить редактирование", "Redaktəyə davam et", "Continue editing")
            action = "save"
        else:
            message = t("Изменения сохранены.", "Dəyişikliklər saxlanıldı.", "Changes saved.")
            action = "save"
        queue_editor_result(request, action=action, message=message, next_url=next_url, next_label=next_label)
        self.message_user(request, message, level=messages.SUCCESS)

    def response_add(self, request, obj, post_url_continue=None):
        self._close_private_working_draft(request, obj, change=False)
        if "_save_draft" in request.POST:
            return self._handle_save_draft_submit(
                request,
                obj,
                message=_("Черновик сохранён. Можно вернуться и продолжить заполнение позже."),
            )
        if "_publish_place" in request.POST:
            return self._handle_publish_submit(request, obj)
        if "_unpublish_place" in request.POST:
            return self._handle_unpublish_submit(request, obj)
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Карточка сохранена."),
            )
        if getattr(request, "_km_place_publish_requires_explicit_action", False):
            self.message_user(
                request,
                _("Обычное сохранение не публикует карточку. Для публикации используйте кнопку “Опубликовать”."),
                level=messages.WARNING,
            )
        response = super().response_add(request, obj, post_url_continue=post_url_continue)
        self._queue_place_save_result(request, obj)
        return response

    def response_change(self, request, obj):
        self._close_private_working_draft(request, obj, change=True)
        if "_save_draft" in request.POST:
            return self._handle_save_draft_submit(
                request,
                obj,
                message=_("Изменения сохранены как черновик. Можно продолжить редактирование позже."),
            )
        if "_publish_place" in request.POST:
            return self._handle_publish_submit(request, obj)
        if "_unpublish_place" in request.POST:
            return self._handle_unpublish_submit(request, obj)
        if "_refresh_coordinates_from_address" in request.POST:
            return self._handle_refresh_coordinates_submit(
                request,
                obj,
                saved_prefix=_("Изменения сохранены."),
            )
        if getattr(request, "_km_place_publish_requires_explicit_action", False):
            self.message_user(
                request,
                _("Обычное сохранение не публикует карточку. Для публикации используйте кнопку “Опубликовать”."),
                level=messages.WARNING,
            )
        response = super().response_change(request, obj)
        self._queue_place_save_result(request, obj)
        return response

    def _handle_save_draft_submit(self, request, obj, *, message: str):
        from catalog.services.place_editor_feedback import queue_editor_result
        queue_editor_result(request, action="draft", message=message)
        self.message_user(request, message, level=messages.SUCCESS)
        return HttpResponseRedirect(self._place_change_url(obj))

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        edit_url = self._place_change_url(obj)
        actions = [
            format_html(
                '<a class="km-admin-icon-action km-admin-icon-action--edit" href="{}" title="{}" aria-label="{}"><i class="fas fa-pen"></i></a>',
                edit_url,
                _("Редактировать"),
                _("Редактировать"),
            )
        ]
        if obj.is_deleted:
            actions.append(
                format_html(
                    '<a class="km-admin-icon-action km-admin-icon-action--restore" href="{}" title="{}" aria-label="{}"><i class="fas fa-undo"></i></a>',
                    self._place_restore_url(obj),
                    _("Восстановить"),
                    _("Восстановить"),
                )
            )
        else:
            is_published = obj.status == Place.STATUS_PUBLISHED and obj.is_active
            visibility_label = _("Снять с публикации") if is_published else _("Опубликовать")
            visibility_icon = "fas fa-eye-slash" if is_published else "fas fa-bullhorn"
            visibility_tone = "unpublish" if is_published else "publish"
            actions.extend(
                [
                    format_html(
                        '<button type="button" class="km-admin-icon-action km-admin-icon-action--{}" data-place-visibility-url="{}" title="{}" aria-label="{}"><i class="{}"></i></button>',
                        visibility_tone,
                        reverse("admin:catalog_place_toggle_publication", args=[obj.pk]),
                        visibility_label,
                        visibility_label,
                        visibility_icon,
                    ),
                    format_html(
                        '<a class="km-admin-icon-action km-admin-icon-action--open" href="{}" title="{}" aria-label="{}" target="_blank" rel="noopener"><i class="fas fa-eye"></i></a>',
                        self._place_view_url(obj),
                        self._place_view_label(obj, _("Открыть")),
                        self._place_view_label(obj, _("Открыть")),
                    ),
                    format_html(
                        '<a class="km-admin-icon-action km-admin-icon-action--delete km-admin-action-menu__link--danger" href="{}" title="{}" aria-label="{}"><i class="far fa-trash-alt"></i></a>',
                        self._place_delete_url(obj),
                        _("В удалённые"),
                        _("В удалённые"),
                    ),
                ]
            )

        return format_html(
            '<div class="km-place-row-actions km-place-row-actions--icons">{}</div>',
            format_html_join("", "{}", ((action,) for action in actions)),
        )

class PlaceReviewStatusFilter(admin.SimpleListFilter):
    title = _("Статус отзывов")
    parameter_name = "review_status"

    def lookups(self, request, model_admin):
        return [
            ("with_reviews", _("С отзывами (>0)")),
            ("top_rated", _("Высокий рейтинг (4.5+)")),
            ("low_rated", _("Требуют внимания (<3.5)")),
            ("no_reviews", _("Без отзывов (0)")),
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val == "with_reviews":
            return queryset.filter(visible_review_count__gt=0)
        elif val == "top_rated":
            return queryset.filter(visible_rating_avg__gte=4.5)
        elif val == "low_rated":
            return queryset.filter(visible_review_count__gt=0, visible_rating_avg__lt=3.5)
        elif val == "no_reviews":
            return queryset.filter(visible_review_count=0)
        return queryset

@admin.register(PlaceReviewsByClub)
class PlaceReviewsByClubAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placereviewsbyclub/change_list.html"
    list_display = ("display_name", "visible_review_count", "visible_rating_avg", "reviews_link", "updated_at")
    list_display_links = None
    list_filter = (PlaceReviewStatusFilter, "category", "district", "is_active")
    search_fields = ("name_ru", "name_en", "name_az", "name")
    ordering = ()
    readonly_fields = ("rating_count", "rating_avg")
    list_per_page = 25

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def change_view(self, request, object_id, form_url="", extra_context=None):
        from django.shortcuts import redirect
        return redirect(reverse("admin:catalog_place_change", args=[object_id]))

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        base_qs = self.get_queryset(request)
        total_count = base_qs.count()
        with_reviews_count = base_qs.filter(visible_review_count__gt=0).count()
        unrated_count = total_count - with_reviews_count
        top_rated_count = base_qs.filter(visible_rating_avg__gte=4.5).count()
        low_rated_count = base_qs.filter(visible_review_count__gt=0, visible_rating_avg__lt=3.5).count()

        avg_res = base_qs.filter(visible_review_count__gt=0).aggregate(avg=Avg("visible_rating_avg"))
        catalog_avg = avg_res["avg"] if avg_res["avg"] is not None else 0.0

        extra_context.update({
            "rating_total_count": total_count,
            "rating_with_reviews_count": with_reviews_count,
            "rating_unrated_count": unrated_count,
            "rating_top_rated_count": top_rated_count,
            "rating_low_rated_count": low_rated_count,
            "rating_catalog_avg": f"{catalog_avg:.1f}",
            "km_disable_search_suggestions": False,
            "km_suggestions_url": reverse("admin:catalog_place_search_suggestions"),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        """Show only live Place rows and calculate stats from public reviews.

        PlaceReviewsByClub is a proxy model, so a soft-deleted Place used
        to leak into this admin list with stale cached rating fields.
        """

        # A rating is meaningful only for a card that is actually available in
        # the public catalog. This also keeps legacy/demo cards that fail the
        # catalog quality gate out of this list.
        queryset = public_place_queryset(super().get_queryset(request))
        queryset = queryset.annotate(
            # public_place_queryset() joins structured schedule rows. Count
            # review primary keys distinctly so one review is not multiplied by
            # the number of schedule days (for example, 1 review × 7 days).
            visible_review_count=Count("reviews", filter=public_review_filter("reviews__"), distinct=True),
            visible_rating_avg=Avg("reviews__rating", filter=public_review_filter("reviews__")),
        )
        return queryset.order_by("-visible_review_count", "-visible_rating_avg", "-updated_at")

    @admin.display(description=_("Заведение"), ordering="name")
    def display_name(self, obj):
        name = obj.name_ru or obj.name_az or obj.name_en or obj.name
        category_name = obj.get_category_display() if hasattr(obj, "get_category_display") else (obj.category or "")
        district_name = obj.get_district_display() if hasattr(obj, "get_district_display") else (obj.district or "")
        change_url = reverse("admin:catalog_place_change", args=[obj.pk])

        meta_chips = []
        if category_name:
            meta_chips.append(format_html('<span class="km-ratings-chip km-ratings-chip--cat">{}</span>', category_name))
        if district_name:
            meta_chips.append(format_html('<span class="km-ratings-chip km-ratings-chip--dist">{}</span>', district_name))

        return format_html(
            '<div class="km-ratings-place-cell">'
            '<a href="{}" class="km-ratings-place-link">{}</a>'
            '<div class="km-ratings-place-meta">{}</div>'
            '</div>',
            change_url,
            name,
            mark_safe("".join(meta_chips)),
        )

    @admin.display(description=_("Количество отзывов"), ordering="visible_review_count")
    def visible_review_count(self, obj):
        count = obj.visible_review_count or 0
        if count > 0:
            unit = _("отзывов") if count >= 5 else (_("отзыва") if count > 1 else _("отзыв"))
            return format_html(
                '<span class="km-reviews-badge km-reviews-badge--has">'
                '<svg class="km-i" viewBox="0 0 960 960" width="13" height="13" fill="currentColor" aria-hidden="true"><use href="#kmi-chat"></use></svg>'
                '<strong class="km-reviews-count">{}</strong>'
                '<span class="km-reviews-unit">{}</span>'
                '</span>',
                count,
                unit,
            )
        return format_html(
            '<span class="km-reviews-badge km-reviews-badge--zero">'
            '<span class="km-reviews-count">0</span>'
            '<span class="km-reviews-unit">{}</span>'
            '</span>',
            _("отзывов"),
        )

    @admin.display(description=_("Средний рейтинг"), ordering="visible_rating_avg")
    def visible_rating_avg(self, obj):
        count = obj.visible_review_count or 0
        avg_val = float(obj.visible_rating_avg or 0)
        formatted_val = f"{avg_val:.1f}"

        if count == 0 or avg_val == 0:
            return format_html(
                '<span class="km-rating-pill km-rating-pill--zero">'
                '<span class="km-rating-star">★</span>'
                '<span class="km-rating-val">0.0</span>'
                '<span class="km-rating-label">{}</span>'
                '</span>',
                _("нет оценок"),
            )

        if avg_val >= 4.8:
            tone = "km-rating-pill--gold"
        elif avg_val >= 4.0:
            tone = "km-rating-pill--high"
        elif avg_val >= 3.0:
            tone = "km-rating-pill--medium"
        else:
            tone = "km-rating-pill--low"

        return format_html(
            '<span class="km-rating-pill {}">'
            '<span class="km-rating-star">★</span>'
            '<strong class="km-rating-val">{}</strong>'
            '</span>',
            tone,
            formatted_val,
        )

    @admin.display(description=_("Отзывы"))
    def reviews_link(self, obj):
        url = reverse("admin:catalog_placereview_changelist")
        count = obj.visible_review_count or 0
        if count > 0:
            return format_html(
                '<a href="{}?place__id__exact={}" class="km-ratings-btn km-ratings-btn--primary">'
                '<svg class="km-i" viewBox="0 0 960 960" width="13" height="13" fill="currentColor" aria-hidden="true"><use href="#kmi-chat"></use></svg>'
                '<span>{} ({})</span>'
                '<svg class="km-i" viewBox="0 0 960 960" width="12" height="12" fill="currentColor" aria-hidden="true"><use href="#kmi-chevron_right"></use></svg>'
                '</a>',
                url,
                obj.id,
                _("Открыть отзывы"),
                count,
            )
        return format_html(
            '<a href="{}?place__id__exact={}" class="km-ratings-btn km-ratings-btn--ghost">'
            '<span>{}</span>'
            '</a>',
            url,
            obj.id,
            _("Открыть отзывы"),
        )
