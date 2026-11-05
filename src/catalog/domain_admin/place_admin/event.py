"""Django admin for events."""

from django.conf import settings
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from catalog.models import (
    Place,
    Event,
    EventPhoto,
)
from ..queue_sorting import QueueSortingAdminMixin, QueueSortParameter
from ..ui_utils import render_primary_action, render_action_menu
from .filters import EventDeletedFilter
from .forms import EventAdminForm
from .inlines import EventPhotoInline


@admin.register(Event)
class EventAdmin(QueueSortingAdminMixin, admin.ModelAdmin):
    form = EventAdminForm
    inlines = [EventPhotoInline]
    actions = ("mark_published", "mark_draft", "mark_pending", "mark_rejected")
    list_display = (
        "display_name",
        "category",
        "start_datetime_display",
        "end_datetime_display",
        "owner",
        "lifecycle_status_display",
        "updated_at",
        "row_actions",
    )
    list_filter = (QueueSortParameter, EventDeletedFilter, "status", "category", "start_datetime", "owner")
    search_fields = ("name", "name_az", "name_ru", "name_en", "address", "phone", "owner__username", "owner__email")
    readonly_fields = ("slug", "created_at", "updated_at")
    list_select_related = ("owner", "related_place")
    list_per_page = 15
    change_form_template = "admin/catalog/event/change_form.html"
    autocomplete_fields = ("organizer_organization", "organizer_specialist", "related_place", "owner")
    EVENT_FORM_PRIMARY_SECTIONS = (
        {"id": "basics", "step": "01", "title": _("Событие"),
         "description": _("Организатор, название и описание."), "fieldset_indexes": (0,)},
        {"id": "schedule", "step": "02", "title": _("Когда и где"),
         "description": _("Дата, возраст, стоимость и площадка."), "fieldset_indexes": (1,)},
        {"id": "media", "step": "03", "title": _("Фото и запись"),
         "description": _("Обложка и способ связи с организатором."), "fieldset_indexes": (2,)},
    )
    EVENT_FORM_SECONDARY_SECTIONS = (
        {"id": "translations", "title": _("Переводы RU / EN"),
         "description": _("Необязательно"), "fieldset_indexes": (3,)},
        {"id": "service", "title": _("Служебные настройки"),
         "description": _("Владелец, статус и история записи"), "fieldset_indexes": (4,)},
    )
    fieldsets = (
        (_("Событие"), {"fields": ("name_az", "category", ("organizer_organization", "organizer_specialist"), "description_az")}),
        (_("Когда и где"), {"fields": (("start_datetime", "end_datetime"), ("age_from", "age_to"),
            "price_mode", ("price_amount", "price_amount_max", "price_currency"), "price_text", "event_format",
            "related_place", ("region", "district", "metro"), "address", ("lat", "lng"))}),
        (_("Фото и запись"), {"fields": ("photo", "registration_method", "phone", "whatsapp", "registration_url",
            "instagram", "website", "moderation_note")}),
        (_("Переводы RU / EN"), {"fields": (("name_ru", "description_ru"), ("name_en", "description_en"))}),
        (_("Служебные настройки"), {"fields": ("owner", "slug", "status", "published_at", "rejection_reason",
            ("deleted_at", "created_at", "updated_at"))}),
    )
    add_fieldsets = fieldsets

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("status", Event.STATUS_DRAFT)
        initial.setdefault("price_mode", "unknown")
        from catalog.models import Organization, Specialist
        organizations = list(Organization.objects.filter(owner=request.user, archived_at__isnull=True).values_list("pk", flat=True)[:2])
        specialists = list(Specialist.objects.filter(verified_person_user=request.user, person_verified_at__isnull=False, is_active=True).values_list("pk", flat=True)[:2])
        if len(organizations) + len(specialists) == 1:
            initial.setdefault("organizer_organization" if organizations else "organizer_specialist", (organizations or specialists)[0])
        return initial

    def get_fieldsets(self, request, obj=None):
        if obj is not None:
            return self.fieldsets
        return self.fieldsets[:-1] + ((self.fieldsets[-1][0], {"fields": ("owner", "status", "rejection_reason")}),)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        context["google_maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        adminform = context.get("adminform")
        if adminform is not None:
            inline_admin_formsets = context.get("inline_admin_formsets", [])
            context["km_event_gallery_inline"] = next(
                (
                    inline_admin_formset
                    for inline_admin_formset in inline_admin_formsets
                    if inline_admin_formset.opts.model is EventPhoto
                ),
                None,
            )
            context["km_event_form_sections"] = self._build_event_form_sections(adminform)
            context["km_event_secondary_sections"] = self._build_event_secondary_sections(adminform)
            context["km_event_form_summary"] = self._build_event_form_summary(
                form=adminform.form,
                obj=obj,
                add=add,
            )
        from catalog.services.event_presentation import EVENT_UI_CONFIG
        context["km_event_ui_config"] = EVENT_UI_CONFIG
        context["km_event_review_mode"] = bool(obj and obj.status == Event.STATUS_PENDING and not adminform.form.is_bound)
        if obj and obj.pk:
            context["km_event_review_url"] = reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_review", args=[obj.pk])
            context["km_event_repeat_url"] = reverse(f"admin:{self.opts.app_label}_{self.opts.model_name}_repeat", args=[obj.pk])
        if adminform:
            form = adminform.form
            context["km_event_translation_errors"] = any(name in form.errors for name in ("name_ru", "description_ru", "name_en", "description_en"))
            context["km_event_service_errors"] = any(name in form.errors for name in ("owner", "status", "rejection_reason", "published_at"))
        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def _fieldset_list(self, adminform):
        return list(adminform) if adminform is not None else []

    def _build_event_form_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.EVENT_FORM_PRIMARY_SECTIONS:
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
                    "step": section["step"],
                    "title": section["title"],
                    "description": section["description"],
                    "fieldsets": section_fieldsets,
                }
            )
        return sections

    def _build_event_secondary_sections(self, adminform):
        fieldsets = self._fieldset_list(adminform)
        sections = []
        for section in self.EVENT_FORM_SECONDARY_SECTIONS:
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

    def _event_visibility_state(self, obj=None):
        if obj is None or not getattr(obj, "pk", None):
            return {
                "label": str(_("Новая карточка")),
                "tone": "muted",
                "hint": str(_("Мероприятие ещё не опубликовано на сайте.")),
                "is_public": False,
            }
        if obj.deleted_at:
            return {
                "label": str(_("В удалённых")),
                "tone": "muted",
                "hint": str(_("Карточка удалена и не показывается на сайте.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_PENDING:
            return {
                "label": str(_("На модерации")),
                "tone": "warn",
                "hint": str(_("Мероприятие сохранено, но ещё не доступно на сайте.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_REJECTED:
            return {
                "label": str(_("Отклонено")),
                "tone": "danger",
                "hint": str(_("Нужно исправить карточку перед следующей публикацией.")),
                "is_public": False,
            }
        if obj.status == Event.STATUS_CANCELLED:
            return {
                "label": str(_("Скрыто с сайта")),
                "tone": "warn",
                "hint": str(_("Мероприятие сохранено, но вручную снято с публикации.")),
                "is_public": False,
            }
        if obj.is_public:
            return {
                "label": str(_("Опубликовано")),
                "tone": "good",
                "hint": str(_("Событие видно на сайте и участвует в афише мероприятий.")),
                "is_public": True,
            }
        if obj.effective_status == Event.STATUS_EXPIRED:
            return {
                "label": str(_("Завершено")),
                "tone": "muted",
                "hint": str(_("Дата события уже прошла, поэтому оно не показывается как актуальное.")),
                "is_public": False,
            }
        return {
            "label": str(_("Черновик")),
            "tone": "muted",
            "hint": str(_("Событие пока не опубликовано на сайте.")),
            "is_public": False,
        }

    def _build_event_form_summary(self, *, form, obj=None, add=False):
        from copy import copy
        from catalog.services.event_readiness import publication_errors, has_possible_duplicate
        probe_data = form.data.copy() if form.is_bound else {
            name: form[name].value() for name in form.fields if name != "photo"
        }
        for action in ("_save_draft", "_unpublish_event"):
            probe_data.pop(action, None)
        probe_data["_publish_event"] = "1"
        probe = type(form)(data=probe_data, files=form.files, instance=copy(form.instance), check_version=False)
        server_ready = probe.is_valid()
        requirements = publication_errors(probe.instance)
        missing = []
        for field_name, message in requirements.items():
            target = field_name if field_name in form.fields else "organizer_organization"
            label = str(form.fields[target].label) if target in form.fields else str(message)
            missing.append({"label": label, "message": str(message), "field_id": f"id_{target}"})
        saved_obj = Event.objects.filter(pk=obj.pk).first() if form.is_bound and obj and obj.pk else obj
        visibility = self._event_visibility_state(saved_obj)
        title = obj.name_i18n() if obj and obj.pk else str(_("Новое мероприятие"))
        return {
            "title": title, "visibility": visibility, "missing": missing,
            "server_ready": server_ready, "error_count": len(form.errors),
            "publication_errors": [errors for name, errors in probe.errors.items() if name not in requirements],
            "readiness_label": str(_("Можно опубликовать")) if server_ready else str(_("Проверьте обязательные поля")),
            "readiness_tone": "good" if server_ready else "warn",
            "duplicate_warning": has_possible_duplicate(probe.instance),
            # Compatibility for existing consumers; the editor no longer displays percentages.
            "total": max(len(form.fields), 1), "completed": len(form.fields) if server_ready else 0,
            "completion_pct": 100 if server_ready else 0,
            "progress_items": [], "state_badges": [], "meta_items": [],
            "checklist_items": [{"field_name": item["field_id"][3:]} for item in missing],
        }

    def get_urls(self):
        names = f"{self.opts.app_label}_{self.opts.model_name}"
        return [
            path("<path:object_id>/repeat/", self.admin_site.admin_view(self.repeat_view), name=f"{names}_repeat"),
            path("<path:object_id>/review/", self.admin_site.admin_view(self.review_view), name=f"{names}_review"),
            path("venue-facts/", self.admin_site.admin_view(self.venue_facts_view), name=f"{names}_venue_facts"),
            path("search-suggestions/", self.admin_site.admin_view(self.search_suggestions_view), name=f"{names}_search_suggestions"),
        ] + super().get_urls()

    def search_suggestions_view(self, request):
        if not self.has_view_or_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        variants = list(dict.fromkeys([term, term.lower(), term.capitalize(), term.upper()]))
        q_filter = Q()
        fields = ("name", "name_az", "name_ru", "name_en", "slug", "venue_label", "district", "related_place__name", "owner__username", "owner__email")
        for v in variants:
            for fld in fields:
                q_filter |= Q(**{f"{fld}__icontains": v})

        queryset = Event.objects.filter(q_filter).select_related("category", "related_place", "owner").distinct()[:8]

        results = []
        for event in queryset:
            title = (event.name_i18n(language_code) or event.name or "").strip()
            if not title:
                continue

            meta_parts = []
            venue_title = ""
            if event.related_place:
                venue_title = event.related_place.name_i18n(language_code) or event.related_place.name
            elif event.venue_label:
                venue_title = event.venue_label
            if venue_title:
                meta_parts.append(venue_title)

            time_str = ""
            if event.start_datetime:
                local_dt = timezone.localtime(event.start_datetime)
                time_str = local_dt.strftime("%d.%m %H:%M")
                meta_parts.append(time_str)

            if event.district:
                meta_parts.append(str(event.district))

            owner_label = ""
            if event.owner:
                owner_label = event.owner.get_username() or getattr(event.owner, "email", "")
                if owner_label:
                    meta_parts.append(str(owner_label))

            change_url = reverse("admin:catalog_event_change", args=[event.pk])

            tone = "muted"
            if event.status == Event.STATUS_PUBLISHED:
                tone = "good"
            elif event.status == Event.STATUS_PENDING:
                tone = "warn"
            elif event.status in (Event.STATUS_REJECTED, getattr(Event, "STATUS_CANCELLED", "cancelled")):
                tone = "danger"

            category_label = event.category.name_i18n(language_code) if event.category else ""
            format_label = event.get_event_format_display() if hasattr(event, "get_event_format_display") else ""
            cat_combined = f"{category_label} · {format_label}" if (category_label and format_label) else (category_label or format_label)

            results.append(
                {
                    "id": event.pk,
                    "value": title,
                    "label": title,
                    "meta": " • ".join(part for part in meta_parts if part)[:180],
                    "status": event.status,
                    "status_label": event.get_status_display(),
                    "status_tone": tone,
                    "category": cat_combined,
                    "district": venue_title or event.district,
                    "address": time_str,
                    "phone": "",
                    "owner": owner_label,
                    "change_url": change_url,
                    "public_url": "",
                }
            )

        return JsonResponse(
            {
                "results": results,
                "labels": {
                    "edit": str(_("Редактировать мероприятие")),
                    "found": str(_("Найдено")),
                },
            }
        )

    def venue_facts_view(self, request):
        if not self.has_add_permission(request) and not self.has_change_permission(request):
            raise PermissionDenied
        venue = Place.objects.filter(pk=request.GET.get("id"), deleted_at__isnull=True, is_active=True).first() if str(request.GET.get("id", "")).isdigit() else None
        if venue is None:
            raise Http404
        if venue.status != Place.STATUS_PUBLISHED and venue.owner_id != request.user.pk and not request.user.has_perm("catalog.view_place") and not request.user.has_perm("catalog.change_place"):
            raise PermissionDenied
        from catalog.services.locations import init_location_fields
        from types import SimpleNamespace
        location = SimpleNamespace(initial={})
        init_location_fields(location, venue)
        return JsonResponse({"address": venue.address, "phone": venue.phone1,
            "lat": str(venue.lat) if venue.lat is not None else "", "lng": str(venue.lng) if venue.lng is not None else "",
            "region": location.initial.get("region", ""), "district": venue.district, "metro": venue.metro})

    def repeat_view(self, request, object_id):
        from django.http import HttpResponseNotAllowed
        from catalog.services.event_domain import repeat_event
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        if not self.has_change_permission(request, obj) or not self.has_add_permission(request):
            raise PermissionDenied
        try:
            draft = repeat_event(actor=request.user, event_id=obj.pk,
                expected_updated_at=request.POST.get("expected_updated_at"), review=True)
        except ValidationError as exc:
            return HttpResponse("; ".join(exc.messages), status=409)
        from catalog.services.phone_numbers import contact_copy
        self.message_user(request, contact_copy("Создан новый черновик. Выберите дату и проверьте условия.", "Yeni qaralama yaradıldı. Tarixi seçin və şərtləri yoxlayın.", "A new draft was created. Choose its date and review the details."), messages.SUCCESS)
        return HttpResponseRedirect(self._event_change_url(draft))

    def review_view(self, request, object_id):
        from django.http import HttpResponseNotAllowed
        from catalog.services.event_domain import review_event
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        try:
            review_event(actor=request.user, event_id=obj.pk,
                expected_updated_at=request.POST.get("expected_updated_at"),
                decision=request.POST.get("decision"), reason=request.POST.get("reason", ""))
        except ValidationError as exc:
            stale = getattr(exc, "code", None) == "stale_version" or any(getattr(item, "code", None) == "stale_version" for item in getattr(exc, "error_list", []))
            return HttpResponse("; ".join(exc.messages), status=409 if stale else 400)
        self.message_user(request, _("Решение сохранено."), messages.SUCCESS)
        return HttpResponseRedirect(reverse("admin:catalog_event_change", args=[obj.pk]))

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_i18n()
        meta = [f"ID {obj.pk}"]
        if obj.deleted_at:
            meta.append(str(_("Удалено")))
        preview = ""
        if obj.photo and getattr(obj.photo, "name", ""):
            preview = format_html('<img src="{}" alt="" class="km-admin-thumb" loading="lazy">', obj.photo.url)
        else:
            preview = mark_safe('<span class="km-admin-thumb km-admin-thumb--placeholder" aria-hidden="true">•</span>')
        return format_html(
            '<div class="km-admin-entry">{}<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div></div>',
            preview,
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((item,) for item in meta)),
        )

    @admin.display(description=_("Статус"))
    def lifecycle_status_display(self, obj):
        from django.utils.html import format_html
        if obj.deleted_at:
            tone, label = "danger", _("В удаленных")
        elif obj.status == Event.STATUS_PUBLISHED:
            tone, label = "good", _("Опубликовано")
        elif obj.status == Event.STATUS_PENDING:
            tone, label = "warn", _("На модерации")
        elif obj.status == Event.STATUS_REJECTED:
            tone, label = "danger", _("Отклонено")
        elif obj.status == Event.STATUS_EXPIRED:
            tone, label = "muted", _("Завершено")
        else:
            tone, label = "muted", dict(Event.STATUS_CHOICES).get(obj.status, obj.status)

        return format_html(
            '<div class="km-admin-badges"><span class="km-admin-badge km-admin-badge--{}">{}</span></div>',
            tone,
            label,
        )

    @admin.display(description=_("Начало мероприятия"), ordering="start_datetime")
    def start_datetime_display(self, obj):
        if not obj.start_datetime:
            return "—"
        from django.utils import timezone
        from django.utils.html import format_html
        from django.utils.formats import date_format

        now = timezone.now()
        local_start = timezone.localtime(obj.start_datetime)
        local_now = timezone.localtime(now)
        dt_str = date_format(local_start, "d E Y, H:i")

        is_past = (now > obj.end_datetime) if obj.end_datetime else (now > obj.start_datetime)

        if is_past:
            badge_html = '<span class="km-timing-badge km-timing-badge--ended">Завершено</span>'
        elif obj.end_datetime and obj.start_datetime <= now <= obj.end_datetime:
            badge_html = '<span class="km-timing-badge km-timing-badge--live">Идёт сейчас</span>'
        elif local_start.date() == local_now.date():
            badge_html = '<span class="km-timing-badge km-timing-badge--today">Сегодня</span>'
        elif local_start.date() == (local_now + timezone.timedelta(days=1)).date():
            badge_html = '<span class="km-timing-badge km-timing-badge--upcoming">Завтра</span>'
        else:
            diff_days = (local_start.date() - local_now.date()).days
            if diff_days > 0:
                badge_html = f'<span class="km-timing-badge km-timing-badge--upcoming">через {diff_days} дн.</span>'
            else:
                badge_html = '<span class="km-timing-badge km-timing-badge--ended">Завершено</span>'

        from django.utils.safestring import mark_safe
        return format_html(
            '<div class="km-event-timing"><span class="km-event-timing__date">{}</span> <div class="km-event-timing__badge">{}</div></div>',
            dt_str,
            mark_safe(badge_html),
        )

    @admin.display(description=_("Окончание мероприятия"), ordering="end_datetime")
    def end_datetime_display(self, obj):
        if not obj.end_datetime:
            return "—"
        from django.utils import timezone
        from django.utils.formats import date_format

        local_end = timezone.localtime(obj.end_datetime)
        if obj.start_datetime:
            local_start = timezone.localtime(obj.start_datetime)
            if local_end.date() == local_start.date():
                return date_format(local_end, "H:i")
        return date_format(local_end, "d E Y, H:i")

    @admin.display(description="")
    def row_actions(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html, format_html_join
        edit_url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_change", args=[obj.pk])
        primary_action = render_primary_action(edit_url, _("Редактировать"))

        extra_actions = []
        if obj.is_public and hasattr(obj, "get_absolute_url"):
            extra_actions.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--ghost btn" href="{}" target="_blank" rel="noopener" title="{}"><i class="fas fa-external-link-alt" style="margin-right: 4px;"></i>{}</a>',
                    obj.get_absolute_url(),
                    _("Открыть на сайте"),
                    _("На сайте ↗"),
                )
            )

        menu_actions = []
        menu_html = render_action_menu(menu_actions)
        return format_html(
            '<div class="km-place-row-actions">{}{} {}</div>',
            primary_action,
            format_html_join("", "{}", ((a,) for a in extra_actions)),
            menu_html,
        )

    def save_model(self, request, obj, form, change):
        if "_save_draft" in request.POST:
            obj.status = Event.STATUS_DRAFT
            obj.rejection_reason = ""
        if "_unpublish_event" in request.POST:
            obj.status = Event.STATUS_DRAFT
        previous = Event.objects.filter(pk=obj.pk).values_list("status", flat=True).first() if change else None
        publish = "_publish_event" in request.POST or (obj.status == Event.STATUS_PUBLISHED and previous != Event.STATUS_PUBLISHED)
        if publish:
            obj.status = Event.STATUS_PENDING
        super().save_model(request, obj, form, change)
        if publish:
            from catalog.services.event_domain import publish_event
            approved = publish_event(actor=request.user, event_id=obj.pk, expected_updated_at=obj.updated_at)
            obj.__dict__.update(approved.__dict__)

    def response_add(self, request, obj, post_url_continue=None):
        if "_save_draft" in request.POST:
            return self._handle_event_save_draft_submit(
                request,
                obj,
                message=_("Черновик мероприятия сохранён. Можно продолжить позже."),
            )
        if "_publish_event" in request.POST:
            return self._handle_publish_event_submit(request, obj)
        if "_unpublish_event" in request.POST:
            return self._handle_unpublish_event_submit(request, obj)
        return super().response_add(request, obj, post_url_continue=post_url_continue)

    def response_change(self, request, obj):
        if "_save_draft" in request.POST:
            return self._handle_event_save_draft_submit(
                request,
                obj,
                message=_("Изменения сохранены как черновик. Можно вернуться к мероприятию позже."),
            )
        if "_publish_event" in request.POST:
            return self._handle_publish_event_submit(request, obj)
        if "_unpublish_event" in request.POST:
            return self._handle_unpublish_event_submit(request, obj)
        return super().response_change(request, obj)

    def _event_change_url(self, obj: Event) -> str:
        return reverse(
            f"admin:{self.opts.app_label}_{self.opts.model_name}_change",
            args=[obj.pk],
            current_app=self.admin_site.name,
        )

    def _handle_event_save_draft_submit(self, request, obj, *, message: str):
        self.message_user(request, message, level=messages.SUCCESS)
        return HttpResponseRedirect(self._event_change_url(obj))

    def _handle_publish_event_submit(self, request, obj: Event):
        from catalog.services.event_domain import publish_event
        try:
            publish_event(actor=request.user, event_id=obj.pk, expected_updated_at=obj.updated_at)
        except (ValidationError, PermissionDenied) as exc:
            self.message_user(request, str(exc), level=messages.WARNING)
            return HttpResponseRedirect(self._event_change_url(obj))
        self.message_user(
            request,
            _("Мероприятие опубликовано и теперь может показываться на сайте."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._event_change_url(obj))

    def _handle_unpublish_event_submit(self, request, obj: Event):
        obj.status = Event.STATUS_DRAFT
        obj.save(update_fields=["status", "updated_at"])
        self.message_user(
            request,
            _("Мероприятие снято с публикации и скрыто с сайта."),
            level=messages.SUCCESS,
        )
        return HttpResponseRedirect(self._event_change_url(obj))

    change_list_template = "admin/catalog/event/change_list.html"
    km_primary_filters = ("category", "status", "start_datetime")

    def _event_dashboard_counts(self):
        return Event.objects.aggregate(
            total=Count("id", filter=Q(deleted_at__isnull=True)),
            published=Count("id", filter=Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__gt=timezone.now()) | Q(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True, end_datetime__isnull=True)),
            pending=Count("id", filter=Q(status=Event.STATUS_PENDING, deleted_at__isnull=True)),
            expired=Count("id", filter=Q(deleted_at__isnull=True) & (Q(status=Event.STATUS_EXPIRED) | Q(end_datetime__lte=timezone.now()))),
            deleted=Count("id", filter=Q(deleted_at__isnull=False)),
        )

    def _event_dashboard_stats(self, request, counts: dict):
        return (
            {
                "label": _("Всего мероприятий"),
                "count": counts["total"],
                "url": "?",
                "tone": "info",
            },
            {
                "label": _("Опубликовано (Актуальные)"),
                "count": counts["published"],
                "url": "?status__exact=published",
                "tone": "good",
            },
            {
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": "?status__exact=pending",
                "tone": "warn",
            },
            {
                "label": _("Завершенные"),
                "count": counts["expired"],
                "url": "?status__exact=expired",
                "tone": "muted",
            },
            {
                "label": _("Удалённые"),
                "count": counts["deleted"],
                "url": "?deleted_at__isnull=False",
                "tone": "danger",
            },
        )

    def _event_quick_filters(self, request, counts: dict):
        current_status = request.GET.get("status__exact")
        current_deleted = request.GET.get("deleted_at__isnull")

        return [
            {
                "key": "all",
                "label": _("Все карточки"),
                "count": counts["total"],
                "url": "?",
                "active": not current_status and not current_deleted,
            },
            {
                "key": "published",
                "label": _("Опубликовано"),
                "count": counts["published"],
                "url": "?status__exact=published",
                "active": current_status == "published",
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": "?status__exact=pending",
                "active": current_status == "pending",
            },
            {
                "key": "deleted",
                "label": _("Удалённые"),
                "count": counts["deleted"],
                "url": "?deleted_at__isnull=False",
                "active": current_deleted == "False",
            },
        ]

    def _event_bulk_actions(self):
        return [
            {
                "name": "mark_published",
                "label": _("Опубликовать"),
                "tone": "good",
                "icon": "fas fa-bullhorn",
                "description": _("Опубликовать выбранные мероприятия."),
            },
            {
                "name": "mark_draft",
                "label": _("В черновик"),
                "tone": "muted",
                "icon": "far fa-file-alt",
                "description": _("Снять выбранные мероприятия с публикации и вернуть в черновики."),
            },
            {
                "name": "mark_pending",
                "label": _("На модерацию"),
                "tone": "warn",
                "icon": "fas fa-hourglass-half",
                "description": _("Отправить выбранные мероприятия на модерацию."),
            },
        ]

    @admin.action(description=_("Опубликовать выбранные мероприятия"))
    def mark_published(self, request, queryset):
        from catalog.services.event_domain import publish_event
        updated_count = 0
        for event in queryset.iterator(chunk_size=100):
            try:
                publish_event(actor=request.user, event_id=event.pk, expected_updated_at=event.updated_at)
            except (ValidationError, PermissionDenied):
                continue
            updated_count += 1
        self.message_user(
            request,
            ngettext(
                "Опубликовано %(count)d мероприятие.",
                "Опубликовано %(count)d мероприятия.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Вернуть мероприятия в черновик"))
    def mark_draft(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_DRAFT,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d мероприятие переведено в черновик.",
                "%(count)d мероприятия переведены в черновик.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отправить мероприятия на модерацию"))
    def mark_pending(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_PENDING,
            rejection_reason="",
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext(
                "%(count)d мероприятие отправлено на модерацию.",
                "%(count)d мероприятия отправлены на модерацию.",
                updated_count,
            )
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить выбранные мероприятия"))
    def mark_rejected(self, request, queryset):
        updated_count = queryset.update(
            status=Event.STATUS_REJECTED,
            rejection_reason=_("Мероприятие требует доработки перед публикацией."),
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("Отклонено %(count)d мероприятие.", "Отклонено %(count)d мероприятия.", updated_count)
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    def changelist_view(self, request, extra_context=None):
        counts = self._event_dashboard_counts()
        quick_filters = self._event_quick_filters(request, counts=counts)
        extra_context = {
            "event_dashboard_stats": self._event_dashboard_stats(request, counts=counts),
            "km_primary_quick_filters": quick_filters,
            "km_secondary_quick_filters": [],
            "event_bulk_actions": self._event_bulk_actions(),
            "km_search_label": _("Поиск мероприятий"),
            "km_search_placeholder": _("Название, адрес, телефон, организатор..."),
            "km_changelist_reset_url": "?",
            "km_suggestions_url": reverse("admin:catalog_event_search_suggestions"),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)
