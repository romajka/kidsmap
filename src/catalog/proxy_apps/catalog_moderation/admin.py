from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from catalog.domain_admin.place import PlaceAdmin, EventAdmin
from catalog.domain_admin.review import PlaceReviewAdmin
from catalog.domain_admin.specialist import SpecialistAdmin
from catalog.domain_admin.owner import PlaceOwnershipRequestAdmin
from catalog.models.place import Place, Event
from catalog.models.specialist import Specialist
from catalog.models.review import PlaceReview

from .models import (
    ModerationPlace, 
    ModerationEvent, 
    ModerationReview, 
    ModerationSpecialist,
    ModerationPlaceOwnershipRequest
)


class PendingModerationAdminMixin:
    """A separate admin workspace for records waiting for a decision."""

    change_list_template = "admin/catalog/moderation/change_list.html"
    moderation_title = ""
    moderation_description = ""
    moderation_empty_title = ""
    moderation_empty_description = ""
    moderation_actions = ()

    def _source_admin(self):
        return self.admin_site._registry[self.model._meta.concrete_model]

    def has_module_permission(self, request):
        return self._source_admin().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return self._source_admin().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        return self._source_admin().has_change_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        if not self.has_change_permission(request):
            return {}
        actions = {}
        for name in self.moderation_actions:
            action = self.get_action(name)
            if action is not None:
                actions[name] = action
        return actions

    @admin.action(permissions=['change'], description=_("Вернуть на доработку"))
    def return_for_revision(self, request, queryset):
        if not self.has_change_permission(request):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        self.mark_draft(request, queryset)

    def changelist_view(self, request, extra_context=None):
        action_labels = {
            "mark_published": _("Одобрить и опубликовать"),
            "mark_rejected": _("Отклонить"),
            "return_for_revision": _("Вернуть на доработку"),
            "approve_selected": _("Одобрить"),
            "reject_selected": _("Отклонить"),
        }
        extra_context = {
            "moderation_title": self.moderation_title,
            "moderation_description": self.moderation_description,
            "moderation_empty_title": self.moderation_empty_title,
            "moderation_empty_description": self.moderation_empty_description,
            "moderation_actions": tuple(
                {"name": name, "label": action_labels[name]}
                for name in self.moderation_actions
            ),
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ModerationPlace)
class ModerationPlaceAdmin(PendingModerationAdminMixin, PlaceAdmin):
    moderation_title = _("Места на проверке")
    moderation_description = _("Проверьте данные, фото, адрес и готовность карточки перед публикацией на сайте.")
    moderation_empty_title = _("Нет мест, ожидающих проверки")
    moderation_empty_description = _("Новые места появятся здесь после отправки на модерацию.")
    moderation_actions = ("mark_published", "mark_rejected", "return_for_revision")

    def _place_view_url(self, obj):
        if getattr(getattr(obj, "volunteer_revision", None), "status", None) == "pending":
            from django.urls import reverse
            return reverse("admin:catalog_place_site_preview", args=[obj.pk], current_app=self.admin_site.name)
        return super()._place_view_url(obj)

    def _place_view_label(self, obj, public_label):
        if getattr(getattr(obj, "volunteer_revision", None), "status", None) == "pending":
            return _("Предпросмотр")
        return super()._place_view_label(obj, public_label)

    # Columns that the moderation queue folds into others: the address moves
    # under the place name, home/map marks already sit in the place cell, and
    # author + dates become one "Добавлено" cell.
    _moderation_folded_columns = ("col_location", "col_marks", "col_updated", "created_summary", "owner_display")

    def get_list_display(self, request):
        columns = [c for c in super().get_list_display(request) if c not in self._moderation_folded_columns]
        if "col_place" in columns:
            columns[columns.index("col_place")] = "moderation_place"
        if "col_actions" in columns:
            columns.insert(columns.index("col_actions"), "moderation_submitted")
        else:
            columns.append("moderation_submitted")
        return tuple(columns)

    @admin.display(description=_("Место"), ordering="name")
    def moderation_place(self, obj):
        return format_html(
            '<div class="km-mod-place">{}<div class="km-mod-place__location">{}</div></div>',
            self.col_place(obj),
            self.col_location(obj),
        )

    @admin.display(description=_("Добавлено"), ordering="created_at")
    def moderation_submitted(self, obj):
        owner = self.owner_display(obj)
        created_at = timezone.localtime(obj.created_at)
        updated_at = timezone.localtime(obj.updated_at)
        updated_html = ""
        if (updated_at - created_at).total_seconds() > 60:
            updated_html = format_html(
                '<span class="km-mod-submitted__updated">{} {}</span>',
                _("Обновл."),
                updated_at.strftime("%d.%m.%Y, %H:%M"),
            )
        return format_html(
            '<div class="km-mod-submitted">{}'
            '<span class="km-mod-submitted__date">{}</span>{}</div>',
            owner,
            created_at.strftime("%d.%m.%Y, %H:%M"),
            updated_html,
        )

    # --- Decisions with a reason: "На доработку" / "Отклонить" -------------
    @admin.action(permissions=['change'], description=_("Вернуть на доработку"))
    def return_for_revision(self, request, queryset):
        from catalog.services.place_moderation_decision import NEEDS_CHANGES
        self._decide_selected(request, queryset, NEEDS_CHANGES)

    @admin.action(permissions=['change'], description=_("Отклонить"))
    def mark_rejected(self, request, queryset):
        from catalog.services.place_moderation_decision import REJECTED
        self._decide_selected(request, queryset, REJECTED)

    def _decide_selected(self, request, queryset, decision):
        from catalog.services.permanent_place_rules import copy as t
        from catalog.services.place_moderation_decision import NEEDS_CHANGES, clean_reason, decide
        reason = request.POST.get("moderation_comment", "")
        try:
            clean_reason(reason)
        except ValidationError:
            self.message_user(request, t(
                "Укажите причину — без неё автор не поймёт, что исправить. Решение не сохранено.",
                "Səbəbi yazın — onsuz müəllif nəyi düzəltməli olduğunu bilməyəcək. Qərar saxlanmadı.",
                "Add a reason — without it the author won't know what to fix. Nothing was saved."),
                level=messages.ERROR)
            return
        done, problems = 0, []
        for place_id in queryset.values_list("pk", flat=True):
            try:
                decide(actor=request.user, place_id=place_id, decision=decision, reason=reason)
            except PermissionDenied:
                problems.append(f"#{place_id}: " + t("нет прав", "icazə yoxdur", "no permission"))
            except ValidationError as exc:
                problems.append(f"#{place_id}: " + "; ".join(exc.messages))
            else:
                done += 1
        if done:
            text = (t("На доработку отправлено: %(n)s. Автор увидит причину в кабинете и получит письмо.",
                      "Düzəlişə göndərildi: %(n)s. Müəllif səbəbi kabinetdə görəcək və məktub alacaq.",
                      "Sent back for changes: %(n)s. The author will see the reason in their account and by email.")
                    if decision == NEEDS_CHANGES else
                    t("Отклонено: %(n)s. Автор увидит причину в кабинете и получит письмо.",
                      "Rədd edildi: %(n)s. Müəllif səbəbi kabinetdə görəcək və məktub alacaq.",
                      "Declined: %(n)s. The author will see the reason in their account and by email."))
            self.message_user(request, text % {"n": done}, level=messages.SUCCESS)
        if problems:
            self.message_user(request, t("Не удалось: ", "Alınmadı: ", "Not done: ") + " · ".join(problems[:10]),
                              level=messages.WARNING)

    @admin.display(description=_("Состояние"))
    def col_state(self, obj):
        from catalog.services.permanent_place_rules import copy as t
        state = super().col_state(obj)
        if not getattr(obj, "km_list_publish_allowed", False) or obj.is_deleted:
            return state
        name = obj.name_i18n() if callable(getattr(obj, "name_i18n", None)) else (obj.name_az or obj.name)
        revision = getattr(obj, "volunteer_revision", None)
        edits = int(bool(obj.is_public and revision is not None and revision.status == "pending"))
        return format_html(
            '{}<div class="km-mod-decide">'
            '<button type="button" class="km-mod-decide__btn km-mod-decide__btn--changes" data-km-decide="return_for_revision" '
            'data-place-id="{}" data-place-name="{}" data-edits="{}">{}</button>'
            '<button type="button" class="km-mod-decide__btn km-mod-decide__btn--reject" data-km-decide="mark_rejected" '
            'data-place-id="{}" data-place-name="{}" data-edits="{}">{}</button>'
            '</div>',
            state,
            obj.pk, name, edits, t("На доработку", "Düzəlişə", "Request changes"),
            obj.pk, name, edits, t("Отклонить", "Rədd et", "Decline"),
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = {"km_decision_dialog": _decision_dialog_copy(), **(extra_context or {})}
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        from catalog.services.moderation_queue import actionable_place_filter
        qs = super().get_queryset(request)
        return qs.filter(actionable_place_filter())


def _decision_dialog_copy():
    """All dialog text in the admin's language, plus ready-made reasons."""
    from catalog.services.permanent_place_rules import copy as t
    presets = {
        "return_for_revision": [
            (t("Фото", "Foto", "Photos"),
             t("Добавьте качественные фото места: вход, помещения, занятия. Без чужих логотипов и водяных знаков.",
               "Məkanın keyfiyyətli fotolarını əlavə edin: giriş, otaqlar, məşğələlər. Başqa loqo və su nişanı olmadan.",
               "Add good photos of the place: entrance, rooms, classes. No third-party logos or watermarks.")),
            (t("Адрес и карта", "Ünvan və xəritə", "Address and map"),
             t("Проверьте адрес и точку на карте: сейчас они не совпадают или указаны неточно.",
               "Ünvanı və xəritədəki nöqtəni yoxlayın: hazırda uyğun gəlmir və ya dəqiq deyil.",
               "Check the address and the map pin: they don't match or aren't precise.")),
            (t("Описание", "Təsvir", "Description"),
             t("Расширьте описание: чем занимаются дети, для какого возраста, как проходят занятия.",
               "Təsviri genişləndirin: uşaqlar nə ilə məşğul olur, hansı yaş üçündür, dərslər necə keçir.",
               "Expand the description: what children do, for which ages, how classes run.")),
            (t("Контакты и расписание", "Əlaqə və cədvəl", "Contacts and schedule"),
             t("Укажите рабочий телефон и актуальное расписание занятий.",
               "İşlək telefon nömrəsini və aktual dərs cədvəlini göstərin.",
               "Add a working phone number and the current class schedule.")),
            (t("Цены", "Qiymətlər", "Prices"),
             t("Уточните цены: стоимость разового занятия или абонемента.",
               "Qiymətləri dəqiqləşdirin: birdəfəlik dərsin və ya abonementin dəyəri.",
               "Clarify prices: the cost of a single class or a membership.")),
        ],
        "mark_rejected": [
            (t("Дубликат", "Dublikat", "Duplicate"),
             t("Это место уже есть в каталоге. Чтобы управлять им, подайте заявку на владение существующей карточкой.",
               "Bu məkan artıq kataloqdadır. Onu idarə etmək üçün mövcud kart üzrə sahiblik müraciəti göndərin.",
               "This place is already in the catalog. To manage it, request ownership of the existing listing.")),
            (t("Не для детей", "Uşaqlar üçün deyil", "Not for children"),
             t("Место не относится к занятиям для детей, поэтому не может быть опубликовано в KidsMap.",
               "Məkan uşaq məşğələləri ilə bağlı deyil, ona görə KidsMap-də dərc oluna bilməz.",
               "The place isn't about children's activities, so it can't be published on KidsMap.")),
            (t("Не работает", "Fəaliyyət göstərmir", "Closed"),
             t("Место закрыто или не удалось подтвердить, что оно работает.",
               "Məkan bağlanıb və ya onun fəaliyyət göstərdiyini təsdiqləmək mümkün olmadı.",
               "The place is closed or we couldn't confirm that it operates.")),
        ],
    }
    modes = {
        "return_for_revision": {
            "title": t("Вернуть на доработку", "Düzəlişə qaytar", "Request changes"),
            "hint": t("Автор сможет исправить карточку и отправить её снова. Причину он увидит в кабинете и в письме.",
                      "Müəllif kartı düzəldib yenidən göndərə biləcək. Səbəbi kabinetdə və məktubda görəcək.",
                      "The author can fix the listing and resubmit it. They'll see the reason in their account and by email."),
            "submit": t("Вернуть на доработку", "Düzəlişə qaytar", "Request changes"),
        },
        "mark_rejected": {
            "title": t("Отклонить", "Rədd et", "Decline"),
            "hint": t("Окончательное решение: карточка не будет опубликована. Причину автор увидит в кабинете и в письме.",
                      "Son qərar: kart dərc olunmayacaq. Səbəbi müəllif kabinetdə və məktubda görəcək.",
                      "Final decision: the listing won't be published. The author will see the reason in their account and by email."),
            "submit": t("Отклонить", "Rədd et", "Decline"),
        },
    }
    selected = t("Выбрано мест", "Seçilmiş məkan", "Places selected")
    return {
        "client": {
            "modes": {key: {name: str(value) for name, value in mode.items()} for key, mode in modes.items()},
            "selected": str(selected),
            "presets": {mode: [{"label": str(a), "text": str(b)} for a, b in items] for mode, items in presets.items()},
        },
        "edits_note": t("Это правки к опубликованной карточке — версия на сайте останется без изменений.",
                        "Bu, dərc olunmuş karta düzəlişlərdir — saytdakı versiya dəyişməyəcək.",
                        "These are edits to a published listing — the version on the site stays unchanged."),
        "reason_label": t("Причина для автора", "Müəllif üçün səbəb", "Reason for the author"),
        "placeholder": t("Например: добавьте фото помещения и уточните расписание.",
                         "Məsələn: otağın fotosunu əlavə edin və cədvəli dəqiqləşdirin.",
                         "For example: add a photo of the room and update the schedule."),
        "presets_label": t("Быстрые причины", "Hazır səbəblər", "Quick reasons"),
        "cancel": t("Отмена", "Ləğv et", "Cancel"),
        "close": t("Закрыть", "Bağla", "Close"),
        "required": t("Напишите причину — без неё автор не поймёт, что исправить.",
                      "Səbəbi yazın — onsuz müəllif nəyi düzəltməli olduğunu bilməyəcək.",
                      "Write a reason — without it the author won't know what to fix."),
    }


@admin.register(ModerationEvent)
class ModerationEventAdmin(PendingModerationAdminMixin, EventAdmin):
    moderation_title = _("Мероприятия на проверке")
    moderation_description = _("Проверьте даты, программу, контакты и сведения о месте проведения до публикации мероприятия.")
    moderation_empty_title = _("Нет мероприятий, ожидающих проверки")
    moderation_empty_description = _("Отправленные на модерацию мероприятия появятся здесь.")
    moderation_actions = ("mark_published", "mark_rejected", "return_for_revision")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=Event.STATUS_PENDING, deleted_at__isnull=True)


@admin.register(ModerationSpecialist)
class ModerationSpecialistAdmin(PendingModerationAdminMixin, SpecialistAdmin):
    moderation_title = _("Специалисты на проверке")
    moderation_description = _("Проверьте профиль, специализации, документы и формат работы перед публикацией специалиста.")
    moderation_empty_title = _("Нет специалистов, ожидающих проверки")
    moderation_empty_description = _("Профили, отправленные на модерацию, будут показаны здесь.")
    moderation_actions = ("mark_published", "mark_rejected", "return_for_revision")

    @admin.action(permissions=['change'], description=_("Вернуть на доработку"))
    def return_for_revision(self, request, queryset):
        # The pending-queue mixin defines a generic version; specialists use
        # the shared one (author's draft reopened, comment + notification).
        return SpecialistAdmin.return_for_revision(self, request, queryset)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=Specialist.STATUS_PENDING)

    def get_list_display(self, request):
        from catalog.services.specialist_documents import can_review_documents
        cols = ["profile_column", "directions_column", "owner", "format_badge"]
        if self._can_review_identity(request.user):
            cols.insert(3, 'identity_review_column')
        if can_review_documents(request.user):
            cols.append("documents_count")
        cols.append("row_actions")
        return tuple(cols)

    def changelist_view(self, request, extra_context=None):
        extra_context = {
            "km_primary_quick_filters": None,
            "km_secondary_quick_filters": None,
            **(extra_context or {}),
        }
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(ModerationReview)
class ModerationReviewAdmin(PendingModerationAdminMixin, PlaceReviewAdmin):
    moderation_title = _("Отзывы на проверке")
    moderation_description = _("Проверьте текст, оценку, автора и связанные данные. Одобрение сделает отзыв видимым на сайте.")
    moderation_empty_title = _("Нет отзывов, ожидающих проверки")
    moderation_empty_description = _("Новые отзывы, требующие решения, появятся здесь.")
    moderation_actions = ("approve_selected", "reject_selected")

    def get_actions(self, request):
        from catalog.domain_admin.review_versions import VersionedReviewAdminMixin
        actions = VersionedReviewAdminMixin.get_actions(self, request)
        return {name: action for name, action in actions.items() if name in self.moderation_actions}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(is_current=True, candidate_revision__status="pending")

admin.site.register(ModerationPlaceOwnershipRequest, PlaceOwnershipRequestAdmin)
