from functools import partial, update_wrapper

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import display_for_field
from django.db import models
from django.db.models import Count, Q
from django.utils.html import format_html, format_html_join, mark_safe
from .ui_utils import render_action_menu, render_row_actions_container
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.urls import reverse
from .queue_sorting import QueueSortingAdminMixin, QueueSortParameter
from .moderation_actor import ModerationActorAdminMixin
from catalog.forms_specialist_locations import BasePracticeLocationFormSet

from catalog.models import (
    Region,
    District,
    MetroStation,
    SpecialistSpecialization,
    Specialist,
    SpecialistPracticeLocation,
    SpecialistDocument,
    SpecialistReview,
    Place,
)

class SpecialistAdminForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = "__all__"
        widgets = {"specializations": forms.CheckboxSelectMultiple()}

    def clean(self):
        data = super().clean()
        if self.instance.pk:
            # Admin changeform POST is already atomic. Lock the parent before
            # writing profile/inlines; document decisions advance this epoch too.
            locked=Specialist.objects.select_for_update().get(pk=self.instance.pk)
            if self.data.get('expected_updated_at','')!=locked.updated_at.isoformat():
                raise forms.ValidationError(_('Запись изменилась. Обновите страницу.'),code='stale_version')
        # When this role has no location inline, do not accept an empty offline
        # profile or disclose row metadata. Editable rows are checked by formset.
        if data.get('consultation_format') in (Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH) and 'practice_locations-TOTAL_FORMS' not in self.data:
            if not self.instance.pk or not self.instance.practice_locations.filter(is_active=True,region__isnull=False).exclude(Q(place__isnull=True,address='')).exists():
                raise forms.ValidationError(_('Для очного формата работы (или онлайн и очно) необходимо указать хотя бы одно активное место приема.'))
        return data



class RegionContentPresenceFilter(admin.SimpleListFilter):
    title = _("Наличие объектов")
    parameter_name = "content_status"

    def lookups(self, request, model_admin):
        return (
            ("with_objects", _("С объектами (места/события)")),
            ("with_districts", _("С районами города")),
            ("empty", _("Без объектов")),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if not val:
            return queryset

        dist_to_reg = dict(District.objects.values_list("key", "region_id"))
        place_districts = set(Place.objects.exclude(district="").values_list("district", flat=True).distinct())
        regions_with_objects = set()
        for d in place_districts:
            r = dist_to_reg.get(d, d)
            regions_with_objects.add(r)

        spec_regions = set(SpecialistPracticeLocation.objects.exclude(region__isnull=True).values_list("region_id", flat=True).distinct())
        regions_with_objects.update(spec_regions)

        regions_with_districts = set(District.objects.values_list("region_id", flat=True).distinct())

        if val == "with_objects":
            return queryset.filter(key__in=regions_with_objects)
        if val == "with_districts":
            return queryset.filter(key__in=regions_with_districts)
        if val == "empty":
            return queryset.exclude(key__in=regions_with_objects)
        return queryset


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    fields = ("key", "name_ru", "name_az", "name_en")
    verbose_name = _("Район")
    verbose_name_plural = _("Районы региона")
    show_change_link = True


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/region/change_list.html"
    change_form_template = "admin/catalog/region/change_form.html"
    inlines = [DistrictInline]
    list_display = (
        "region_title",
        "localization_summary",
        "districts_badge",
        "places_badge",
        "events_badge",
        "specialists_badge",
        "actions_cell",
    )
    list_display_links = ("region_title",)
    search_fields = ("key", "name_ru", "name_az", "name_en")
    list_filter = (RegionContentPresenceFilter,)
    list_per_page = 25
    ordering = ("name_ru",)

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ("key",)
        return ()

    def get_list_display(self, request):
        metrics = self._get_metrics(request)
        metric_columns = {"districts_badge", "places_badge", "events_badge", "specialists_badge"}
        columns = []
        for column in super().get_list_display(request):
            if column in metric_columns:
                method = getattr(self, column)
                columns.append(update_wrapper(partial(method, metrics=metrics), method))
            else:
                columns.append(column)
        return columns

    def _get_metrics(self, request=None):
        # ModelAdmin lives for the whole worker lifetime; only cache per request.
        if request is not None and hasattr(request, "_kidsmap_region_metrics"):
            return request._kidsmap_region_metrics
        dist_to_reg = dict(District.objects.values_list("key", "region_id"))
        reg_keys = set(Region.objects.values_list("key", flat=True))

        place_counts = {}
        for item in Place.objects.filter(is_temporary=False).exclude(district="").values("district").annotate(c=Count("id")):
            d = item["district"]
            r = dist_to_reg.get(d, d)
            if r in reg_keys:
                place_counts[r] = place_counts.get(r, 0) + item["c"]

        event_counts = {}
        for item in Place.objects.filter(is_temporary=True).exclude(district="").values("district").annotate(c=Count("id")):
            d = item["district"]
            r = dist_to_reg.get(d, d)
            if r in reg_keys:
                event_counts[r] = event_counts.get(r, 0) + item["c"]

        spec_counts = dict(
            SpecialistPracticeLocation.objects.exclude(region__isnull=True)
            .values_list("region_id")
            .annotate(c=Count("specialist", distinct=True))
        )

        district_counts = dict(
            District.objects.values_list("region_id")
            .annotate(c=Count("key"))
        )

        metrics = {
            "districts": district_counts,
            "places": place_counts,
            "events": event_counts,
            "specialists": spec_counts,
        }
        if request is not None:
            request._kidsmap_region_metrics = metrics
        return metrics

    @admin.display(description=_("Регион / Город"), ordering="name_ru")
    def region_title(self, obj):
        return format_html(
            '<div class="km-region-title-cell">'
            '  <strong>{}</strong>'
            '  <div><span class="km-region-code-badge">{}</span></div>'
            '</div>',
            obj.name_ru,
            obj.key,
        )

    @admin.display(description=_("Локализация (AZ / EN)"))
    def localization_summary(self, obj):
        az = obj.name_az or "—"
        en = obj.name_en or "—"
        return format_html(
            '<div class="km-region-title-cell">'
            '  <div class="km-lang-row"><span class="km-lang-pill">AZ</span> {}</div>'
            '  <div class="km-lang-row"><span class="km-lang-pill km-lang-pill--en">EN</span> {}</div>'
            '</div>',
            az,
            en,
        )

    @admin.display(description=_("Районы"))
    def districts_badge(self, obj, *, metrics=None):
        metrics = metrics if metrics is not None else self._get_metrics()
        count = metrics["districts"].get(obj.key, 0)
        if count > 0:
            url = reverse("admin:catalog_district_changelist") + f"?region__key__exact={obj.key}"
            return format_html(
                '<a href="{}" class="km-admin-badge km-admin-badge--info" title="{}">'
                '  <i class="fas fa-layer-group"></i> {} {}'
                '</a>',
                url,
                _("Открыть список районов"),
                count,
                _("р-н") if count > 1 else _("р-н"),
            )
        return mark_safe('<span class="km-admin-meta text-muted">—</span>')

    @admin.display(description=_("Места"))
    def places_badge(self, obj, *, metrics=None):
        metrics = metrics if metrics is not None else self._get_metrics()
        count = metrics["places"].get(obj.key, 0)
        if count > 0:
            url = reverse("admin:catalog_place_changelist") + f"?q={obj.key}"
            return format_html(
                '<a href="{}" class="km-admin-badge km-admin-badge--good" title="{}">'
                '  <i class="fas fa-map-marker-alt"></i> {} {}'
                '</a>',
                url,
                _("Открыть места в каталоге"),
                count,
                _("мест") if count != 1 else _("место"),
            )
        return mark_safe('<span class="km-admin-meta text-muted">0</span>')

    @admin.display(description=_("События"))
    def events_badge(self, obj, *, metrics=None):
        metrics = metrics if metrics is not None else self._get_metrics()
        count = metrics["events"].get(obj.key, 0)
        if count > 0:
            url = reverse("admin:catalog_event_changelist") + f"?q={obj.key}"
            return format_html(
                '<a href="{}" class="km-admin-badge km-admin-badge--warn" title="{}">'
                '  <i class="fas fa-calendar-alt"></i> {}'
                '</a>',
                url,
                _("Открыть события региона"),
                count,
            )
        return mark_safe('<span class="km-admin-meta text-muted">0</span>')

    @admin.display(description=_("Специалисты"))
    def specialists_badge(self, obj, *, metrics=None):
        metrics = metrics if metrics is not None else self._get_metrics()
        count = metrics["specialists"].get(obj.key, 0)
        if count > 0:
            url = reverse("admin:catalog_specialist_changelist") + f"?locations__region__key={obj.key}"
            return format_html(
                '<a href="{}" class="km-admin-badge km-admin-badge--purple" title="{}">'
                '  <i class="fas fa-user-md"></i> {}'
                '</a>',
                url,
                _("Открыть специалистов"),
                count,
            )
        return mark_safe('<span class="km-admin-meta text-muted">0</span>')

    @admin.display(description=_("Действия"))
    def actions_cell(self, obj):
        edit_url = reverse("admin:catalog_region_change", args=[obj.key])
        add_district_url = reverse("admin:catalog_district_add") + f"?region={obj.key}"
        return format_html(
            '<div class="km-admin-actions-cell">'
            '  <a href="{}" class="km-action-btn km-action-btn--primary" title="{}">'
            '    <i class="fas fa-pen"></i> {}'
            '  </a>'
            '  <a href="{}" class="km-action-btn km-action-btn--secondary" title="{}">'
            '    <i class="fas fa-plus"></i> {}'
            '  </a>'
            '</div>',
            edit_url,
            _("Редактировать регион"),
            _("Изменить"),
            add_district_url,
            _("Добавить район"),
            _("Район"),
        )

    def _region_bulk_actions(self):
        return (
            {
                "name": "delete_selected",
                "label": _("Удалить"),
                "tone": "danger",
                "icon": "fas fa-trash-alt",
                "confirm": _("Вы собираетесь удалить {count} выбранных регионов.\n\nПродолжить?"),
                "description": _("Удаление выбранных регионов."),
            },
        )

    def changelist_view(self, request, extra_context=None):
        metrics = self._get_metrics(request)
        total_regions = Region.objects.count()

        regions_with_objects = set(metrics["places"].keys()) | set(metrics["events"].keys()) | set(metrics["specialists"].keys())
        regions_with_districts = set(metrics["districts"].keys())

        total_places = sum(metrics["places"].values())
        total_events = sum(metrics["events"].values())
        total_districts = sum(metrics["districts"].values())

        current_status = request.GET.get("content_status", "")

        region_dashboard_stats = [
            {"label": _("Всего регионов"), "count": total_regions, "url": "?", "tone": "info"},
            {"label": _("С объектами"), "count": len(regions_with_objects), "url": "?content_status=with_objects", "tone": "good"},
            {"label": _("Мест в каталоге"), "count": total_places, "url": reverse("admin:catalog_place_changelist"), "tone": "good"},
            {"label": _("Событий"), "count": total_events, "url": reverse("admin:catalog_event_changelist"), "tone": "warn"},
            {"label": _("Районов городов"), "count": total_districts, "url": reverse("admin:catalog_district_changelist"), "tone": "muted"},
        ]

        quick_filters = [
            {"key": "all", "label": _("Все регионы"), "count": total_regions, "url": "?", "active": not current_status},
            {"key": "with_objects", "label": _("С объектами"), "count": len(regions_with_objects), "url": "?content_status=with_objects", "active": current_status == "with_objects"},
            {"key": "with_districts", "label": _("С районами"), "count": len(regions_with_districts), "url": "?content_status=with_districts", "active": current_status == "with_districts"},
            {"key": "empty", "label": _("Без объектов"), "count": total_regions - len(regions_with_objects), "url": "?content_status=empty", "active": current_status == "empty"},
        ]

        extra_context = {
            "region_dashboard_stats": region_dashboard_stats,
            "km_primary_quick_filters": quick_filters,
            "region_bulk_actions": self._region_bulk_actions(),
            "km_search_placeholder": _("Поиск по названию RU/AZ/EN или коду региона..."),
            "km_disable_search_suggestions": True,
            "km_changelist_reset_url": "?",
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def get_search_results(self, request, queryset, search_term):
        filtered_queryset = queryset
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if search_term:
            term = search_term.strip()
            q_extras = (
                Q(key__icontains=term)
                | Q(name_ru__icontains=term)
                | Q(name_ru__icontains=term.lower())
                | Q(name_ru__icontains=term.capitalize())
                | Q(name_ru__icontains=term.upper())
                | Q(name_az__icontains=term)
                | Q(name_az__icontains=term.lower())
                | Q(name_az__icontains=term.capitalize())
                | Q(name_az__icontains=term.upper())
                | Q(name_en__icontains=term)
            )
            queryset = filtered_queryset.filter(q_extras)
        return queryset, use_distinct

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        if obj:
            metrics = self._get_metrics(request)
            districts_count = metrics["districts"].get(obj.key, 0)
            places_count = metrics["places"].get(obj.key, 0)
            events_count = metrics["events"].get(obj.key, 0)
            specialists_count = metrics["specialists"].get(obj.key, 0)
            context["km_region_summary"] = {
                "key": obj.key,
                "name_ru": obj.name_ru,
                "name_az": obj.name_az,
                "name_en": obj.name_en,
                "districts_count": districts_count,
                "places_count": places_count,
                "events_count": events_count,
                "specialists_count": specialists_count,
                "places_url": reverse("admin:catalog_place_changelist") + f"?q={obj.key}",
                "events_url": reverse("admin:catalog_event_changelist") + f"?q={obj.key}",
                "districts_url": reverse("admin:catalog_district_changelist") + f"?region__key__exact={obj.key}",
            }
        return super().render_change_form(request, context, add, change, form_url, obj)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("key", "region", "name_ru", "name_az", "name_en")
    list_filter = ("region",)
    search_fields = ("key", "name_ru", "name_az", "name_en")
    list_select_related = ("region",)
    ordering = ("region__name_ru", "name_ru")


@admin.register(MetroStation)
class MetroStationAdmin(admin.ModelAdmin):
    list_display = ("key", "name_ru", "name_az", "name_en")
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(SpecialistSpecialization)
class SpecialistSpecializationAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "name_az", "name_en", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("code", "name_ru", "name_az", "name_en")


class SpecialistPracticeLocationInline(admin.StackedInline):
    formset = BasePracticeLocationFormSet
    model = SpecialistPracticeLocation
    extra = 1
    verbose_name = _("Место приёма")
    verbose_name_plural = _("8. Места работы и приёма")
    fields = ("place", "address", "region", "district", "metro", "lat", "lng", "schedule", "price_per_session", "phone", "is_primary", "is_active")
    autocomplete_fields = ("place",)


class SpecialistDocumentInline(admin.TabularInline):
    model = SpecialistDocument
    extra = 0
    verbose_name = _("Документ")
    verbose_name_plural = _("10. Подтверждение квалификации")
    fields = ("document_type", "name", "download_link", "status", "is_published", "rejection_reason")
    readonly_fields = ("document_type", "name", "download_link", "is_published")

    def has_view_permission(self, request, obj=None):
        from catalog.services.specialist_documents import can_review_documents
        return can_review_documents(request.user)

    def has_change_permission(self, request, obj=None):
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        return False  # Only the verified person uploads evidence through the person service.

    def has_delete_permission(self, request, obj=None):
        return False  # Document retention is a separate policy, not a generic admin operation.

    @admin.display(description=_("Скачать"))
    def download_link(self, obj):
        if obj and obj.pk:
            url = reverse("serve_specialist_document", args=[obj.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, _("Скачать / Просмотреть"))
        return "-"


@admin.register(Specialist)
class SpecialistAdmin(QueueSortingAdminMixin, admin.ModelAdmin):
    class Media:
        css = {"all": ("admin/css/pages/specialist_form.css",)}
        js = ()

    form = SpecialistAdminForm
    change_form_template = "admin/catalog/specialist/change_form.html"
    change_list_template = "admin/catalog/specialist/change_list.html"
    km_primary_filters = ("status", "is_active", "consultation_format")
    
    list_display = ("profile_column", "directions_column", "owner", "format_badge", "status_badge", "documents_count", "rating_column", "row_actions")
    list_filter = (QueueSortParameter, "status", "is_active", "consultation_format", "specializations")
    search_fields = ("name", "name_alt", "bio_ru", "bio_az", "bio_en")
    readonly_fields = ("owner", "verified_person_user", "identity_verification_date", "created_by",
                       "rating_avg", "rating_count", "created_at", "updated_at")
    filter_horizontal = ()
    inlines = [SpecialistPracticeLocationInline, SpecialistDocumentInline]
    actions = ("mark_published", "mark_draft", "mark_pending", "mark_rejected")

    def get_readonly_fields(self, request, obj=None):
        fields = tuple(super().get_readonly_fields(request, obj))
        return fields + ("slug",) if obj is not None else fields

    @admin.display(description=_("Дата подтверждения личности"))
    def identity_verification_date(self, obj):
        return display_for_field(
            obj.person_verified_at, Specialist._meta.get_field("person_verified_at"),
            self.get_empty_value_display(),
        )

    def render_change_form(self, request, context, *args, **kwargs):
        # Keys depend on configured structure, never the translated display heading.
        numbers = (1,2,3,4,5,6,7,9,11,12)
        sections = {number: {'number':number,'id':f'km-sec-{number}','title':fieldset.name,'fieldset':fieldset}
                    for number,fieldset in zip(numbers,context['adminform'])}
        for inline in context.get('inline_admin_formsets',[]):
            number = 8 if inline.opts.model is SpecialistPracticeLocation else 10
            sections[number]={'number':number,'id':f'km-sec-{number}','title':inline.opts.verbose_name_plural,'inline':inline}
        sections.setdefault(10,{'number':10,'id':'km-sec-10','title':_('10. Подтверждение квалификации'),'private':True})
        sections.setdefault(8,{'number':8,'id':'km-sec-8','title':_('8. Места работы и приёма'),'unavailable':True})
        context['specialist_sections']=[sections[i] for i in range(1,13)]
        original=context.get('original')
        context['specialist_expected_updated_at']=(request.POST.get('expected_updated_at','') if request.method=='POST' and context.get('errors') else original.updated_at.isoformat()) if original else ''
        return super().render_change_form(request,context,*args,**kwargs)

    def get_queryset(self, request):
        from catalog.services.specialist_documents import can_review_documents
        queryset = super().get_queryset(request).select_related("owner").prefetch_related("specializations")
        return queryset.prefetch_related("documents") if can_review_documents(request.user) else queryset

    def get_list_display(self, request):
        from catalog.services.specialist_documents import can_review_documents
        fields = super().get_list_display(request)
        return fields if can_review_documents(request.user) else tuple(field for field in fields if field != 'documents_count')

    def _build_changelist_query_string(self, request, *, clear=(), **updates):
        params = request.GET.copy()
        params.pop("p", None)
        for key in clear:
            params.pop(key, None)
        for key, value in updates.items():
            params.pop(key, None)
            if value not in (None, ""):
                params[key] = value
        encoded = params.urlencode()
        return f"?{encoded}" if encoded else "?"

    def _dashboard_counts(self):
        counts = Specialist.objects.aggregate(
            total=Count("pk"),
            published=Count(
                "pk",
                filter=Q(status=Specialist.STATUS_PUBLISHED, is_active=True),
            ),
            pending=Count("pk", filter=Q(status=Specialist.STATUS_PENDING)),
            inactive=Count("pk", filter=Q(is_active=False)),
            draft=Count("pk", filter=Q(status=Specialist.STATUS_DRAFT)),
            rejected=Count("pk", filter=Q(status=Specialist.STATUS_REJECTED)),
        )
        return {key: int(value or 0) for key, value in counts.items()}

    def _dashboard_stats(self, request, *, counts):
        clear = ("status__exact", "is_active__exact", "is_verified__exact")
        return (
            {
                "label": _("Всего специалистов"),
                "count": counts["total"],
                "url": self._build_changelist_query_string(request, clear=clear),
                "tone": "info",
            },
            {
                "label": _("Опубликовано"),
                "count": counts["published"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_PUBLISHED,
                    is_active__exact="1",
                ),
                "tone": "good",
            },
            {
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_PENDING,
                ),
                "tone": "warn",
            },
            {
                "label": _("Неактивные"),
                "count": counts["inactive"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    is_active__exact="0",
                ),
                "tone": "muted",
            },
        )

    def _quick_filters(self, request, *, counts):
        current_status = request.GET.get("status__exact")
        current_active = request.GET.get("is_active__exact")
        clear = ("status__exact", "is_active__exact", "is_verified__exact")
        return (
            {
                "key": "all",
                "label": _("Все профили"),
                "count": counts["total"],
                "url": self._build_changelist_query_string(request, clear=clear),
                "active": not any((current_status, current_active)),
            },
            {
                "key": "published",
                "label": _("Опубликованы"),
                "count": counts["published"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_PUBLISHED,
                    is_active__exact="1",
                ),
                "active": current_status == Specialist.STATUS_PUBLISHED and current_active == "1",
            },
            {
                "key": "pending",
                "label": _("На модерации"),
                "count": counts["pending"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_PENDING,
                ),
                "active": current_status == Specialist.STATUS_PENDING and not current_active,
            },
            {
                "key": "inactive",
                "label": _("Неактивные"),
                "count": counts["inactive"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    is_active__exact="0",
                ),
                "active": current_active == "0" and not current_status,
            },
            {
                "key": "draft",
                "label": _("Черновики"),
                "count": counts["draft"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_DRAFT,
                ),
                "active": current_status == Specialist.STATUS_DRAFT and not current_active,
            },
            {
                "key": "rejected",
                "label": _("Отклонены"),
                "count": counts["rejected"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    status__exact=Specialist.STATUS_REJECTED,
                ),
                "active": current_status == Specialist.STATUS_REJECTED and not current_active,
            },
        )

    def _bulk_actions(self):
        return (
            {"name": "mark_published", "label": _("Опубликовать"), "tone": "good", "icon": "fas fa-bullhorn", "description": _("Опубликовать выбранные профили.")},
            {"name": "mark_draft", "label": _("В черновик"), "tone": "muted", "icon": "far fa-file-alt", "description": _("Снять выбранные профили с публикации.")},
            {"name": "mark_pending", "label": _("На модерацию"), "tone": "warn", "icon": "fas fa-hourglass-half", "description": _("Отправить выбранные профили на проверку.")},
        )

    def get_urls(self):
        from django.urls import path
        names = f"{self.opts.app_label}_{self.opts.model_name}"
        extra = [
            path(
                "search-suggestions/",
                self.admin_site.admin_view(self.search_suggestions_view),
                name=f"{names}_search_suggestions",
            ),
        ]
        return extra + super().get_urls()

    def search_suggestions_view(self, request):
        if not self.has_view_or_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        from django.http import JsonResponse
        from django.urls import reverse
        term = (request.GET.get("q") or "").strip()
        if len(term) < 2:
            return JsonResponse({"results": []})
        language_code = getattr(request, "LANGUAGE_CODE", None)

        variants = list(dict.fromkeys([term, term.lower(), term.capitalize(), term.upper()]))
        q_filter = Q()
        fields = ("name", "name_alt", "slug", "bio_ru", "bio_az", "bio_en", "owner__username", "owner__email")
        for v in variants:
            for f in fields:
                q_filter |= Q(**{f"{f}__icontains": v})

        queryset = Specialist.objects.filter(q_filter).select_related("owner").prefetch_related("specializations").distinct()[:8]

        results = []
        for specialist in queryset:
            title = (specialist.name or "").strip()
            if not title:
                continue

            meta_parts = []
            specs = [s.name_i18n(language_code) for s in specialist.specializations.all()[:2]]
            specs_label = ", ".join(specs) if specs else ""
            if specs_label:
                meta_parts.append(specs_label)

            format_label = specialist.get_consultation_format_display()
            if format_label:
                meta_parts.append(format_label)

            exp_label = ""
            if specialist.experience_years:
                exp_label = f"Стаж {specialist.experience_years} л."
                meta_parts.append(exp_label)

            owner_label = ""
            if specialist.owner:
                owner_label = specialist.owner.get_username() or getattr(specialist.owner, "email", "")
                if owner_label:
                    meta_parts.append(str(owner_label))

            change_url = reverse("admin:catalog_specialist_change", args=[specialist.pk])

            tone = "muted"
            if specialist.status == Specialist.STATUS_PUBLISHED and specialist.is_active:
                tone = "good"
            elif specialist.status == Specialist.STATUS_PENDING:
                tone = "warn"
            elif specialist.status == Specialist.STATUS_REJECTED:
                tone = "danger"

            results.append(
                {
                    "id": specialist.pk,
                    "value": title,
                    "label": title,
                    "meta": " • ".join(part for part in meta_parts if part)[:180],
                    "status": specialist.status,
                    "status_label": specialist.get_status_display(),
                    "status_tone": tone,
                    "category": specs_label,
                    "district": format_label,
                    "address": exp_label,
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
                    "edit": str(_("Редактировать профиль")),
                    "found": str(_("Найдено")),
                },
            }
        )

    def changelist_view(self, request, extra_context=None):
        counts = self._dashboard_counts()
        quick_filters = self._quick_filters(request, counts=counts)
        from django.urls import reverse
        extra_context = {
            "specialist_dashboard_stats": self._dashboard_stats(request, counts=counts),
            "km_primary_quick_filters": quick_filters[:5],
            "km_secondary_quick_filters": quick_filters[5:],
            "specialist_bulk_actions": self._bulk_actions(),
            "km_changelist_reset_url": "?",
            "km_search_label": _("Поиск по имени специалиста"),
            "km_search_placeholder": _("Имя специалиста..."),
            "km_suggestions_url": reverse("admin:catalog_specialist_search_suggestions"),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description=_("Опубликовать выбранных специалистов"))
    def mark_published(self, request, queryset):
        updated_count = queryset.update(
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
            rejection_reason="",
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("Опубликован %(count)d профиль.", "Опубликовано %(count)d профиля.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Вернуть выбранных специалистов в черновик"))
    def mark_draft(self, request, queryset):
        updated_count = queryset.update(
            status=Specialist.STATUS_DRAFT,
            is_active=False,
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("%(count)d профиль переведён в черновик.", "%(count)d профиля переведены в черновик.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отправить выбранных специалистов на модерацию"))
    def mark_pending(self, request, queryset):
        updated_count = queryset.update(
            status=Specialist.STATUS_PENDING,
            is_active=False,
            rejection_reason="",
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("%(count)d профиль отправлен на модерацию.", "%(count)d профиля отправлены на модерацию.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить выбранных специалистов"))
    def mark_rejected(self, request, queryset):
        updated_count = queryset.update(
            status=Specialist.STATUS_REJECTED,
            is_active=False,
            rejection_reason=_("Профиль требует доработки перед публикацией."),
            updated_at=timezone.now(),
        )
        self.message_user(
            request,
            ngettext("Отклонён %(count)d профиль.", "Отклонено %(count)d профиля.", updated_count)
            % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )


    @admin.display(description=_("Профиль"), ordering="name")
    def profile_column(self, obj):
        change_url = reverse("admin:catalog_specialist_change", args=[obj.pk])
        if obj.photo:
            photo = format_html('<img src="{}" alt="" class="km-admin-spec-photo">', obj.photo.url)
        else:
            photo = format_html(
                '<span class="km-admin-spec-photo km-admin-spec-photo--empty" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-person"></use></svg>'
                '</span>',
                obj.name,
            )
            
        sub_badges = []
        if obj.name_alt:
            sub_badges.append(format_html('<span class="km-spec-alt-title">{}</span>', obj.name_alt))
        if getattr(obj, "is_verified", False) or getattr(obj, "person_verified_at", None):
            sub_badges.append(format_html('<span class="km-verified-chip" title="{}"><svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-check_circle"></use></svg> {}</span>', _("Личность подтверждена"), _("Верифицирован")))
        elif obj.status == Specialist.STATUS_PUBLISHED:
            public_url = obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else ""
            if public_url:
                sub_badges.append(format_html('<a href="{}" class="km-spec-site-link" target="_blank" rel="noopener noreferrer">{} ↗</a>', public_url, _("На сайте")))
        if getattr(obj, "created_at", None):
            sub_badges.append(format_html('<span class="km-spec-date-chip" title="{}"><i class="far fa-clock"></i> {}</span>', _("Дата создания / подачи"), obj.created_at.strftime('%d.%m.%Y')))
                
        sub_html = format_html_join(" ", "{}", ((b,) for b in sub_badges)) if sub_badges else format_html('<small class="km-spec-slug">{}</small>', obj.slug)
        
        return format_html(
            '<div class="km-admin-spec-profile">'
            '{}'
            '<div class="km-admin-spec-info">'
            '<a class="km-admin-spec-name" href="{}" title="{}"><strong>{}</strong></a>'
            '<div class="km-admin-spec-sub">{}</div>'
            '</div>'
            '</div>',
            photo,
            change_url,
            _("Проверить и редактировать профиль специалиста"),
            obj.name,
            sub_html,
        )

    @admin.display(description=_("Направления"))
    def directions_column(self, obj):
        items = list(obj.specializations.all()[:3])
        if not items:
            return format_html('<span class="km-admin-muted">{}</span>', _("Не выбрано"))
        total = obj.specializations.count()
        more_badge = ""
        if total > 3:
            more_badge = format_html('<span class="km-spec-tag km-spec-tag--more">+{}</span>', total - 3)
        tags_html = format_html_join("", '<span class="km-spec-tag" title="{}">{}</span>', ((item.name_i18n(), item.name_i18n()) for item in items))
        return format_html(
            '<div class="km-admin-spec-tags">{}{}</div>',
            tags_html,
            more_badge,
        )

    @admin.display(description=_("Владелец профиля"), ordering="owner")
    def owner(self, obj):
        if not obj.owner:
            return format_html('<span class="km-admin-muted">{}</span>', _("Без владельца"))
        user = obj.owner
        name = user.get_full_name() or user.username
        handle = f"@{user.username}" if user.username else ""
        return format_html(
            '<div class="km-spec-owner-cell">'
            '<span class="km-spec-owner-avatar"><i class="fas fa-user"></i></span>'
            '<div class="km-spec-owner-info">'
            '<strong>{}</strong>'
            '<small>{}</small>'
            '</div>'
            '</div>',
            name,
            handle or user.email or "",
        )

    @admin.display(description=_("Формат"), ordering="consultation_format")
    def format_badge(self, obj):
        fmt = str(obj.consultation_format or "").strip().lower()
        if fmt == Specialist.FORMAT_BOTH:
            icon = "fa-laptop-house"
            label = _("Онлайн и очно")
            tone = "both"
        elif fmt in (Specialist.FORMAT_OFFLINE, "in_person"):
            icon = "fa-map-marker-alt"
            label = _("Только очно")
            tone = "offline"
        elif fmt == Specialist.FORMAT_ONLINE:
            icon = "fa-video"
            label = _("Только онлайн")
            tone = "online"
        else:
            icon = "fa-user-clock"
            label = obj.get_consultation_format_display() or _("Уточняется")
            tone = "muted"
            
        return format_html(
            '<span class="km-admin-spec-badge km-format-{}"><i class="fas {}"></i>{}</span>',
            tone,
            icon,
            label,
        )

    @admin.display(description=_("Статус"), ordering="status")
    def status_badge(self, obj):
        status_tones = {
            Specialist.STATUS_PUBLISHED: "good",
            Specialist.STATUS_PENDING: "warn",
            Specialist.STATUS_REJECTED: "danger",
            Specialist.STATUS_DRAFT: "muted",
        }
        tone = status_tones.get(obj.status, "muted")
        label = obj.get_status_display()
        return format_html(
            '<span class="km-status-pill km-status-pill--{}">'
            '<span class="km-status-dot"></span>'
            '{}'
            '</span>',
            tone,
            label,
        )

    @admin.display(description=_("Документы"))
    def documents_count(self, obj):
        count = obj.documents.count()
        change_url = reverse("admin:catalog_specialist_change", args=[obj.pk])
        doc_url = f"{change_url}#km-sec-10"
        if count > 0:
            return format_html(
                '<a href="{}" class="km-spec-doc-badge km-spec-doc-badge--has" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-description"></use></svg> '
                '{} {}</a>',
                doc_url,
                _("Перейти к дипломам и сертификатам (секция 10)"),
                count,
                _("док."),
            )
        return format_html(
            '<a href="{}" class="km-spec-doc-badge km-spec-doc-badge--empty" title="{}">'
            '<svg class="km-i" viewBox="0 0 960 960"><use href="#kmi-description"></use></svg> '
            '{}</a>',
            doc_url,
            _("Загрузить документы специалиста (секция 10)"),
            _("Нет док."),
        )

    @admin.display(description=_("Отзывы и оценка"), ordering="rating_avg")
    def rating_column(self, obj):
        if not obj.rating_count:
            return format_html('<span class="km-admin-muted">{}</span>', _("Нет отзывов"))
        rating_val = f"{float(obj.rating_avg or 0):.1f}"
        return format_html(
            '<div class="km-spec-rating-cell">'
            '<span class="km-spec-rating-stars"><i class="fas fa-star text-warning"></i> <strong>{}</strong></span>'
            '<span class="km-spec-rating-count">({} {})</span>'
            '</div>',
            rating_val,
            int(obj.rating_count or 0),
            _("отз."),
        )

    @admin.display(description=_("Действия"))
    def row_actions(self, obj):
        change_url = reverse("admin:catalog_specialist_change", args=[obj.pk])
        buttons = []
        
        # Primary "Проверить" action
        buttons.append(
            format_html(
                '<a class="km-admin-action km-admin-action--primary" href="{}" title="{}">'
                '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-edit"></use></svg>'
                '<span>{}</span></a>',
                change_url,
                _("Проверить все 12 секций анкеты специалиста"),
                _("Проверить"),
            )
        )
        
        # Moderation quick actions:
        if obj.status == Specialist.STATUS_PENDING:
            buttons.append(
                format_html(
                    '<button type="button" class="km-admin-action km-admin-action--good" data-specialist-action="mark_published" data-specialist-id="{}" title="{}">'
                    '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-check"></use></svg>'
                    '<span>{}</span></button>',
                    obj.pk,
                    _("Одобрить и опубликовать профиль специалиста"),
                    _("Одобрить"),
                )
            )
            buttons.append(
                format_html(
                    '<button type="button" class="km-admin-action km-admin-action--warn" data-specialist-action="mark_rejected" data-specialist-id="{}" title="{}">'
                    '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-close"></use></svg>'
                    '<span>{}</span></button>',
                    obj.pk,
                    _("Отклонить профиль специалиста"),
                    _("Отклонить"),
                )
            )
        elif obj.status == Specialist.STATUS_PUBLISHED:
            buttons.append(
                format_html(
                    '<button type="button" class="km-admin-action km-admin-action--muted" data-specialist-action="mark_draft" data-specialist-id="{}" title="{}">'
                    '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-visibility_off"></use></svg>'
                    '<span>{}</span></button>',
                    obj.pk,
                    _("Снять с публикации и перевести в черновик"),
                    _("В черновик"),
                )
            )
        elif obj.status in (Specialist.STATUS_DRAFT, Specialist.STATUS_REJECTED):
            buttons.append(
                format_html(
                    '<button type="button" class="km-admin-action km-admin-action--good" data-specialist-action="mark_published" data-specialist-id="{}" title="{}">'
                    '<svg class="km-i" viewBox="0 0 960 960" aria-hidden="true"><use href="#kmi-check"></use></svg>'
                    '<span>{}</span></button>',
                    obj.pk,
                    _("Опубликовать специалиста"),
                    _("Опубликовать"),
                )
            )
            
        public_url = obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else ""
        if public_url and obj.status == Specialist.STATUS_PUBLISHED:
            buttons.append(
                format_html(
                    '<a class="km-admin-action km-admin-action--ghost" href="{}" target="_blank" rel="noopener" title="{}">'
                    '<i class="fas fa-external-link-alt" style="margin-right: 4px;"></i>'
                    '<span>{}</span></a>',
                    public_url,
                    _("Открыть публичный профиль на сайте"),
                    _("На сайте ↗"),
                )
            )

        menu_items = [
            (f"{change_url}#km-sec-10", _("Документы и дипломы"), ""),
            (f"{change_url}#km-sec-8", _("Места работы и приёма"), ""),
        ]
        if public_url:
            menu_items.insert(0, (public_url, _("Страница на сайте ↗"), ""))
        delete_url = reverse("admin:catalog_specialist_delete", args=[obj.pk])
        menu_items.append((delete_url, _("Удалить"), "km-admin-action-menu__link--danger"))
        
        buttons_html = mark_safe(" ".join(buttons))
        menu_html = render_action_menu(menu_items)
        return render_row_actions_container(buttons_html, menu_html)
    
    fieldsets = (
        (
            _("1. Основная информация"),
            {
                "fields": (
                    "created_by", "verified_person_user", "identity_verification_date", "owner",
                    "name",
                    "name_alt",
                    "slug",
                )
            },
        ),
        (
            _("2. Фото и описание"),
            {
                "fields": (
                    "photo",
                    "bio_az",
                    "bio_ru",
                    "bio_en",
                )
            },
        ),
        (
            _("3. Направления деятельности"),
            {
                "fields": (
                    "specializations",
                )
            },
        ),
        (
            _("4. Возраст детей"),
            {
                "fields": (
                    ("age_from", "age_to"),
                )
            },
        ),
        (
            _("5. Языки работы"),
            {
                "fields": (
                    ("language_az", "language_ru", "language_en"),
                )
            },
        ),
        (
            _("6. Онлайн / очно"),
            {
                "fields": (
                    "consultation_format",
                )
            },
        ),
        (
            _("7. Стоимость и продолжительность"),
            {
                "fields": (
                    ("price_from", "price_to"),
                    "duration_minutes",
                )
            },
        ),
        # 8 = SpecialistPracticeLocationInline
        (
            _("9. Образование и опыт"),
            {
                "fields": (
                    "experience_years",
                    "education_az",
                    "education_ru",
                    "education_en",
                    "experience_info_az",
                    "experience_info_ru",
                    "experience_info_en",
                )
            },
        ),
        # 10 = SpecialistDocumentInline
        (
            _("11. Контакты"),
            {
                "fields": (
                    "phone",
                    "whatsapp",
                    "instagram",
                    "website",
                )
            },
        ),
        (
            _("12. Модерация и публикация"),
            {
                "fields": (
                    "status",
                    "is_active",
                    "rejection_reason",
                    "rating_avg",
                    "rating_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )



from .review_versions import VersionedReviewAdminMixin


@admin.register(SpecialistReview)
class SpecialistReviewAdmin(VersionedReviewAdminMixin, ModerationActorAdminMixin, admin.ModelAdmin):
    list_display = ("specialist", "author_name", "rating", "status", "is_approved", "created_at")
    list_filter = ("status", "is_approved", "rating", "created_at")
    search_fields = ("specialist__name", "author_name", "text")
    readonly_fields = ("created_at",)
    actions = ["approve_selected", "hide_selected", "reject_selected"]
    fieldsets = (
        (
            _("Отзыв"),
            {
                "fields": (
                    "specialist",
                    "user",
                    "author_name",
                    "rating",
                    "text",
                )
            },
        ),
        (
            _("Статус и модерация"),
            {
                "fields": (
                    "status",
                    "is_approved",
                    "rejection_reason",
                    "created_at",
                )
            },
        ),
    )

    # VersionedReviewAdminMixin owns signed candidate decisions and visibility.
    # Raw queryset updates leave revision history and pending candidates divergent.
