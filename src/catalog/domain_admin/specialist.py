from django import forms
from django.contrib import admin, messages
from django.db import models
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext
from django.urls import reverse

from catalog.models import (
    Region,
    District,
    MetroStation,
    SpecialistSpecialization,
    Specialist,
    SpecialistPracticeLocation,
    SpecialistDocument,
    SpecialistReview
)

class SpecialistAdminForm(forms.ModelForm):
    class Meta:
        model = Specialist
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        consultation_format = cleaned_data.get("consultation_format")
        
        # Enforce that if format is offline or both, at least one location must be provided and active.
        if consultation_format in [Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH]:
            total_forms_raw = self.data.get("practice_locations-TOTAL_FORMS")
            has_location = False
            if total_forms_raw is not None:
                try:
                    total_forms = int(total_forms_raw)
                    for i in range(total_forms):
                        # Skip deleted rows
                        delete_val = self.data.get(f"practice_locations-{i}-DELETE")
                        if delete_val in ["on", "1", "true"]:
                            continue
                        
                        place = self.data.get(f"practice_locations-{i}-place")
                        address = self.data.get(f"practice_locations-{i}-address")
                        region = self.data.get(f"practice_locations-{i}-region")
                        is_active_val = self.data.get(f"practice_locations-{i}-is_active")
                        
                        is_active = (is_active_val not in ["off", "false", "0"])
                        
                        if is_active and (place or address):
                            has_location = True
                            
                            # Validate region is filled for active locations
                            if not region:
                                raise forms.ValidationError(
                                    _("Для очной локации необходимо указать город/регион.")
                                )
                except ValueError:
                    pass
            
            if not has_location:
                raise forms.ValidationError(
                    _("Для очного формата работы (или онлайн и очно) необходимо указать хотя бы одно активное место приема.")
                )
                
        return cleaned_data


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("key", "name_ru", "name_az", "name_en")
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("key", "region", "name_ru", "name_az", "name_en")
    list_filter = ("region",)
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(MetroStation)
class MetroStationAdmin(admin.ModelAdmin):
    list_display = ("key", "name_ru", "name_az", "name_en")
    search_fields = ("key", "name_ru", "name_az", "name_en")


@admin.register(SpecialistSpecialization)
class SpecialistSpecializationAdmin(admin.ModelAdmin):
    list_display = ("code", "name_ru", "name_az", "name_en", "is_active", "order")
    list_editable = ("is_active", "order")
    search_fields = ("code", "name_ru", "name_az", "name_en")


class SpecialistPracticeLocationInline(admin.TabularInline):
    model = SpecialistPracticeLocation
    extra = 0
    verbose_name = _("Место приёма")
    verbose_name_plural = _("8. Места работы и приёма")
    fields = ("place", "address", "region", "district", "metro", "price_per_session", "phone", "is_primary", "is_active")
    autocomplete_fields = ("place",)


class SpecialistDocumentInline(admin.TabularInline):
    model = SpecialistDocument
    extra = 0
    verbose_name = _("Документ")
    verbose_name_plural = _("10. Подтверждение квалификации")
    fields = ("document_type", "name", "file", "download_link", "status", "is_published", "rejection_reason")
    readonly_fields = ("download_link",)

    @admin.display(description=_("Скачать"))
    def download_link(self, obj):
        if obj and obj.pk:
            url = reverse("serve_specialist_document", args=[obj.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, _("Скачать / Просмотреть"))
        return "-"


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    class Media:
        css = {"all": ("admin/css/pages/specialist_form.css",)}
        js = ("admin/js/specialist_admin.js",)

    form = SpecialistAdminForm
    change_form_template = "admin/catalog/specialist/change_form.html"
    change_list_template = "admin/catalog/specialist/change_list.html"
    km_primary_filters = ("status", "is_verified", "is_active", "consultation_format")
    
    list_display = ("profile_column", "directions_column", "owner", "format_badge", "status_badge", "verification_badge", "documents_count", "rating_column", "updated_at")
    list_filter = ("status", "is_verified", "is_active", "consultation_format", "specializations")
    search_fields = ("name", "name_alt", "bio_ru", "bio_az", "bio_en")
    readonly_fields = ("rating_avg", "rating_count", "created_at", "updated_at")
    filter_horizontal = ("specializations",)
    inlines = [SpecialistPracticeLocationInline, SpecialistDocumentInline]
    actions = ("mark_published", "mark_draft", "mark_pending", "mark_verified", "mark_rejected")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("owner").prefetch_related(
            "specializations",
            "documents",
        )

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
            unverified=Count("pk", filter=Q(is_verified=False)),
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
            {
                "label": _("Без проверки"),
                "count": counts["unverified"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    is_verified__exact="0",
                ),
                "tone": "info",
            },
        )

    def _quick_filters(self, request, *, counts):
        current_status = request.GET.get("status__exact")
        current_active = request.GET.get("is_active__exact")
        current_verified = request.GET.get("is_verified__exact")
        clear = ("status__exact", "is_active__exact", "is_verified__exact")
        return (
            {
                "key": "all",
                "label": _("Все профили"),
                "count": counts["total"],
                "url": self._build_changelist_query_string(request, clear=clear),
                "active": not any((current_status, current_active, current_verified)),
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
                "active": current_status == Specialist.STATUS_PUBLISHED and current_active == "1" and not current_verified,
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
                "active": current_status == Specialist.STATUS_PENDING and not current_active and not current_verified,
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
                "active": current_active == "0" and not current_status and not current_verified,
            },
            {
                "key": "unverified",
                "label": _("Без проверки"),
                "count": counts["unverified"],
                "url": self._build_changelist_query_string(
                    request,
                    clear=clear,
                    is_verified__exact="0",
                ),
                "active": current_verified == "0" and not current_status and not current_active,
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
                "active": current_status == Specialist.STATUS_DRAFT and not current_active and not current_verified,
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
                "active": current_status == Specialist.STATUS_REJECTED and not current_active and not current_verified,
            },
        )

    def _bulk_actions(self):
        return (
            {"name": "mark_published", "label": _("Опубликовать"), "tone": "good", "icon": "fas fa-bullhorn", "description": _("Опубликовать выбранные профили.")},
            {"name": "mark_draft", "label": _("В черновик"), "tone": "muted", "icon": "far fa-file-alt", "description": _("Снять выбранные профили с публикации.")},
            {"name": "mark_pending", "label": _("На модерацию"), "tone": "warn", "icon": "fas fa-hourglass-half", "description": _("Отправить выбранные профили на проверку.")},
            {"name": "mark_verified", "label": _("Подтвердить"), "tone": "good", "icon": "fas fa-check-circle", "description": _("Отметить выбранные профили как проверенные.")},
        )

    def changelist_view(self, request, extra_context=None):
        counts = self._dashboard_counts()
        quick_filters = self._quick_filters(request, counts=counts)
        extra_context = {
            "specialist_dashboard_stats": self._dashboard_stats(request, counts=counts),
            "km_primary_quick_filters": quick_filters[:5],
            "km_secondary_quick_filters": quick_filters[5:],
            "specialist_bulk_actions": self._bulk_actions(),
            "km_changelist_reset_url": "?",
            "km_search_label": _("Поиск по имени специалиста"),
            "km_search_placeholder": _("Имя специалиста..."),
            "km_disable_search_suggestions": True,
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

    @admin.action(description=_("Отметить выбранных специалистов как проверенных"))
    def mark_verified(self, request, queryset):
        updated_count = queryset.update(is_verified=True, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("%(count)d профиль подтверждён.", "%(count)d профиля подтверждены.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.display(description=_("Профиль"), ordering="name")
    def profile_column(self, obj):
        if obj.photo:
            photo = format_html('<img src="{}" alt="" class="km-admin-spec-photo">', obj.photo.url)
        else:
            photo = format_html(
                '<span class="km-admin-spec-photo km-admin-spec-photo--empty"><i class="fas fa-user-tie"></i>{}</span>',
                "",
            )
        return format_html(
            '<div class="km-admin-spec-profile">{}<div><strong>{}</strong><small>{}</small></div></div>',
            photo,
            obj.name,
            obj.slug,
        )

    @admin.display(description=_("Направления"))
    def directions_column(self, obj):
        items = list(obj.specializations.all()[:3])
        if not items:
            return format_html('<span class="km-admin-muted">{}</span>', _("Не выбрано"))
        return format_html(
            '<div class="km-admin-spec-tags">{}</div>',
            format_html("".join('<span>{}</span>' for _ in items), *(item.name_i18n() for item in items)),
        )

    @admin.display(description=_("Формат"), ordering="consultation_format")
    def format_badge(self, obj):
        icon = "fa-video" if obj.consultation_format == Specialist.FORMAT_ONLINE else "fa-map-marker-alt"
        if obj.consultation_format == Specialist.FORMAT_BOTH:
            icon = "fa-laptop-house"
        return format_html('<span class="km-admin-spec-badge"><i class="fas {}"></i>{}</span>', icon, obj.get_consultation_format_display())

    @admin.display(description=_("Статус"), ordering="status")
    def status_badge(self, obj):
        return format_html('<span class="km-status-badge km-status-{}">{}</span>', obj.status, obj.get_status_display())

    @admin.display(description=_("Проверка"), boolean=False)
    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html('<span class="km-status-badge km-status-verified"><i class="fas fa-check-circle"></i>{}</span>', _("Проверен"))
        return format_html('<span class="km-admin-muted">{}</span>', _("Нет"))

    @admin.display(description=_("Документы"))
    def documents_count(self, obj):
        count = obj.documents.count()
        return format_html('<span class="km-admin-spec-badge"><i class="fas fa-file-alt"></i>{}</span>', count)

    @admin.display(description=_("Рейтинг"), ordering="rating_avg")
    def rating_column(self, obj):
        if not obj.rating_count:
            return format_html('<span class="km-admin-muted">{}</span>', _("Нет отзывов"))
        return format_html('<span class="km-admin-spec-badge"><i class="fas fa-star"></i>{} ({})</span>', obj.rating_avg, obj.rating_count)
    
    fieldsets = (
        (
            _("1. Основная информация"),
            {
                "fields": (
                    "owner",
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
                    "is_verified",
                    "rejection_reason",
                    "rating_avg",
                    "rating_count",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )



@admin.register(SpecialistReview)
class SpecialistReviewAdmin(admin.ModelAdmin):
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

    @admin.action(description=_("Опубликовать выбранные отзывы"))
    def approve_selected(self, request, queryset):
        specialist_ids = list(queryset.values_list("specialist_id", flat=True).distinct())
        updated_count = queryset.exclude(is_approved=True, status=SpecialistReview.STATUS_APPROVED).update(
            is_approved=True, status=SpecialistReview.STATUS_APPROVED
        )
        from catalog.models.specialist import sync_specialist_rating_stats
        sync_specialist_rating_stats(specialist_ids)
        self.message_user(
            request,
            ngettext("Опубликован %(count)d отзыв.", "Опубликовано %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Скрыть выбранные отзывы"))
    def hide_selected(self, request, queryset):
        specialist_ids = list(queryset.values_list("specialist_id", flat=True).distinct())
        updated_count = queryset.exclude(is_approved=False, status=SpecialistReview.STATUS_PENDING).update(
            is_approved=False, status=SpecialistReview.STATUS_PENDING
        )
        from catalog.models.specialist import sync_specialist_rating_stats
        sync_specialist_rating_stats(specialist_ids)
        self.message_user(
            request,
            ngettext("Скрыт %(count)d отзыв.", "Скрыто %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить выбранные отзывы"))
    def reject_selected(self, request, queryset):
        specialist_ids = list(queryset.values_list("specialist_id", flat=True).distinct())
        updated_count = queryset.exclude(is_approved=False, status=SpecialistReview.STATUS_REJECTED).update(
            is_approved=False, status=SpecialistReview.STATUS_REJECTED
        )
        from catalog.models.specialist import sync_specialist_rating_stats
        sync_specialist_rating_stats(specialist_ids)
        self.message_user(
            request,
            ngettext("Отклонён %(count)d отзыв.", "Отклонено %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

