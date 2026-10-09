"""Authorized stage06 transitions. Team grants/full revisions are later scopes.

Lock order: Organization -> Place -> Program -> Activity -> request. Never grant
business rights from authorship, pending requests or informational affiliation.
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from catalog.models import Organization, Place, Program, Activity, OrganizationPlaceRequest, PlaceOwnershipRequest, OrganizationOwnershipRequest, OwnerTeamMembership, OwnerTeamInvitation, OrganizationGrant, PlaceOwnershipRequestAudit
from catalog.services.staff_roles import is_volunteer
from catalog.services.catalog_structure import _lock, _active
from catalog.services.workflow_notifications import emit


def _actor(actor, *, business=True):
    if not getattr(actor,'is_authenticated',False) or not actor.pk:
        raise PermissionDenied
    fresh=get_user_model().objects.filter(pk=actor.pk,is_active=True).first()
    if fresh is None or (business and is_volunteer(fresh)):
        raise PermissionDenied
    return fresh


def _reviewer(actor):
    actor=_actor(actor)
    if not actor.is_staff or not (actor.is_superuser or actor.has_perm('catalog.change_placeownershiprequest')):
        raise PermissionDenied
    return actor


def _target(target_type):
    if target_type=='place':return Place,PlaceOwnershipRequest,'place'
    if target_type=='organization':return Organization,OrganizationOwnershipRequest,'organization'
    raise ValidationError('Unknown target type.')


def _parents(target_type,target_id):
    model,_,_=_target(target_type)
    before=model.objects.filter(pk=target_id).values('organization_id' if model is Place else 'id').first()
    if before is None:raise model.DoesNotExist
    if model is Place:
        _lock(Organization,[before['organization_id']],'default')
        row=_lock(Place,[target_id],'default')[target_id]
        if row.organization_id!=before['organization_id']:raise ValidationError('Structure changed; reload.',code='structure_changed')
        if row.deleted_at is not None:raise ValidationError('Deleted Place.')
    else:
        row=_lock(Organization,[target_id],'default')[target_id];_active(row)
    return row


def _version(value):
    if not isinstance(value,int) or isinstance(value,bool) or value<1:raise ValidationError('Invalid version.')
    return value


def suspend_place_team(place_id):
    OwnerTeamMembership.objects.filter(place_id=place_id,is_active=True).update(is_active=False,version=F('version')+1,updated_at=timezone.now())
    OwnerTeamInvitation.objects.filter(place_id=place_id,status='PENDING').update(status='CANCELED',responded_at=timezone.now(),updated_at=timezone.now())


def save_organization(instance,*args,**kwargs):
    using=kwargs.get('using') or instance._state.db or 'default'
    with transaction.atomic(using=using):
        old=Organization.objects.using(using).select_for_update().filter(pk=instance.pk).first() if instance.pk else None
        fields=kwargs.get('update_fields')
        if old is not None:
            if fields is None:
                instance.owner_id=old.owner_id
                instance.ownership_verified_at=old.ownership_verified_at
                instance.ownership_verified_by_id=old.ownership_verified_by_id
            instance.ownership_version=old.ownership_version
            if (fields is None or {'owner','owner_id'}.intersection(fields)) and old.owner_id!=instance.owner_id:
                instance.ownership_version+=1;instance.ownership_verified_at=None;instance.ownership_verified_by=None
                from catalog.services.business_team import suspend_organization_team
                suspend_organization_team(instance.pk)
                if fields is not None:kwargs['update_fields']=set(fields)|{'ownership_version','ownership_verified_at','ownership_verified_by'}
        return models.Model.save(instance,*args,**kwargs)


def warn_possible_duplicate(*,actor,model,name,allow_separate=False):
    duplicate=model.objects.filter(name_az__iexact=name.strip())
    visible=Q(owner=actor)|Q(created_by=actor)
    if model is Place:visible|=Q(is_active=True,status='published',deleted_at__isnull=True)
    else:visible|=Q(status='published',archived_at__isnull=True)
    duplicate=duplicate.filter(visible)
    if duplicate.exists() and not allow_separate:
        raise ValidationError('Possible duplicate; choose an existing public object or explicitly create an independent one.',code='possible_duplicate')


def _create(actor,values,model,allow_separate):
    actor=_actor(actor,business=model is Place)
    if not isinstance(values,dict) or not isinstance(allow_separate,bool):raise ValidationError('Invalid create payload.')
    allowed={'name_az','name_ru','name_en','description_az','description_ru','description_en','website'}
    allowed|= {'phone','whatsapp'} if model is Organization else {'category_id','address','lat','lng','phone1','phone2','phone3'}
    if set(values)-allowed:raise ValidationError('Unsupported create fields.')
    if not isinstance(values.get('name_az'),str) or not values['name_az'].strip():raise ValidationError('Azerbaijani name required.')
    warn_possible_duplicate(actor=actor,model=model,name=values['name_az'],allow_separate=allow_separate)
    obj=model(**values);obj.name_az=obj.name_az.strip();obj.created_by=actor
    obj.owner=None if is_volunteer(actor) else actor
    obj.status='draft'
    if model is Place:
        obj.name=obj.name_az;obj.is_active=False;obj.is_verified=False
    obj.full_clean();obj.save();return obj


def create_organization(*,actor,values,allow_separate=False):return _create(actor,values,Organization,allow_separate)

def create_place(*,actor,values,allow_separate=False):return _create(actor,values,Place,allow_separate)


@transaction.atomic
def submit_claim(*,actor,target_type,target_id,note=''):
    actor=_actor(actor);model,request_model,field=_target(target_type);row=_parents(target_type,target_id)
    if row.owner_id==actor.pk:raise ValidationError('Already owner.')
    query={field+'_id':row.pk,'applicant':actor,'status':'PENDING'}
    if model is Place:query['request_kind']='CLAIM'
    existing=request_model.objects.filter(**query).first()
    if existing:
        if existing.base_ownership_version!=row.ownership_version or existing.base_owner_id!=row.owner_id:
            raise ValidationError('Pending claim is stale; review/reject and resubmit.')
        return existing
    return request_model.objects.create(**query,note=note,base_ownership_version=row.ownership_version,base_owner_id=row.owner_id)


def _change_owner(row,new_owner_id):
    old_owner_id = row.owner_id
    grants = list((OwnerTeamMembership.objects.filter(place_id=row.pk, is_active=True) if isinstance(row, Place) else OrganizationGrant.objects.filter(organization_id=row.pk, is_active=True)).values_list('pk', 'member_id', 'version'))
    changes={'owner_id':new_owner_id,'ownership_version':F('ownership_version')+1,'updated_at':timezone.now()}
    if isinstance(row,Place):suspend_place_team(row.pk)
    else:
        from catalog.services.business_team import suspend_organization_team
        suspend_organization_team(row.pk)
        changes.update(ownership_verified_at=None,ownership_verified_by=None)
    type(row).objects.filter(pk=row.pk).update(**changes)
    row.refresh_from_db()
    entity = 'place' if isinstance(row, Place) else 'organization'
    for user_id in {old_owner_id, new_owner_id} - {None}:
        emit(kind='ownership_transfer', entity_type=entity, entity_id=row.pk, version=row.ownership_version, recipient_user=get_user_model().objects.get(pk=user_id))
    for grant_id, member_id, version in grants:
        emit(kind='access_disabled', entity_type=f'{entity}_team_grant', entity_id=grant_id, version=version+1, recipient_user=get_user_model().objects.get(pk=member_id))
    return row


@transaction.atomic
def transfer_owner(*,actor,target_type,target_id,new_owner_id,expected_ownership_version):
    actor=_actor(actor);row=_parents(target_type,target_id)
    if row.owner_id!=actor.pk:raise PermissionDenied
    if row.ownership_version!=_version(expected_ownership_version):raise ValidationError('Stale ownership version.')
    new_owner=get_user_model().objects.filter(pk=new_owner_id,is_active=True).first()
    if new_owner is None or is_volunteer(new_owner):raise ValidationError('New owner must be active business account.')
    if row.owner_id==new_owner_id:return row
    return _change_owner(row,new_owner_id)


@transaction.atomic
def moderate_claim(*,actor,target_type,request_id,approve,note=''):
    if not isinstance(approve,bool):raise ValidationError('Approval must be boolean.')
    actor=_reviewer(actor);model,request_model,field=_target(target_type)
    anchor=request_model.objects.filter(pk=request_id).values(field+'_id').first()
    if anchor is None:raise request_model.DoesNotExist
    row=_parents(target_type,anchor[field+'_id']);item=_lock(request_model,[request_id],'default')[request_id]
    if getattr(item,field+'_id')!=row.pk:raise ValidationError('Request changed.')
    if model is Place and item.request_kind!='CLAIM':raise ValidationError('This is a publication request.')
    return _decide_claim(actor,row,item,approve,note)


def _decide_claim(actor,row,item,approve,note):
    if item.status!='PENDING':raise ValidationError('Claim already processed.')
    if approve:
        if item.base_ownership_version is None or item.base_ownership_version!=row.ownership_version or item.base_owner_id!=row.owner_id:
            raise ValidationError('Stale claim; new confirmation required.')
        applicant=get_user_model().objects.filter(pk=item.applicant_id,is_active=True).first()
        if applicant is None or is_volunteer(applicant):raise ValidationError('Applicant is unavailable.')
        if row.owner_id!=applicant.pk:_change_owner(row,applicant.pk)
    old=item.status;item.status='APPROVED' if approve else 'REJECTED';item.moderated_by=actor;item.moderated_at=timezone.now();item.moderation_note=note
    item.save(update_fields=['status','moderated_by','moderated_at','moderation_note','updated_at'])
    if isinstance(item,PlaceOwnershipRequest):PlaceOwnershipRequestAudit.log_event(ownership_request=item,actor=actor,action=item.status,from_status=old,to_status=item.status,note=note)
    return item


@transaction.atomic
def moderate_place_request(*,actor,request_id,new_status,note=''):
    actor=_reviewer(actor)
    if new_status not in ('APPROVED','REJECTED'):raise ValueError('Unsupported transition')
    anchor=PlaceOwnershipRequest.objects.filter(pk=request_id).values('place_id').first()
    if anchor is None:raise PlaceOwnershipRequest.DoesNotExist
    from catalog.services import publication
    row=publication.locked_target('place',anchor['place_id']);item=_lock(PlaceOwnershipRequest,[request_id],'default')[request_id]
    if item.request_kind=='CLAIM':return _decide_claim(actor,row,item,new_status=='APPROVED',note)
    if item.status!='PENDING':raise ValueError('Request is not pending')
    if new_status=='APPROVED':
        if item.base_ownership_version!=row.ownership_version or item.base_owner_id!=row.owner_id or item.applicant_id!=row.owner_id:raise ValidationError('Stale publication request.')
        from catalog.models import VolunteerPlaceRevision
        revision=VolunteerPlaceRevision.objects.select_for_update().filter(place=row).first()
        if item.base_content_version!=row.content_version or item.base_candidate_version!=(revision.version if revision else 0):raise ValidationError('Stale publication content/candidate; resubmit.')
        publication.publish(actor=actor,place_id=row.pk,expected_version=item.base_content_version)
    old=item.status;item.status=new_status;item.moderated_by=actor;item.moderated_at=timezone.now();item.moderation_note=note;item.save(update_fields=['status','moderated_by','moderated_at','moderation_note','updated_at'])
    PlaceOwnershipRequestAudit.log_event(ownership_request=item,actor=actor,action=new_status,from_status=old,to_status=new_status,note=note)
    return item


def _link_parents(place_id,organization_id,*,allow_archived=False):
    org=_lock(Organization,[organization_id],'default')[organization_id]
    if not allow_archived:_active(org)
    place=_lock(Place,[place_id],'default')[place_id]
    if place.deleted_at is not None:raise ValidationError('Deleted Place.')
    return place,org


def _side_owner(actor,place,org):
    if actor.pk not in (place.owner_id,org.owner_id):raise PermissionDenied


def _request_matches(item,place,org):
    return (item.base_place_owner_id==place.owner_id and item.base_organization_owner_id==org.owner_id and item.base_place_ownership_version==place.ownership_version and item.base_organization_ownership_version==org.ownership_version)


def affiliation_current(place,org):
    return (place.organization_id==org.pk and org.archived_at is None and place.organization_relationship_kind in ('business','informational') and place.organization_join_place_ownership_version==place.ownership_version and place.organization_join_org_ownership_version==org.ownership_version)


def join_visible_places(*, actor, organization_id=None):
    """Connection visibility, without granting any business permissions.

    A private Place can also be shared with the specific organization by its
    current direct owner's current confirmation. An organization-only pending
    request is never evidence of visibility.
    """
    from catalog.services import business_team
    from catalog.services.content_quality import public_place_queryset
    actor = _actor(actor, business=False)
    public_ids = public_place_queryset(Place.objects.all()).values('pk')
    own_ids = business_team.accessible_place_ids(user=actor, action='place.view')
    visible = Q(pk__in=public_ids) | Q(pk__in=own_ids)
    if organization_id is not None:
        shared_ids = OrganizationPlaceRequest.objects.filter(
            organization_id=organization_id, organization__owner=actor,
            organization__archived_at__isnull=True, status='pending',
            relationship_kind='business', place_owner_confirmed_at__isnull=False,
            base_place_owner_id=F('place__owner_id'),
            base_organization_owner_id=F('organization__owner_id'),
            base_place_ownership_version=F('place__ownership_version'),
            base_organization_ownership_version=F('organization__ownership_version'),
            base_place_content_version=F('place__content_version')).values('place_id')
        visible |= Q(pk__in=shared_ids)
    return Place.objects.filter(visible, deleted_at__isnull=True).distinct()


def _require_join_visible(actor, place, org):
    if not join_visible_places(actor=actor, organization_id=org.pk).filter(pk=place.pk).exists():
        raise PermissionDenied(_('Карточка недоступна'))


def _apply_link(item,place,org,actor):
    if place.organization_id not in (None,org.pk):raise ValidationError('Detach previous affiliation first.')
    if Activity.objects.filter(place=place,program__isnull=False).exclude(program__organization_id=org.pk).exists():raise ValidationError('Programs belong to another organization.')
    Place.objects.filter(pk=place.pk).update(organization_id=org.pk,organization_relationship_kind=item.relationship_kind,organization_join_place_ownership_version=place.ownership_version,organization_join_org_ownership_version=org.ownership_version,content_version=F('content_version')+1,updated_at=timezone.now())
    item.status='approved';item.decided_at=timezone.now();item.decided_by=actor;item.save(update_fields=['status','decided_at','decided_by'])
    for user_id in {place.owner_id, org.owner_id, item.requested_by_id} - {None}:
        emit(kind='join_approved', entity_type='organization_place_request', entity_id=item.pk, version=2, recipient_user=get_user_model().objects.get(pk=user_id))
    return item


@transaction.atomic
def request_join(*,actor,place_id,organization_id,relationship_kind='business'):
    if relationship_kind not in ('business','informational'):raise ValidationError('Invalid relationship kind.')
    from catalog.services.staff_roles import is_volunteer, can_use_volunteer_workspace
    actor = _actor(actor, business=relationship_kind != 'informational')
    place,org=_link_parents(place_id,organization_id)
    if relationship_kind=='informational' and is_volunteer(actor):
        if not can_use_volunteer_workspace(actor):raise PermissionDenied
        own_place = place.created_by_id == actor.pk and place.owner_id is None
        own_org = org.created_by_id == actor.pk and org.owner_id is None
        public_place = place.status == 'published' and place.is_active
        public_org = org.status == 'published'
        if not ((own_place or public_place) and (own_org or public_org)):
            raise PermissionDenied
    elif relationship_kind=='informational':actor=_reviewer(actor)
    else:
        _side_owner(actor,place,org)
        _require_join_visible(actor,place,org)
        if place.owner_id is None or org.owner_id is None:raise ValidationError('Both business owners must exist.')
    if place.organization_id not in (None,org.pk):raise ValidationError('Detach previous affiliation first.')
    existing=OrganizationPlaceRequest.objects.filter(place=place,organization=org,status='approved',relationship_kind=relationship_kind).order_by('-pk').first()
    if existing and _request_matches(existing,place,org) and affiliation_current(place,org):
        if is_volunteer(actor):raise ValidationError('Affiliation already current.')
        return existing
    item=OrganizationPlaceRequest.objects.select_for_update().filter(place=place,organization=org,status='pending').first()
    if item and is_volunteer(actor) and item.requested_by_id != actor.pk:
        raise PermissionDenied
    if item and not _request_matches(item,place,org):
        item.status='canceled';item.decided_at=timezone.now();item.decided_by=actor;item.save(update_fields=['status','decided_at','decided_by']);item=None
    if item and item.relationship_kind!=relationship_kind:raise ValidationError('Another relationship request is pending.')
    if item is None:
        item=OrganizationPlaceRequest.objects.create(place=place,organization=org,requested_by=actor,relationship_kind=relationship_kind,base_place_ownership_version=place.ownership_version,base_organization_ownership_version=org.ownership_version,base_place_content_version=place.content_version,base_place_owner_id=place.owner_id,base_organization_owner_id=org.owner_id)
    if relationship_kind=='business':return _confirm(actor,item,place,org)
    return item


def _confirm(actor,item,place,org):
    _side_owner(actor,place,org)
    if item.relationship_kind!='business':raise ValidationError('Informational request needs KidsMap approval.')
    _require_join_visible(actor,place,org)
    if not _request_matches(item,place,org):raise ValidationError('Owner changed; new confirmations required.')
    if item.status=='approved':
        if not affiliation_current(place,org):raise ValidationError('Affiliation is no longer current.')
        return item
    if item.status!='pending' or item.base_place_content_version!=place.content_version:raise ValidationError('Request is stale.')
    if place.owner_id is None or org.owner_id is None:raise ValidationError('Both owners required.')
    if actor.pk==place.owner_id:item.place_owner_confirmed_at=timezone.now()
    if actor.pk==org.owner_id:item.organization_owner_confirmed_at=timezone.now()
    item.save(update_fields=['place_owner_confirmed_at','organization_owner_confirmed_at'])
    if item.place_owner_confirmed_at and item.organization_owner_confirmed_at:return _apply_link(item,place,org,actor)
    other_owner_id = org.owner_id if actor.pk == place.owner_id else place.owner_id
    if other_owner_id and other_owner_id != actor.pk:
        emit(kind='join_confirmation', entity_type='organization_place_request', entity_id=item.pk, version=1, recipient_user=get_user_model().objects.get(pk=other_owner_id))
    return item


def _locked_join(request_id):
    anchor=OrganizationPlaceRequest.objects.filter(pk=request_id).values('place_id','organization_id').first()
    if anchor is None:raise OrganizationPlaceRequest.DoesNotExist
    place,org=_link_parents(anchor['place_id'],anchor['organization_id']);item=_lock(OrganizationPlaceRequest,[request_id],'default')[request_id]
    if (item.place_id,item.organization_id)!=(place.pk,org.pk):raise ValidationError('Request changed.')
    return item,place,org


JOIN_RECOVERY_SALT = 'catalog.organization-place.cancel.v1'


def _cancel_parents(request_id):
    """Same join lock order, permitting safe withdrawal after archive/deletion."""
    anchor = OrganizationPlaceRequest.objects.filter(pk=request_id).values('place_id', 'organization_id').first()
    if anchor is None:
        raise OrganizationPlaceRequest.DoesNotExist
    org = _lock(Organization, [anchor['organization_id']], 'default')[anchor['organization_id']]
    place = _lock(Place, [anchor['place_id']], 'default')[anchor['place_id']]
    item = _lock(OrganizationPlaceRequest, [request_id], 'default')[request_id]
    if (item.place_id, item.organization_id) != (place.pk, org.pk):
        raise ValidationError('Request changed.', code='request_conflict')
    return item, place, org


def _cancel_owner(actor, item, place, org):
    _side_owner(actor, place, org)
    if item.relationship_kind != 'business':
        raise PermissionDenied


def _cancel_snapshot(item, place, org):
    import json
    from django.utils.crypto import salted_hmac
    values = [item.status, item.relationship_kind, item.base_place_owner_id,
        item.base_organization_owner_id, item.base_place_ownership_version,
        item.base_organization_ownership_version, item.base_place_content_version,
        str(item.place_owner_confirmed_at), str(item.organization_owner_confirmed_at),
        place.owner_id, place.ownership_version, place.content_version, str(place.deleted_at),
        org.owner_id, org.ownership_version, org.content_version, str(org.archived_at)]
    return salted_hmac(JOIN_RECOVERY_SALT + '.state', json.dumps(values), algorithm='sha256').hexdigest()


@transaction.atomic
def join_recovery_state(*, actor, request_id):
    from django.core import signing
    actor = _actor(actor)
    item, place, org = _cancel_parents(request_id)
    _cancel_owner(actor, item, place, org)
    return signing.dumps({'actor': actor.pk, 'request': item.pk,
        'state': _cancel_snapshot(item, place, org)}, salt=JOIN_RECOVERY_SALT, compress=True)


@transaction.atomic
def cancel_join(*, actor, request_id, expected_state):
    from django.core import signing
    actor = _actor(actor)
    item, place, org = _cancel_parents(request_id)
    _cancel_owner(actor, item, place, org)
    if not isinstance(expected_state, str) or not 1 <= len(expected_state) <= 8192:
        raise ValidationError('State required.', code='invalid_state')
    try:
        state = signing.loads(expected_state, salt=JOIN_RECOVERY_SALT, max_age=1800)
    except signing.SignatureExpired:
        raise ValidationError('State expired.', code='request_conflict')
    except signing.BadSignature:
        raise ValidationError('Invalid state.', code='invalid_state')
    if not isinstance(state, dict) or state.get('actor') != actor.pk or state.get('request') != item.pk:
        raise ValidationError('Invalid state.', code='invalid_state')
    if item.status == 'canceled':
        return item
    if item.status != 'pending' or state.get('state') != _cancel_snapshot(item, place, org):
        raise ValidationError('Request changed; review again.', code='request_conflict')
    item.status = 'canceled'
    item.decided_by = actor
    item.decided_at = timezone.now()
    item.note = (item.note + '\n' if item.note else '') + 'Explicit withdrawal by current owner.'
    item.save(update_fields=['status', 'decided_by', 'decided_at', 'note'])
    return item


def join_recovery_rows(*, actor, items):
    """Safe request labels. Cancellation authority never grants parent visibility."""
    from catalog.services.organization_connections import organization_visible, organization_name
    actor = _actor(actor)
    items = list(items)
    visible = {org_id: set(join_visible_places(actor=actor, organization_id=org_id).filter(
        pk__in=[r.place_id for r in items if r.organization_id == org_id]).values_list('pk', flat=True))
        for org_id in {r.organization_id for r in items}}
    for item in items:
        item.recovery_place_name = item.place.name_i18n() if item.place_id in visible[item.organization_id] else ''
        item.recovery_org_name = organization_name(item.organization) if organization_visible(actor, item.organization) else ''
        item.recovery_stale = (not _request_matches(item, item.place, item.organization)
            or item.base_place_content_version != item.place.content_version
            or item.place.deleted_at is not None or item.organization.archived_at is not None)
    return items


@transaction.atomic
def confirm_join(*,actor,request_id):
    actor=_actor(actor);item,place,org=_locked_join(request_id);return _confirm(actor,item,place,org)


@transaction.atomic
def approve_informational_join(*,actor,request_id):
    actor=_reviewer(actor);item,place,org=_locked_join(request_id)
    if item.relationship_kind!='informational' or not _request_matches(item,place,org):raise ValidationError('Stale informational request.')
    if item.status=='approved':
        if not affiliation_current(place,org):raise ValidationError('Affiliation changed.')
        return item
    if item.status!='pending' or item.base_place_content_version!=place.content_version:raise ValidationError('Request is not current.')
    return _apply_link(item,place,org,actor)


def approved_program_data(program):
    return {**{name:getattr(program,name) for name in ('name_az','name_ru','name_en','description_az','description_ru','description_en')},'category_id':program.category_id,'subcategory_id':program.subcategory_id,'organization_id':program.organization_id}


@transaction.atomic
def detach(*,actor,place_id,organization_id,expected_ownership_version):
    actor=_actor(actor);place,org=_link_parents(place_id,organization_id,allow_archived=True);_side_owner(actor,place,org)
    if place.ownership_version!=_version(expected_ownership_version):raise ValidationError('Stale ownership version.')
    if place.organization_id is None:
        if actor.pk!=place.owner_id and not OrganizationPlaceRequest.objects.filter(place=place,organization=org,status='approved').exists():raise PermissionDenied
        return place
    if place.organization_id!=org.pk:raise ValidationError('Affiliation target mismatch.')
    programs=_lock(Program,Activity.objects.filter(place=place,program__isnull=False).values_list('program_id',flat=True),'default')
    activities=list(Activity.objects.select_for_update().filter(place=place,program__isnull=False).order_by('pk'))
    for activity in activities:
        program=programs[activity.program_id]
        snapshot=activity.program_snapshot;version=activity.source_program_version
        if program.status=='published' and program.approved_at is not None:snapshot=approved_program_data(program);version=program.content_version
        elif not snapshot and (program.approved_at is not None or activity.status=='published'):raise ValidationError('Approved snapshot unavailable; manual review required.')
        values={'program_id':None,'updated_at':timezone.now(),'content_version':F('content_version')+1}
        if snapshot:
            if not version:raise ValidationError('Approved snapshot version unavailable.')
            values.update(program_snapshot=snapshot,source_program_id=program.pk,source_program_version=version)
            values.update(category_id=snapshot.get('category_id'),subcategory_id=snapshot.get('subcategory_id'))
            for lang in ('az','ru','en'):
                for prefix in ('name','description'):
                    field=prefix+'_'+lang
                    if not getattr(activity,field):values[field]=snapshot.get(field,'')
        Activity.objects.filter(pk=activity.pk).update(**values)
    Place.objects.filter(pk=place.pk).update(organization_id=None,organization_relationship_kind=None,organization_join_place_ownership_version=None,organization_join_org_ownership_version=None,content_version=F('content_version')+1,updated_at=timezone.now())
    place.refresh_from_db()
    for user_id in {place.owner_id, org.owner_id} - {None}:
        emit(kind='affiliation_detached', entity_type='place', entity_id=place.pk, version=place.content_version, recipient_user=get_user_model().objects.get(pk=user_id))
    return place


def effective_contacts(*,place_id):
    place=Place.objects.select_related('organization').get(pk=place_id)
    inherited=place.organization if place.organization_id and affiliation_current(place,place.organization) else None
    return {'phone':place.phone1 or place.phone2 or place.phone3 or (inherited.phone if inherited else ''),'website':place.website or (inherited.website if inherited else ''),'whatsapp':inherited.whatsapp if inherited else ''}
