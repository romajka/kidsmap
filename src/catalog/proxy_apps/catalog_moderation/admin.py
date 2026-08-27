from django.contrib import admin
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
        actions = {}
        for name in self.moderation_actions:
            action = self.get_action(name)
            if action is not None:
                actions[name] = action
        return actions

    @admin.action(description=_("Вернуть на доработку"))
    def return_for_revision(self, request, queryset):
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

    def get_list_display(self, request):
        columns = list(super().get_list_display(request))
        columns.insert(columns.index("engagement_summary"), "created_summary")
        return tuple(columns)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(
            status=Place.STATUS_PENDING,
            deleted_at__isnull=True,
            is_temporary=False,
        )


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

    def get_queryset(self, request):
        return super().get_queryset(request).filter(status=Specialist.STATUS_PENDING)


@admin.register(ModerationReview)
class ModerationReviewAdmin(PendingModerationAdminMixin, PlaceReviewAdmin):
    moderation_title = _("Отзывы на проверке")
    moderation_description = _("Проверьте текст, оценку, автора и связанные данные. Одобрение сделает отзыв видимым на сайте.")
    moderation_empty_title = _("Нет отзывов, ожидающих проверки")
    moderation_empty_description = _("Новые отзывы, требующие решения, появятся здесь.")
    moderation_actions = ("approve_selected", "reject_selected")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=PlaceReview.STATUS_PENDING)

admin.site.register(ModerationPlaceOwnershipRequest, PlaceOwnershipRequestAdmin)
