"""Login-protected workflow inbox; state changes are POST-only."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from catalog.models import WorkflowNotification
from catalog.services import business_team


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


@login_required
@require_GET
def inbox(request):
    items = list(_mine(request.user).order_by('-created_at', '-pk')[:100])
    from catalog.services.workflow_notifications import _invitation_current, _join_confirmation_current
    from catalog.models import OrganizationPlaceRequest
    join_ids = [item.entity_id for item in items if item.event_kind == 'join_confirmation']
    joins = {row.pk: row for row in OrganizationPlaceRequest.objects.filter(pk__in=join_ids)}
    for item in items:
        item.can_accept = item.event_kind == 'team_invitation' and _invitation_current(item, (request.user.email or '').strip().lower(), timezone.now())
        item.join_action_url = ''
        if item.event_kind == 'join_confirmation' and item.entity_id in joins and _join_confirmation_current(item):
            item.join_action_url = reverse('organization_workspace_confirm', args=[joins[item.entity_id].organization_id, item.entity_id])
    return render(request, 'pages/account_notifications.html', {'notifications': items})


@login_required
@require_POST
def mark_read(request, notification_id):
    item = get_object_or_404(_mine(request.user), pk=notification_id)
    if item.read_at is None:
        item.read_at = timezone.now()
        item.save(update_fields=['read_at'])
    return redirect('account_notifications')


@login_required
@require_POST
def accept_invitation(request, notification_id):
    item = get_object_or_404(_mine(request.user), pk=notification_id, event_kind='team_invitation')
    target_type = {'place_team_invitation': 'place', 'organization_team_invitation': 'organization'}.get(item.entity_type)
    if not target_type:
        raise PermissionDenied
    try:
        business_team.accept(actor=request.user, target_type=target_type, invitation_id=item.entity_id)
    except (ValidationError, business_team.TeamConflict, PermissionDenied, business_team.OwnerTeamInvitation.DoesNotExist, business_team.OrganizationTeamInvitation.DoesNotExist):
        return HttpResponseForbidden()
    return redirect('account_notifications')
