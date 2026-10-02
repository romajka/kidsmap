"""Explicit owner confirmation of the currently saved local group conditions."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from catalog.models import VolunteerPlaceRevision
from catalog.services import business_team, publication


@require_POST
def confirm_group_conditions(request, place_id, group_id):
    if not request.user.is_authenticated:
        raise Http404
    with transaction.atomic():
        try:
            group = publication.locked_target('offering_group', group_id)
        except ValidationError:
            raise Http404
        place = group.activity.place
        if place.pk != place_id or not business_team.has_action(user=request.user, target=place, action='place.edit'):
            raise Http404
        try:
            expected = int(request.POST['expected_version'])
        except (KeyError, TypeError, ValueError):
            return HttpResponse(status=409)
        if expected != group.content_version:
            return HttpResponse(status=409)
        group_revision = VolunteerPlaceRevision.objects.select_for_update().filter(offering_group=group).first()
        place_revision = VolunteerPlaceRevision.objects.select_for_update().filter(place=place).first()
        if (group_revision and group_revision.status in ('draft', 'pending') and
                any(key.startswith('conditions_') for key in group_revision.changed_fields)):
            return HttpResponse(status=409)
        if (place_revision and place_revision.status in ('draft', 'pending') and
                'nested_pricing' in place_revision.payload):
            return HttpResponse(status=409)
        type(group).objects.filter(pk=group.pk).update(
            conditions_verified_at=timezone.now(), content_version=F('content_version') + 1,
            updated_at=timezone.now())
    return redirect('owner_place_edit', pk=place_id)
