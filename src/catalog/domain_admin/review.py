from django import forms
from django.contrib import admin, messages
from django.db import models
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _, ngettext
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from catalog.models import PlaceReview, SiteReview
from catalog.services.content_quality import review_quality_check
from .ui_utils import render_primary_action, render_inline_action, render_action_menu, render_row_actions_container, build_admin_query_string

def _localized_admin_url(path: str) -> str:
    from django.utils.translation import get_language
    language = (get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
    if language == default_lang:
        for code, _label in settings.LANGUAGES:
            prefix = f"/{code}/"
            if path.startswith(prefix):
                return f"/{path[len(prefix):].lstrip('/')}"
        return path

    localized_prefix = f"/{language}/"
    if path.startswith(localized_prefix):
        return path

    for code, _label in settings.LANGUAGES:
        prefix = f"/{code}/"
        if path.startswith(prefix):
            return f"{localized_prefix}{path[len(prefix):].lstrip('/')}"

    return f"{localized_prefix}{path.lstrip('/')}"


class PlaceReviewInline(admin.TabularInline):
    model = PlaceReview
    extra = 0
    fields = ("review_author_display", "rating", "text", "is_approved", "created_at_display")
    readonly_fields = ("review_author_display", "created_at_display")
    ordering = ("-created_at",)
    show_change_link = True
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 4, "cols": 52})},
    }

    @admin.display(description=_("Автор"))
    def review_author_display(self, obj):
        if not obj or not obj.pk:
            return _("Без автора")

        primary = (obj.author_name or "").strip()
        if not primary and obj.user_id:
            primary = obj.user.get_full_name().strip() or obj.user.username or obj.user.email or ""
        if not primary:
            primary = str(_("Без имени"))

        meta_bits = []
        if obj.user_id:
            if obj.user.username:
                meta_bits.append(f"@{obj.user.username}")
            if obj.user.email:
                meta_bits.append(obj.user.email)
        else:
            meta_bits.append(str(_("Без аккаунта")))

        return format_html(
            '<div class="km-inline-review-author"><strong>{}</strong><span>{}</span></div>',
            primary,
            " · ".join(bit for bit in meta_bits if bit),
        )

    @admin.display(description=_("Создан"))
    def created_at_display(self, obj):
        return getattr(obj, "created_at", None)


class ReviewModerationStatusFilter(admin.SimpleListFilter):
    title = _("Статус модерации")
    parameter_name = "review_status"

    def lookups(self, request, model_admin):
        return (
            ("published", _("Опубликован")),
            ("hidden", _("Скрыт")),
            ("suspicious", _("Требует проверки")),
            ("only_rating", _("Только оценка")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "published":
            return queryset.filter(is_approved=True, contains_profanity=False)
        if value == "hidden":
            return queryset.filter(is_approved=False)
        if value == "suspicious":
            return queryset.filter(Q(contains_profanity=True) | Q(is_approved=False, dislikes_count__gt=0))
        if value == "only_rating":
            return queryset.filter(Q(text__isnull=True) | Q(text__exact=""))
        return queryset


class ReviewTextPresenceFilter(admin.SimpleListFilter):
    title = _("Текст")
    parameter_name = "text_presence"

    def lookups(self, request, model_admin):
        return (
            ("with_text", _("Есть текст")),
            ("only_rating", _("Только оценка")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "with_text":
            return queryset.exclude(text__isnull=True).exclude(text__exact="")
        if value == "only_rating":
            return queryset.filter(Q(text__isnull=True) | Q(text__exact=""))
        return queryset


class ReviewRiskFilter(admin.SimpleListFilter):
    title = _("Сигналы риска")
    parameter_name = "risk_signal"

    def lookups(self, request, model_admin):
        return (
            ("profanity", _("Есть скрытая лексика")),
            ("low_rating", _("Низкая оценка")),
            ("many_dislikes", _("Много дизлайков")),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "profanity":
            return queryset.filter(contains_profanity=True)
        if value == "low_rating":
            return queryset.filter(rating__lte=2)
        if value == "many_dislikes":
            return queryset.filter(dislikes_count__gt=0)
        return queryset


@admin.register(PlaceReview)
class PlaceReviewAdmin(admin.ModelAdmin):
    change_list_template = "admin/catalog/placereview/change_list.html"
    km_primary_filters = ("review_status", "risk_signal", "rating")
    list_per_page = 15
    change_form_template = "admin/catalog/placereview/change_form.html"
    list_select_related = ("place", "user")
    list_display = (
        "review_summary",
        "author_summary",
        "rating_summary",
        "moderation_status_summary",
        "risk_flags_summary",
        "engagement_summary",
        "created_at_display",
        "row_actions",
    )
    list_filter = (
        ReviewModerationStatusFilter,
        ReviewTextPresenceFilter,
        ReviewRiskFilter,
        "rating",
        "contains_profanity",
        "is_approved",
        "status",
        "place",
        "created_at",
    )
    search_fields = ("place__name_ru", "place__name_en", "place__name_az", "author_name", "user__username", "user__email", "text")
    readonly_fields = (
        "moderation_status_summary",
        "likes_count",
        "dislikes_count",
        "contains_profanity",
        "popularity_score_display",
        "created_at",
        "updated_at",
        "session_key",
    )
    actions = ("approve_selected", "hide_selected", "reject_selected", "delete_selected")
    fieldsets = (
        (
            _("Отзыв"),
            {
                "fields": (
                    "place",
                    "user",
                    "author_name",
                    "rating",
                    "text",
                )
            },
        ),
        (
            _("Модерация"),
            {
                "fields": (
                    ("status", "is_approved"),
                    "rejection_reason",
                )
            },
        ),
        (
            _("Служебное и метрики"),
            {
                "classes": ("collapse",),
                "fields": (
                    ("likes_count", "dislikes_count", "popularity_score_display"),
                    ("contains_profanity", "moderation_status_summary"),
                    "session_key",
                    ("created_at", "updated_at"),
                )
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("place", "user")

    def _review_has_text(self, obj) -> bool:
        return bool((obj.text or "").strip())

    def _render_review_badge(self, *, label: str, tone: str = "muted"):
        return format_html(
            '<span class="km-admin-badge km-admin-badge--{}">{}</span>',
            tone,
            label,
        )

    def _place_admin_change_url(self, obj) -> str:
        return _localized_admin_url(reverse("admin:catalog_place_change", args=[obj.place_id], current_app=self.admin_site.name))

    def _review_change_url(self, obj) -> str:
        return _localized_admin_url(reverse("admin:catalog_placereview_change", args=[obj.pk], current_app=self.admin_site.name))

    def _review_delete_url(self, obj) -> str:
        return _localized_admin_url(reverse("admin:catalog_placereview_delete", args=[obj.pk], current_app=self.admin_site.name))

    def _review_action_url(self, obj, action: str) -> str:
        return _localized_admin_url(reverse(f"admin:catalog_placereview_{action}", args=[obj.pk], current_app=self.admin_site.name))

    def _review_preview_text(self, obj) -> str:
        text = (obj.text or "").strip()
        if not text:
            return str(_("Только оценка без комментария"))
        if len(text) <= 180:
            return text
        return f"{text[:177].rstrip()}..."

    def _place_public_link(self, obj) -> str:
        if not obj.place_id:
            return ""
        try:
            return obj.place.get_absolute_url()
        except Exception:
            return ""

    def _review_status(self, obj) -> tuple[str, str]:
        if obj.status == obj.STATUS_REJECTED:
            return str(_("Отклонен")), "danger"
        if obj.status == obj.STATUS_PENDING:
            return str(_("На модерации")), "warn"
        if not obj.is_approved:
            return str(_("Скрыт")), "muted"
        if obj.contains_profanity:
            return str(_("Требует проверки")), "warn"
        return str(_("Опубликован")), "good"

    @admin.display(description=_("Отзыв"))
    def review_summary(self, obj):
        place_name = obj.place.name_ru or obj.place.name
        preview = self._review_preview_text(obj)
        public_link = self._place_public_link(obj)
        public_html = ""
        if public_link:
            public_html = format_html(
                '<a class="km-admin-meta-link" href="{}" target="_blank" rel="noopener noreferrer">{}</a>',
                public_link,
                _("На сайте"),
            )
        return format_html(
            '<div class="km-admin-stack">'
            '<a class="km-review-place-link" href="{}">{}</a>'
            '<span class="km-admin-meta">{}</span>'
            '<div class="km-admin-inline-links">{}</div>'
            "</div>",
            self._place_admin_change_url(obj),
            place_name,
            preview,
            public_html,
        )

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        return obj.author_name or _("Без имени")

    @admin.display(description=_("Автор"))
    def author_summary(self, obj):
        badges = []
        if obj.user_id:
            badges.append(self._render_review_badge(label=_("Есть аккаунт"), tone="info"))
        else:
            badges.append(self._render_review_badge(label=_("Гость"), tone="muted"))
        name = self.display_author(obj)
        if obj.user_id:
            meta_parts = []
            if obj.user.username:
                meta_parts.append(f"@{obj.user.username}")
            if obj.user.email:
                meta_parts.append(obj.user.email)
            meta = " · ".join(meta_parts) or _("Профиль без email")
        else:
            meta = _("Без профиля пользователя")
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title">{}</span><span class="km-admin-meta">{}</span><div class="km-admin-badges">{}</div></div>',
            name,
            meta,
            format_html_join("", "{}", ((badge,) for badge in badges)),
        )

    @admin.display(description=_("Рейтинг"))
    def rating_summary(self, obj):
        tone = "warn" if obj.rating <= 2 else "info" if obj.rating == 3 else "good"
        stars = "★" * int(obj.rating or 0) + "☆" * max(0, 5 - int(obj.rating or 0))
        return format_html(
            '<div class="km-admin-stack"><span class="km-review-rating km-review-rating--{}" title="{}">{}</span>{}</div>',
            tone,
            _("Оценка: %(rating)s из 5") % {"rating": obj.rating},
            stars,
            format_html(
                '<span class="km-admin-meta">{}</span>',
                _("Только оценка") if not self._review_has_text(obj) else _("Есть комментарий"),
            ),
        )

    @admin.display(description=_("Статус"))
    def moderation_status_summary(self, obj):
        label, tone = self._review_status(obj)
        if obj.status == obj.STATUS_PENDING:
            help_text = _("Ждёт решения администратора")
        elif obj.status == obj.STATUS_REJECTED:
            help_text = _("Отклонён и скрыт")
        else:
            help_text = _("Виден на сайте") if obj.is_approved else _("На сайте скрыт")
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-badge km-admin-badge--{}">{}</span><span class="km-admin-meta">{}</span></div>',
            tone,
            label,
            help_text,
        )

    @admin.display(description=_("Риски"))
    def risk_flags_summary(self, obj):
        flags = []
        quality = review_quality_check(obj)
        if obj.contains_profanity:
            flags.append(self._render_review_badge(label=_("Есть скрытая лексика"), tone="warn"))
        if not quality.is_ready:
            flags.append(self._render_review_badge(label=_("Низкое качество"), tone="warn"))
        if not self._review_has_text(obj):
            flags.append(self._render_review_badge(label=_("Только оценка"), tone="info"))
        if obj.rating <= 2:
            flags.append(self._render_review_badge(label=_("Низкая оценка"), tone="warn"))
        if obj.dislikes_count > obj.likes_count:
            flags.append(self._render_review_badge(label=_("Много дизлайков"), tone="warn"))
        if not flags:
            flags.append(self._render_review_badge(label=_("Без сигналов риска"), tone="good"))
        return format_html('<div class="km-admin-badges">{}</div>', format_html_join("", "{}", ((flag,) for flag in flags)))

    @admin.display(description=_("Реакции"))
    def engagement_summary(self, obj):
        balance_value = f"{int(obj.popularity_score or 0):+d}"
        return format_html(
            '<div class="km-admin-stack"><span class="km-admin-title"><i class="fas fa-thumbs-up text-warning"></i> {} · <i class="fas fa-thumbs-down text-warning"></i> {}</span><span class="km-admin-meta">{} {}</span><span class="km-admin-meta">{}</span></div>',
            int(obj.likes_count or 0),
            int(obj.dislikes_count or 0),
            _("Баланс:"),
            balance_value,
            _("Лайки и дизлайки к отзыву"),
        )

    @admin.display(description=_("Создан"))
    def created_at_display(self, obj):
        return obj.created_at

    @admin.display(description=_("Баланс реакций"))
    def popularity_score_display(self, obj):
        return obj.popularity_score

    def _build_review_form_summary(self, obj) -> dict:
        if not obj or not obj.pk:
            return {}
        
        status_label, status_tone = self._review_status(obj)
        flags = []
        if obj.contains_profanity:
            flags.append({"label": str(_("Скрытая лексика")), "tone": "warn"})
        if not self._review_has_text(obj):
            flags.append({"label": str(_("Только оценка")), "tone": "info"})
        if obj.rating <= 2:
            flags.append({"label": str(_("Низкая оценка")), "tone": "warn"})

        return {
            "is_approved": obj.is_approved,
            "status_label": status_label,
            "status_tone": status_tone,
            "author": self.display_author(obj),
            "rating": obj.rating,
            "has_text": self._review_has_text(obj),
            "likes": obj.likes_count or 0,
            "dislikes": obj.dislikes_count or 0,
            "flags": flags,
            "place_name": obj.place.name_ru or obj.place.name,
            "place_url": self._place_admin_change_url(obj),
        }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        if obj:
            context["km_review_form_summary"] = self._build_review_form_summary(obj)
            context["km_action_approve_url"] = self._review_action_url(obj, "approve")
            context["km_action_hide_url"] = self._review_action_url(obj, "hide")
            context["km_action_reject_url"] = self._review_action_url(obj, "reject")
            context["km_action_delete_url"] = self._review_delete_url(obj)
        return super().render_change_form(request, context, add, change, form_url, obj)

    def _build_review_changelist_query_string(self, request, *, clear: tuple[str, ...] = (), **updates) -> str:
        params = request.GET.copy()
        params.pop("p", None)
        for key in clear:
            params.pop(key, None)
        for key, value in updates.items():
            params.pop(key, None)
            if value not in (None, ""):
                params[key] = value
        encoded = params.urlencode()
        return f"?{encoded}" if encoded else ""

    def _review_quick_filters(self, request):
        keys = ("review_status", "risk_signal", "text_presence", "rating__exact")
        current_status = request.GET.get("review_status")
        current_risk = request.GET.get("risk_signal")
        current_text = request.GET.get("text_presence")
        current_rating = request.GET.get("rating__exact")
        return (
            {"label": _("Все отзывы"), "url": self._build_review_changelist_query_string(request, clear=keys), "active": not any((current_status, current_risk, current_text, current_rating))},
            {"label": _("Опубликованы"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="published"), "active": current_status == "published"},
            {"label": _("Скрытые"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="hidden"), "active": current_status == "hidden"},
            {"label": _("Требуют проверки"), "url": self._build_review_changelist_query_string(request, clear=keys, review_status="suspicious"), "active": current_status == "suspicious"},
            {"label": _("Только оценка"), "url": self._build_review_changelist_query_string(request, clear=keys, text_presence="only_rating"), "active": current_text == "only_rating"},
            {"label": _("Низкая оценка"), "url": self._build_review_changelist_query_string(request, clear=keys, risk_signal="low_rating"), "active": current_risk == "low_rating"},
        )

    def _review_bulk_actions(self):
        return (
            {"name": "approve_selected", "label": _("Опубликовать"), "tone": "good", "description": _("Сделать выбранные отзывы видимыми на сайте.")},
            {"name": "hide_selected", "label": _("Скрыть"), "tone": "muted", "confirm": _("Вы собираетесь скрыть {count} выбранных отзывов.\n\nОтзывы останутся в базе и их можно будет снова опубликовать.\n\nПродолжить?"), "description": _("Скрыть отзывы с сайта без удаления.")},
            {"name": "reject_selected", "label": _("Отклонить"), "tone": "warn", "confirm": _("Вы собираетесь отклонить {count} выбранных отзывов.\n\nОтзывы останутся в базе как скрытые, их можно будет позже опубликовать вручную.\n\nПродолжить?"), "description": _("Скрыть отзывы как отклонённые после модерации.")},
            {"name": "delete_selected", "label": _("Удалить"), "tone": "danger", "confirm": _("Вы собираетесь удалить {count} выбранных отзывов.\n\nЭто действие удалит отзывы из базы после стандартного экрана подтверждения Django admin.\n\nПродолжить?"), "description": _("Полное удаление отзывов из базы.")},
        )

    def get_urls(self):
        custom_urls = [
            path("<path:object_id>/approve/", self.admin_site.admin_view(self.approve_view), name="catalog_placereview_approve"),
            path("<path:object_id>/hide/", self.admin_site.admin_view(self.hide_view), name="catalog_placereview_hide"),
            path("<path:object_id>/reject/", self.admin_site.admin_view(self.reject_view), name="catalog_placereview_reject"),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "km_primary_quick_filters": self._review_quick_filters(request),
            "km_secondary_quick_filters": [],
            "review_bulk_actions": self._review_bulk_actions(),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)

    def _message_for_single_review_action(self, *, request, obj, action_key: str):
        messages_map = {
            "approve": _("Отзыв опубликован и виден на сайте."),
            "hide": _("Отзыв скрыт. Его можно снова опубликовать позже."),
            "reject": _("Отзыв отклонён и скрыт. При необходимости его можно снова опубликовать."),
        }
        self.message_user(request, messages_map[action_key], level=messages.SUCCESS)

    def _toggle_review_visibility(self, *, obj, is_approved: bool, rejected: bool = False):
        target_status = obj.STATUS_APPROVED if is_approved else (obj.STATUS_REJECTED if rejected else obj.STATUS_PENDING)
        if obj.is_approved == is_approved and obj.status == target_status:
            return False
        obj.status = target_status
        obj.is_approved = is_approved
        obj.save(update_fields=["status", "is_approved", "updated_at"])
        return True

    def approve_view(self, request, object_id):
        from django.core.exceptions import PermissionDenied
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=True)
            self._message_for_single_review_action(request=request, obj=obj, action_key="approve")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Опубликовать отзыв"),
            "action_label": _("Опубликовать"),
            "action_key": "approve",
            "description": _("Отзыв станет снова виден на сайте."),
            "object": obj,
            "opts": self.opts,
        })

    def hide_view(self, request, object_id):
        from django.core.exceptions import PermissionDenied
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=False)
            self._message_for_single_review_action(request=request, obj=obj, action_key="hide")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Скрыть отзыв"),
            "action_label": _("Скрыть"),
            "action_key": "hide",
            "description": _("Отзыв исчезнет с сайта, но останется в базе и его можно будет снова опубликовать."),
            "object": obj,
            "opts": self.opts,
        })

    def reject_view(self, request, object_id):
        from django.core.exceptions import PermissionDenied
        obj = self.get_object(request, object_id)
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        if obj is None:
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        if request.method == "POST":
            self._toggle_review_visibility(obj=obj, is_approved=False, rejected=True)
            self._message_for_single_review_action(request=request, obj=obj, action_key="reject")
            return HttpResponseRedirect(reverse("admin:catalog_placereview_changelist", current_app=self.admin_site.name))
        return TemplateResponse(request, "admin/catalog/placereview/moderation_confirm.html", {
            **self.admin_site.each_context(request),
            "title": _("Отклонить отзыв"),
            "action_label": _("Отклонить"),
            "action_key": "reject",
            "description": _("Отзыв останется в базе как скрытый. Это решение можно будет изменить позже."),
            "object": obj,
            "opts": self.opts,
        })

    @admin.action(description=_("Опубликовать выбранные отзывы"))
    def approve_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=True, status=PlaceReview.STATUS_APPROVED).update(is_approved=True, status=PlaceReview.STATUS_APPROVED, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Опубликован %(count)d отзыв.", "Опубликовано %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Скрыть выбранные отзывы"))
    def hide_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=False, status=PlaceReview.STATUS_PENDING).update(is_approved=False, status=PlaceReview.STATUS_PENDING, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Скрыт %(count)d отзыв.", "Скрыто %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.action(description=_("Отклонить выбранные отзывы"))
    def reject_selected(self, request, queryset):
        updated_count = queryset.exclude(is_approved=False, status=PlaceReview.STATUS_REJECTED).update(is_approved=False, status=PlaceReview.STATUS_REJECTED, updated_at=timezone.now())
        self.message_user(
            request,
            ngettext("Отклонён %(count)d отзыв.", "Отклонено %(count)d отзыва.", updated_count) % {"count": updated_count},
            level=messages.SUCCESS if updated_count else messages.WARNING,
        )

    @admin.display(description="")
    def row_actions(self, obj):
        primary_action = render_primary_action(self._review_change_url(obj), _("Открыть"))
        visible_actions = [primary_action]
        if obj.status == obj.STATUS_PENDING or not obj.is_approved:
            visible_actions.append(render_inline_action(self._review_action_url(obj, "approve"), _("Одобрить"), "good", "fas fa-check"))
            visible_actions.append(render_inline_action(self._review_action_url(obj, "reject"), _("Отклонить"), "warn", "fas fa-ban"))
        elif obj.is_approved:
            visible_actions.append(render_inline_action(self._review_action_url(obj, "hide"), _("Скрыть"), "secondary", "fas fa-eye-slash"))
        
        menu_actions = [
            (self._place_admin_change_url(obj), _("К кружку"), "")
        ]
        
        if obj.is_approved:
            menu_actions.append((self._review_action_url(obj, "hide"), _("Скрыть"), "km-admin-action-menu__link--warn"))
        else:
            menu_actions.append((self._review_action_url(obj, "approve"), _("Опубликовать"), "km-admin-action-menu__link--good"))
            menu_actions.append((self._review_action_url(obj, "reject"), _("Отклонить"), "km-admin-action-menu__link--warn"))
            
        menu_actions.append((self._review_delete_url(obj), _("Удалить"), "km-admin-action-menu__link--danger"))
        
        menu_html = render_action_menu(menu_actions)
        return render_row_actions_container(format_html_join(" ", "{}", ((item,) for item in visible_actions)), menu_html)


@admin.register(SiteReview)
class SiteReviewAdmin(admin.ModelAdmin):
    list_display = ("display_author", "rating", "status", "is_approved", "likes_count", "dislikes_count", "contains_profanity", "created_at")
    list_filter = ("status", "is_approved", "rating", "contains_profanity", "created_at")
    search_fields = ("author_name", "text")
    readonly_fields = ("likes_count", "dislikes_count", "contains_profanity", "created_at", "updated_at", "session_key")
    fieldsets = (
        (_("Отзыв"), {"fields": ("user", "author_name", "rating", "text")}),
        (_("Модерация"), {"fields": ("status", "is_approved", "rejection_reason", "contains_profanity")}),
        (_("Реакции"), {"fields": ("likes_count", "dislikes_count")}),
        (_("Служебное"), {"classes": ("collapse",), "fields": ("session_key", "created_at", "updated_at")}),
    )

    @admin.display(description=_("Автор"))
    def display_author(self, obj):
        return obj.author_name or _("Без имени")
