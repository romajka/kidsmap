"""Admin-origin, revision-bound moderation; immutable source history stays read-only."""
from django.contrib import admin, messages
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
from catalog.models import ActivityReview, EventReview, PlaceReviewResponse, SpecialistReviewResponse, ActivityReviewResponse, EventReviewResponse
from catalog.services.review_versions import type_for_head, moderate_candidate, set_review_visibility, ReviewConflict


class VersionedReviewAdminMixin:
    change_list_template = 'admin/catalog/reviews/change_list.html'
    actions = ('approve_selected', 'reject_selected', 'hide_selected')
    snapshot_salt = 'catalog.admin.review-versions.v1'

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields) + ('review_workflow_link', 'version_history')

    def get_fieldsets(self, request, obj=None):
        return (( _('Отзыв'), {'fields': ('review_workflow_link', 'version_history')}), ( _('Служебное и метрики'), {'fields': tuple(field.name for field in self.model._meta.fields)}))

    def get_actions(self, request):
        return admin.ModelAdmin.get_actions(self, request)

    def _concrete_admin(self):
        return self.admin_site._registry[self.model._meta.concrete_model]

    def _review_url(self, obj, action='workflow'):
        opts = self.model._meta.concrete_model._meta
        return reverse(f'admin:{opts.app_label}_{opts.model_name}_{action}', args=[obj.pk], current_app=self.admin_site.name)

    def _review_object(self, request, object_id):
        source = self._concrete_admin()
        obj = source.get_object(request, object_id)
        if obj is None:
            raise Http404
        if not source.has_change_permission(request, obj):
            raise PermissionDenied
        return obj

    def get_urls(self):
        prefix = f'{self.opts.app_label}_{self.opts.model_name}'
        urls = [path('<path:object_id>/workflow/', self.admin_site.admin_view(self.workflow_view), name=f'{prefix}_workflow')]
        for action in ('approve', 'reject', 'hide', 'restore'):
            urls.append(path(f'<path:object_id>/{action}/', self.admin_site.admin_view(getattr(self, action + '_view')), name=f'{prefix}_{action}'))
        return urls + super().get_urls()

    def _workflow_response(self, request, obj, *, action=None):
        return TemplateResponse(request, 'admin/catalog/reviews/workflow.html', {
            **self.admin_site.each_context(request),
            'title': _('Проверка KidsMap'), 'opts': obj._meta, 'head': obj,
            'target': getattr(obj, type_for_head(obj)[0]),
            'candidate': obj.candidate_revision if obj.candidate_revision_id and obj.candidate_revision.status == 'pending' else None,
            'current': obj.current_revision,
            'history': obj.revisions.order_by('-created_at', '-pk'),
            'review_return_url': reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_changelist'),
            'review_workflow_url': self._review_url(obj),
            'approve_url': self._review_url(obj, 'approve'), 'reject_url': self._review_url(obj, 'reject'),
            'hide_url': self._review_url(obj, 'hide'), 'restore_url': self._review_url(obj, 'restore'),
            'confirm_action': action,
        })

    def workflow_view(self, request, object_id):
        if request.method != 'GET':
            return HttpResponse(status=405, headers={'Allow': 'GET'})
        return self._workflow_response(request, self._review_object(request, object_id))

    def _decision_view(self, request, object_id, action):
        obj = self._review_object(request, object_id)
        if request.method == 'GET':
            return self._workflow_response(request, obj, action=action)
        if request.method != 'POST':
            return HttpResponse(status=405, headers={'Allow': 'GET, POST'})
        try:
            self._apply_review_action(request, obj, action, {
                'candidate': request.POST.get('revision_id'),
                'current': request.POST.get('expected_current_revision_id'),
                'visible': request.POST.get('expected_visibility'),
            })
        except (TypeError, ValueError):
            return HttpResponse(_('Invalid review version'), status=400)
        except ReviewConflict:
            return HttpResponse(_('Отзыв изменился. Обновите страницу.'), status=409)
        except PermissionError:
            raise PermissionDenied
        self.message_user(request, _('Решение сохранено.'), level=messages.SUCCESS)
        return redirect(self._review_url(obj))

    def _apply_review_action(self, request, obj, action, expected):
        if action in {'approve', 'reject'}:
            token = str(expected.get('candidate') or '')
            if not token.isascii() or not token.isdecimal() or len(token) > 32 or int(token) <= 0:
                raise ValueError('Candidate revision required')
            return moderate_candidate(head=obj, revision_id=int(token), actor=request.user,
                approve=action == 'approve', reason=request.POST.get('reason', '')[:5000])
        token = str(expected.get('current') or '')
        visible = str(expected.get('visible'))
        if not token.isascii() or not token.isdecimal() or len(token) > 32 or int(token) <= 0 or visible not in {'0', '1'}:
            raise ValueError('Visible revision and state required')
        return set_review_visibility(head=obj, revision_id=int(token), actor=request.user,
            visible=action == 'restore', expected_visible=visible == '1')

    def approve_view(self, request, object_id):
        return self._decision_view(request, object_id, 'approve')

    def reject_view(self, request, object_id):
        return self._decision_view(request, object_id, 'reject')

    def hide_view(self, request, object_id):
        return self._decision_view(request, object_id, 'hide')

    def restore_view(self, request, object_id):
        return self._decision_view(request, object_id, 'restore')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if hasattr(response, 'context_data') and response.context_data and 'cl' in response.context_data:
            rows = response.context_data['cl'].result_list
            snapshot = {str(row.pk): {'candidate': row.candidate_revision_id,
                'current': row.current_revision_id, 'visible': '1' if row.is_approved else '0'} for row in rows}
            response.context_data['review_snapshot'] = signing.dumps({
                'actor': request.user.pk, 'model': self.model._meta.concrete_model._meta.label_lower,
                'rows': snapshot}, salt=self.snapshot_salt, compress=True)
        return response

    def _bulk_review_action(self, request, queryset, action):
        try:
            snapshot = signing.loads(request.POST.get('review_snapshot', ''), salt=self.snapshot_salt, max_age=3600)
        except signing.BadSignature:
            return HttpResponse(_('Invalid review version'), status=400)
        if snapshot.get('actor') != request.user.pk or snapshot.get('model') != self.model._meta.concrete_model._meta.label_lower:
            raise PermissionDenied
        objects = list(queryset)
        ids = {str(obj.pk) for obj in objects}
        selected = set(request.POST.getlist('_selected_action'))
        if not objects or (request.POST.get('select_across') != '1' and ids != selected) or not ids.issubset(snapshot['rows']):
            return HttpResponse(_('Отзыв изменился. Обновите страницу.'), status=409)
        source = self._concrete_admin()
        # Deterministic target lock order matches submit/moderate/visibility services.
        objects.sort(key=lambda obj: (getattr(obj, type_for_head(obj)[0] + '_id'), obj.pk))
        try:
            with transaction.atomic():
                for obj in objects:
                    if not source.has_change_permission(request, obj):
                        raise PermissionDenied
                    self._apply_review_action(request, obj, action, snapshot['rows'][str(obj.pk)])
        except (TypeError, ValueError):
            return HttpResponse(_('Invalid review version'), status=400)
        except ReviewConflict:
            return HttpResponse(_('Отзыв изменился. Обновите страницу.'), status=409)
        except PermissionError:
            raise PermissionDenied
        self.message_user(request, _('Обработано отзывов: %(count)d') % {'count': len(objects)}, level=messages.SUCCESS)
        return None

    @admin.action(description=_('Одобрить'), permissions=['change'])
    def approve_selected(self, request, queryset):
        return self._bulk_review_action(request, queryset, 'approve')

    @admin.action(description=_('Отклонить'), permissions=['change'])
    def reject_selected(self, request, queryset):
        return self._bulk_review_action(request, queryset, 'reject')

    @admin.action(description=_('Скрыть'), permissions=['change'])
    def hide_selected(self, request, queryset):
        return self._bulk_review_action(request, queryset, 'hide')

    @admin.display(description=_('Модерация'))
    def review_workflow_link(self, obj):
        if not obj:
            return ''
        return format_html('<a href="{}">{}</a>', self._review_url(obj), _('Проверка KidsMap'))

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


@admin.register(ActivityReviewResponse, EventReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ('pk', 'kind', 'revision', 'created_at')
    list_filter = ('kind',)
    def has_add_permission(self, request):
        return False
    def get_readonly_fields(self, request, obj=None):
        return tuple(field.name for field in self.model._meta.fields)


@admin.register(PlaceReviewResponse, SpecialistReviewResponse)
class OfficialReviewResponseAdmin(ReviewResponseAdmin):
    def get_list_display(self, request):
        from catalog.services.staff_roles import can_moderate_review_reply
        fields = super().get_list_display(request)
        if can_moderate_review_reply(request.user, self.model):
            return (*fields, 'visibility_link')
        return fields

    def get_urls(self):
        prefix = f'{self.opts.app_label}_{self.opts.model_name}'
        routes = [
            path(f'<int:object_id>/{action}/', self.admin_site.admin_view(self.visibility_view),
                 {'action': action}, name=f'{prefix}_{action}')
            for action in ('hide', 'restore')
        ]
        return routes + super().get_urls()

    @admin.display(description=_('Публикация'))
    def visibility_link(self, obj):
        if obj.kind not in {'reply', 'hidden'}:
            return '—'
        if obj.hidden_at:
            action = 'restore'
            labels = {'ru': 'Восстановить ответ', 'az': 'Cavabı bərpa et', 'en': 'Restore reply'}
        else:
            action = 'hide'
            labels = {'ru': 'Скрыть ответ', 'az': 'Cavabı gizlət', 'en': 'Hide reply'}
        url = reverse(f'admin:catalog_{self.opts.model_name}_{action}', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, labels.get(get_language(), labels['az']))

    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        from catalog.services.staff_roles import can_moderate_review_reply
        if obj and obj.kind in {'reply', 'hidden'} and can_moderate_review_reply(request.user, self.model):
            extra_context = {**(extra_context or {}), 'response_visibility_link': self.visibility_link(obj)}
        return super().change_view(request, object_id, form_url, extra_context)

    change_form_template = 'admin/catalog/reviews/official_response_change.html'

    def visibility_view(self, request, object_id, action):
        from catalog.services.staff_roles import can_moderate_review_reply
        if not can_moderate_review_reply(request.user, self.model):
            raise PermissionDenied
        if request.method not in {'GET', 'POST'}:
            return HttpResponse(status=405, headers={'Allow': 'GET, POST'})
        hide = action == 'hide'
        url = reverse(f'admin:catalog_{self.opts.model_name}_change', args=[object_id])
        with transaction.atomic():
            queryset = self.get_queryset(request)
            if request.method == 'POST':
                queryset = queryset.select_for_update()
            obj = queryset.filter(pk=object_id, kind__in=['reply', 'hidden']).first()
            if obj is None:
                raise Http404
            reason = request.POST.get('reason', '').strip()
            status, error = 200, ''
            if request.method == 'POST':
                expected = request.POST.get('decision_at')
                decision_at = obj.moderated_at.isoformat() if obj.moderated_at else ''
                if (hide == bool(obj.hidden_at)) or (expected is not None and expected != decision_at):
                    status, error = 409, 'stale'
                elif (hide and not reason) or len(reason) > 5000:
                    status, error = 400, 'reason'
                else:
                    now = timezone.now()
                    obj.kind = 'hidden' if hide else 'reply'
                    obj.hidden_at = now if hide else None
                    obj.moderated_at = now
                    obj.moderated_by = request.user
                    obj.moderation_reason = reason or None
                    obj.save(update_fields=('kind', 'hidden_at', 'moderated_at', 'moderated_by', 'moderation_reason'))
                    self.log_change(request, obj, f'{action}: {reason}' if reason else action)
                    return redirect(url)
            return TemplateResponse(request, 'admin/catalog/reviews/official_response_visibility.html', {
                **self.admin_site.each_context(request), 'opts': self.opts, 'original': obj,
                'hide': hide, 'error': error, 'reason': reason, 'back_url': url,
                'decision_at': obj.moderated_at.isoformat() if obj.moderated_at else '',
            }, status=status)
