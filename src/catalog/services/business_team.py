"""Canonical business actions and serialized team transitions.

Writers lock Organization -> Place(s) -> grant/invitation and re-read actors.
No network access comes from NULL-place legacy records or informational links.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q, F
from django.utils import timezone
from catalog.models import Place, Organization, Program, Activity, OfferingGroup, OwnerTeamMembership, OwnerTeamInvitation, OrganizationGrant, OrganizationTeamInvitation
from catalog.models.business_team import invitation_expiry
from catalog.services.place_access import (
    PLACE_BUSINESS_ACTIONS, ORGANIZATION_BUSINESS_ACTIONS, GRANTABLE_ACTIONS,
    permissions_for_role, validated_business_actions, direct_place_permissions,
)
from catalog.services.organization_ownership import _actor, _parents, affiliation_current, _version
from catalog.services.staff_roles import is_volunteer
from catalog.services.workflow_notifications import emit


class TeamConflict(ValidationError):
    pass


def _fresh(user):
    try:
        return _actor(user)
    except PermissionDenied:
        return None


def _business_link(place, org):
    return place.deleted_at is None and place.organization_relationship_kind == 'business' and affiliation_current(place, org)


def _grant_current(grant, org):
    return grant.is_active and grant.owner_id == org.owner_id and grant.base_ownership_version == org.ownership_version


def _place_grant_current(grant, place):
    return grant.is_active and grant.owner_id == (place.owner_id or place.created_by_id) and (grant.base_ownership_version is None or grant.base_ownership_version == place.ownership_version)


def platform_has_action(*, user, action):
    user = _fresh(user)
    if user is None or not user.is_staff:
        return False
    permission = {'place.publish':'catalog.change_place', 'place.reviews.moderate':'catalog.change_placereview'}.get(action)
    return permission is not None and (user.is_superuser or user.has_perm(permission))


def has_action(*, user, target, action):
    user = _fresh(user)
    if user is None or not isinstance(action, str):
        return False
    if isinstance(target, (Activity, OfferingGroup)):
        current = type(target).objects.filter(pk=target.pk, archived_at__isnull=True).first()
        if current is None:
            return False
        if isinstance(current, OfferingGroup) and current.activity.archived_at is not None:
            return False
        target = current.place if isinstance(current, Activity) else current.activity.place
    if isinstance(target, Program):
        current = Program.objects.filter(pk=target.pk, archived_at__isnull=True).first()
        if current is None or action != 'program.manage':
            return False
        target = Organization.objects.filter(pk=current.organization_id).first()
    if isinstance(target, Place):
        place = Place.objects.filter(pk=target.pk, deleted_at__isnull=True).first()
        if place is None:
            return False
        if action in ('place.publish', 'place.reviews.moderate'):
            return platform_has_action(user=user, action=action)
        if action not in PLACE_BUSINESS_ACTIONS | {'place.team.manage','ownership.transfer'}:
            return False
        if action in direct_place_permissions(user=user, place=place) or (action == 'ownership.transfer' and place.owner_id == user.pk):
            return True
        if action not in PLACE_BUSINESS_ACTIONS:
            return False
        for grant in OwnerTeamMembership.objects.filter(place=place, member=user, is_active=True):
            if _place_grant_current(grant, place) and action in grant.get_permissions():
                return True
        org = Organization.objects.filter(pk=place.organization_id, archived_at__isnull=True).first()
        if org is None or not _business_link(place, org):
            return False
        if org.owner_id == user.pk:
            return True
        for grant in OrganizationGrant.objects.filter(organization=org, member=user, is_active=True):
            if not _grant_current(grant, org) or action not in validated_business_actions(grant.actions):
                continue
            if grant.scope == 'all_network' or (grant.scope == 'selected_places' and grant.selected_places.filter(pk=place.pk).exists()):
                return True
        return False
    if isinstance(target, Organization):
        org = Organization.objects.filter(pk=target.pk, archived_at__isnull=True).first()
        if org is None or action not in ORGANIZATION_BUSINESS_ACTIONS | {'organization.team.manage','ownership.transfer'}:
            return False
        if org.owner_id == user.pk:
            return True
        if action not in ORGANIZATION_BUSINESS_ACTIONS:
            return False
        return any(_grant_current(g, org) and action in validated_business_actions(g.actions) for g in OrganizationGrant.objects.filter(organization=org, member=user, is_active=True))
    return False


def accessible_place_ids(*, user, action='place.view'):
    user = _fresh(user)
    if user is None:
        return []
    # Candidate IDs are not authorization: every result passes the same resolver.
    candidates = Place.objects.filter(
        Q(owner=user) | Q(owner__isnull=True, created_by=user) |
        Q(team_memberships__member=user, team_memberships__is_active=True) |
        Q(organization__owner=user) | Q(organization__team_grants__member=user, organization__team_grants__is_active=True),
        deleted_at__isnull=True).distinct()
    return [p.pk for p in candidates if has_action(user=user, target=p, action=action)]


def _owner(actor, parent):
    actor = _actor(actor)
    owner_id = parent.owner_id or (parent.created_by_id if isinstance(parent, Place) else None)
    if owner_id != actor.pk:
        raise PermissionDenied
    return actor


def _models(target_type):
    if target_type == 'place':
        return OwnerTeamMembership, OwnerTeamInvitation, 'place'
    if target_type == 'organization':
        return OrganizationGrant, OrganizationTeamInvitation, 'organization'
    raise ValidationError('Unknown team target.')


def _actions(value, role, target_type):
    if role not in ('EDITOR','MANAGER','MODERATOR'):
        raise ValidationError('Unknown preset.')
    value = sorted(permissions_for_role(role)) if value is None else value
    valid = validated_business_actions(value, target_type=target_type)
    if not isinstance(value, list) or len(value) != len(valid):
        raise ValidationError('Unknown, duplicate or forbidden business action.')
    return sorted(valid)


def _scope(org, scope, place_ids, actions):
    if scope not in ('selected_places','all_network') or not isinstance(place_ids, list) or any(not isinstance(pk,int) or isinstance(pk,bool) or pk < 1 for pk in place_ids) or len(place_ids) != len(set(place_ids)):
        raise ValidationError('Invalid scope.')
    if scope == 'all_network':
        if place_ids:
            raise ValidationError('All-network scope cannot contain selected places.')
        return {}
    if not place_ids and set(actions) & PLACE_BUSINESS_ACTIONS:
        raise ValidationError('Select at least one place.')
    places = list(Place.objects.select_for_update().filter(pk__in=place_ids).order_by('pk'))
    if len(places) != len(place_ids) or any(not _business_link(p,org) for p in places):
        raise ValidationError('Selected places must be current business branches.')
    return {str(p.pk): p.ownership_version for p in places}


def _grant_for_email(model, field, parent, email):
    return model.objects.filter(**{field:parent, 'member__email__iexact':email}).first()


@transaction.atomic
def invite(*, actor, target_type, target_id, email, role='EDITOR', actions=None, scope='selected_places', place_ids=None):
    grant_model, invite_model, field = _models(target_type)
    parent = _parents(target_type,target_id);actor = _owner(actor,parent)
    if not isinstance(email,str):
        raise ValidationError('Email required.')
    email=email.strip().lower();validate_email(email)
    if email == actor.email.strip().lower():
        raise ValidationError('Cannot invite owner.')
    actions = _actions(actions,role,target_type)
    if target_type == 'place':
        if scope != 'selected_places' or place_ids not in (None,[],[parent.pk]):
            raise ValidationError('Place team is concrete-place only.')
        snapshot = None
    else:
        place_ids = [] if place_ids is None else place_ids
        snapshot = _scope(parent,scope,place_ids,actions)
    old = _grant_for_email(grant_model,field,parent,email)
    pending=invite_model.objects.filter(**{field:parent,'email':email,'status':'PENDING'}).first()
    if pending:
        if pending.expires_at is not None and pending.expires_at > timezone.now() and pending.base_ownership_version == parent.ownership_version:
            raise TeamConflict('Pending invitation exists; cancel before replacing.')
        invite_model.objects.filter(pk=pending.pk).update(status='CANCELED',responded_at=timezone.now())
    values={field:parent,'owner':actor,'email':email,'role':role,'actions':actions,'base_ownership_version':parent.ownership_version,'base_grant_version':old.version if old else None,'expires_at':invitation_expiry()}
    if target_type == 'place':
        values['invited_by']=actor
    else:
        values.update(scope=scope,selected_place_ids=sorted(place_ids),scope_snapshot=snapshot)
    item = invite_model.objects.create(**values)
    emit(kind="team_invitation", entity_type=f"{target_type}_team_invitation", entity_id=item.pk, version=1, recipient_email=email)
    return item


def _locked_item(target_type, item_id, invitation=False, expected_target_id=None):
    grant_model, invite_model, field = _models(target_type)
    model = invite_model if invitation else grant_model
    anchor = model.objects.filter(pk=item_id).values(field+'_id').first()
    if anchor is None:
        raise model.DoesNotExist
    if expected_target_id is not None and anchor[field+'_id'] != expected_target_id:
        raise PermissionDenied
    if anchor[field+'_id'] is None:
        raise ValidationError('Unscoped legacy row cannot authorize.')
    parent = _parents(target_type,anchor[field+'_id'])
    item = model.objects.select_for_update().get(pk=item_id)
    if expected_target_id is not None and parent.pk != expected_target_id:
        raise PermissionDenied
    if getattr(item,field+'_id') != parent.pk:
        raise TeamConflict('Target changed.')
    return parent,item,grant_model,field


@transaction.atomic
def accept(*, actor, target_type, invitation_id, expected_target_id=None):
    parent,item,grant_model,field = _locked_item(target_type,invitation_id,invitation=True,expected_target_id=expected_target_id)
    actor = _actor(actor)
    if not actor.email or actor.email.strip().lower() != item.email.lower():
        raise PermissionDenied
    if item.status != 'PENDING' or item.expires_at is None or item.expires_at <= timezone.now():
        raise ValidationError('Invitation unavailable or expired.')
    if item.owner_id != (parent.owner_id or (parent.created_by_id if isinstance(parent,Place) else None)) or item.base_ownership_version != parent.ownership_version or actor.pk == item.owner_id:
        raise TeamConflict('Invitation ownership is stale.')
    actions = _actions(item.actions,item.role,target_type)
    if target_type == 'organization':
        if _scope(parent,item.scope,item.selected_place_ids,actions) != item.scope_snapshot:
            raise TeamConflict('Invitation selected scope changed.')
    grant = grant_model.objects.filter(**{field:parent,'member':actor}).first()
    if (grant.version if grant else None) != item.base_grant_version:
        raise TeamConflict('Grant changed since invitation.')
    values={'owner_id':item.owner_id,'role':item.role,'actions':actions,'base_ownership_version':parent.ownership_version,'is_active':True,'version':grant.version+1 if grant else 1}
    if target_type == 'organization':
        values['scope']=item.scope
    else:
        values['invited_by_id']=item.invited_by_id
    grant,_=grant_model.objects.update_or_create(**{field:parent,'member':actor},defaults=values)
    if target_type == 'organization':
        grant.selected_places.set(item.selected_place_ids)
    item.status='ACCEPTED';item.invited_user=actor;item.responded_at=timezone.now();item.save(update_fields=['status','invited_user','responded_at','updated_at'])
    emit(kind='team_invitation_decision', entity_type=f'{target_type}_team_invitation', entity_id=item.pk, version=2, recipient_user=item.owner)
    return grant


@transaction.atomic
def decide_invitation(*, actor, target_type, invitation_id, cancel=False, expected_target_id=None):
    parent,item,_,_ = _locked_item(target_type,invitation_id,invitation=True,expected_target_id=expected_target_id)
    actor = _owner(actor,parent) if cancel else _actor(actor)
    if not cancel and (not actor.email or actor.email.strip().lower() != item.email.lower()):
        raise PermissionDenied
    if item.status != 'PENDING':
        raise TeamConflict('Invitation already handled.')
    item.status = 'CANCELED' if cancel else 'REJECTED';item.responded_at=timezone.now();item.save(update_fields=['status','responded_at','updated_at'])
    if not cancel:
        emit(kind='team_invitation_decision', entity_type=f'{target_type}_team_invitation', entity_id=item.pk, version=2, recipient_user=item.owner)
    return item


@transaction.atomic
def change_grant(*, actor, target_type, grant_id, expected_version, active=None, role=None, actions=None, scope=None, place_ids=None, expected_target_id=None):
    parent,grant,_,_ = _locked_item(target_type,grant_id,expected_target_id=expected_target_id);_owner(actor,parent)
    if grant.version != _version(expected_version):
        raise TeamConflict('Stale grant version.')
    if active is not None and not isinstance(active,bool):
        raise ValidationError('Active must be boolean.')
    if active is True and not grant.is_active:
        raise ValidationError('Suspended team needs explicit confirmation.')
    if grant.owner_id != (parent.owner_id or (parent.created_by_id if isinstance(parent,Place) else None)) or (grant.base_ownership_version is not None and grant.base_ownership_version != parent.ownership_version):
        raise TeamConflict('Grant owner changed; explicit confirmation required.')
    if role is not None or actions is not None:
        grant.actions=_actions(actions,role or grant.role,target_type);grant.role=role or grant.role
    if target_type == 'place' and (scope is not None or place_ids is not None):
        raise ValidationError('Place grants cannot become network grants.')
    if target_type == 'organization' and (scope is not None or place_ids is not None or actions is not None):
        ids=list(grant.selected_places.values_list('pk',flat=True)) if place_ids is None else place_ids
        grant.scope=scope or grant.scope;_scope(parent,grant.scope,ids,grant.actions);grant.selected_places.set(ids)
    if active is not None:
        grant.is_active=active
    grant.version+=1;grant.save()
    if active is False:
        emit(kind="access_disabled", entity_type=f"{target_type}_team_grant", entity_id=grant.pk, version=grant.version, recipient_user=grant.member)
    return grant


@transaction.atomic
def leave(*, actor, target_type, grant_id, expected_target_id=None):
    _,grant,_,_ = _locked_item(target_type,grant_id,expected_target_id=expected_target_id);actor=_actor(actor)
    if actor.pk != grant.member_id:
        raise PermissionDenied
    if grant.is_active:
        grant.is_active=False;grant.version+=1;grant.save(update_fields=['is_active','version','updated_at'])
        emit(kind='access_disabled', entity_type=f'{target_type}_team_grant', entity_id=grant.pk, version=grant.version, recipient_user=grant.member)
    return grant


def suspended(*, actor, target_type, target_id):
    grant_model,_,field = _models(target_type)
    with transaction.atomic():
        parent = _parents(target_type,target_id);_owner(actor,parent)
        return list(grant_model.objects.filter(**{field:parent,'is_active':False}).order_by('pk'))


@transaction.atomic
def confirm_member(*, actor, target_type, grant_id, expected_version, expected_target_id=None):
    parent,grant,_,_ = _locked_item(target_type,grant_id,expected_target_id=expected_target_id);actor=_owner(actor,parent)
    if grant.version != _version(expected_version):
        raise TeamConflict('Stale grant version.')
    member = _fresh(grant.member)
    if member is None or member.pk == actor.pk:
        raise ValidationError('Invalid employee account.')
    _actions(grant.actions,grant.role,target_type)
    if target_type == 'organization':
        _scope(parent,grant.scope,list(grant.selected_places.values_list('pk',flat=True)),grant.actions)
    grant.owner=actor;grant.base_ownership_version=parent.ownership_version;grant.is_active=True;grant.version+=1;grant.save();return grant


def suspend_organization_team(organization_id):
    OrganizationGrant.objects.filter(organization_id=organization_id,is_active=True).update(is_active=False,version=F('version')+1,updated_at=timezone.now())
    OrganizationTeamInvitation.objects.filter(organization_id=organization_id,status='PENDING').update(status='CANCELED',responded_at=timezone.now(),updated_at=timezone.now())


@transaction.atomic
def create_branch(*, actor, organization_id, values, allow_separate=False):
    org = _parents('organization',organization_id);actor=_actor(actor)
    if not has_action(user=actor,target=org,action='branch.create'):
        raise PermissionDenied
    from catalog.services.organization_ownership import _create
    # Owner receives ownership; actor remains the audit author. No selected grants are extended.
    owner=_actor(org.owner)
    place=_create(owner,values,Place,allow_separate)
    Place.objects.filter(pk=place.pk).update(created_by=actor,organization=org,organization_relationship_kind='business',organization_join_place_ownership_version=place.ownership_version,organization_join_org_ownership_version=org.ownership_version)
    place.refresh_from_db();return place
