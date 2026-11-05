"""PlaceAdmin: changelist columns, list displays, quick filters and dashboard."""

from django.conf import settings
import json
from django.contrib import admin
from django.db.models import Count, Exists, OuterRef, Q
from django.http import QueryDict
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

from catalog.models import (
    Place,
    PlaceChangeAudit,
    SiteSettings,
)
from catalog.services.content_quality import (
    place_quality_check,
    place_quality_error_labels as get_place_quality_error_labels,
    public_place_queryset,
)
from catalog.services.admin_place_presentation import with_saved_location, saved_presentation, saved_thumbnail_url
from catalog.services.place_identity_copy import identity_copy
from catalog.services.place_readiness import (
    evaluate_saved_place_readiness,
    evaluate_place_readiness,
    format_readiness_issues,
)
from .common import place_quality_error_labels
from .inlines import PlacePhotoInline


class PlaceAdminChangelistMixin:
    """Changelist columns, list displays, quick filters and dashboard."""

    def _is_trash_changelist(self, request) -> bool:
        return request.GET.get("deleted_state") == "deleted"

    def get_list_display(self, request):
        if self._is_trash_changelist(request):
            return self.trash_list_display
        return super().get_list_display(request)

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        if obj is None:
            return [inline for inline in inline_instances if isinstance(inline, PlacePhotoInline)]
        return inline_instances

    @staticmethod
    def _state_visual(obj: Place, score: int) -> tuple[str, str, str, str]:
        """Visual states from the redesign: icon + dot, never a red cross."""
        if obj.is_deleted:
            return "deleted", "delete", str(_("В удалённых")), "km-dot--deleted"
        if obj.status == Place.STATUS_PUBLISHED and obj.is_active:
            if score >= 100:
                return "published", "public", str(_("Опубликовано")), "km-dot--published"
            return "published-incomplete", "public", str(_("Опубликовано · неполная")), "km-dot--published"
        if obj.status == Place.STATUS_PENDING:
            return "pending", "hourglass_top", str(_("На модерации")), "km-dot--pending"
        if obj.status == Place.STATUS_REJECTED:
            return "blocked", "block", str(_("Нельзя опубликовать")), "km-dot--draft"
        if obj.has_coordinates:
            return "draft", "edit_note", str(_("Черновик")), "km-dot--draft"
        return "draft-incomplete", "visibility_off", str(_("Черновик")), "km-dot--draft"

    @admin.display(description=_("Место"), ordering="name")
    def col_place(self, obj):
        image_url = saved_thumbnail_url(obj)
        obj = saved_presentation(obj)
        name = (obj.name_i18n() if callable(getattr(obj, "name_i18n", None)) else (getattr(obj, "name_i18n", "") or obj.name_az or obj.name_ru or obj.name_en or obj.name)) or f"Place #{obj.pk}"
        cat_label = obj.category.name_i18n() if obj.category else obj.get_category_display()
        req = getattr(self, "_current_request", None)
        if obj.category:
            cat_url = self._build_changelist_query_string(req, category__id__exact=str(obj.category_id))
            cat_html = format_html(
                '<a href="{}" class="km-col-tag-link" title="{}">{}</a>',
                cat_url,
                _("Отфильтровать по категории: %(cat)s") % {"cat": cat_label},
                cat_label,
            )
        else:
            cat_html = format_html('<span class="km-col-tag-plain">{}</span>', cat_label)

        sub_html = ""
        if getattr(obj, "subcategory_id", None) and obj.subcategory:
            sub_name = obj.subcategory.name_i18n() if callable(getattr(obj.subcategory, "name_i18n", None)) else (getattr(obj.subcategory, "name_i18n", "") or obj.subcategory.name)
            if sub_name:
                sub_url = self._build_changelist_query_string(req, subcategory__id__exact=str(obj.subcategory_id))
                sub_html = format_html(
                    ' · <a href="{}" class="km-col-tag-link" title="{}">{}</a>',
                    sub_url,
                    _("Отфильтровать по подкатегории: %(sub)s") % {"sub": sub_name},
                    sub_name,
                )

        meta = format_html('ID {} · {}{}', obj.pk, cat_html, sub_html)

        preview = ""
        if image_url:
            try:
                preview = format_html(
                    '<img src="{}" alt="" class="km-col-thumb" loading="lazy" onerror="this.style.display=\'none\';if(this.nextElementSibling)this.nextElementSibling.style.display=\'block\';">'
                    '<span class="km-col-thumb km-col-thumb--pattern" style="display:none;" aria-hidden="true"></span>',
                    image_url,
                )
            except Exception:
                preview = ""
        if not preview:
            preview = mark_safe('<span class="km-col-thumb km-col-thumb--pattern" aria-hidden="true"></span>')

        home_on = bool(obj.is_home_recommended)
        home_title = _("На главной") if home_on else _("Не на главной")
        home_class = "is-on" if home_on else "is-off"

        map_on = bool(obj.has_coordinates)
        map_title = _("Точка на карте есть") if map_on else _("Нет координат")
        map_class = "is-on" if map_on else "is-off"
        map_icon = "place" if map_on else "location_off"

        marks_inline = format_html(
            '<span class="km-place-marks-inline" aria-label="{}">'
            '<span class="km-mark-wrap {}" title="{}"><svg class="km-i km-mark km-mark--home" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-home"></use></svg></span>'
            '<span class="km-mark-wrap {}" title="{}"><svg class="km-i km-mark km-mark--map" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-{}"></use></svg></span>'
            '</span>',
            _("Метки карточки"),
            home_class,
            home_title,
            map_class,
            map_title,
            map_icon,
        )
        working = getattr(obj, '_km_working_draft', None)
        if working:
            from django.template.loader import render_to_string
            marks_inline = format_html('{}{}', marks_inline, mark_safe(render_to_string('admin/catalog/place/private_draft_actions.html',
                {'draft': working, 'working_drafts_copy': getattr(obj, '_km_working_draft_copy', {})})))
        return format_html(
            '<div class="km-col-place">'
            '{}'
            '<div class="km-col-place-info">'
            '<a href="{}" class="km-col-place-name" title="{}">{}</a>'
            '<span class="km-col-place-meta">{}</span>'
            '{}'
            '</div>'
            '</div>',
            preview,
            self._place_change_url(obj),
            name,
            name,
            meta,
            marks_inline,
        )

    @admin.display(description=_("Локация"))
    def col_location(self, obj):
        obj = saved_presentation(obj)
        address = obj.address_i18n() if callable(getattr(obj, "address_i18n", None)) else (obj.address or "")
        address = (address or "").strip() or "—"
        req = getattr(self, "_current_request", None)
        if obj.has_coordinates:
            district_label = (obj.district_i18n() if callable(getattr(obj, "district_i18n", None)) else getattr(obj, "district", "")) or ""
            loc2_parts = []
            if district_label and getattr(obj, "district_id", None):
                district_url = self._build_changelist_query_string(req, district__id__exact=str(obj.district_id))
                loc2_parts.append(
                    format_html(
                        '<a href="{}" class="km-col-tag-link" title="{}">{}</a>',
                        district_url,
                        _("Отфильтровать по району: %(dist)s") % {"dist": district_label},
                        district_label,
                    )
                )
            elif district_label:
                loc2_parts.append(format_html('<span>{}</span>', district_label))

            if getattr(obj, "metro", None):
                metro_label = (obj.metro_i18n() if callable(getattr(obj, "metro_i18n", None)) else getattr(obj, "metro", "")) or ""
                if metro_label and getattr(obj, "metro_id", None):
                    metro_url = self._build_changelist_query_string(req, metro__id__exact=str(obj.metro_id))
                    loc2_parts.append(
                        format_html(
                            '<a href="{}" class="km-col-tag-link" title="{}">{}</a>',
                            metro_url,
                            _("Отфильтровать по метро: %(metro)s") % {"metro": metro_label},
                            metro_label,
                        )
                    )
                elif metro_label:
                    loc2_parts.append(format_html('<span>{}</span>', metro_label))

            if loc2_parts:
                loc2_html = format_html('<span class="km-col-loc-sub">{}</span>', mark_safe(" · ".join(loc2_parts)))
            else:
                loc2_html = ""
        else:
            without_coords_url = self._build_changelist_query_string(req, clear=("coordinates_status",), coordinates_status="no")
            loc2_html = format_html(
                '<a href="{}" class="km-col-loc-sub km-col-loc-sub--warn" title="{}">{}</a>',
                without_coords_url,
                _("Показать карточки без координат"),
                _("нет координат"),
            )

        return format_html(
            '<div class="km-col-location">'
            '<span class="km-col-loc-addr" title="{}">{}</span>'
            '{}'
            '</div>',
            address,
            address,
            loc2_html,
        )

    def _list_readiness(self, obj):
        result = getattr(obj, "_km_list_readiness", None)
        if result is None:
            result = (evaluate_place_readiness(obj)
                      if getattr(obj, "km_saved_candidate_allowed", None) is False
                      else evaluate_saved_place_readiness(obj))
            obj._km_list_readiness = result
        return result

    def _list_publication_blockers(self, obj):
        """Known source blockers, separate from saved form completeness.

        This is a read-only list preflight. The publication service still
        rechecks author, dependencies and source inside its transaction.
        """
        cached = getattr(obj, "_km_list_publication_blockers", None)
        if cached is not None:
            return cached
        blockers = []
        revision = (getattr(obj, "volunteer_revision", None)
                    if getattr(obj, "km_saved_candidate_allowed", False) else None)
        if self._list_readiness(obj).is_ready and revision is not None:
            if revision.status in {"draft", "rejected"} and not evaluate_place_readiness(obj).is_ready:
                blockers.append({
                    "label": _("Проверить рабочую версию"), "anchor": "verification",
                    "message": _("Поля рабочей версии заполнены, но основная карточка ещё не готова. Отправьте рабочую версию на проверку перед публикацией."),
                })
            elif revision.status == "pending":
                from catalog.services import publication
                live = publication.snapshot(obj, "place")
                conflict = (revision.schema_version != publication.SCHEMA_VERSION or
                            revision.dependencies != publication.dependencies(obj, "place") or
                            any(live.get(key) != revision.base_snapshot.get(key)
                                for key in revision.changed_fields))
                if conflict:
                    blockers.append({
                        "label": _("Конфликт рабочей версии"), "anchor": "verification",
                        "message": _("Исходные данные рабочей версии изменились. Откройте карточку и согласуйте версии перед публикацией."),
                    })
        obj._km_list_publication_blockers = tuple(blockers)
        return obj._km_list_publication_blockers

    def _list_is_publish_ready(self, obj):
        return self._list_readiness(obj).is_ready and not self._list_publication_blockers(obj)

    def _ready_place_ids(self, request):
        ready_pks = getattr(request, "_km_ready_pks", None)
        if ready_pks is None:
            # Filter/count the same authorized live or saved copy as each row.
            candidates = (
                self.get_queryset(request)
                .filter(deleted_at__isnull=True, km_in_public_catalog=False)
                .prefetch_related(None)
                .prefetch_related("gallery", "schedule_days__intervals", "pricing_plan_records")
            )
            ready_pks = [place.pk for place in candidates if self._list_is_publish_ready(place)]
            if request is not None:
                request._km_ready_pks = ready_pks
        return ready_pks

    def _list_can_publish(self, obj):
        # Permission belongs to this row's request, never ModelAdmin's shared
        # _current_request (another simultaneous request can replace it).
        return bool(getattr(obj, "km_list_publish_allowed", False)) and not obj.is_deleted

    def _list_publication_action(self, obj, readiness):
        if not self._list_can_publish(obj):
            return ""
        published = obj.status == Place.STATUS_PUBLISHED and obj.is_active
        blockers = self._list_publication_blockers(obj)
        if not published and (not readiness.is_ready or blockers):
            reason = "; ".join(str(item["message"]) for item in blockers) or format_readiness_issues(readiness)
            return format_html(
                '<a href="{}" class="km-publication-fix" title="{}">{}</a>',
                self._place_change_url(obj), reason, _("Исправить"))
        label = _("Снять с публикации") if published else _("Опубликовать")
        return format_html(
            '<button type="button" class="km-publication-action {}" data-publication-action="toggle_pub" '
            'data-place-id="{}" data-place-name="{}" data-status="{}" data-is-active="{}" '
            'data-toggle-publication-url="{}" aria-label="{} — {}">{}</button>',
            "km-publication-action--unpublish" if published else "km-publication-action--publish",
            obj.pk, saved_presentation(obj).name_i18n(), obj.status, int(obj.is_active),
            reverse("admin:catalog_place_toggle_publication", args=[obj.pk]),
            label, saved_presentation(obj).name_i18n(), label)

    @admin.display(description=_("Состояние"))
    def col_state(self, obj):
        # The row badge, its popover and the publish button must not argue:
        # every flag below is one of the twelve readiness items.
        readiness = self._list_readiness(obj)
        score = readiness.percentage
        completed = {item.code: item.is_complete for item in readiness.items}
        bar_color_class = "km-bar--warn" if score < 60 else "km-bar--good"

        state_key, state_icon, lifecycle_text, dot_class = self._state_visual(saved_presentation(obj), score)
        visibility = self._place_visibility_state(obj)
        if visibility["is_public"]:
            state_key, state_icon, status_text, dot_class = "published", "public", _("Опубликовано"), "km-dot--published"
            hint = _("Видно на сайте")
        elif obj.is_deleted:
            status_text, hint = _("В удалённых"), _("Не видно на сайте")
        elif obj.status == Place.STATUS_PUBLISHED and obj.is_active:
            state_key, state_icon, status_text, dot_class = "blocked", "visibility_off", _("Скрыто с сайта"), "km-dot--rejected"
            hint = _("Исправить")
        else:
            status_text = _("Не опубликовано")
            hint = (_("Проверить рабочую версию") if self._list_publication_blockers(obj)
                    else _("Готово к публикации") if readiness.is_ready else lifecycle_text)
        revision = getattr(obj, "volunteer_revision", None)
        revision_hint = ""
        if getattr(obj, "km_saved_candidate_allowed", False) and revision is not None:
            if revision.status == "pending":
                revision_hint = _("Правки на модерации") if visibility["is_public"] else _("На модерации")
            elif visibility["is_public"] and revision.status in {"draft", "rejected"}:
                revision_hint = _("Есть неопубликованные правки")
        details = format_html(
            '<span class="km-publication-hint" title="{}">{}</span>{}{}',
            visibility["hint"], hint,
            format_html('<span class="km-publication-revision">{}</span>', revision_hint) if revision_hint else "",
            self._list_publication_action(obj, readiness))

        name = (obj.name_i18n() if callable(getattr(obj, "name_i18n", None)) else getattr(obj, "name_i18n", "")) or obj.name_az or obj.name_ru or obj.name_en or obj.name or f"Place #{obj.pk}"

        # The popover lists exactly the twelve readiness items, with the same
        # labels and the same actionable messages the form shows. Nothing here
        # decides on its own what counts as done.
        checklist = json.dumps(
            [
                {
                    "code": item.code,
                    "label": str(item.label),
                    "done": bool(item.is_complete),
                    "message": str(item.issue.message) if item.issue else "",
                    "section": item.requirement.section,
                    "anchor": item.requirement.anchor,
                }
                for item in readiness.items
            ],
            ensure_ascii=False,
        )

        req = getattr(self, "_current_request", None)
        status_clear = ("deleted_state", "publication_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")
        if obj.is_deleted:
            status_url = self._build_changelist_query_string(req, clear=status_clear, deleted_state="deleted")
        else:
            status_url = self._build_changelist_query_string(req, clear=status_clear,
                publication_state="published" if visibility["is_public"] else "unpublished")

        status_top_html = format_html(
            '<a href="{}" class="km-col-state-link" title="{}">'
            '<span class="km-state-dot {}"></span>'
            '<svg class="km-i km-state-visibility" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-{}"></use></svg>'
            '<span class="km-state-label">{}</span>'
            '</a>',
            status_url,
            _("Отфильтровать по статусу: %(status)s") % {"status": status_text},
            dot_class,
            state_icon,
            status_text,
        )

        return format_html(
            '<div class="km-col-state km-col-state--{}" data-state="{}">'
            '<div class="km-col-state-top">'
            '{}'
            '</div>'
            '<span class="km-readiness-caption">{}</span>'
            '<div class="km-col-state-bottom">'
            '<span class="km-state-bar-wrap"><span class="km-state-bar {} km-state-bar--{}"></span></span>'
            '<button type="button" class="km-readiness-trigger" data-readiness-trigger '
            'data-place-id="{}" data-place-name="{}" data-score="{}" '
            'data-done="{}" data-total="{}" data-readiness="{}" '
            'data-edit-url="{}">{}%</button>'
            '</div>{}'
            '</div>',
            state_key,
            state_key,
            status_top_html,
            _("Готовность заполнения"),
            bar_color_class,
            score,
            obj.pk,
            name,
            score,
            readiness.completed_count,
            readiness.required_count,
            checklist,
            self._place_change_url(obj),
            score,
            details,
        )

    @admin.display(description=_("Метки"))
    def col_marks(self, obj):
        obj = saved_presentation(obj)
        home_on = bool(obj.is_home_recommended)
        home_title = _("На главной") if home_on else _("Не на главной")
        home_class = "is-on" if home_on else "is-off"

        map_on = bool(obj.has_coordinates)
        map_title = _("Точка на карте есть") if map_on else _("Нет координат")
        map_class = "is-on" if map_on else "is-off"
        map_icon = "place" if map_on else "location_off"

        has_rating = bool(obj.rating_avg)
        rating_val = f"{float(obj.rating_avg or 0):.1f}" if has_rating else "—"
        rating_class = "has-rating" if has_rating else "no-rating"
        reviews_count = int(obj.rating_count or 0)
        reviews_title = _("Отзывов: %(count)d") % {"count": reviews_count}
        rating_title = _("Рейтинг: %(rating)s") % {"rating": rating_val}

        return format_html(
            '<div class="km-col-marks">'
            '<div class="km-marks-flags">'
            '<span class="km-mark-wrap {}" title="{}"><svg class="km-i km-mark km-mark--home" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-home"></use></svg></span>'
            '<span class="km-mark-wrap {}" title="{}"><svg class="km-i km-mark km-mark--map" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-{}"></use></svg></span>'
            '</div>'
            '<div class="km-marks-metrics">'
            '<span class="km-mark-stat km-mark-stat--reviews" title="{}" aria-label="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-chat_bubble"></use></svg>'
            '<span class="km-mark-stat__val">{}</span>'
            '</span>'
            '<span class="km-mark-stat km-mark-stat--rating {}" title="{}" aria-label="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-star"></use></svg>'
            '<span class="km-mark-stat__val">{}</span>'
            '</span>'
            '</div>'
            '</div>',
            home_class,
            home_title,
            map_class,
            map_title,
            map_icon,
            reviews_title,
            reviews_title,
            reviews_count,
            rating_class,
            rating_title,
            rating_title,
            rating_val,
        )

    @admin.display(description=_("Обновлено / Создано"), ordering="updated_at")
    def col_updated(self, obj):
        req = getattr(self, "_current_request", None)
        current_sort = req.GET.get("sort") if req else None

        audit = self._latest_place_audit(obj)
        if audit:
            actor = self._user_label(audit.changed_by) or _("система")
            source = audit.get_source_display().lower()
            dt = timezone.localtime(audit.created_at)
        else:
            actor = self._user_label(obj.created_by) or _("админка")
            source = _("создано")
            dt = timezone.localtime(obj.updated_at)

        created_dt = timezone.localtime(obj.created_at)
        created_dt_str = created_dt.strftime("%d.%m.%Y")
        created_author = self._user_label(obj.created_by) or _("не указан")

        # Author filter link
        creator_id = obj.created_by_id
        if creator_id:
            author_url = self._build_changelist_query_string(req, created_by=str(creator_id))
            author_html = format_html(
                '<a href="{}" class="km-col-tag-link km-col-author-link" title="{}">{}</a> <span class="km-col-upd-source">· {}</span>',
                author_url,
                _("Показать карточки автора: %(name)s") % {"name": actor},
                actor,
                source,
            )
        else:
            author_html = format_html('<span class="km-col-upd-author" title="{}">{} · {}</span>', actor, actor, source)

        # Full tooltip
        tooltip = _("Создано: %(created)s (%(creator)s) · Обновлено: %(updated)s (%(updator)s)") % {
            "created": created_dt.strftime("%d.%m.%Y %H:%M"),
            "creator": created_author,
            "updated": dt.strftime("%d.%m.%Y %H:%M"),
            "updator": actor,
        }

        # If sorted by creation date, show created_at prominently!
        if current_sort in ("created_desc", "created_asc"):
            primary_time = created_dt.strftime("%d.%m %H:%M")
            sub_created = format_html(
                '<span class="km-col-upd-created" title="{}"><small>{}: {}</small></span>',
                _("Обновлено: %(dt)s") % {"dt": dt.strftime("%d.%m.%Y %H:%M")},
                _("Обновл."),
                dt.strftime("%d.%m.%Y"),
            )
        else:
            primary_time = dt.strftime("%d.%m %H:%M")
            sub_created = format_html(
                '<span class="km-col-upd-created" title="{}"><small>{}: {}</small></span>',
                _("Создано: %(dt)s (автор: %(author)s)") % {"dt": created_dt.strftime("%d.%m.%Y %H:%M"), "author": created_author},
                _("Создано"),
                created_dt_str,
            )

        return format_html(
            '<div class="km-col-updated" title="{}">'
            '<span class="km-col-upd-time">{}</span>'
            '{}'
            '{}'
            '</div>',
            tooltip,
            primary_time,
            author_html,
            sub_created,
        )


    def _place_view_url(self, obj):
        if obj.is_public:
            return obj.get_absolute_url()
        return reverse("admin:catalog_place_site_preview", args=[obj.pk], current_app=self.admin_site.name)

    def _place_view_label(self, obj, public_label):
        return public_label if obj.is_public else _("Предпросмотр")

    @admin.display(description=_("Действия"))
    def col_actions(self, obj):
        can_toggle = self._list_can_publish(obj) and (
            (obj.status == Place.STATUS_PUBLISHED and obj.is_active) or self._list_is_publish_ready(obj))
        reason = (format_readiness_issues(self._list_readiness(obj)) if self._list_can_publish(obj)
                  else str(_("Недостаточно прав для этого действия.")))
        blockers = self._list_publication_blockers(obj)
        if blockers:
            reason = "; ".join(str(item["message"]) for item in blockers)
        obj = saved_presentation(obj)
        edit_url = self._place_change_url(obj)
        view_url = self._place_view_url(obj)
        action_base_url = edit_url.rsplit("change/", 1)[0]
        name = (obj.name_i18n() if callable(getattr(obj, "name_i18n", None)) else getattr(obj, "name_i18n", "")) or obj.name_az or obj.name_ru or obj.name_en or obj.name or f"Place #{obj.pk}"

        return format_html(
            '<div class="km-col-actions">'
            '<a href="{}" class="km-action-icon-btn" title="{}"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-edit"></use></svg></a>'
            '<a href="{}" target="_blank" class="km-action-icon-btn" title="{}"><svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-visibility"></use></svg></a>'
            '<button type="button" class="km-action-icon-btn km-action-more-btn" data-more-actions-btn '
            'data-place-id="{}" data-place-name="{}" data-status="{}" data-is-active="{}" '
            'data-is-deleted="{}" data-has-coords="{}" data-is-home="{}" data-edit-url="{}" data-view-url="{}" '
            'data-can-toggle-publication="{}" data-publication-reason="{}" '
            'data-toggle-publication-url="{}toggle-publication/" data-quick-action-url="{}quick-action/" title="{}">'
            '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-more_horiz"></use></svg>'
            '</button>'
            '</div>',
            edit_url,
            _("Редактировать"),
            view_url,
            self._place_view_label(obj, _("Просмотр на сайте")),
            obj.pk,
            name,
            obj.status,
            1 if obj.is_active else 0,
            1 if obj.is_deleted else 0,
            1 if obj.has_coordinates else 0,
            1 if obj.is_home_recommended else 0,
            edit_url,
            view_url,
            1 if can_toggle else 0,
            reason,
            action_base_url,
            action_base_url,
            _("Ещё действия"),
        )

    def _build_place_card_data(self, obj, request=None):
        pres = saved_presentation(obj)
        name = (pres.name_i18n() if callable(getattr(pres, "name_i18n", None)) else (getattr(pres, "name_i18n", "") or pres.name_az or pres.name_ru or pres.name_en or pres.name)) or f"Place #{obj.pk}"
        readiness = self._list_readiness(obj)
        publication_blockers = self._list_publication_blockers(obj)
        is_publish_ready = readiness.is_ready and not publication_blockers
        score = readiness.percentage
        visibility = self._place_visibility_state(obj)
        can_pub = self._list_can_publish(obj)

        if visibility["is_public"]:
            status_label = _("Опубликовано")
            status_desc = _("Видно на сайте и на карте")
            status_tone = "good"
            state_key = "published"
        elif obj.is_deleted:
            status_label = _("В удалённых")
            status_desc = _("Скрыто в корзине")
            status_tone = "muted"
            state_key = "deleted"
        elif publication_blockers:
            status_label = _("Проверить рабочую версию")
            status_desc = publication_blockers[0]["message"]
            status_tone = "warn"
            state_key = "draft"
        elif is_publish_ready:
            status_label = _("Готово к публикации")
            status_desc = _("Все требования выполнены")
            status_tone = "ready"
            state_key = "ready"
        elif obj.status == Place.STATUS_PENDING:
            status_label = _("На модерации")
            status_desc = _("Ожидает проверки редактора")
            status_tone = "warn"
            state_key = "pending"
        else:
            status_label = _("Черновик")
            status_desc = _("Заполняются данные")
            status_tone = "draft"
            state_key = "draft"

        readiness_tone = ("warn" if publication_blockers else
                          "good" if score >= 80 else "warn" if score >= 50 else "danger")

        missing_items = []
        for item in readiness.items:
            if not item.is_complete:
                missing_items.append({
                    "code": item.code,
                    "label": str(item.label),
                    "anchor": item.requirement.anchor or "step-1",
                    "message": str(item.issue.message) if item.issue else "",
                })

        category_name = pres.category.name_i18n() if pres.category and callable(getattr(pres.category, "name_i18n", None)) else (pres.category.name if pres.category else "")
        subcategory_name = pres.subcategory.name_i18n() if pres.subcategory and callable(getattr(pres.subcategory, "name_i18n", None)) else (pres.subcategory.name if pres.subcategory else "")

        cat_url = self._build_changelist_query_string(request, category__id__exact=str(pres.category_id)) if pres.category else None
        sub_url = self._build_changelist_query_string(request, subcategory__id__exact=str(pres.subcategory_id)) if pres.subcategory else None

        address = (pres.address_i18n() if callable(getattr(pres, "address_i18n", None)) else pres.address) or ""
        district = (pres.district_i18n() if callable(getattr(pres, "district_i18n", None)) else getattr(pres, "district", "")) or ""
        metro = (pres.metro_i18n() if callable(getattr(pres, "metro_i18n", None)) else getattr(pres, "metro", "")) or ""

        rating_avg = f"{float(obj.rating_avg or 0):.1f}" if obj.rating_avg else None
        rating_count = int(obj.rating_count or 0)

        edit_url = self._place_change_url(obj)
        view_url = self._place_view_url(obj)
        action_base_url = edit_url.rsplit("change/", 1)[0]
        toggle_pub_url = reverse("admin:catalog_place_toggle_publication", args=[obj.pk])
        quick_action_url = f"{action_base_url}quick-action/"
        can_toggle = can_pub and ((obj.status == Place.STATUS_PUBLISHED and obj.is_active) or is_publish_ready)
        pub_reason = format_readiness_issues(readiness) if can_pub else str(_("Недостаточно прав для этого действия."))

        if publication_blockers:
            pub_reason = "; ".join(str(item["message"]) for item in publication_blockers)

        updated_str = obj.updated_at.strftime("%d.%m.%Y %H:%M") if obj.updated_at else ""

        return {
            "pk": obj.pk,
            "name": name,
            "thumbnail_url": saved_thumbnail_url(obj),
            "change_url": edit_url,
            "view_url": view_url,
            "toggle_pub_url": toggle_pub_url,
            "quick_action_url": quick_action_url,
            "category_name": category_name,
            "subcategory_name": subcategory_name,
            "category_url": cat_url,
            "subcategory_url": sub_url,
            "is_home_recommended": bool(obj.is_home_recommended),
            "has_coordinates": bool(pres.has_coordinates),
            "address": address,
            "district": district,
            "metro": metro,
            "rating_avg": rating_avg,
            "rating_count": rating_count,
            "status_label": status_label,
            "status_desc": status_desc,
            "status_tone": status_tone,
            "state_key": state_key,
            "readiness_score": score,
            "readiness_tone": readiness_tone,
            "is_ready": is_publish_ready,
            "publication_blockers": publication_blockers,
            "completed_count": readiness.completed_count,
            "required_count": readiness.required_count,
            "missing_items": missing_items,
            "missing_count": len(missing_items),
            "first_missing_anchor": (publication_blockers[0]["anchor"] if publication_blockers
                                     else missing_items[0]["anchor"] if missing_items else "step-1"),
            "is_public": visibility["is_public"],
            "is_deleted": obj.is_deleted,
            "status": obj.status,
            "is_active_num": 1 if obj.is_active else 0,
            "is_deleted_num": 1 if obj.is_deleted else 0,
            "has_coords_num": 1 if pres.has_coordinates else 0,
            "is_home_num": 1 if obj.is_home_recommended else 0,
            "can_toggle_num": 1 if can_toggle else 0,
            "can_publish": can_pub,
            "pub_reason": pub_reason,
            "updated_label": updated_str,
        }

    @admin.display(description=_("Название"))
    def display_name(self, obj):
        title = obj.name_az or obj.name_ru or obj.name_en or obj.name
        meta: list[str] = [f"ID {obj.pk}"]
        if obj.is_deleted:
            meta.append(str(_("В удаленных")))
            meta.append(str(_("Сейчас скрыта в разделе удалённых")))
        preview = ""
        image_field = obj.photo or obj.cover_photo
        if image_field and getattr(image_field, "name", ""):
            try:
                preview = format_html(
                    '<img src="{}" alt="" class="km-admin-thumb" loading="lazy">',
                    image_field.url,
                )
            except Exception:
                preview = ""
        if not preview:
            preview = mark_safe('<span class="km-admin-thumb km-admin-thumb--placeholder" aria-hidden="true">•</span>')
        return format_html(
            '<div class="km-admin-entry">'
            '{}'
            '<div class="km-admin-stack">'
            '<span class="km-admin-title">{}</span>'
            '{}'
            "</div>"
            "</div>",
            preview,
            title,
            format_html_join("", '<span class="km-admin-meta">{}</span>', ((item,) for item in meta)),
        )

    def _render_place_state_badge(self, *, label: str, tone: str = "muted"):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            tone,
            label,
        )

    @admin.display(description=_("Статус"))
    def lifecycle_status(self, obj):
        if obj.is_deleted:
            return self._render_place_state_badge(label=_("В удаленных"), tone="muted")
        visibility = self._place_visibility_state(obj)
        if obj.status == obj.STATUS_PUBLISHED and obj.is_active:
            return self._render_place_state_badge(label=visibility["label"], tone=visibility["tone"])
        return self._render_place_state_badge(label=_("Неактивно"), tone="warn")

    @admin.display(description=_("Статус"))
    def lifecycle_status_display(self, obj):
        return self.lifecycle_status(obj)

    @admin.display(description=_("Координаты"))
    def coordinates_status(self, obj):
        obj = saved_presentation(obj)
        return self._render_place_state_badge(
            label=_("Есть координаты") if obj.has_coordinates else _("Нужны координаты"),
            tone="good" if obj.has_coordinates else "warn",
        )

    @admin.display(description=_("Координаты"))
    def coordinates_status_display(self, obj):
        return self.coordinates_status(obj)

    @admin.display(description=_("На карте"))
    def map_ready_status(self, obj):
        return self._render_place_state_badge(
            label=_("Готово для карты") if obj.is_map_ready else _("Не готово для карты"),
            tone="good" if obj.is_map_ready else "muted",
        )

    @admin.display(description=_("На карте"))
    def map_ready_status_display(self, obj):
        return self.map_ready_status(obj)

    @admin.display(description=_("Качество"))
    def quality_status_display(self, obj):
        check = place_quality_check(obj)
        tone = "good" if check.is_ready else "warn"
        label = _("Готово к публикации") if check.is_ready else _("Нужна доработка")
        details = place_quality_error_labels(check.errors) if check.errors else _("Критичных замечаний нет")
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-badge km-admin-badge--{}">{} / 100</span><span class="km-admin-meta">{} · {}</span></div>',
            tone,
            check.score,
            label,
            details,
        )

    @admin.display(description=_("Проверено модератором"))
    def last_verified_at_display(self, obj):
        if not obj or not obj.last_verified_at:
            return _("Ещё не отмечено")
        return timezone.localtime(obj.last_verified_at).strftime("%d.%m.%Y %H:%M")

    @admin.display(description=_("Дата публикации"))
    def published_at_display(self, obj):
        if not obj or not obj.published_at:
            return _("Ещё не опубликовано")
        return timezone.localtime(obj.published_at).strftime("%d.%m.%Y %H:%M")

    def _user_label(self, user) -> str:
        if not user:
            return ""
        return user.get_full_name() or user.get_username() or user.email or str(user.pk)

    def _latest_place_audit(self, obj):
        audits = getattr(obj, "km_prefetched_change_audits", None)
        if audits is not None:
            return audits[0] if audits else None
        return obj.change_audits.select_related("changed_by").order_by("-created_at").first()

    def _creation_place_audit(self, obj):
        audits = getattr(obj, "km_prefetched_change_audits", None)
        if audits is not None:
            return next((audit for audit in reversed(audits) if audit.field_name == "created"), None)
        return (
            obj.change_audits.select_related("changed_by")
            .filter(field_name="created")
            .order_by("created_at", "pk")
            .first()
        )

    def _first_ownership_request(self, obj):
        requests = getattr(obj, "km_prefetched_ownership_requests", None)
        if requests is not None:
            return requests[0] if requests else None
        return obj.ownership_requests.select_related("applicant").order_by("created_at").first()

    @admin.display(description=_("Категория"))
    def category_summary(self, obj):
        category = obj.category
        label = category.name_i18n() if category else obj.get_category_display()
        icon = (getattr(category, "icon", "") or "").strip() if category else ""
        if icon:
            icon_src = icon if icon.startswith(("http://", "https://", "/")) else f"{settings.STATIC_URL}{icon}"
            icon_html = format_html('<img src="{}" alt="" class="km-admin-category-icon" loading="lazy">', icon_src)
        else:
            icon_html = mark_safe('<span class="km-admin-category-icon km-admin-category-icon--fallback" aria-hidden="true">#</span>')
        subcategory = obj.subcategory.name_i18n() if getattr(obj, "subcategory_id", None) and obj.subcategory else ""
        return format_html(
            '<div class="km-admin-category-cell">{}<div class="km-admin-stack"><span class="km-admin-title">{}</span>{}</div></div>',
            icon_html,
            label,
            format_html('<span class="km-admin-meta">{}</span>', subcategory) if subcategory else "",
        )

    @admin.display(description=_("Локация"))
    def location_summary(self, obj):
        address = (obj.address or "").strip()
        if address:
            return format_html(
                '<span class="km-admin-address" title="{}">{}</span>',
                address,
                address,
            )
        fallback = " / ".join(part for part in (obj.district, obj.metro) if part)
        if fallback:
            return format_html('<span class="km-admin-address km-admin-address--muted">{}</span>', fallback)
        return format_html(
            '<span class="km-admin-address km-admin-address--empty">{}</span>',
            _("Адрес не заполнен"),
        )

    @admin.display(description=_("Публикация"))
    def publication_status(self, obj):
        visibility = self._place_visibility_state(obj)
        badges = [
            self._render_place_state_badge(label=visibility["label"], tone=visibility["tone"]),
        ]

        if obj.status != obj.STATUS_PUBLISHED or not visibility["is_public"]:
            status_tone = {
                obj.STATUS_DRAFT: "muted",
                obj.STATUS_PENDING: "warn",
                obj.STATUS_PUBLISHED: "muted",
                obj.STATUS_REJECTED: "danger",
            }.get(obj.status, "muted")
            status_label = (
                _("Статус: %(status)s") % {"status": obj.get_status_display()}
                if obj.status == obj.STATUS_PUBLISHED and not visibility["is_public"]
                else obj.get_status_display()
            )
            badges.append(self._render_place_state_badge(label=status_label, tone=status_tone))

        meta_bits: list[str] = []
        if obj.is_temporary:
            meta_bits.append(str(_("Временное")))
        if obj.rejection_reason and obj.status == obj.STATUS_REJECTED:
            meta_bits.append(str(_("Есть причина отклонения")))

        badges_html = mark_safe(" ".join(badges))
        return format_html(
            '<div class="km-admin-status-line">{}</div>{}',
            badges_html,
            format_html(
                '<span class="km-admin-meta km-admin-status-note">{}</span>',
                " · ".join(meta_bits),
            ) if meta_bits else "",
        )

    @admin.display(description=_("Готовность"))
    def publication_readiness(self, obj):
        """Show the exact publication checklist result for unpublished places."""
        visibility = self._place_visibility_state(obj)
        if visibility["is_public"]:
            return self._render_place_state_badge(label=_("Опубликована"), tone="good")

        check = place_quality_check(obj)
        if check.is_ready:
            tone = "good"
            title = _("Карточка готова")
            hint = _("Можно отправлять на модерацию или публиковать.")
        elif "test_content" in check.errors:
            tone = "danger"
            title = _("Нужна доработка")
            hint = _("Удалите тестовые данные перед публикацией.")
        else:
            tone = "warn" if check.score >= 50 else "danger"
            title = _("Не хватает данных")
            hint = _("Заполните пункты ниже, чтобы карточка стала готова.")

        issue_labels = get_place_quality_error_labels(check.errors)
        issues_html = format_html_join(
            "",
            '<span class="km-admin-readiness__issue">{}</span>',
            ((label,) for label in issue_labels),
        )

        return format_html(
            '<div class="km-admin-readiness km-admin-readiness--{}" aria-label="{}: {}%">'
            '<div class="km-admin-readiness__top"><strong>{}</strong><b>{}%</b></div>'
            '<div class="km-admin-readiness__track" aria-hidden="true"><span style="width: {}%"></span></div>'
            '<span class="km-admin-readiness__hint">{}</span>'
            '<div class="km-admin-readiness__issues">{}</div>'
            '</div>',
            tone,
            title,
            check.score,
            title,
            check.score,
            check.score,
            hint,
            issues_html,
        )

    @admin.display(boolean=True, description=_("На главной"))
    def home_recommendation_status(self, obj):
        return obj.is_home_recommended

    @admin.display(description=_("Карта"))
    def map_status_summary(self, obj):
        visibility = self._place_visibility_state(obj)
        if visibility["is_public"] and obj.has_coordinates:
            label = _("Готово для карты")
            return format_html('<span class="km-admin-map-state km-admin-map-state--good" title="{}" aria-label="{}"><i class="fas fa-check"></i></span>', label, label)
        if not visibility["is_public"]:
            label = _("Скрыто с сайта")
        else:
            label = _("Нужны координаты") if not obj.has_coordinates else _("Не готово для карты")
        return format_html('<span class="km-admin-map-state km-admin-map-state--bad" title="{}" aria-label="{}"><i class="fas fa-times"></i></span>', label, label)

    @admin.display(description=_("Добавил"))
    def owner_display(self, obj):
        creation_audit = self._creation_place_audit(obj)
        creator = creation_audit.changed_by if creation_audit and creation_audit.changed_by_id else obj.created_by
        creator_label = self._user_label(creator)

        if creation_audit and creation_audit.source == PlaceChangeAudit.SOURCE_ADMIN:
            source_label = _("Сотрудник через админку")
        elif creation_audit and creation_audit.source == PlaceChangeAudit.SOURCE_OWNER_PANEL:
            source_label = _("Пользователь через сайт")
        elif creation_audit and creation_audit.source == PlaceChangeAudit.SOURCE_SYSTEM:
            source_label = _("Система")
        elif creator:
            source_label = _("Сотрудник через админку") if creator.is_staff else _("Пользователь через сайт")
        else:
            source_label = _("Источник не определён")

        if creator_label:
            return format_html(
                '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
                creator_label,
                source_label,
            )
        return format_html('<span class="km-admin-meta">{}</span>', source_label)

    @admin.display(description=_("Добавлено"), ordering="created_at")
    def created_summary(self, obj):
        created_at = timezone.localtime(obj.created_at)
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
            created_at.strftime("%d.%m.%Y"),
            created_at.strftime("%H:%M"),
        )

    @admin.display(description=_("Статистика"))
    def engagement_summary(self, obj):
        likes_value = int(obj.likes_count or 0)
        rating_value = f"{float(obj.rating_avg or 0):.1f}"
        reviews_value = int(obj.rating_count or 0)
        return format_html(
            '<div class="km-admin-stats" aria-label="{}">'
            '<span title="{}"><i class="far fa-comment-dots"></i>{}</span>'
            '<span title="{}"><i class="fas fa-star"></i>{}</span>'
            '<span title="{}"><i class="far fa-heart"></i>{}</span>'
            "</div>",
            _("Статистика карточки"),
            _("Отзывы"),
            reviews_value,
            _("Средний рейтинг"),
            rating_value,
            _("Лайки"),
            likes_value,
        )

    @admin.display(description=_("Обновлено"), ordering="updated_at")
    def updated_summary(self, obj):
        audit = self._latest_place_audit(obj)
        if audit:
            actor = self._user_label(audit.changed_by) or _("Система")
            source = audit.get_source_display()
            dt = timezone.localtime(audit.created_at)
            return format_html(
                '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{} · {}</span></div>',
                dt.strftime("%d.%m.%Y %H:%M"),
                actor,
                source,
            )
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
            timezone.localtime(obj.updated_at).strftime("%d.%m.%Y %H:%M"),
            _("без истории изменений"),
        )

    @admin.display(description=_("Удалено"))
    def deleted_at_display(self, obj):
        if not obj.deleted_at:
            return format_html('<span class="km-admin-meta">{}</span>', _("Нет данных"))
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span></div>',
            timezone.localtime(obj.deleted_at).strftime("%d.%m.%Y"),
            timezone.localtime(obj.deleted_at).strftime("%H:%M"),
        )

    @admin.display(description=_("Удалил"))
    def deleted_by_display(self, obj):
        if not obj.deleted_by:
            return format_html('<span class="km-admin-meta">{}</span>', _("Не указано"))
        label = obj.deleted_by.get_username() or obj.deleted_by.email or str(obj.deleted_by_id)
        return format_html('<span class="km-admin-title">{}</span>', label)

    def _build_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
        if request and hasattr(request, "GET"):
            params = request.GET.copy()
        else:
            params = QueryDict("", mutable=True)
        params.pop("p", None)
        for key in clear:
            params.pop(key, None)
        for key, value in updates.items():
            params.pop(key, None)
            if value not in (None, ""):
                params[key] = value
        encoded = params.urlencode()
        return f"?{encoded}" if encoded else "?"

    def _place_quick_filters(self, request, *, counts: dict[str, int] | None = None):
        counts = counts or self._place_dashboard_counts(request)
        status_keys = ("deleted_state", "publication_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")
        current_deleted = request.GET.get("deleted_state")
        current_publication = request.GET.get("publication_state")
        current_active = request.GET.get("is_active__exact")
        current_coordinates = request.GET.get("coordinates_status")
        current_map_ready = request.GET.get("map_ready_status")
        current_status = request.GET.get("status__exact")
        return (
            {
                "key": "all",
                "label": _("Все карточки"),
                "count": int(counts["quick_all"]),
                "url": self._build_changelist_query_string(request, clear=status_keys),
                "active": not any((current_deleted, current_publication, current_active, current_coordinates, current_map_ready, current_status)),
            },
            {
                "key": "published",
                "label": _("Опубликованы"),
                "count": int(counts["quick_published"]),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    publication_state="published",
                ),
                "active": current_publication == "published" and not current_coordinates and not current_map_ready,
            },
            {
                "key": "ready",
                "label": _("Готовы к публикации"),
                "count": int(counts.get("quick_ready", 0)),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    publication_state="ready",
                ),
                "active": current_deleted == "active" and current_publication == "ready" and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "unpublished",
                "label": _("Не опубликованы"),
                "count": int(counts["quick_unpublished"]),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    publication_state="unpublished",
                ),
                "active": current_deleted == "active" and current_publication == "unpublished" and not current_active and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "inactive",
                "label": _("Неактивные"),
                "count": int(counts["quick_inactive"]),
                "url": self._build_changelist_query_string(
                    request,
                    clear=status_keys,
                    deleted_state="active",
                    is_active__exact="0",
                ),
                "active": current_deleted == "active" and current_active == "0" and not current_publication and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "draft",
                "label": _("Черновики"),
                "count": int(counts["quick_draft"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_DRAFT),
                "active": current_status == Place.STATUS_DRAFT and not current_deleted and not current_publication and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": int(counts["quick_pending"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, publication_state="review"),
                "active": current_publication == "review" and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "rejected",
                "label": _("Отклонены"),
                "count": int(counts["quick_rejected"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, status__exact=Place.STATUS_REJECTED),
                "active": current_status == Place.STATUS_REJECTED and not current_deleted and not current_active and not current_coordinates and not current_map_ready,
            },
            {
                "key": "deleted",
                "label": _("В удалённых"),
                "count": int(counts["quick_deleted"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, deleted_state="deleted"),
                "active": current_deleted == "deleted" and not current_active and not current_coordinates and not current_map_ready and not current_status,
            },
            {
                "key": "without_coordinates",
                "label": _("Без координат"),
                "count": int(counts["quick_without_coordinates"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, coordinates_status="no"),
                "active": current_coordinates == "no" and not current_deleted and not current_active and not current_map_ready and not current_status,
            },
            {
                "key": "not_ready_for_map",
                "label": _("Не готовы для карты"),
                "count": int(counts["quick_not_ready_for_map"]),
                "url": self._build_changelist_query_string(request, clear=status_keys, map_ready_status="no"),
                "active": current_map_ready == "no" and not current_deleted and not current_active and not current_coordinates and not current_status,
            },
        )

    def _place_dashboard_counts(self, request=None) -> dict[str, int]:
        queryset = with_saved_location(Place.objects.all(), request, self).annotate(
            km_in_public_catalog=Exists(public_place_queryset(Place.objects.filter(pk=OuterRef("pk")))))
        review = Q(status=Place.STATUS_PENDING) | Q(km_saved_candidate_allowed=True, volunteer_revision__status="pending")
        counts = queryset.aggregate(
            quick_all=Count("pk", filter=Q(deleted_at__isnull=True)),
            quick_published=Count("pk", filter=Q(deleted_at__isnull=True, km_in_public_catalog=True)),
            quick_unpublished=Count("pk", filter=Q(deleted_at__isnull=True, km_in_public_catalog=False)),
            quick_inactive=Count("pk", filter=Q(deleted_at__isnull=True, is_active=False)),
            quick_draft=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_DRAFT)),
            quick_pending=Count("pk", filter=Q(deleted_at__isnull=True) & review),
            quick_rejected=Count("pk", filter=Q(deleted_at__isnull=True, status=Place.STATUS_REJECTED)),
            quick_deleted=Count("pk", filter=Q(deleted_at__isnull=False)),
            quick_without_coordinates=Count("pk", filter=Q(deleted_at__isnull=True, km_saved_has_coordinates=False)),
            quick_not_ready_for_map=Count(
                "pk",
                filter=Q(deleted_at__isnull=True) & (~Q(is_active=True, status=Place.STATUS_PUBLISHED) | Q(lat__isnull=True) | Q(lng__isnull=True)),
            ),
            stat_total=Count("pk", filter=Q(deleted_at__isnull=True)),
            stat_published=Count("pk", filter=Q(deleted_at__isnull=True, km_in_public_catalog=True)),
            stat_pending=Count("pk", filter=Q(deleted_at__isnull=True) & review),
            stat_inactive=Count("pk", filter=Q(deleted_at__isnull=True, km_in_public_catalog=False)),
            stat_without_coordinates=Count(
                "pk",
                filter=Q(deleted_at__isnull=True, km_saved_has_coordinates=False),
            ),
        )
        ready_pks = self._ready_place_ids(request)
        counts_dict = {key: int(value or 0) for key, value in counts.items()}
        counts_dict["quick_ready"] = len(ready_pks)
        counts_dict["stat_ready"] = len(ready_pks)
        return counts_dict

    def _place_dashboard_stats(self, request, *, counts: dict[str, int] | None = None):
        counts = counts or self._place_dashboard_counts(request)
        current_deleted = request.GET.get("deleted_state") if request else None
        current_publication = request.GET.get("publication_state") if request else None
        current_active = request.GET.get("is_active__exact") if request else None
        current_coordinates = request.GET.get("coordinates_status") if request else None
        current_status = request.GET.get("status__exact") if request else None

        is_all_active = (not current_publication and not current_coordinates and not current_status and (not current_deleted or current_deleted == "active") and not current_active)
        is_published_active = (current_publication == "published" and (not current_deleted or current_deleted == "active"))
        is_ready_active = (current_publication == "ready" and (not current_deleted or current_deleted == "active"))
        is_pending_active = (current_publication == "review")
        is_unpublished_active = (current_publication == "unpublished" and (not current_deleted or current_deleted == "active"))
        is_no_coords_active = (current_coordinates == "no")

        return (
            {
                "label": _("Всего"),
                "count": counts["stat_total"],
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact")),
                "tone": "info",
                "is_active": is_all_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
            },
            {
                "label": _("Опубликовано"),
                "count": counts["stat_published"],
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", publication_state="published"),
                "tone": "good",
                "is_active": is_published_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            },
            {
                "label": _("Готовы к публикации"),
                "count": counts.get("stat_ready", 0),
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", publication_state="ready"),
                "tone": "ready",
                "is_active": is_ready_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
            },
            {
                "label": _("На модерации"),
                "count": counts["stat_pending"],
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), publication_state="review"),
                "tone": "warn",
                "is_active": is_pending_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
            },
            {
                "label": _("Не опубликованы"),
                "count": counts["stat_inactive"],
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), deleted_state="active", publication_state="unpublished"),
                "tone": "muted",
                "is_active": is_unpublished_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"/></svg>',
            },
            {
                "label": _("Без координат"),
                "count": counts["stat_without_coordinates"],
                "url": self._build_changelist_query_string(request, clear=("publication_state", "deleted_state", "is_active__exact", "coordinates_status", "map_ready_status", "status__exact"), coordinates_status="no"),
                "tone": "warn",
                "is_active": is_no_coords_active,
                "icon": '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>',
            },
        )

    def _place_bulk_actions(self):
        return (
            {
                "name": "mark_published",
                "label": _("Опубликовать"),
                "tone": "good",
                "icon": "fas fa-bullhorn",
                "description": _("Опубликовать выбранные карточки с проверкой качества."),
            },
            {
                "name": "mark_inactive",
                "label": _("Снять с публикации"),
                "tone": "muted",
                "icon": "fas fa-eye-slash",
                "description": _("Оставить карточки в базе, но скрыть их с сайта."),
            },
            {
                "name": "mark_draft",
                "label": _("Вернуть в черновик"),
                "tone": "muted",
                "icon": "far fa-file-alt",
                "description": _("Снять выбранные карточки с сайта и перевести в черновики."),
            },
            {
                "name": "mark_pending",
                "label": _("На модерацию"),
                "tone": "warn",
                "icon": "fas fa-hourglass-half",
                "description": _("Отправить выбранные карточки на повторную модерацию."),
            },
            {
                "name": "refresh_coordinates",
                "label": _("Обновить координаты"),
                "tone": "info",
                "icon": "fas fa-location-arrow",
                "description": _("Повторно рассчитать координаты по адресу."),
            },
            {
                "name": "restore_selected",
                "label": _("Восстановить"),
                "tone": "good",
                "icon": "fas fa-undo",
                "confirm": _("Вы собираетесь восстановить {count} выбранных карточек из удалённых.\n\nПосле восстановления карточки останутся неактивными, их можно будет отдельно опубликовать.\n\nПродолжить?"),
                "description": _("Вернуть карточки из удалённых в базовый список."),
            },
            {
                "name": "move_selected_to_deleted",
                "label": _("В удалённые"),
                "tone": "danger",
                "icon": "far fa-trash-alt",
                "confirm": _("Вы собираетесь переместить в удалённые {count} выбранных карточек.\n\nКарточки исчезнут с сайта, но останутся в базе и их можно будет восстановить.\n\nПродолжить?"),
                "description": _("Безопасное мягкое удаление с возможностью восстановления."),
            },
        )

    def _place_trash_bulk_actions(self):
        return (
            {
                "name": "restore_selected",
                "label": _("Восстановить"),
                "tone": "good",
                "icon": "fas fa-undo",
                "confirm": _("Вы собираетесь восстановить {count} выбранных карточек из удалённых.\n\nПосле восстановления карточки останутся неактивными, их можно будет отдельно опубликовать.\n\nПродолжить?"),
                "description": _("Вернуть карточки из удалённых в базовый список."),
            },
        )

    def changelist_view(self, request, extra_context=None):
        from catalog.services.place_editor_drafts import working_drafts_context
        original_params = request.GET
        draft_context = working_drafts_context(user=request.user, params=original_params)
        request.GET = original_params.copy()
        request.GET.pop('draft_page', None)
        try:
            response = self._place_changelist_with_drafts(request, {**draft_context, **(extra_context or {})})
            context = getattr(response, 'context_data', None)
            if context and context.get('cl'):
                is_trash = self._is_trash_changelist(request)
                context['cl'].can_connect_organization = not is_trash and 'connect_to_organization' in self.get_actions(request)
                for place in context['cl'].result_list:
                    place._km_working_draft = draft_context['working_drafts_by_target'].get(place.pk)
                    place._km_working_draft_copy = draft_context['working_drafts_copy']
                context['cl'].place_cards = [self._build_place_card_data(p, request) for p in context['cl'].result_list]
            return response
        finally:
            request.GET = original_params

    def _place_changelist_with_drafts(self, request, extra_context=None):
        self._current_request = request
        dashboard_counts = self._place_dashboard_counts(request)
        quick_filters = self._place_quick_filters(request, counts=dashboard_counts)
        is_trash = self._is_trash_changelist(request)
        primary_filter_order = ["all", "published", "ready", "unpublished", "pending", "without_coordinates", "deleted"]
        if is_trash:
            primary_filter_order = ["all", "deleted"]

        quick_filter_map = {item.get("key"): item for item in quick_filters}
        primary_quick_filters = [quick_filter_map[key] for key in primary_filter_order if key in quick_filter_map]
        secondary_quick_filters = [item for item in quick_filters if item.get("key") not in primary_filter_order]

        sort_val = request.GET.get("sort", "updated_desc")
        sort_labels = {
            "created_desc": _("Создано (новые)"),
            "created_asc": _("Создано (старые)"),
            "updated_desc": _("Обновлено (новые)"),
            "updated_asc": _("Обновлено (старые)"),
            "name_asc": _("По названию (А → Я)"),
            "name_desc": _("По названию (Я → А)"),
        }
        km_current_sort = sort_val if sort_val in sort_labels else "updated_desc"
        km_current_sort_label = sort_labels[km_current_sort]

        extra_context = {
            "place_dashboard_stats": self._place_dashboard_stats(request, counts=dashboard_counts),
            "km_primary_quick_filters": primary_quick_filters,
            "km_secondary_quick_filters": secondary_quick_filters,
            "km_current_sort": km_current_sort,
            "km_current_sort_label": km_current_sort_label,
            "km_total_places_count": dashboard_counts.get("quick_all", 0),
            "km_total_trash_count": dashboard_counts.get("quick_deleted", 0),
            "place_bulk_actions": self._place_trash_bulk_actions() if is_trash else self._place_bulk_actions(),
            "km_can_connect_organization": not is_trash and 'connect_to_organization' in self.get_actions(request),
            "km_is_trash_changelist": is_trash,
            "km_changelist_reset_url": "?deleted_state=deleted" if is_trash else "?",
            "km_identity_copy": identity_copy(),
            "km_identity_registry_url": reverse("admin:catalog_place_identity_registry"),
            "km_place_quality_report_url": (
                reverse(
                    f"admin:{self.opts.app_label}_{self.opts.model_name}_quality_report",
                    current_app=self.admin_site.name,
                )
                if not is_trash and self.has_view_permission(request)
                else ""
            ),
            "home_recommendation_editor": (
                {
                    "cards": [
                        self._serialize_home_recommendation(
                            place,
                            language_code=getattr(request, "LANGUAGE_CODE", None),
                        )
                        for place in self._home_recommendation_queryset()
                        .filter(is_home_recommended=True)
                        .order_by("home_recommended_order", "-updated_at")[
                            : self._home_recommendations_limit(
                                SiteSettings.get_solo().home_recommendations_limit
                            )
                        ]
                    ],
                    "save_url": reverse("admin:catalog_place_home_recommendations_save"),
                    "candidates_url": reverse("admin:catalog_place_home_recommendation_candidates"),
                    "max_items": self._home_recommendations_limit(
                        SiteSettings.get_solo().home_recommendations_limit
                    ),
                }
                if not is_trash and self.has_change_permission(request)
                else None
            ),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)
