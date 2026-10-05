"""Staff edits use versioned moderation; historical sources are read-only."""
from django.contrib import admin
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext_lazy as _
from catalog.models import ActivityReview, EventReview, PlaceReviewResponse, SpecialistReviewResponse, ActivityReviewResponse, EventReviewResponse
from catalog.services.review_versions import type_for_head


class VersionedReviewAdminMixin:
    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields) + ('review_workflow_link', 'version_history')

    def get_fieldsets(self, request, obj=None):
        return (( _('Отзыв'), {'fields': ('review_workflow_link', 'version_history')}), ( _('Служебное и метрики'), {'fields': tuple(field.name for field in self.model._meta.fields)}))

    def get_actions(self, request):
        actions = super().get_actions(request)
        return {key: value for key, value in actions.items() if key == 'delete_selected'}

    def _toggle_review_visibility(self, **kwargs):
        raise PermissionError('Use the versioned reviewer workflow')

    def approve_view(self, request, object_id):
        return HttpResponseForbidden()

    hide_view = reject_view = approve_view

    @admin.display(description=_('Модерация'))
    def review_workflow_link(self, obj):
        if not obj:
            return ''
        kind = type_for_head(obj)[0]
        return format_html('<a href="{}">{}</a>', reverse('typed_reviews', args=[kind, getattr(obj, kind + '_id')]), _('Проверка KidsMap'))

    @admin.display(description=_('История'))
    def version_history(self, obj):
        if not obj:
            return ''
        rows = [(item.pk, item.created_at, item.status, item.rating, item.text, item.author_name, item.rejection_reason) for item in obj.revisions.order_by('created_at', 'pk')]
        return format_html('<div>{}</div>', format_html_join('', '<div><strong>#{} · {} · {} · {}/5</strong><p>{}</p><p>{}</p><p>{}</p></div>', rows))


@admin.register(ActivityReview, EventReview)
class TypedReviewAdmin(VersionedReviewAdminMixin, admin.ModelAdmin):
    list_display = ('pk', 'author_name', 'rating', 'status', 'is_current', 'review_workflow_link')
    list_filter = ('is_current', 'status')
    search_fields = ('text', 'author_name')


@admin.register(PlaceReviewResponse, SpecialistReviewResponse, ActivityReviewResponse, EventReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('pk', 'kind', 'revision', 'created_at')
    list_filter = ('kind',)
    def has_add_permission(self, request):
        return False
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)
