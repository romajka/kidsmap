"""Search and durable per-row operations over canonical ownership transitions.

No direct affiliation writes or role-based business bypass. Receipts contain
only IDs/version snapshots/codes, never copies of private display fields.
"""
import hashlib
import json
import logging
import uuid
from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import get_language

from catalog.models import (Activity, Organization, OrganizationConnectionItem,
    OrganizationConnectionOperation, OrganizationPlaceRequest, Place, Program,
    VolunteerPlaceRevision, OrganizationGrant, OwnerTeamMembership, OfferingGroup, PricingPlan)
from catalog.services import business_team, organization_ownership as ownership

logger = logging.getLogger(__name__)
EXECUTABLE = frozenset({'connected', 'requested', 'waiting_owner', 'already_connected', 'detached', 'already_detached'})
PAGE_SIZE = 20
MAX_ITEMS = 100


def _uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError('Invalid operation key.', code='invalid_key')


def _ids(value):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_ITEMS or any(
        not isinstance(pk, int) or isinstance(pk, bool) or pk < 1 for pk in value
    ) or len(set(value)) != len(value):
        raise ValidationError('Select 1–100 unique place IDs.', code='invalid_ids')
    return sorted(value)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def visible_places(actor):
    """Public detail visibility or the existing business place.view resolver."""
    actor = ownership._actor(actor)
    return ownership.join_visible_places(actor=actor)


def organization_visible(actor, org):
    return (org.status == 'published' and org.archived_at is None) or business_team.has_action(
        user=actor, target=org, action='organization.view')


def organization_name(org):
    language=(get_language() or 'az').split('-')[0]
    return getattr(org,'name_'+language,'') or org.name_az or org.name_ru or org.name_en or f'#{org.pk}'


def _snapshot(place, org):
    activities = list(Activity.objects.filter(place=place).order_by('pk').values(
        'id', 'content_version', 'program_id', 'archived_at', 'status', 'source_program_id', 'source_program_version', 'program_snapshot'))
    programs = list(Program.objects.filter(pk__in=[a['program_id'] for a in activities if a['program_id']]).order_by('pk').values(
        'id', 'organization_id', 'content_version', 'archived_at', 'status', 'approved_at'))
    requests = list(OrganizationPlaceRequest.objects.filter(place=place).order_by('pk').values(
        'id', 'organization_id', 'relationship_kind', 'status', 'base_place_ownership_version',
        'base_organization_ownership_version', 'base_place_content_version', 'base_place_owner_id',
        'base_organization_owner_id', 'place_owner_confirmed_at', 'organization_owner_confirmed_at'))
    revisions=list(VolunteerPlaceRevision.objects.filter(Q(place=place)|Q(organization=org)|Q(program_id__in=[p['id'] for p in programs])|Q(activity__place=place)).order_by('pk').values('id','version','status'))
    grants=list(OrganizationGrant.objects.filter(organization=org).order_by('pk').values('id','version','is_active','base_ownership_version','scope','actions'))
    direct=list(OwnerTeamMembership.objects.filter(place=place).order_by('pk').values('id','version','is_active','base_ownership_version','actions'))
    groups=list(OfferingGroup.objects.filter(activity__place=place).order_by('pk').values('id','content_version','archived_at'))
    prices=list(PricingPlan.objects.filter(Q(place=place)|Q(offering_group__activity__place=place)).order_by('pk').values('id','updated_at'))
    selections=list(OrganizationGrant.selected_places.through.objects.filter(organizationgrant__organization=org).order_by('pk').values_list('organizationgrant_id','place_id'))
    return {'place': [place.owner_id, place.ownership_version, place.content_version, place.organization_id,
        place.organization_relationship_kind, place.organization_join_place_ownership_version,
        place.organization_join_org_ownership_version, str(place.deleted_at)],
        'organization': [org.owner_id, org.ownership_version, org.content_version, str(org.archived_at)],
        'dependencies': _hash([activities, programs, revisions, grants, direct,groups,prices,selections]), 'requests': _hash(requests)}


@transaction.atomic
def detach_access(*, actor, place_id, organization_id, expected_ownership_version=None):
    """Canonical mutation authority, without granting visibility or changing a link."""
    actor = ownership._actor(actor)
    place, org = ownership._link_parents(place_id, organization_id, allow_archived=True)
    ownership._side_owner(actor, place, org)
    if expected_ownership_version is not None and place.ownership_version != ownership._version(expected_ownership_version):
        raise ValidationError('Stale ownership version.')
    if place.organization_id is None:
        if actor.pk != place.owner_id and not OrganizationPlaceRequest.objects.filter(
            place=place, organization=org, status='approved').exists():
            raise PermissionDenied
    elif place.organization_id != org.pk:
        raise ValidationError('Affiliation target mismatch.')
    return actor, place, org


def _decision(actor, place, org, kind, action='connect'):
    if action == 'detach':
        if actor.pk not in (place.owner_id, org.owner_id): return 'no_rights'
        if place.deleted_at is not None: return 'unavailable'
        if place.organization_id is None:
            if actor.pk != place.owner_id and not OrganizationPlaceRequest.objects.filter(place=place,organization=org,status='approved').exists(): return 'no_rights'
            return 'already_detached'
        if place.organization_id != org.pk: return 'other_network'
        for activity in Activity.objects.filter(place=place, program__isnull=False).select_related('program'):
            program = activity.program
            if program.status == 'published' and program.approved_at is not None: continue
            if (not activity.program_snapshot and (program.approved_at is not None or activity.status == 'published')) or (activity.program_snapshot and not activity.source_program_version):
                return 'manual_review'
        return 'detached'
    if org.archived_at is not None: return 'archived'
    if kind == 'business':
        if actor.pk not in (place.owner_id, org.owner_id): return 'no_rights'
        if place.owner_id is None or org.owner_id is None: return 'owner_required'
    else:
        try: ownership._reviewer(actor)
        except PermissionDenied: return 'no_rights'
    if place.organization_id not in (None, org.pk): return 'other_network'
    if place.organization_id == org.pk and place.organization_relationship_kind != kind: return 'kind_conflict'
    if Activity.objects.filter(place=place, program__isnull=False).exclude(program__organization_id=org.pk).exists():
        return 'program_conflict'
    if ownership.affiliation_current(place, org): return 'already_connected'
    pending = OrganizationPlaceRequest.objects.filter(place=place, organization=org, status='pending').first()
    if pending and ownership._request_matches(pending, place, org):
        if pending.relationship_kind != kind: return 'kind_conflict'
        if pending.base_place_content_version != place.content_version: return 'manual_review'
        other_confirmed = pending.organization_owner_confirmed_at if actor.pk == place.owner_id else pending.place_owner_confirmed_at
        if kind == 'informational' or other_confirmed or place.owner_id == org.owner_id: return 'connected'
        return 'waiting_owner'
    return 'connected' if kind == 'informational' or place.owner_id == org.owner_id else 'requested'


def _row(actor, place, org, code):
    current = place.organization
    pending = OrganizationPlaceRequest.objects.filter(place=place, organization=org, status='pending').first()
    can_read_request=actor.pk in (place.owner_id,org.owner_id)
    return {'id':place.pk, 'name':place.name_i18n(), 'address':place.address, 'publication':place.get_status_display(),
        'current_organization':organization_name(current) if current and organization_visible(actor,current) else None,
        'has_organization':bool(current), 'affiliation_current':bool(current and ownership.affiliation_current(place,current)),
        'current_kind':place.organization_relationship_kind, 'code':code,
        'request_id':pending.pk if pending and can_read_request else None,
        'request_status':pending.status if pending and can_read_request else None,
        'recovery_required':bool(pending and pending.relationship_kind == 'business' and can_read_request and (not ownership._request_matches(pending,place,org) or pending.base_place_content_version != place.content_version)),
        'recovery_organization_id':org.pk if pending and can_read_request else None,
        'waiting_for':('place_owner' if not pending.place_owner_confirmed_at else 'organization_owner') if can_read_request and pending and pending.relationship_kind == 'business' else None}


def search_places(*, actor, organization_id, query='', cursor=0):
    actor = ownership._actor(actor); org = Organization.objects.get(pk=organization_id)
    try: offset = int(cursor)
    except (TypeError, ValueError): raise ValidationError('Invalid page.')
    if offset < 0: raise ValidationError('Invalid page.')
    qs = visible_places(actor).select_related('organization')
    for word in str(query).strip().split()[:10]:
        qs = qs.filter(Q(name__icontains=word) | Q(name_az__icontains=word) | Q(name_ru__icontains=word) | Q(name_en__icontains=word) | Q(address__icontains=word))
    total = qs.count(); places = list(qs.order_by('pk')[offset:offset+PAGE_SIZE])
    return {'rows':[_row(actor,p,org,_decision(actor,p,org,'business')) for p in places],
        'total':total, 'next_cursor':offset+PAGE_SIZE if offset+PAGE_SIZE<total else None}


@transaction.atomic
def _preview(*, actor, organization_id, relationship_kind, place_ids, action):
    actor = ownership._actor(actor)
    if relationship_kind not in ('business','informational'): raise ValidationError('Invalid relationship kind.')
    _ids([organization_id])
    ids = _ids(place_ids); org = Organization.objects.get(pk=organization_id)
    if action == 'detach':
        # Mutating a link does not entitle its side-owner to read a private place.
        visible = {pk:detach_access(actor=actor,place_id=pk,organization_id=org.pk)[1] for pk in ids}
    else:
        visible = {p.pk:p for p in visible_places(actor).filter(pk__in=ids)}
        if len(visible) != len(ids): raise PermissionDenied
    states = {pk:_snapshot(visible[pk],org) for pk in ids}
    operation = OrganizationConnectionOperation.objects.create(actor=actor, organization=org, action=action,
        relationship_kind=relationship_kind, expires_at=timezone.now()+timedelta(minutes=10),
        fingerprint=_hash([actor.pk, org.pk, action, relationship_kind, states]))
    OrganizationConnectionItem.objects.bulk_create([OrganizationConnectionItem(operation=operation,place_id=pk,
        snapshot=states[pk],decision=_decision(actor,visible[pk],org,relationship_kind,action)) for pk in ids])
    return operation


def preview_connections(*, actor, organization_id, relationship_kind, place_ids):
    return _preview(actor=actor, organization_id=organization_id, relationship_kind=relationship_kind, place_ids=place_ids, action='connect')


def preview_detach(*, actor, place_id, organization_id):
    place = Place.objects.get(pk=place_id)
    return _preview(actor=actor, organization_id=organization_id, relationship_kind=place.organization_relationship_kind or 'business', place_ids=[place_id], action='detach')


def _bind(actor, preview_id, key, action):
    with transaction.atomic():
        operation = OrganizationConnectionOperation.objects.select_for_update().get(pk=_uuid(preview_id))
        if operation.actor_id != actor.pk: raise PermissionDenied
        if operation.action != action: raise ValidationError('Wrong operation action.')
        if operation.idempotency_key:
            if operation.idempotency_key != key: raise ValidationError('Preview already confirmed with another key.', code='key_conflict')
            return operation
        if operation.expires_at <= timezone.now(): raise ValidationError('Preview expired; review again.', code='expired')
        existing = OrganizationConnectionOperation.objects.filter(actor=actor,idempotency_key=key).first()
        if existing: raise ValidationError('Key belongs to another preview.', code='key_conflict')
        operation.idempotency_key=key;operation.status='running'
        try:
            with transaction.atomic():operation.save(update_fields=['idempotency_key','status','updated_at'])
        except IntegrityError: raise ValidationError('Key belongs to another preview.', code='key_conflict')
        return operation


def _execute_row(actor, operation, item_id):
    with transaction.atomic():
        item = OrganizationConnectionItem.objects.select_for_update().get(pk=item_id)
        if item.completed_at: return
        # Domain lock order matches the canonical transitions. No whole-batch lock.
        org = Organization.objects.select_for_update().get(pk=operation.organization_id)
        place = Place.objects.select_for_update().get(pk=item.place_id)
        program_ids = Activity.objects.filter(place=place,program__isnull=False).values_list('program_id',flat=True)
        list(Program.objects.select_for_update().filter(pk__in=program_ids).order_by('pk'))
        list(Activity.objects.select_for_update().filter(place=place).order_by('pk'))
        list(OrganizationPlaceRequest.objects.select_for_update().filter(place=place).order_by('pk'))
        fresh_actor = ownership._actor(actor)
        code = _decision(fresh_actor,place,org,operation.relationship_kind,operation.action) if operation.action == 'detach' or visible_places(fresh_actor).filter(pk=place.pk).exists() else 'unavailable'
        if code in EXECUTABLE and _snapshot(place,org) != item.snapshot: code='changed'
        request = None
        if code in EXECUTABLE and code not in ('already_connected','already_detached'):
            try:
                with transaction.atomic():
                    if operation.action == 'detach':
                        ownership.detach(actor=fresh_actor,place_id=place.pk,organization_id=org.pk,expected_ownership_version=place.ownership_version)
                        code='detached'
                    else:
                        pending = OrganizationPlaceRequest.objects.filter(place=place,organization=org,status='pending',relationship_kind=operation.relationship_kind).first()
                        if pending and ownership._request_matches(pending,place,org) and operation.relationship_kind=='business':
                            request=ownership.confirm_join(actor=fresh_actor,request_id=pending.pk)
                        else:
                            request=ownership.request_join(actor=fresh_actor,place_id=place.pk,organization_id=org.pk,relationship_kind=operation.relationship_kind)
                        if operation.relationship_kind=='informational':request=ownership.approve_informational_join(actor=fresh_actor,request_id=request.pk)
                        code='connected' if request.status=='approved' else 'requested'
            except PermissionDenied: code='no_rights'; request=None
            except ValidationError: code='manual_review'; request=None
            except Exception:
                # The inner savepoint rolls back transition and canonical outbox.
                logger.exception('Organization connection row failed', extra={'operation_id':str(operation.pk),'place_id':place.pk})
                code='failed';request=None
        item.result=code;item.request=request;item.completed_at=timezone.now()
        item.save(update_fields=['result','request','completed_at'])


def _execute(*, actor, preview_id, idempotency_key, action):
    actor = ownership._actor(actor); key=_uuid(idempotency_key)
    operation = _bind(actor,preview_id,key,action)
    if operation.status == 'completed': return operation
    for item_id in operation.items.values_list('pk',flat=True): _execute_row(actor,operation,item_id)
    with transaction.atomic():
        operation=OrganizationConnectionOperation.objects.select_for_update().get(pk=operation.pk)
        if not operation.items.filter(completed_at__isnull=True).exists():
            operation.status='completed';operation.save(update_fields=['status','updated_at'])
    return operation


def execute_connections(*, actor, preview_id, idempotency_key):
    return _execute(actor=actor,preview_id=preview_id,idempotency_key=idempotency_key,action='connect')


def execute_detach(*, actor, preview_id, idempotency_key):
    return _execute(actor=actor,preview_id=preview_id,idempotency_key=idempotency_key,action='detach')


def connection_result(*, actor, operation_id):
    actor=ownership._actor(actor);operation=OrganizationConnectionOperation.objects.get(pk=_uuid(operation_id))
    if operation.actor_id != actor.pk: raise PermissionDenied
    visible={p.pk:p for p in visible_places(actor).filter(pk__in=operation.items.values('place_id')).select_related('organization')}
    rows=[]
    for item in operation.items.select_related('request'):
        code=item.result or item.decision
        if item.place_id not in visible:
            if operation.action == 'detach':
                place = Place.objects.get(pk=item.place_id)
                decision = _decision(actor,place,operation.organization,operation.relationship_kind,'detach')
                lawful = decision in EXECUTABLE or decision == 'manual_review'
                rows.append({'id':item.place_id, 'code':code if item.completed_at or lawful else 'unavailable',
                    'complete':item.completed_at is not None, 'executable':lawful and item.decision in EXECUTABLE, 'redacted':True})
            else:
                rows.append({'id':item.place_id,'code':'unavailable'})
            continue
        place=visible[item.place_id]
        row = _row(actor,place,operation.organization,code)
        if item.request_id and actor.pk in (place.owner_id,operation.organization.owner_id):
            row.update(request_id=item.request_id,request_status=item.request.status)
        row.update(complete=item.completed_at is not None,executable=item.decision in EXECUTABLE)
        rows.append(row)
    org=operation.organization
    result={'id':str(operation.pk),'action':operation.action,'status':operation.status,'organization_id':org.pk,
        'organization_name':organization_name(org) if organization_visible(actor,org) else None,'relationship_kind':operation.relationship_kind,
        'expires_at':operation.expires_at,'rows':rows,'executable_count':sum(r.get('executable',False) for r in rows)}
    if operation.action=='detach' and operation.status!='completed' and any(r.get('redacted') and r.get('executable') for r in rows):
        result['redacted_detach'] = True
    if operation.action=='detach' and operation.status!='completed' and visible:
        place=next(iter(visible.values()))
        if actor.pk in (place.owner_id,org.owner_id):
            grants=OrganizationGrant.objects.filter(organization=org,is_active=True,base_ownership_version=org.ownership_version).filter(Q(scope='all_network')|Q(selected_places=place)).distinct()
            result['impact']={'programs':Activity.objects.filter(place=place,program__isnull=False).count(),
                'network_grants':sum(g.member.is_active and business_team._grant_current(g,org) and business_team._business_link(place,org) and bool(set(g.actions)&business_team.PLACE_BUSINESS_ACTIONS) for g in grants.select_related('member')),
                'direct_grants':sum(g.member.is_active and business_team._place_grant_current(g,place) and bool(g.get_permissions()&business_team.PLACE_BUSINESS_ACTIONS) for g in OwnerTeamMembership.objects.filter(place=place,is_active=True).select_related('member')),
                'inherited_contacts':bool(ownership.affiliation_current(place,org) and ((org.phone and not (place.phone1 or place.phone2 or place.phone3)) or (org.website and not place.website) or org.whatsapp))}
    return result
