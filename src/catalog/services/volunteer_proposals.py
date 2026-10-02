"""Volunteer-scoped entrypoints for the shared publication and affiliation services."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from catalog.models import OrganizationPlaceRequest, VolunteerPlaceRevision
from catalog.services import publication, organization_ownership
from catalog.services.staff_roles import can_use_volunteer_workspace


def _volunteer(actor):
    actor = publication.fresh_actor(actor)
    if not can_use_volunteer_workspace(actor):
        raise PermissionDenied
    return actor


def get_candidate(*, actor, revision_id):
    actor = _volunteer(actor)
    revision = get_object_or_404(VolunteerPlaceRevision, pk=revision_id, author_id=actor.pk)
    kind, pk = publication._kind(revision)
    target = publication.locked_target(kind, pk) if transaction.get_connection().in_atomic_block else publication.TARGETS[kind].objects.get(pk=pk)
    if not publication.volunteer_can_author(actor, target, kind):
        raise PermissionDenied
    return revision


def propose(*, actor, kind, target_id, patch, expected_version, revision_version=0,
            submit=True, schema_version=publication.SCHEMA_VERSION):
    actor = _volunteer(actor)
    if kind not in publication.TARGETS:
        raise ValidationError('Unknown proposal target.')
    return publication.propose(actor=actor, target_type=kind, target_id=target_id,
        patch=patch, schema_version=schema_version, expected_version=expected_version,
        revision_version=revision_version, submit=submit, explicit_save=False)


def review(*, actor, revision_id, version, action, reason):
    if action not in {'approve', 'return', 'reject'}:
        raise ValidationError('Unknown review action.')
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError('Review reason required.')
    return publication.review(actor=actor, revision_id=revision_id, version=version,
        approve=action == 'approve', note=reason, final_reject=action == 'reject')


def submit_informational_link(*, actor, place_id, organization_id):
    actor = _volunteer(actor)
    return organization_ownership.request_join(actor=actor, place_id=place_id,
        organization_id=organization_id, relationship_kind='informational')


@transaction.atomic
def review_informational_link(*, actor, request_id, action, reason, expected_place_version):
    actor = organization_ownership._reviewer(actor)
    if action not in {'approve', 'return', 'reject'} or not isinstance(reason, str) or not reason.strip():
        raise ValidationError('Review action and reason required.')
    item, place, org = organization_ownership._locked_join(request_id)
    if item.relationship_kind != 'informational' or item.status != 'pending':
        raise ValidationError('Informational request is not pending.')
    if not isinstance(expected_place_version, int) or place.content_version != expected_place_version:
        raise ValidationError('Place version conflict.')
    if action == 'approve':
        result = organization_ownership.approve_informational_join(actor=actor, request_id=request_id)
        result.note = reason.strip()
        result.save(update_fields=['note'])
        return result
    from django.utils import timezone
    item.status = 'canceled' if action == 'return' else 'rejected'
    item.note = reason.strip()
    item.decided_by = actor
    item.decided_at = timezone.now()
    item.save(update_fields=['status', 'note', 'decided_by', 'decided_at'])
    from catalog.services.workflow_notifications import emit
    emit(kind='affiliation_decision', entity_type='organization_place_request', entity_id=item.pk, version=1, recipient_user=item.requested_by)
    return item


def get_target(*, actor, kind, target_id):
    actor = _volunteer(actor)
    if kind not in publication.TARGETS:
        raise ValidationError('Unknown proposal target.')
    target = get_object_or_404(publication.TARGETS[kind], pk=target_id)
    if not publication.volunteer_can_author(actor, target, kind):
        raise PermissionDenied
    revision = VolunteerPlaceRevision.objects.filter(**{kind: target}).first()
    if revision and revision.author_id != actor.pk:
        raise PermissionDenied
    return target, revision


@transaction.atomic
def create_and_propose(*, actor, kind, parent_id=None, patch, submit=False):
    actor = _volunteer(actor)
    if kind not in {'organization', 'program', 'activity', 'offering_group'}:
        raise ValidationError('Unsupported volunteer create target.')
    if not isinstance(patch, dict) or not set(patch) <= publication.fields_for(kind):
        raise ValidationError('Unknown/protected proposal fields.')
    name = patch.get('name_az', '')
    if not isinstance(name, str) or (submit and not name.strip()):
        raise ValidationError('Azerbaijani name required for submission.')
    if kind == 'organization':
        from catalog.models import Organization
        from catalog.services.organization_ownership import create_organization
        target = (create_organization(actor=actor, values={'name_az': name.strip()})
            if name.strip() else Organization.objects.create(created_by=actor, owner=None))
    elif kind == 'program':
        from catalog.models import Organization, Program
        org = get_object_or_404(Organization, pk=parent_id)
        if not publication.volunteer_can_author(actor, org, 'organization'):
            raise PermissionDenied
        if name.strip() and Program.objects.filter(organization=org, name_az__iexact=name.strip(), archived_at__isnull=True).exists():
            raise ValidationError('Program with this name already exists in the organization.')
        target = Program.objects.create(organization=org, created_by=actor, name_az=name.strip())
    elif kind == 'activity':
        from catalog.models import Place, Activity
        place = get_object_or_404(Place, pk=parent_id)
        if not publication.volunteer_can_author(actor, place, 'place'):
            raise PermissionDenied
        target = Activity.objects.create(place=place, name_az=name.strip())
    else:
        from catalog.models import Activity, OfferingGroup
        activity = get_object_or_404(Activity, pk=parent_id)
        if not publication.volunteer_can_author(actor, activity, 'activity'):
            raise PermissionDenied
        target = OfferingGroup.objects.create(activity=activity, name_az=name.strip())
    return propose(actor=actor, kind=kind, target_id=target.pk, patch=patch,
        expected_version=target.content_version, revision_version=0, submit=submit)


def own_proposal_rows(actor):
    from django.urls import reverse
    from catalog.services.moderation_hub import kind_label, status_label
    if not can_use_volunteer_workspace(actor):
        raise PermissionDenied
    rows = []
    revisions = VolunteerPlaceRevision.objects.filter(author_id=actor.pk).select_related(
        'organization', 'program__organization', 'activity__place', 'offering_group__activity__place')
    for revision in revisions:
        kind, pk = publication._kind(revision)
        if kind == 'place':
            continue  # Existing Place dashboard already renders these cards.
        target = getattr(revision, kind)
        if not publication.volunteer_can_author(actor, target, kind):
            continue
        rows.append({'kind': kind, 'status': revision.status, 'kind_label': kind_label(kind), 'status_label': status_label(revision.status), 'name': revision.payload.get('name_az')
            or getattr(target, 'name_az', '') or f'#{pk}',
            'summary': revision.payload.get('description_az') or revision.review_note,
            'url': reverse('admin:volunteer_proposal_edit', args=[kind, pk]),
            'child_url': (reverse('admin:volunteer_proposal_add', args=['program']) + f'?parent_id={pk}') if kind == 'organization'
                else (reverse('admin:volunteer_proposal_add', args=['offering_group']) + f'?parent_id={pk}') if kind == 'activity' else '',
            'child_label': kind_label('program') if kind == 'organization' else kind_label('offering_group') if kind == 'activity' else '',
            'updated_at': revision.updated_at})
    for item in OrganizationPlaceRequest.objects.filter(requested_by_id=actor.pk, relationship_kind='informational').select_related('place', 'organization'):
        rows.append({'kind': 'affiliation', 'status': item.status, 'kind_label': kind_label('affiliation'), 'status_label': status_label(item.status), 'name': f"{item.place} → {item.organization.name_az or item.organization.name_ru or item.organization.name_en or ('#' + str(item.organization_id))}",
            'summary': item.note, 'url': reverse('admin:volunteer_affiliation_add'),
            'updated_at': item.created_at})
    return sorted(rows, key=lambda row: row['updated_at'], reverse=True)
