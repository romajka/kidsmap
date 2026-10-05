"""One versioned candidate pipeline, backed by existing VolunteerPlaceRevision.

Only approved patches write live content. No autosave transport is implemented.
All entry points acquire structural parents before targets and their revision.
"""
import copy
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from catalog.models import Place, Organization, Program, Activity, OfferingGroup, VolunteerPlaceRevision
from catalog.services.catalog_structure import _lock
from catalog.services.business_team import platform_has_action

SCHEMA_VERSION = 1
TARGETS = {'place': Place, 'organization': Organization, 'program': Program, 'activity': Activity, 'offering_group': OfferingGroup}
TEXTS = {f'{prefix}_{lang}' for prefix in ('name','description') for lang in ('az','ru','en')}
PRICES = {'price_from','price_to','price_per_lesson','price_per_month','price_per_8_lessons'}
SCHEDULE = {'schedule','schedule_mode','structured_schedule','schedule_note_az','schedule_note_ru','schedule_note_en'}
CONDITIONS = {'extra_conditions','extra_conditions_az','extra_conditions_ru','extra_conditions_en','lesson_format','lesson_duration_minutes','lessons_per_week','lessons_per_month','price_mode'}


def fields_for(kind):
    from catalog.volunteer_forms import CONTENT_FIELDS
    return {
        'place': set(CONTENT_FIELDS) | PRICES | {'nature','operating_state','pricing_plans','nested_pricing','structured_schedule','gallery','location_override'},
        'organization': TEXTS | {'phone','whatsapp','website'},
        'program': TEXTS | {'category','subcategory'},
        'activity': TEXTS | {'supplement_az','supplement_ru','supplement_en','category','subcategory'},
        'offering_group': {'name_az','name_ru','name_en','age_from','age_to','lesson_format','language','schedule_text','teachers_text','conditions_az','conditions_ru','conditions_en'},
    }[kind]


def snapshot(target, kind):
    from catalog.services.volunteer_places import json_value
    result={}
    for name in fields_for(kind):
        if name=='location_override':
            value = target.location_overrides.filter(is_current=True).values('city','district','reason','lat','lng','changed_by_id').first() if target.pk else None
            if value:
                # A signed form token is readable by its recipient. Bind source
                # conflicts to the audit without exposing staff reason/actor.
                import json
                from django.utils.crypto import salted_hmac
                value = salted_hmac('publication-location-audit',
                    json.dumps(json_value(value),sort_keys=True,separators=(',',':')),
                    algorithm='sha256').hexdigest()
        elif name=='gallery':value=list(target.gallery.order_by('order','pk').values('id','image','caption','order')) if target.pk else []
        elif name=='pricing_plans': value=[{k:v for k,v in plan.items() if k!='verified_at'} for plan in target.pricing_plans]
        elif name=='nested_pricing':
            from catalog.services.pricing_plans import serialize_nested_pricing
            value=serialize_nested_pricing(target) if target.pk else {'pricing_schema_version':2,'activities':[]}
            for activity in value['activities']:
                for group in activity['groups']:
                    for plan in group['pricing_plans']:plan.pop('verified_at',None)
        elif name=='structured_schedule':
            from catalog.services.place_schedule import serialize_place_schedule
            value=serialize_place_schedule(target)
        else:
            field=target._meta.get_field(name);value=getattr(target,field.attname)
            if name in {'photo','cover_photo'}:value=str(value or '')
        result[name]=json_value(value)
    return result


def _kind(revision):
    for name in TARGETS:
        if getattr(revision,name+'_id') is not None:return name,getattr(revision,name+'_id')
    raise ValidationError('Revision target missing.')


def locked_target(kind,pk):
    if kind not in TARGETS:raise ValidationError('Unknown publication target.')
    model=TARGETS[kind];anchor=model.objects.filter(pk=pk).first()
    if anchor is None:raise ValidationError('Publication target missing.')
    places=[];programs=[];activities=[];orgids=[]
    if kind=='place':places=[anchor.pk]
    elif kind=='organization':orgids=[anchor.pk]
    elif kind=='program':programs=[anchor.pk];orgids=[anchor.organization_id];places=list(Activity.objects.filter(program=anchor,archived_at__isnull=True).values_list('place_id',flat=True))
    elif kind=='activity':activities=[anchor.pk];places=[anchor.place_id];programs=[anchor.program_id]
    else:
        a=Activity.objects.get(pk=anchor.activity_id);activities=[a.pk];places=[a.place_id];programs=[a.program_id]
    place_anchors=list(Place.objects.filter(pk__in=places).values('pk','organization_id'))
    orgids += [x['organization_id'] for x in place_anchors]
    orgids += list(Program.objects.filter(pk__in=programs).values_list('organization_id',flat=True))
    ancestor_anchors=list(Activity.objects.filter(pk__in=activities).values('pk','place_id','program_id'))
    orgs=_lock(Organization,orgids,'default')
    if kind=='program':
        places=list(Activity.objects.filter(program_id=pk,archived_at__isnull=True).values_list('place_id',flat=True))
        place_anchors=list(Place.objects.filter(pk__in=places).values('pk','organization_id'))
        if any(x['organization_id']!=anchor.organization_id for x in place_anchors):raise ValidationError('Program link parent conflict.')
    ps=_lock(Place,places,'default');prs=_lock(Program,programs,'default');acts=_lock(Activity,activities,'default')
    if any(acts[x['pk']].place_id!=x['place_id'] or acts[x['pk']].program_id!=x['program_id'] for x in ancestor_anchors):raise ValidationError('Publication ancestor changed.')
    if any(ps[x['pk']].organization_id!=x['organization_id'] for x in place_anchors):raise ValidationError('Publication parent changed.')
    if kind=='place':target=ps[pk]
    elif kind=='organization':target=orgs[pk]
    elif kind=='program':target=prs[pk]
    elif kind=='activity':target=acts[pk]
    else:target=_lock(OfferingGroup,[pk],'default')[pk]
    for row in [target,*orgs.values(),*ps.values(),*prs.values(),*acts.values()]:
        if getattr(row,'archived_at',None) is not None or getattr(row,'deleted_at',None) is not None:raise ValidationError('Archived/deleted publication target or parent.')
    for name in ('organization_id','place_id','program_id','activity_id'):
        if getattr(anchor,name,None)!=getattr(target,name,None):raise ValidationError('Publication parent changed.')
    return target


def dependencies(target,kind):
    result={}
    if kind=='place':
        result={name:getattr(target,name) for name in ('owner_id','created_by_id','ownership_version','organization_id','organization_relationship_kind','organization_join_place_ownership_version','organization_join_org_ownership_version')}
        if target.organization_id:
            org=Organization.objects.get(pk=target.organization_id);result['organization']=[org.owner_id,org.ownership_version,org.status,str(org.approved_at),str(org.archived_at)]
    elif kind=='organization':result={'owner_id':target.owner_id,'ownership_version':target.ownership_version}
    elif kind=='program':
        org=Organization.objects.get(pk=target.organization_id);result={'organization_id':org.pk,'owner_id':org.owner_id,'ownership_version':org.ownership_version}
    elif kind=='activity':result={'place_id':target.place_id,'program_id':target.program_id,'parent':dependencies(Place.objects.get(pk=target.place_id),'place')}
    else:result={'activity_id':target.activity_id,'parent':dependencies(Activity.objects.get(pk=target.activity_id),'activity')}
    return result


def fresh_actor(actor):
    if not getattr(actor,'pk',None):raise PermissionDenied
    current=get_user_model().objects.filter(pk=actor.pk,is_active=True).first()
    if current is None:raise PermissionDenied
    return current


def volunteer_can_author(actor, target, kind):
    """Authorship permits a candidate, never a business grant."""
    from catalog.services.staff_roles import can_use_volunteer_workspace
    if not can_use_volunteer_workspace(actor):
        return False
    if kind == 'place':
        return target.created_by_id == actor.pk and target.owner_id is None and not target.is_temporary
    if kind == 'organization':
        return target.created_by_id == actor.pk and target.owner_id is None
    if kind == 'program':
        org = target.organization
        return (target.created_by_id == actor.pk and org.created_by_id == actor.pk
                and org.owner_id is None)
    if kind in {'activity', 'offering_group'}:
        activity = target if kind == 'activity' else target.activity
        place = activity.place
        if not (place.created_by_id == actor.pk and place.owner_id is None and not place.is_temporary):
            return False
        return activity.program_id is None or volunteer_can_author(actor, activity.program, 'program')
    return False


def authorize(actor,target,kind,review=False):
    from catalog.services.business_team import has_action,platform_has_action
    from catalog.services.staff_roles import can_use_volunteer_workspace
    if review:
        if not platform_has_action(user=actor,action='place.publish'):raise PermissionDenied
        return
    action={'place':'place.edit','organization':'organization.edit','program':'program.manage','activity':'place.edit','offering_group':'place.edit'}[kind]
    if has_action(user=actor,target=target,action=action):return
    if kind=='place' and platform_has_action(user=actor,action='place.publish'):return
    if volunteer_can_author(actor,target,kind):return
    raise PermissionDenied


def _integer(value):
    if isinstance(value,bool) or not isinstance(value,int) or value<0:raise ValidationError('Invalid version.')
    return value


def _validate_patch(target,kind,patch):
    from catalog.services.volunteer_places import json_value
    if not isinstance(patch,dict) or not set(patch)<=fields_for(kind):raise ValidationError('Unknown/protected publication fields.')
    candidate=copy.copy(target);candidate._state=copy.copy(target._state);normalized={}
    for name,value in patch.items():
        if name=='location_override':
            if value is not None and value != snapshot(target,kind)['location_override']:
                from django.contrib.auth import get_user_model
                from catalog.services.location_assignment import set_location_override
                if not isinstance(value,dict) or set(value)!={'city','district','reason','lat','lng','actor_id'}:
                    raise ValidationError('Invalid location override metadata.')
                override_actor = get_user_model().objects.filter(pk=value['actor_id']).first()
                location_candidate = copy.copy(candidate)
                location_candidate.lat, location_candidate.lng = value['lat'], value['lng']
                set_location_override(location_candidate,actor=override_actor,city=value['city'],district=value['district'],reason=value['reason'])
        elif name=='gallery':
            from catalog.models import PlacePhoto
            if not isinstance(value,list) or len(value)>10:raise ValidationError('Invalid gallery.')
            existing={p.pk:p for p in target.gallery.all()};seen=set();clean=[]
            for row in value:
                if not isinstance(row,dict) or not set(row)<={'id','image','caption','order'}:raise ValidationError('Invalid gallery fields.')
                pk=row.get('id');image=str(row.get('image') or '')
                if pk is not None and (isinstance(pk,bool) or pk not in existing or pk in seen):raise ValidationError('Foreign/duplicate gallery photo.')
                if pk is not None:seen.add(pk)
                if not image:raise ValidationError('Gallery image required.')
                if (pk is None or image!=str(existing[pk].image)) and not PlacePhoto._meta.get_field('image').storage.exists(image):raise ValidationError('Uploaded gallery image missing.')
                caption=PlacePhoto._meta.get_field('caption').clean(row.get('caption',''),None)
                order=PlacePhoto._meta.get_field('order').clean(row.get('order',0),None)
                clean.append({'id':pk,'image':image,'caption':caption,'order':order})
            value=clean
        elif name=='pricing_plans':
            from catalog.services.pricing_plans import normalize_pricing_plans
            value=normalize_pricing_plans(value,allow_verified=False)
            # Validate ownership of supplied plan IDs even for gated candidates.
            ids={int(p['id']) for p in value if p.get('id')}
            if ids and set(target.pricing_plan_records.filter(pk__in=ids).values_list('pk',flat=True))!=ids:raise ValidationError('Foreign pricing plan.')
        elif name=='nested_pricing':
            from catalog.services.pricing_plans import validate_nested_pricing
            value=validate_nested_pricing(target,value,allow_verified=False)
        elif name=='structured_schedule':
            import json
            from catalog.services.place_schedule import validate_schedule_payload
            if not isinstance(value,list):raise ValidationError('Schedule must be a list.')
            checked=validate_schedule_payload(json.dumps(value))
            if checked.errors:raise ValidationError('Invalid schedule.')
            value=checked.days
        else:
            field=target._meta.get_field(name)
            if name in {'photo','cover_photo'}:
                # Only form adapters may supply names already held by storage.
                if value and str(value)!=str(getattr(target,name) or '') and not field.storage.exists(str(value)):raise ValidationError('Uploaded file missing.')
            value=field.to_python(value) if not field.is_relation else value
            setattr(candidate,field.attname,value)
            if field.is_relation:
                field.validate(value,candidate)
                if value is not None and not field.remote_field.model.objects.filter(pk=value).exists():raise ValidationError('Publication relation missing.')
            else:field.validate(value,candidate);field.run_validators(value)
        normalized[name]=json_value(value)
    if kind in {'place','offering_group'} and candidate.age_from is not None and candidate.age_to is not None and candidate.age_from>candidate.age_to:raise ValidationError('Age range invalid.')
    if kind=='place' and candidate.subcategory_id and candidate.subcategory.category_id!=candidate.category_id:raise ValidationError('Category mismatch.')
    if kind in {'program','activity'}:
        from catalog.services.catalog_structure import validate_taxonomy
        validate_taxonomy(candidate.category_id,candidate.subcategory_id)
        if kind=='activity' and target.program_id and {'category','subcategory'} & set(patch):
            raise ValidationError('Linked Activity taxonomy comes from the approved Program.')
    return normalized


def _apply(target,kind,patch):
    values={};now=timezone.now()
    for name,value in patch.items():
        if name in {'pricing_plans','nested_pricing','structured_schedule','gallery','location_override'}:continue
        field=target._meta.get_field(name);values[field.attname]=field.to_python(value) if not field.is_relation else value
    if kind=='activity' and target.program_id is None and {'category','subcategory'} & set(patch):
        # A detached approved copy must not revive old taxonomy after an explicit clear.
        common=dict(target.program_snapshot)
        common['category_id']=values.get('category_id',target.category_id)
        common['subcategory_id']=values.get('subcategory_id',target.subcategory_id)
        values['program_snapshot']=common
    if kind=='place':
        if {'lat','lng','district','location_override'} & set(patch):
            from django.contrib.auth import get_user_model
            from catalog.services.location_assignment import prepare_place_location, set_location_override
            previous = copy.copy(target)
            for name in ('lat','lng','district'):
                if name in values:setattr(target,name,values[name])
            requested = patch.get('location_override')
            if requested:
                if (float(target.lat),float(target.lng)) != (float(requested['lat']),float(requested['lng'])):
                    raise ValidationError('Location override coordinates conflict.')
                set_location_override(target,actor=get_user_model().objects.get(pk=requested['actor_id']),
                    city=requested['city'],district=requested['district'],reason=requested['reason'])
            location_fields, location_audit = prepare_place_location(target,previous=previous,
                update_fields=None,using=target._state.db or 'default')
            values.update({name:getattr(target,name) for name in location_fields})
            if location_audit:
                target.location_overrides.create(**location_audit)
                del target._location_override_request
        from catalog.services.map_payload import venue_identity_patch_changed
        if target.confirmed_location_id and venue_identity_patch_changed(previous if {'lat','lng','district','location_override'} & set(patch) else target, values):
            values.update(confirmed_location_id=None, venue_confirmed_at=None)
        if 'nature' in patch:values['nature_approved_at']=now
        if 'operating_state' in patch:values['operating_state_approved_at']=now
        if any(n.startswith('name_') for n in patch):values['name']=next((patch.get('name_'+l) or getattr(target,'name_'+l) for l in ('az','ru','en') if patch.get('name_'+l) or getattr(target,'name_'+l)),target.name)
    if kind == 'offering_group' and ({'age_from', 'age_to'} & set(patch)):
        from catalog.services.pricing_plans import validate_group_plan_ages
        validate_group_plan_ages(target, values.get('age_from', target.age_from), values.get('age_to', target.age_to))
    if kind == 'offering_group' and any(name.startswith('conditions_') for name in patch):
        values['conditions_verified_at'] = None
    values.update(content_version=F('content_version')+1,updated_at=now);type(target).objects.filter(pk=target.pk).update(**values);target.refresh_from_db()
    if kind in {'activity', 'offering_group'} and ({'status', 'archived_at'} & set(patch)):
        from catalog.services.pricing_plans import sync_legacy_price_fields
        place_id = target.place_id if kind == 'activity' else target.activity.place_id
        sync_legacy_price_fields(place_id)
    if 'pricing_plans' in patch:
        from catalog.services.pricing_plans import replace_place_pricing_plans
        replace_place_pricing_plans(target,patch['pricing_plans'])
    if 'nested_pricing' in patch:
        from catalog.services.pricing_plans import replace_nested_pricing
        replace_nested_pricing(target,patch['nested_pricing'])
    if 'structured_schedule' in patch:
        from catalog.services.place_schedule import sync_place_schedule
        sync_place_schedule(target,patch['structured_schedule'])
    if 'gallery' in patch:
        from catalog.models import PlacePhoto
        keep=[]
        for row in patch['gallery']:
            values={k:v for k,v in row.items() if k!='id'}
            if row['id'] is None:photo=PlacePhoto.objects.create(place=target,**values);keep.append(photo.pk)
            else:PlacePhoto.objects.filter(place=target,pk=row['id']).update(**values);keep.append(row['id'])
        target.gallery.exclude(pk__in=keep).delete()
    target.refresh_from_db()
    from django.core.cache import cache
    transaction.on_commit(lambda: cache.delete("catalog:publication"))


def _immediate(target,kind,patch,explicit):
    if not explicit:return set()
    if kind=='offering_group':return {'schedule_text'} & patch.keys()
    if kind!='place':return set()
    price_keys=PRICES & patch.keys()
    if not CONDITIONS.intersection(patch):
        if 'pricing_plans' in patch:
            old=target.pricing_plans;new=patch['pricing_plans'];amounts={'price','price_min','price_max'}
            strip=lambda plans:[{k:v for k,v in p.items() if k not in amounts | {'verified_at'}} for p in plans]
            if strip(old)==strip(new):price_keys.add('pricing_plans')
        return (SCHEDULE & patch.keys()) | price_keys
    return SCHEDULE & patch.keys()


@transaction.atomic
def propose(*,actor,target_type,target_id,patch,schema_version,expected_version,revision_version=0,submit=True,explicit_save=True):
    if not isinstance(submit,bool) or not isinstance(explicit_save,bool):raise ValidationError('Save flags must be boolean.')
    actor=fresh_actor(actor);target=locked_target(target_type,target_id);authorize(actor,target,target_type)
    if isinstance(patch,dict) and 'location_override' in patch and patch['location_override'] != snapshot(target,target_type).get('location_override'):
        from catalog.services.location_assignment import can_override_location
        if not can_override_location(actor) or (patch['location_override'] is not None and
            (not isinstance(patch['location_override'],dict) or patch['location_override'].get('actor_id') != actor.pk)):
            raise PermissionDenied
    if _integer(schema_version)!=SCHEMA_VERSION:raise ValidationError('Publication schema conflict.')
    if _integer(expected_version)!=target.content_version:raise ValidationError('Publication source conflict.')
    revision=VolunteerPlaceRevision.objects.select_for_update().filter(**{target_type:target}).first()
    actual=revision.version if revision else 0
    if _integer(revision_version)!=actual:raise ValidationError('Candidate version conflict.')
    from catalog.services.staff_roles import is_volunteer
    if revision and is_volunteer(actor) and revision.author_id != actor.pk:
        raise PermissionDenied
    patch=_validate_patch(target,target_type,patch);live=snapshot(target,target_type)
    if revision and revision.status not in {'approved','rejected','declined'}:
        if revision.schema_version!=SCHEMA_VERSION or revision.dependencies!=dependencies(target,target_type):raise ValidationError('Candidate dependency conflict.')
        if any(live.get(k)!=revision.base_snapshot.get(k) for k in revision.changed_fields):raise ValidationError('Candidate source conflict.')
        base=revision.base_snapshot;pending=dict(revision.payload)
    else:base=live;pending={}
    incoming=dict(patch)
    changed={k:v for k,v in patch.items() if live[k]!=v}
    if 'pricing_plans' in pending and 'pricing_plans' in changed:
        amounts={'price','price_min','price_max'}
        strip=lambda plans:[{k:v for k,v in p.items() if k not in amounts | {'verified_at'}} for p in plans]
        if strip(live['pricing_plans'])==strip(patch['pricing_plans']):
            by_id={p.get('id'):p for p in patch['pricing_plans']}
            incoming['pricing_plans']=[{**p,**{k:v for k,v in by_id.get(p.get('id'),{}).items() if k in amounts}} for p in pending['pricing_plans']]
    immediate=_immediate(target,target_type,changed,explicit_save)
    if 'pricing_plans' in pending:immediate.discard('pricing_plans')
    # Changed conditions in an existing candidate keep newly changed amounts gated.
    if CONDITIONS.intersection(pending):immediate-=PRICES|{'pricing_plans'}
    if immediate:
        _apply(target,target_type,{k:patch[k] for k in immediate});live=snapshot(target,target_type)
        for k in immediate:base[k]=live[k];pending.pop(k,None)
    pending.update({k:v for k,v in incoming.items() if k not in immediate});pending={k:v for k,v in pending.items() if v!=base.get(k)}
    if revision is None:revision=VolunteerPlaceRevision(**{target_type:target},author=actor)
    if not (revision.pk and platform_has_action(user=actor,action='place.publish')):revision.author=actor
    revision.schema_version=SCHEMA_VERSION;revision.base_content_version=target.content_version;revision.base_snapshot=base;revision.dependencies=dependencies(target,target_type);revision.payload=pending;revision.changed_fields=sorted(pending);revision.status='pending' if submit else 'draft';revision.version=actual+1;revision.review_note='' if submit else revision.review_note;revision.reviewed_by=None if submit else revision.reviewed_by;revision.save();return revision


@transaction.atomic
def review(*,actor,revision_id,version,approve,note='',final_reject=False):
    if not isinstance(approve,bool) or not isinstance(final_reject,bool) or (approve and final_reject):raise ValidationError('Approval flags must be valid.')
    actor=fresh_actor(actor);anchor=VolunteerPlaceRevision.objects.get(pk=revision_id);kind,pk=_kind(anchor);target=locked_target(kind,pk);authorize(actor,target,kind,review=True)
    revision=VolunteerPlaceRevision.objects.select_for_update().get(pk=revision_id)
    if _kind(revision)!=(kind,pk) or _integer(version)!=revision.version or revision.status!='pending':raise ValidationError('Candidate version/state conflict.')
    if revision.schema_version!=SCHEMA_VERSION:raise ValidationError('Publication schema conflict.')
    if not approve:
        if not note.strip():raise ValidationError('Rejection reason required.')
    else:
        if dependencies(target,kind)!=revision.dependencies:raise ValidationError('Publication dependency conflict.')
        author=fresh_actor(revision.author)
        authorize(author,target,kind)
        if 'location_override' in revision.payload:
            from catalog.services.location_assignment import can_override_location
            if not can_override_location(author) or (revision.payload['location_override'] is not None and revision.payload['location_override'].get('actor_id') != author.pk):
                raise PermissionDenied
        patch=_validate_patch(target,kind,revision.payload)
        if set(patch)!=set(revision.changed_fields):raise ValidationError('Candidate field conflict.')
        live=snapshot(target,kind)
        if any(live.get(k)!=revision.base_snapshot.get(k) for k in patch):raise ValidationError('Publication source conflict.')
        candidate=copy.copy(target);candidate._state=copy.copy(target._state)
        for name,value in patch.items():
            if name not in {'pricing_plans','nested_pricing','structured_schedule','gallery','location_override'}:field=target._meta.get_field(name);setattr(candidate,field.attname,field.to_python(value) if not field.is_relation else value)
        if kind=='place':
            from catalog.services.place_readiness import evaluate_place_readiness,publication_blocked_message
            # Existing published cards retain their compatibility path.
            if not target.is_public:
                if 'pricing_plans' in patch:candidate.pricing_plans=patch['pricing_plans']
                from types import SimpleNamespace
                from catalog.services.place_readiness import evaluate_form_readiness
                from catalog.services.place_schedule import serialize_place_schedule
                readiness=evaluate_form_readiness(SimpleNamespace(cleaned_data=patch,instance=candidate,cleaned_schedule_days=patch.get('structured_schedule',serialize_place_schedule(target))),candidate)
                if not readiness.is_ready:raise ValidationError(publication_blocked_message(readiness))
        elif not getattr(candidate,'name_az','').strip() and kind in {'organization','program','activity'}:raise ValidationError('AZ name required.')
        _apply(target,kind,patch)
        now=timezone.now()
        if kind=='place':Place.objects.filter(pk=pk).update(status='published',is_active=True,published_at=target.published_at or now,moderated_at=now,moderated_by=actor,rejection_reason='')
        elif kind in {'program','organization'}:type(target).objects.filter(pk=pk).update(status='published',approved_at=now)
        elif kind=='activity':Activity.objects.filter(pk=pk).update(status='published')
        if kind=='program':
            from catalog.services.organization_ownership import approved_program_data
            target.refresh_from_db();rows=list(Activity.objects.select_for_update().filter(program_id=pk,archived_at__isnull=True).order_by('pk'))
            if any(a.place.organization_id!=target.organization_id or a.place.deleted_at is not None for a in rows):raise ValidationError('Program propagation parent changed.')
            Activity.objects.filter(pk__in=[a.pk for a in rows]).update(program_snapshot=approved_program_data(target),source_program=target,source_program_version=target.content_version,content_version=F('content_version')+1,updated_at=now)
    revision.status='approved' if approve else 'declined' if final_reject else 'rejected';revision.reviewed_by=actor;revision.review_note=note.strip();revision.version+=1;revision.save()
    from catalog.services.workflow_notifications import emit
    emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=revision.pk, version=revision.version, recipient_user=revision.author)
    return revision


@transaction.atomic
def publish(*,actor,place_id,expected_version):
    actor=fresh_actor(actor);place=locked_target('place',place_id);authorize(actor,place,'place',review=True)
    if _integer(expected_version)!=place.content_version:raise ValidationError('Publication source conflict.')
    revision=VolunteerPlaceRevision.objects.filter(place=place).first()
    if revision and revision.status=='pending':return review(actor=actor,revision_id=revision.pk,version=revision.version,approve=True)
    from catalog.services.place_readiness import evaluate_place_readiness,publication_blocked_message
    readiness=evaluate_place_readiness(place)
    if not place.is_public and not readiness.is_ready:raise ValidationError(publication_blocked_message(readiness))
    Place.objects.filter(pk=place.pk).update(status='published',is_active=True,published_at=place.published_at or timezone.now(),moderated_at=timezone.now(),moderated_by=actor,content_version=F('content_version')+1);place.refresh_from_db();return place


@transaction.atomic
def unpublish(*, actor, target_type, target_id, expected_version):
    """Withdraw published content with the existing platform reviewer permission."""
    if target_type not in {'place', 'organization', 'program', 'activity'}:
        raise ValidationError('Unsupported publication target.')
    actor = fresh_actor(actor)
    target = locked_target(target_type, target_id)
    authorize(actor, target, target_type, review=True)
    if _integer(expected_version) != target.content_version:
        raise ValidationError('Publication source conflict.')
    revision = VolunteerPlaceRevision.objects.select_for_update().filter(**{target_type: target}).first()
    if revision and revision.status in {'draft', 'pending'}:
        raise ValidationError('Resolve the current candidate before unpublishing.')
    if target.status != 'published':
        raise ValidationError('Target is not published.')
    values = {'status': 'draft', 'content_version': F('content_version') + 1, 'updated_at': timezone.now()}
    if target_type == 'place':
        values['is_active'] = False
    type(target).objects.filter(pk=target.pk).update(**values)
    target.refresh_from_db()
    return target
