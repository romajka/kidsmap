"""PlaceAdmin: change-form layout, sections, tabs and summary."""

from django.conf import settings
import json
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.template.response import TemplateResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from catalog.models import (
    Place,
    PlaceChangeAudit,
    VolunteerPlaceRevision,
)
from catalog.services.content_quality import (
    format_place_quality_errors,
    place_catalog_visibility_reasons,
    place_quality_check,
    public_place_queryset,
)
from catalog.services.place_identity_copy import identity_copy
from catalog.services.place_readiness import (
    PLACE_READINESS_REQUIREMENTS,
    evaluate_form_readiness,
)
from catalog.services.place_schedule import FULL_DAY_LABELS


class PlaceAdminLayoutMixin:
    """Change-form layout, sections, tabs and summary."""

    # The change form renders its fields by hand (see the templates under
    # ``admin/catalog/place/form/``), so a section only carries its identity and
    # its icon. Field placement lives in the templates, completion lives in
    # ``catalog.services.place_readiness`` — never here.
    PLACE_FORM_PRIMARY_SECTIONS = (
        {
            "id": "basics",
            "step": "01",
            "title": _("О месте"),
            "description": _("Название, описание и рубрика карточки."),
            "icon": "tune",
        },
        {
            "id": "pricing",
            "step": "03",
            "title": _("Возраст и цены"),
            "description": _("Возрастные рамки, тарифы и длительность занятий."),
            "icon": "payments",
        },
        {
            "id": "location",
            "step": "02",
            "title": _("Адрес и контакты"),
            "description": _("Адрес, точка на карте, контакты и расписание."),
            "icon": "location_on",
        },
        {
            "id": "media",
            "step": "04",
            "title": _("Фото и проверка"),
            "description": _("Главное изображение и галерея места."),
            "icon": "imagesmode",
        },
    )

    PLACE_FORM_VERIFICATION_SECTION = {
        "id": "verification",
        "step": "05",
        "title": _("Проверка"),
        "description": _("Итоговый вид карточки перед публикацией."),
        "icon": "fact_check",
    }

    # Every field the redesigned template renders itself. Anything on the form
    # that is neither here nor inside a secondary fieldset is emitted as a
    # hidden carry-over input, so a field can never be silently blanked by a
    # save just because the template forgot it.
    PLACE_FORM_RENDERED_FIELDS = frozenset({
        "name", "name_az", "name_ru", "name_en",
        "create_as_distinct_branch",
        "description_az", "description_ru", "description_en",
        "category", "subcategory",
        "age_from", "age_to", "age_open_ended", "age_varies_by_program", "offers_adult_classes",
        "lesson_duration_minutes", "lesson_format", "lessons_per_week", "lessons_per_month", "pricing_plans", "nested_pricing",
        "custom_price_badge_az", "custom_price_badge_ru", "custom_price_badge_en",
        "region", "district", "metro", "address", "lat", "lng", "location_override_reason",
        "phone1", "phone2", "phone3", "phone_country", "whatsapp_mode", "whatsapp_number", "instagram", "website", "public_links",
        "schedule", "schedule_mode", "structured_schedule",
        "schedule_note_az", "schedule_note_ru", "schedule_note_en",
        "extra_conditions", "extra_conditions_az", "extra_conditions_ru", "extra_conditions_en",
        "additional_info", "additional_info_az", "additional_info_ru", "additional_info_en",
        "photo",
        "is_active", "is_home_recommended", "home_recommended_order",
        "status", "rejection_reason", "owner",
    })

    PLACE_FORM_SECONDARY_SECTIONS = (
        {
            "id": "system",
            "title": _("Служебное"),
            "description": _("Служебные и административные поля, которые не нужны в основном сценарии заполнения."),
            "fieldset_indexes": (7, 8),
        },
    )

    ADD_FIELDSETS = (
        (
            _("Основное"),
            {
                "fields": (
                    ("category", "subcategory"),
                    "create_as_distinct_branch",
                )
            },
        ),
        (
            _("Названия и описания (i18n)"),
            {
                "fields": (
                    ("name_az", "description_az"),
                    ("name_ru", "description_ru"),
                    ("name_en", "description_en"),
                )
            },
        ),
        (
            _("Цена и возраст"),
            {
                "fields": (
                ("age_from", "age_to", "age_open_ended", "lesson_duration_minutes"),
                    "age_varies_by_program",
                    "offers_adult_classes",
                    ("lesson_format", "lessons_per_week", "lessons_per_month"),
                    "price_mode",
                    "pricing_plans", "nested_pricing",
                    ("custom_price_badge_az", "custom_price_badge_ru", "custom_price_badge_en"),
                )
            },
        ),
        (
            _("Локация"),
            {
                "fields": (
                    ("region", "district", "metro"),
                    "address",
                    ("lat", "lng"),
                    ("coordinates_status_display", "map_ready_status_display"),
                )
            },
        ),
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
        (
            _("Служебное"),
            {
                "classes": ("collapse",),
                "fields": (
                    "cover_photo",

                    "published_at_display",
                    "lifecycle_status_display",
                    "quality_status_display",
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    )

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == 'POST':
            request._km_explicit_save_cutoff = timezone.now()
        if object_id is not None and request.method == "POST" and "_unpublish_place" in request.POST:
            obj = self.get_object(request, object_id)
            if obj is None or not self.has_change_permission(request, obj):
                raise PermissionDenied
            try:
                expected_version = int(request.POST.get("unpublish_version", "-1"))
                from catalog.services.publication import unpublish
                unpublish(actor=request.user, target_type="place", target_id=obj.pk,
                          expected_version=expected_version)
            except (ValueError, ValidationError) as exc:
                detail = "; ".join(exc.messages) if isinstance(exc, ValidationError) else str(_("Неверная версия карточки."))
                self.message_user(request, detail, level=messages.ERROR)
            else:
                self.message_user(request, _("Карточка снята с публикации и скрыта с сайта."), level=messages.SUCCESS)
            return HttpResponseRedirect(self._place_change_url(obj))
        if object_id is not None:
            obj = self.get_object(request, object_id)
            revision = (
                VolunteerPlaceRevision.objects.select_related("author", "reviewed_by")
                .filter(place=obj)
                .exclude(status=VolunteerPlaceRevision.Status.APPROVED)
                .first()
                if obj is not None
                else None
            )
            if request.method == "POST" and "_restart_working_revision" in request.POST:
                if obj is None or not self.has_change_permission(request, obj):
                    raise PermissionDenied
                from catalog.services.volunteer_places import restart_working_revision
                try:
                    restart_working_revision(
                        user=request.user, place_id=obj.pk,
                        version=int(request.POST.get("revision_version", -1)),
                        token=request.POST.get("base_token", ""),
                        source=PlaceChangeAudit.SOURCE_ADMIN,
                    )
                except (ValueError, ValidationError) as exc:
                    message = "; ".join(exc.messages) if isinstance(exc, ValidationError) else _("Обновите страницу.")
                    self.message_user(request, message, level=messages.ERROR)
                else:
                    self.message_user(request, _("Загружена текущая версия. Предыдущие правки сохранены в истории."), level=messages.SUCCESS)
                return HttpResponseRedirect(self._place_change_url(obj))
            from catalog.services.staff_roles import is_volunteer
            if revision is not None and revision.author is not None and is_volunteer(revision.author):
                if not self.has_change_permission(request, obj):
                    raise PermissionDenied
                return self._volunteer_revision_changeform_view(request, obj=obj, revision=revision)
        try:
            with transaction.atomic():
                return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)
        except ValidationError as exc:
            if request.method == 'GET':
                # Archived/deleted targets cannot render an editable draft.
                # Redirecting to this same GET would loop forever.
                raise Http404 from exc
            if any(error.code == 'place_identity_duplicate' for error in getattr(exc,'error_list',())):
                request._km_identity_conflict=exc
                with transaction.atomic():
                    return super().changeform_view(request,object_id=object_id,form_url=form_url,extra_context=extra_context)
            if any(error.code == 'candidate_version_conflict' for error in getattr(exc, 'error_list', ())):
                # The first write has rolled back. Redisplay the submitted POST
                # as invalid; never replay a save or replace its stale token.
                request._km_candidate_conflict = exc
                with transaction.atomic():
                    return super().changeform_view(request, object_id=object_id, form_url=form_url, extra_context=extra_context)
            self.message_user(request, "; ".join(exc.messages), level=messages.ERROR)
            return HttpResponseRedirect(request.path)


    def _volunteer_revision_changeform_view(self, request, *, obj, revision):
        from catalog.services.place_editor_drafts import config_for
        from catalog.services.place_taxonomy_config import build_place_taxonomy_config
        from catalog.services.volunteer_editor import editor_context
        from catalog.services.volunteer_places import (
            editor_form, live_snapshot, save_working_revision, revision_base_matches,
            restart_working_revision,
        )

        if request.method == "POST":
            if request.POST.get("action") == "restart":
                try:
                    restart_working_revision(
                        user=request.user, place_id=obj.pk,
                        version=int(request.POST.get("revision_version", -1)),
                        token=request.POST.get("base_token", ""),
                        source=PlaceChangeAudit.SOURCE_ADMIN,
                    )
                except (ValueError, ValidationError) as exc:
                    message = "; ".join(exc.messages) if isinstance(exc, ValidationError) else _("Обновите страницу.")
                    self.message_user(request, message, level=messages.ERROR)
                else:
                    self.message_user(request, _("Загружена текущая версия. Предыдущие правки сохранены в истории."), level=messages.SUCCESS)
                return HttpResponseRedirect(request.path)
            if request.POST.get("action") != "admin_save":
                raise PermissionDenied
            obj, revision, form = save_working_revision(
                user=request.user,
                place_id=obj.pk,
                data=request.POST,
                files=request.FILES,
                source=PlaceChangeAudit.SOURCE_ADMIN,
            )
            if not form.errors:
                self._close_private_working_draft(request, obj, change=True)
                self.message_user(request, _("Рабочая версия волонтёра сохранена."), level=messages.SUCCESS)
                return HttpResponseRedirect(request.path)
        else:
            form = editor_form(obj, revision)

        candidate = form.instance
        public = obj.status == Place.STATUS_PUBLISHED and obj.is_active
        try:
            photo = candidate.photo or candidate.cover_photo
            photo_url = photo.url if photo else ""
        except (ValueError, OSError):
            photo_url = ""
        card = {
            "name": candidate.name_i18n(),
            "status": revision.get_status_display(),
            "note": revision.review_note,
            "detail_url": reverse("admin:volunteer_review", args=[obj.pk]),
            "photo_url": photo_url,
            "public": public,
            "public_url": obj.get_absolute_url() if public else "",
        }
        context = {
            **self.admin_site.each_context(request),
            "title": _("Рабочая версия места"),
            "opts": self.opts,
            "original": obj,
            "object_id": str(obj.pk),
            "form": form,
            "adminform": {"form": form},
            "revision": revision,
            "place": obj,
            "card": card,
            "conflict": not revision_base_matches(revision, obj),
            "admin_working_revision": True,
            "km_place_draft_config": config_for(user=request.user, place=obj, surface='admin'),
            "volunteer_editor": True,
            "km_place_taxonomy_picker": build_place_taxonomy_config(form),
            "google_maps_api_key": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
            **editor_context(form),
        }
        return TemplateResponse(request, self.volunteer_revision_change_form_template, context)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        from catalog.services.permanent_place_wizard import ui_copy
        from catalog.services.place_editor_drafts import config_for
        may_edit = self.has_change_permission(request, obj) if obj and obj.pk else self.has_add_permission(request)
        context['km_place_draft_config'] = config_for(user=request.user, place=obj, surface='admin') if may_edit else {}
        context["km_place_entry_copy"] = ui_copy()
        from ..navigation import place_navigation
        context["km_place_navigation"] = place_navigation(request, obj)
        if obj and obj.pk:
            context["km_place_site_preview_url"] = reverse(
                "admin:catalog_place_site_preview", args=[obj.pk], current_app=self.admin_site.name)

        context["km_place_pending_review"] = None
        context["km_place_revision_recovery"] = None
        if may_edit and obj and obj.pk:
            from catalog.services.volunteer_places import base_token, revision_base_matches
            # ModelForm rendering may have projected a candidate onto obj.
            # Recovery must confirm the actual current record, never that projection.
            current = self.get_object(request, str(obj.pk))
            revision = VolunteerPlaceRevision.objects.filter(place=current).exclude(
                status=VolunteerPlaceRevision.Status.APPROVED).first() if current is not None else None
            if revision is not None and revision.status == 'pending':
                from catalog.services.business_team import platform_has_action
                from catalog.services.staff_roles import is_volunteer
                if not is_volunteer(request.user) and platform_has_action(user=request.user, action='place.publish'):
                    from catalog.services.moderation_hub import field_label
                    from catalog.services.moderation_changes import review_copy
                    context['km_place_pending_review'] = {
                        'url': reverse('admin:volunteer_moderation_detail', args=['content', revision.pk]),
                        'labels': [field_label(current, key) for key in revision.changed_fields],
                        'copy': review_copy(),
                    }
            if revision is not None and not revision_base_matches(revision, current):
                context["km_place_revision_recovery"] = {
                    "version": revision.version,
                    "base_token": base_token(current),
                }
        context["km_place_candidate_conflict"] = getattr(request, '_km_candidate_conflict', None) is not None
        context["km_place_current_version_url"] = request.path
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        context["km_place_draft_save_failed"] = "_save_draft" in request.POST and bool(context.get("errors"))
        fallback_url = reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist",
            current_app=self.admin_site.name,
        )
        referer = request.META.get("HTTP_REFERER", "")
        if referer and url_has_allowed_host_and_scheme(
            referer,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            referer_path = referer.split("?", 1)[0].split("#", 1)[0]
            if referer_path != request.path:
                context["km_admin_back_url"] = referer
            else:
                context["km_admin_back_url"] = fallback_url
        else:
            context["km_admin_back_url"] = fallback_url
        adminform = context.get("adminform")
        if adminform is not None:
            displayed_form = adminform.form
            if not displayed_form.is_bound and displayed_form.instance.pk and 'nested_pricing' in displayed_form.fields and not displayed_form.initial.get('nested_pricing'):
                from catalog.services.pricing_plans import serialize_nested_pricing
                displayed_form.initial['nested_pricing'] = json.dumps(serialize_nested_pricing(displayed_form.instance), ensure_ascii=False)
            inline_admin_formsets = context.get("inline_admin_formsets", [])
            context["km_place_gallery_inline"] = next(
                (
                    inline_admin_formset
                    for inline_admin_formset in inline_admin_formsets
                    if inline_admin_formset.opts.model.__name__ == "PlacePhoto"
                ),
                None,
            )
            context["km_place_form_sections"] = self._build_place_form_sections(adminform)
            context["km_place_verification_section"] = dict(self.PLACE_FORM_VERIFICATION_SECTION)
            context["km_place_secondary_sections"] = self._build_place_secondary_sections(adminform)
            context["km_place_inline_sections"] = self._build_place_inline_sections(inline_admin_formsets)
            context["km_place_carryover_fields"] = self._build_place_carryover_fields(
                adminform,
                context["km_place_secondary_sections"],
            )
            context["km_place_required_fields"] = {
                requirement.field for requirement in PLACE_READINESS_REQUIREMENTS
            }
            context["km_place_form_summary"] = self._build_place_form_summary(
                form=adminform.form,
                obj=obj,
                add=add,
            )
            context["km_place_form_errors"] = self._build_place_form_errors(
                adminform.form,
                inline_admin_formsets=inline_admin_formsets,
            )
            section_states = self._build_place_section_states(
                context["km_place_form_summary"],
                context["km_place_form_errors"],
            )
            context["km_place_form_summary"]["sections"] = section_states
            for section in context["km_place_form_sections"]:
                section["state"] = section_states.get(section["id"], {})
            context["km_place_verification_section"]["state"] = section_states.get(
                self.PLACE_FORM_VERIFICATION_SECTION["id"], {}
            )
            context["km_place_language_tabs"] = self._build_place_language_tabs(adminform.form)
            context["km_place_condition_tabs"] = self._build_place_text_tabs(
                adminform.form, "extra_conditions"
            )
            context["km_place_info_tabs"] = self._build_place_text_tabs(
                adminform.form, "additional_info"
            )
            context["km_place_error_preservation_note"] = bool(context["km_place_form_errors"])
            context["km_place_file_reselect_note"] = bool(request.FILES and context["km_place_form_errors"])
            context["km_place_taxonomy_picker"] = self._build_taxonomy_picker_config(adminform.form)
            context["km_place_map_alert"] = self._build_place_map_alert(
                form=adminform.form,
                obj=obj,
                has_google_maps_api_key=bool(context["google_maps_api_key"]),
            )
            context["km_place_public_link"] = self._build_public_place_link(request, obj=obj)
            context["km_place_duplicates_url"] = reverse(
                f"admin:{self.opts.app_label}_{self.opts.model_name}_duplicate_candidates"
            )
        context["km_identity_copy"] = identity_copy()
        context["km_identity_registry_url"] = reverse("admin:catalog_place_identity_registry")
        context["km_identity_compare_url"] = reverse("admin:catalog_place_identity_compare", args=[obj.pk]) if obj and obj.pk else ""
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def add_view(self, request, form_url='', extra_context=None):
        if not request.GET.get("type"):
            from django.shortcuts import redirect
            return redirect("admin_add_choice")
        return super().add_view(request, form_url=form_url, extra_context=extra_context)


    def _fieldset_list(self, adminform):
        return list(adminform) if adminform is not None else []

    def _build_place_form_errors(self, form, *, inline_admin_formsets=()):
        """Return actionable errors with anchors to the matching form section."""
        # Seed from the readiness requirements so a required field never ends up
        # without a section, then keep the extra fields this panel also covers.
        section_by_field = {
            requirement.field: f"#{requirement.section}"
            for requirement in PLACE_READINESS_REQUIREMENTS
        }
        section_by_field.update({
            "category": "#basics",
            "subcategory": "#basics",
            "name": "#basics",
            "name_az": "#basics",
            "name_ru": "#basics",
            "name_en": "#basics",
            "description_az": "#basics",
            "description_ru": "#basics",
            "description_en": "#basics",
            "age_from": "#pricing",
            "age_to": "#pricing",
            "offers_adult_classes": "#pricing",
            "price_from": "#pricing",
            "price_to": "#pricing",
            "pricing_plans": "#pricing",
            "district": "#location",
            "metro": "#location",
            "address": "#location",
            "phone1": "#location",
            "photo": "#media",
        })
        # Where a click should land, when that is not the field's own input.
        target_by_field = {
            "pricing_plans": "#pricing",
            "structured_schedule": "#admin-place-schedule",
        }
        errors = []

        for weekday, messages_for_day in getattr(form, "schedule_editor_errors", {}).items():
            day_label = FULL_DAY_LABELS.get(weekday, weekday)
            for message in messages_for_day:
                errors.append({
                    "label": str(_("Расписание: %(day)s") % {"day": day_label}),
                    "message": str(message),
                    "target": f"#admin-place-schedule-row-{weekday}",
                    "section": "#location",
                })

        for field_name, messages_for_field in form.errors.items():
            if field_name == "structured_schedule" and getattr(form, "schedule_editor_errors", None):
                # The detailed day errors above are more useful than the generic field error.
                continue
            if field_name == "__all__":
                label = str(_("Карточка"))
                target = "#verification"
                section = "#verification"
            else:
                field = form.fields.get(field_name)
                label = str(field.label) if field is not None else field_name
                section = section_by_field.get(field_name, "")
                target = target_by_field.get(field_name)
                if not target:
                    target = f"#id_{field_name}" if field_name in form.fields else (section or "#verification")
            for message in messages_for_field:
                errors.append({"label": label, "message": str(message), "target": target, "section": section})

        # Django puts inline-form errors (for example, gallery photos) into the
        # top-level ``errors`` object, not into the main form. Surface them here
        # as actionable messages instead of showing the vague fallback alert.
        for inline_admin_formset in inline_admin_formsets:
            formset = inline_admin_formset.formset
            inline_label = str(inline_admin_formset.opts.verbose_name)
            target = "#media" if inline_admin_formset.opts.model.__name__ == "PlacePhoto" else "#verification"
            for message in formset.non_form_errors():
                errors.append({"label": inline_label, "message": str(message), "target": target, "section": target})
            for inline_form in formset.forms:
                for field_name, messages_for_field in inline_form.errors.items():
                    field = inline_form.fields.get(field_name)
                    label = str(field.label) if field is not None else inline_label
                    for message in messages_for_field:
                        errors.append({"label": label, "message": str(message), "target": target, "section": target})

        return errors

    def _build_taxonomy_picker_config(self, form):
        from catalog.services.place_taxonomy_config import build_place_taxonomy_config
        return build_place_taxonomy_config(form)

    def _build_place_form_sections(self, adminform):
        return sorted((dict(section) for section in self.PLACE_FORM_PRIMARY_SECTIONS), key=lambda section: section['step'])

    def _build_place_carryover_fields(self, adminform, secondary_sections):
        """Bound fields the redesigned template does not render anywhere.

        They are written into the form as hidden inputs so a save keeps their
        stored value instead of clearing it.
        """

        form = adminform.form
        rendered = set(self.PLACE_FORM_RENDERED_FIELDS)
        for section in secondary_sections:
            for fieldset in section["fieldsets"]:
                for line in fieldset:
                    for admin_field in line:
                        name = getattr(getattr(admin_field, "field", None), "name", None)
                        if name:
                            rendered.add(name)
        # Only the signed publication token is safe to carry as a hidden
        # field. Unrendered model values must never be echoed back from a
        # stale browser tab as editable POST data.
        return [form["publication_token"]] if "publication_token" in form.fields else []

    def _build_place_secondary_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.PLACE_FORM_SECONDARY_SECTIONS:
            section_fieldsets = [
                fieldsets[index]
                for index in section["fieldset_indexes"]
                if index < len(fieldsets)
            ]
            if not section_fieldsets:
                continue
            sections.append(
                {
                    "id": section["id"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _build_place_inline_sections(self, inline_admin_formsets):
        sections = []
        for inline_admin_formset in inline_admin_formsets or []:
            model_name = inline_admin_formset.opts.model.__name__
            if model_name == "PlacePhoto":
                continue
            elif model_name == "PlaceReview":
                sections.append(
                    {
                        "id": "reviews",
                        "title": _("Отзывы по кружкам"),
                        "description": _("Связанные отзывы и их текущее состояние."),
                        "items": [inline_admin_formset],
                    }
                )
            elif model_name == "PlaceChangeAudit":
                sections.append(
                    {
                        "id": "audit",
                        "title": _("История изменений карточек"),
                        "description": _("Аудит изменений по ключевым полям карточки."),
                        "items": [inline_admin_formset],
                    }
                )
            else:
                sections.append(
                    {
                        "id": f"inline-{model_name.lower()}",
                        "title": inline_admin_formset.opts.verbose_name_plural,
                        "description": "",
                        "items": [inline_admin_formset],
                    }
                )
        return sections

    def _field_has_value(self, form, field_name: str, *, obj=None) -> bool:
        if field_name in form.files and form.files.get(field_name):
            return True

        if form.is_bound:
            raw_value = form.data.get(form.add_prefix(field_name))
        else:
            raw_value = form.initial.get(field_name, getattr(getattr(form, "instance", None), field_name, None))

        if not raw_value and raw_value != 0:
            if obj is not None:
                current_value = getattr(obj, field_name, None)
                if current_value or current_value == 0:
                    return True
            return False

        return True

    def _place_visibility_state(self, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return {
                "label": str(_("Черновик")),
                "tone": "muted",
                "hint": str(_("Карточка ещё не опубликована на сайте.")),
                "is_public": False,
            }
        if obj.is_deleted:
            return {
                "label": str(_("В удалённых")),
                "tone": "muted",
                "hint": str(_("Карточка скрыта с сайта и перемещена в удалённые.")),
                "is_public": False,
            }
        # Changelists receive ``km_in_public_catalog`` as a correlated EXISTS
        # annotation. Do not run a separate visibility query for every column
        # and every row; the fallback is for objects loaded outside get_queryset.
        is_in_public_catalog = False
        if obj.status == obj.STATUS_PUBLISHED and obj.is_active:
            annotated_visibility = getattr(obj, "km_in_public_catalog", None)
            is_in_public_catalog = (
                bool(annotated_visibility)
                if annotated_visibility is not None
                else public_place_queryset(Place.objects.filter(pk=obj.pk)).exists()
            )
        if obj.status == obj.STATUS_PUBLISHED and obj.is_active and not is_in_public_catalog:
            reasons = format_place_quality_errors(place_catalog_visibility_reasons(obj))
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "danger",
                "hint": str(_("Карточка имеет статус публикации, но не проходит проверку качества каталога: %(reasons)s.") % {"reasons": reasons}),
                "is_public": False,
            }
        if is_in_public_catalog:
            return {
                "label": str(_("Опубликовано")),
                "tone": "good",
                "hint": str(_("Карточка видна на сайте при текущих правилах качества каталога.")),
                "is_public": True,
            }
        if obj.status == obj.STATUS_PUBLISHED and not obj.is_active:
            return {
                "label": str(_("Снято с публикации")),
                "tone": "warn",
                "hint": str(_("Карточка была выведена из публичного каталога и сейчас не видна пользователям.")),
                "is_public": False,
            }
        if obj.status == obj.STATUS_PENDING:
            return {
                "label": str(_("На модерации")),
                "tone": "warn",
                "hint": str(_("Карточка сохранена, но ещё не показывается на сайте.")),
                "is_public": False,
            }
        if obj.status == obj.STATUS_REJECTED:
            return {
                "label": str(_("Отклонено")),
                "tone": "danger",
                "hint": str(_("Карточка отклонена и не показывается на сайте.")),
                "is_public": False,
            }
        if not obj.is_active:
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "warn",
                "hint": str(_("Карточка сохранена, но снята с публикации.")),
                "is_public": False,
            }
        return {
            "label": str(_("Черновик")),
            "tone": "muted",
            "hint": str(_("Карточка пока не опубликована на сайте.")),
            "is_public": False,
        }

    def _build_place_map_alert(self, *, form, obj=None, has_google_maps_api_key: bool):
        address_present = self._field_has_value(form, "address", obj=obj)
        lat_present = self._field_has_value(form, "lat", obj=obj)
        lng_present = self._field_has_value(form, "lng", obj=obj)
        should_show_provider_warning = not has_google_maps_api_key and (
            address_present or lat_present or lng_present or (obj is not None and obj.pk)
        )
        if should_show_provider_warning:
            return {
                "tone": "warning",
                "title": str(_("Карта пока не активна")),
                "message": str(
                    _("Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY, чтобы рассчитывать координаты прямо из формы.")
                ),
            }

        if obj is not None and obj.pk and not obj.is_map_ready:
            if obj.is_deleted:
                message = _("Карточка удалена и не может отображаться на карте, пока не будет восстановлена.")
            elif not obj.has_coordinates:
                from catalog.services.permanent_place_wizard import ui_copy
                message = ui_copy()["optional_map"]
            elif not obj.is_active or obj.status != obj.STATUS_PUBLISHED:
                message = _("Координаты есть, но карточка станет доступна на карте только после публикации.")
            else:
                message = _("Карта пока не готова для этой карточки.")
            return {
                "tone": "warning",
                "title": str(_("Проверьте готовность карты")),
                "message": str(message),
            }

        return None

    def _resolve_public_site_host(self, request) -> str:
        current_host = request.get_host()
        current_hostname, separator, port = current_host.partition(":")
        admin_host = (getattr(settings, "ADMIN_HOST", "") or "").strip().lower()

        if admin_host and current_hostname.lower() == admin_host and admin_host.startswith("admin."):
            public_hostname = admin_host[len("admin."):]
            return f"{public_hostname}{separator}{port}" if separator else public_hostname

        return current_host

    def _build_public_place_link(self, request, *, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return None

        visibility = self._place_visibility_state(obj)
        relative_url = obj.get_absolute_url()
        public_host = self._resolve_public_site_host(request)
        absolute_url = f"{'https' if request.is_secure() else request.scheme}://{public_host}{relative_url}"

        return {
            "url": absolute_url,
            "path": relative_url,
            "is_public": visibility["is_public"],
            "label": str(_("Открыть карточку на сайте")),
            "hint": (
                str(_("Карточка опубликована. Ссылка откроет её публичную страницу в новой вкладке."))
                if visibility["is_public"]
                else str(_("Карточка сейчас не видна пользователям. Кнопка появится после публикации."))
            ),
        }

    PLACE_LANGUAGE_TABS = (
        ("az", _("AZ · основной"), _("Название (AZ)"), _("Описание (AZ)"), False),
        ("ru", _("RU"), _("Название (RU)"), _("Описание (RU)"), True),
        ("en", _("EN"), _("Название (EN)"), _("Описание (EN)"), True),
    )

    def _build_place_language_tabs(self, form):
        tabs = []
        for code, label, name_label, description_label, optional in self.PLACE_LANGUAGE_TABS:
            name_field = f"name_{code}"
            description_field = f"description_{code}"
            if name_field not in form.fields or description_field not in form.fields:
                continue
            tabs.append(
                {
                    "code": code,
                    "label": label,
                    "optional": optional,
                    "name_label": name_label,
                    "description_label": description_label,
                    "name_field": form[name_field],
                    "description_field": form[description_field],
                }
            )
        return tabs

    def _build_place_text_tabs(self, form, base_name):
        """AZ/RU/EN variants of one text field, skipping the ones the form lacks."""

        tabs = []
        for code, label in (("az", "AZ"), ("ru", "RU"), ("en", "EN")):
            field_name = f"{base_name}_{code}"
            if field_name in form.fields:
                tabs.append({"code": code, "label": label, "field": form[field_name]})
        if not tabs and base_name in form.fields:
            tabs.append({"code": "az", "label": "AZ", "field": form[base_name]})
        return tabs

    SECTION_STATE_ICONS = {
        "done": "check_circle",
        "partial": "radio_button_checked",
        "error": "error",
        "empty": "radio_button_unchecked",
    }

    def _build_place_section_states(self, summary, form_errors):
        """Per-section status for the sticky navigation and the accordion badges.

        Everything here is derived from the readiness checklist that already sits
        in *summary* plus the form errors — the sections never count anything on
        their own.
        """

        sections_with_errors = {
            str(error.get("section") or "").lstrip("#")
            for error in form_errors
            if error.get("section")
        }
        counts: dict[str, dict] = {}
        for item in summary["checklist_items"]:
            bucket = counts.setdefault(item["section"], {"done": 0, "total": 0, "missing_labels": []})
            bucket["total"] += 1
            if item["initial"]:
                bucket["done"] += 1
            else:
                bucket["missing_labels"].append(item["label"])

        states = {}
        for section in list(self.PLACE_FORM_PRIMARY_SECTIONS) + [self.PLACE_FORM_VERIFICATION_SECTION]:
            section_id = section["id"]
            if section_id == self.PLACE_FORM_VERIFICATION_SECTION["id"]:
                done, total = summary["completed"], summary["total"]
            else:
                bucket = counts.get(section_id, {"done": 0, "total": 0, "missing_labels": []})
                done, total = bucket["done"], bucket["total"]

            if section_id in sections_with_errors:
                state = "error"
            elif total and done >= total:
                state = "done"
            elif done:
                state = "partial"
            else:
                state = "empty"

            if state == "error":
                label = str(_("Есть ошибка"))
            elif not total:
                label = ""
            elif done >= total:
                label = str(_("%(done)s из %(total)s") % {"done": done, "total": total})
            else:
                label = str(_("%(done)s из %(total)s") % {"done": done, "total": total})

            states[section_id] = {
                "id": section_id,
                "state": state,
                "icon": self.SECTION_STATE_ICONS[state],
                "done": done,
                "total": total,
                "label": label,
                "missing_message": (
                    str(_("Не заполнено: %(items)s")) % {"items": ", ".join(bucket["missing_labels"])}
                    if section_id != self.PLACE_FORM_VERIFICATION_SECTION["id"] and bucket["missing_labels"]
                    else ""
                ),
            }
        return states

    def _build_place_form_summary(self, *, form, obj=None, add=False):
        # Progress, the readiness badge and the "Проверка" list all read the
        # same twelve requirements as the publish gate.
        instance = obj if obj is not None else getattr(form, "instance", None)
        # A bound form already decided this in ``clean()``; reuse that verdict so
        # the rendered page cannot disagree with the save that just happened.
        readiness = getattr(form, "place_readiness", None) or evaluate_form_readiness(form, instance)
        if not form.is_bound:
            from catalog.services.permanent_place_rules import readiness_presentation_snapshot
            displayed = readiness_presentation_snapshot(form)
            readiness = evaluate_form_readiness(displayed, displayed.instance)
        # The main photo can be satisfied by a stored cover photo the browser
        # cannot inspect. Tell the live checklist, or it would contradict the
        # server and show a green card as incomplete. Legacy scalar prices are
        # deliberately absent here: they no longer satisfy the price item.
        server_only = {
            "photo": bool(instance is not None and getattr(instance, "cover_photo", None)),
        }
        from catalog.services.contact_policy import contact_client_config
        contact_config = contact_client_config(instance)
        checklist_items = [
            {
                "code": item.code,
                "label": item.label,
                "section": item.requirement.section,
                "field": item.requirement.field,
                "anchor": item.requirement.anchor,
                "check": item.requirement.client_check,
                "config": ({**item.requirement.client_config, **contact_config} if item.code == "phone" else item.requirement.client_config),
                "initial": item.is_complete,
                "message": item.issue.message if item.issue else "",
                "fallback": bool(server_only.get(item.code)) and item.is_complete,
            }
            for item in readiness.items
        ]
        missing = [
            {
                "code": issue.code,
                "label": issue.label,
                "message": issue.message,
                "section": issue.section,
                "field": issue.field,
                "anchor": issue.anchor,
            }
            for issue in readiness.issues
        ]
        advice = [
            {
                "code": issue.code,
                "label": issue.label,
                "message": issue.message,
                "section": issue.section,
                "field": issue.field,
                "anchor": issue.anchor,
            }
            for issue in readiness.advice
        ]
        completed = readiness.completed_count
        total = readiness.required_count
        completion_pct = readiness.percentage

        title = str(_("Новое место"))
        state_badges = []
        meta_items = []
        error_count = len(form.errors)
        visibility = self._place_visibility_state(obj)

        if obj is not None and obj.pk:
            title = obj.name_ru or obj.name or title
            quality = place_quality_check(obj)
            state_badges.append(
                {
                    "label": visibility["label"],
                    "tone": visibility["tone"],
                }
            )
            state_badges.append(
                {
                    "label": (
                        str(_("Статус: %(status)s") % {"status": dict(obj.STATUS_CHOICES).get(obj.status, obj.status)})
                        if obj.status == obj.STATUS_PUBLISHED and not visibility["is_public"]
                        else str(dict(obj.STATUS_CHOICES).get(obj.status, obj.status))
                    ),
                    "tone": "good" if obj.status == obj.STATUS_PUBLISHED and visibility["is_public"] else "muted",
                }
            )
            state_badges.append(
                {
                    "label": str(_("Есть координаты")) if obj.has_coordinates else str(_("Нужны координаты")),
                    "tone": "good" if obj.has_coordinates else "warn",
                }
            )
            meta_items.append(
                {
                    "label": str(_("Качество")),
                    "value": f"{quality.score} / 100",
                }
            )
            if not visibility["is_public"]:
                meta_items.append(
                    {
                        "label": str(_("Почему скрыто")),
                        "value": visibility["hint"],
                    }
                )
            if obj.published_at:
                meta_items.append(
                    {
                        "label": str(_("Опубликовано")),
                        "value": timezone.localtime(obj.published_at).strftime("%d.%m.%Y %H:%M"),
                    }
                )
        else:
            state_badges.append(
                {
                    "label": str(_("Черновой режим")),
                    "tone": "muted",
                }
            )

        if add:
            meta_items.insert(
                0,
                {
                    "label": str(_("Режим")),
                    "value": str(_("Создание новой карточки")),
                }
            )
        else:
            meta_items.insert(
                0,
                {
                    "label": str(_("Режим")),
                    "value": str(_("Редактирование карточки")),
                }
            )

        return {
            "title": title,
            "completion_pct": completion_pct,
            "completed": completed,
            "total": total,
            "error_count": error_count,
            "visibility": visibility,
            "checklist_items": checklist_items,
            "missing": missing,
            "advice": advice,
            "is_ready": readiness.is_ready,
            "readiness_label": str(_("Готово к публикации")) if not missing else str(_("Нужна доработка")),
            "readiness_tone": "good" if not missing else "warn",
            "state_badges": state_badges,
            "meta_items": meta_items,
        }
