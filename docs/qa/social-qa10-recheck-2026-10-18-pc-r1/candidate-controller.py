"""Login-protected workflow inbox; state changes are POST-only."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language
from django.views.decorators.http import require_GET, require_POST

from catalog.models import WorkflowNotification
from catalog.services import business_team

_INVITATION_TARGET_TYPES = {
    'place_team_invitation': 'place',
    'organization_team_invitation': 'organization',
}


def _mine(user):
    current_email = (user.email or '').strip().lower()
    rows = WorkflowNotification.objects.filter(recipient_user=user).filter(Q(recipient_email='') | Q(recipient_email__iexact=current_email))
    if user.email:
        from django.contrib.auth import get_user_model
        if get_user_model().objects.filter(email__iexact=user.email, is_active=True).count() == 1:
            rows = WorkflowNotification.objects.filter(
                (Q(recipient_user=user) & (Q(recipient_email='') | Q(recipient_email__iexact=current_email)))
                | Q(recipient_user__isnull=True, recipient_email__iexact=current_email))
    return rows


def _inbox_items(user):
    items = list(_mine(user).order_by('-created_at', '-pk')[:100])
    from catalog.services.workflow_notifications import _invitation_current, _join_confirmation_current
    from catalog.models import OrganizationPlaceRequest
    join_ids = [item.entity_id for item in items if item.event_kind == 'join_confirmation']
    joins = {row.pk: row for row in OrganizationPlaceRequest.objects.filter(pk__in=join_ids)}
    for item in items:
        item.can_accept = item.event_kind == 'team_invitation' and _invitation_current(item, (user.email or '').strip().lower(), timezone.now())
        item.can_reject = item.can_accept and item.entity_type in _INVITATION_TARGET_TYPES and item.entity_version == 1
        item.join_action_url = ''
        if item.event_kind == 'join_confirmation' and item.entity_id in joins and _join_confirmation_current(item):
            item.join_action_url = reverse('organization_workspace_confirm', args=[joins[item.entity_id].organization_id, item.entity_id])
    return items


def _render_inbox(request, *, error=None, status=200):
    return render(request, 'pages/account_notifications.html', {
        'notifications': _inbox_items(request.user), 'notification_error': error,
    }, status=status)


@login_required(login_url="account_login")
@require_GET
def inbox(request):
    return _render_inbox(request)


@login_required(login_url="account_login")
@require_POST
def mark_read(request, notification_id):
    item = get_object_or_404(_mine(request.user), pk=notification_id)
    if item.read_at is None:
        item.read_at = timezone.now()
        item.save(update_fields=['read_at'])
    return redirect('account_notifications')


@login_required(login_url="account_login")
@require_POST
def accept_invitation(request, notification_id):
    item = get_object_or_404(_mine(request.user), pk=notification_id, event_kind='team_invitation')
    target_type = {'place_team_invitation': 'place', 'organization_team_invitation': 'organization'}.get(item.entity_type)
    if not target_type:
        raise PermissionDenied
    try:
        business_team.accept(actor=request.user, target_type=target_type, invitation_id=item.entity_id)
    except (ValidationError, business_team.TeamConflict, PermissionDenied, business_team.OwnerTeamInvitation.DoesNotExist, business_team.OrganizationTeamInvitation.DoesNotExist):
        return _render_inbox(request, error='invitation_unavailable', status=403)
    return redirect('account_notifications')


@login_required(login_url="account_login")
@require_POST
def reject_invitation(request, notification_id):
    item = get_object_or_404(_mine(request.user), pk=notification_id, event_kind='team_invitation')
    if (request.content_type not in ('application/x-www-form-urlencoded', 'multipart/form-data')
            or set(request.POST) - {'csrfmiddlewaretoken'} or request.FILES):
        return _render_inbox(request, error='invalid_request', status=400)
    target_type = _INVITATION_TARGET_TYPES.get(item.entity_type)
    if target_type is None:
        raise PermissionDenied
    try:
        with transaction.atomic():
            # Follow the canonical parent -> invitation lock order before checking currentness.
            parent, invitation, _, _ = business_team._locked_item(
                target_type, item.entity_id, invitation=True)
            actor = business_team._actor(request.user)
            current = get_object_or_404(_mine(actor), pk=notification_id, event_kind='team_invitation')
            from catalog.services.workflow_notifications import _invitation_current
            if (current.entity_type != item.entity_type or current.entity_id != invitation.pk
                    or current.entity_version != 1
                    or not _invitation_current(current, (actor.email or '').strip().lower(), timezone.now())):
                raise business_team.TeamConflict('Invitation no longer current.')
            business_team.decide_invitation(
                actor=actor, target_type=target_type, invitation_id=invitation.pk,
                cancel=False, expected_target_id=parent.pk)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc
    except ValidationError:
        return _render_inbox(request, error='invitation_unavailable', status=409)

    success = {
        'az': 'Dəvətdən imtina edildi.',
        'en': 'Invitation declined.',
        'ru': 'Приглашение отклонено.',
    }
    messages.success(request, success.get((get_language() or '').split('-')[0], success['ru']))
    return redirect('account_notifications')
