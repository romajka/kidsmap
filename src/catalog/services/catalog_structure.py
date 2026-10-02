"""Internal integrity hooks; callers must authorize/approve before invoking them.

Structural writers lock Organization -> Place -> Program -> Activity (PK order).
Bulk/update SQL bypasses these hooks and is not an authorized structural API.
"""
from django.core.exceptions import ValidationError
from django.db import models, router, transaction
from django.db.models import F
from django.utils import timezone


def _models():
    from catalog.models import Organization, Place, Program, Activity, Location
    return Organization, Place, Program, Activity, Location


def _lock(model, ids, using):
    ids = sorted({pk for pk in ids if pk is not None})
    found = {row.pk: row for row in model.objects.using(using).select_for_update().filter(pk__in=ids).order_by('pk')}
    if set(found) != set(ids):
        raise ValidationError('Structural parent does not exist.')
    return found


def _current(model, pk, fields, using):
    if pk is None:
        return None
    return model.objects.using(using).filter(pk=pk).values(*fields).first()


def _unchanged(before, after):
    if before != after:
        raise ValidationError('Structure changed concurrently; reload and retry.')


def _check_partial_relationships(instance, before, kwargs):
    fields = kwargs.get('update_fields')
    if before is not None and fields is not None:
        fields = set(fields)
        for attname, stored in before.items():
            if attname not in fields and attname.removesuffix('_id') not in fields and getattr(instance, attname) != stored:
                raise ValidationError('Partial save excludes a changed structural parent; reload or save all changed relationships.')


def _active(row):
    if row.archived_at is not None:
        raise ValidationError('Archived parent cannot accept structural writes.')


PLACE_STRUCTURE_DEFAULTS = {
    'organization_id': None, 'confirmed_location_id': None,
    'organization_relationship_kind': None, 'organization_join_place_ownership_version': None, 'organization_join_org_ownership_version': None,
    'venue_confirmed_at': None, 'content_version': 1, 'ownership_version': 1,
    'nature': None, 'nature_approved_at': None,
    'operating_state': None, 'operating_state_approved_at': None,
}


def preserve_place_structure(instance, previous, kwargs):
    """Legacy writer keeps current readonly columns under its existing Place lock.

    Full legacy saves may originate before a structural write. Copy the locked
    columns rather than persisting stale values; explicit structural partial
    writes and non-default structural creation must use internal hooks.
    """
    fields = kwargs.get('update_fields')
    actor_id=getattr(instance,'_authorized_actor_id',None)
    if previous is not None and actor_id is not None:
        from django.contrib.auth import get_user_model
        from django.core.exceptions import PermissionDenied
        from catalog.services.place_access import has_place_permission
        actor=get_user_model().objects.filter(pk=actor_id).first()
        if actor is None or not has_place_permission(user=actor,place=previous,permission_code=instance._required_permission_code):
            raise PermissionDenied
    if previous is not None and fields is None:
        instance.owner_id=previous.owner_id
    protected = set(PLACE_STRUCTURE_DEFAULTS) | {'organization', 'confirmed_location'}
    if fields is not None and protected.intersection(fields):
        raise ValidationError('Use the authorized structural service for readonly Place fields.')
    if previous is None:
        if any(getattr(instance, name) != value for name, value in PLACE_STRUCTURE_DEFAULTS.items()):
            raise ValidationError('Create a legacy-compatible Place, then use authorized structural hooks.')
    else:
        for name in PLACE_STRUCTURE_DEFAULTS:
            setattr(instance, name, getattr(previous, name))
        from catalog.services.map_payload import venue_identity_changed
        if previous.confirmed_location_id and venue_identity_changed(previous, instance, fields):
            instance.confirmed_location_id = None
            instance.venue_confirmed_at = None
            if fields is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'confirmed_location', 'venue_confirmed_at'}
        if (fields is None or {'owner', 'owner_id'}.intersection(fields)) and previous.owner_id != instance.owner_id:
            instance.ownership_version = previous.ownership_version + 1
            if fields is not None:
                kwargs['update_fields'] = set(fields) | {'ownership_version'}
            from catalog.services.organization_ownership import suspend_place_team
            suspend_place_team(instance.pk)



def save_program(instance, *args, **kwargs):
    Organization, Place, Program, Activity, _ = _models()
    using = kwargs.get('using') or router.db_for_write(Program, instance=instance)
    # Optimistic anchor reads are verified after acquiring the locks.
    before = _current(Program, instance.pk, ('organization_id',), using)
    with transaction.atomic(using=using):
        orgs = _lock(Organization, [instance.organization_id, before['organization_id'] if before else None], using)
        if instance.organization_id not in orgs:
            raise ValidationError('Program requires an Organization.')
        _active(orgs[instance.organization_id])
        linked_ids = list(Activity.objects.using(using).filter(program_id=instance.pk).values_list('place_id', flat=True)) if before else []
        places = _lock(Place, linked_ids, using)
        locked_programs = _lock(Program, [instance.pk] if before else [], using)
        _unchanged(before, _current(Program, instance.pk, ('organization_id',), using))
        _check_partial_relationships(instance, before, kwargs)
        # Organization locks serialize Activity creation against this relocation.
        if any(place.organization_id != instance.organization_id for place in places.values()):
            raise ValidationError('Program organization must match every linked Place.')
        instance.organization = orgs[instance.organization_id]
        previous = locked_programs.get(instance.pk)
        if previous is not None and previous.status == 'published' and previous.approved_at is not None:
            from catalog.services.organization_ownership import approved_program_data
            activity_ids = Activity.objects.using(using).filter(program_id=instance.pk).values_list('pk', flat=True)
            _lock(Activity, activity_ids, using)
            Activity.objects.using(using).filter(program_id=instance.pk).update(
                program_snapshot=approved_program_data(previous), source_program_id=previous.pk,
                source_program_version=previous.content_version,
            )
        instance.full_clean()
        return models.Model.save(instance, *args, **kwargs)


def save_activity(instance, *args, **kwargs):
    Organization, Place, Program, Activity, _ = _models()
    using = kwargs.get('using') or router.db_for_write(Activity, instance=instance)
    before = _current(Activity, instance.pk, ('place_id', 'program_id'), using)
    place_ids = {instance.place_id} | ({before['place_id']} if before else set())
    program_ids = {instance.program_id} | ({before['program_id']} if before else set())
    place_before = {pk: _current(Place, pk, ('organization_id',), using) for pk in place_ids if pk is not None}
    program_before = {pk: _current(Program, pk, ('organization_id',), using) for pk in program_ids if pk is not None}
    if any(row is None for row in [*place_before.values(), *program_before.values()]):
        raise ValidationError('Structural parent does not exist.')
    org_ids = [row['organization_id'] for row in [*place_before.values(), *program_before.values()]]
    with transaction.atomic(using=using):
        orgs = _lock(Organization, org_ids, using)
        places = _lock(Place, place_ids, using)
        programs = _lock(Program, program_ids, using)
        _lock(Activity, [instance.pk] if before else [], using)
        _unchanged(before, _current(Activity, instance.pk, ('place_id', 'program_id'), using))
        _check_partial_relationships(instance, before, kwargs)
        for pk, snapshot in place_before.items():
            _unchanged(snapshot, {'organization_id': places[pk].organization_id})
        for pk, snapshot in program_before.items():
            _unchanged(snapshot, {'organization_id': programs[pk].organization_id})
        place = places.get(instance.place_id)
        if place is None:
            raise ValidationError('Activity requires a Place.')
        if place.organization_id is not None:
            _active(orgs[place.organization_id])
        if instance.program_id is not None:
            program = programs[instance.program_id]
            _active(program)
            if program.organization_id != place.organization_id:
                raise ValidationError('Activity Program and Place must share an Organization.')
            instance.program = program
        instance.place = place
        if instance.program_id is not None and not instance.program_snapshot and program.status == 'published' and program.approved_at is not None:
            from catalog.services.organization_ownership import approved_program_data
            instance.program_snapshot = approved_program_data(program)
            instance.source_program = program
            instance.source_program_version = program.content_version
            if kwargs.get('update_fields') is not None:
                kwargs['update_fields'] = set(kwargs['update_fields']) | {'program_snapshot', 'source_program', 'source_program_version'}
        instance.full_clean()
        return models.Model.save(instance, *args, **kwargs)


def set_place_organization(place_id, organization_id, *, expected_content_version, using='default'):
    Organization, Place, _, Activity, _ = _models()
    before = _current(Place, place_id, ('organization_id',), using)
    if before is None:
        raise ValidationError('Place does not exist.')
    with transaction.atomic(using=using):
        orgs = _lock(Organization, [before['organization_id'], organization_id], using)
        if organization_id is not None:
            _active(orgs[organization_id])
        place = _lock(Place, [place_id], using)[place_id]
        _unchanged(before, {'organization_id': place.organization_id})
        if place.content_version != expected_content_version:
            raise ValidationError('Place content version is stale.')
        # Keep archived links valid too; detachment/materialization is stage06.
        if Activity.objects.using(using).filter(place_id=place_id, program__isnull=False).exclude(program__organization_id=organization_id).exists():
            raise ValidationError('Place organization conflicts with linked Programs.')
        Place.objects.using(using).filter(pk=place_id).update(organization_id=organization_id, content_version=F('content_version') + 1, updated_at=timezone.now())
        place.refresh_from_db(using=using)
        return place


def bind_confirmed_location(place_id, location_id, *, expected_content_version, using='default'):
    _, Place, _, _, Location = _models()
    with transaction.atomic(using=using):
        place = _lock(Place, [place_id], using)[place_id]
        location = _lock(Location, [location_id], using)[location_id]
        _active(location)
        if place.content_version != expected_content_version:
            raise ValidationError('Place content version is stale.')
        # Preserve every legacy address/coordinate/owner and Event relation.
        Place.objects.using(using).filter(pk=place_id).update(confirmed_location_id=location_id, venue_confirmed_at=timezone.now(), content_version=F('content_version') + 1, updated_at=timezone.now())
        place.refresh_from_db(using=using)
        return place
