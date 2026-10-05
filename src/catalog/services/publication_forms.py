"""Adapters for validated legacy forms; server-signed source/candidate token."""
from django import forms
from django.core import signing
from django.db import transaction
from django.core.exceptions import ValidationError
from catalog.models import Place, VolunteerPlaceRevision
from catalog.services import publication


def version_token(place):
    if place.pk:place=Place.objects.get(pk=place.pk)
    revision=VolunteerPlaceRevision.objects.filter(place=place).first() if place.pk else None
    return signing.dumps({'id':place.pk,'schema':publication.SCHEMA_VERSION,'source':place.content_version,'candidate':revision.version if revision else 0,'snapshot':publication.snapshot(place,'place'),'dependencies':publication.dependencies(place,'place') if place.pk else {}},salt='publication-source')


def init_version_field(form):
    form.fields['publication_token']=forms.CharField(required=False,widget=forms.HiddenInput())
    live=Place.objects.get(pk=form.instance.pk) if form.instance.pk else form.instance
    form.initial['publication_token']=version_token(live)
    if live.pk and 'location_override_reason' in form.fields:
        from catalog.services.location_assignment import can_override_location
        if can_override_location(getattr(form, 'location_actor', None)):
            revision = VolunteerPlaceRevision.objects.filter(place=live,
                status__in=['draft','pending','rejected']).first()
            metadata = revision.payload.get('location_override') if revision else None
            if metadata:
                form.initial['location_override_reason'] = metadata['reason']


def source_version(form,place):
    try:data=signing.loads(form.data.get('publication_token',''),salt='publication-source')
    except signing.BadSignature:raise ValidationError('Publication source token missing/invalid; reload the form.')
    if data['id']!=place.pk or data['schema']!=publication.SCHEMA_VERSION or data['source']!=place.content_version or data['snapshot']!=publication.snapshot(place,'place') or data['dependencies']!=publication.dependencies(place,'place'):raise ValidationError('Publication source/schema conflict; reload the form.')
    return data


@transaction.atomic
def save_form(*,actor,form,submit=True,explicit_save=True):
    place=publication.locked_target('place',form.instance.pk);base=source_version(form,place)
    candidate=form.instance
    for name in ('photo','cover_photo'):
        value=getattr(candidate,name)
        if value and not value._committed:
            try:value.save(value.name,value.file,save=False)
            except (OSError,RuntimeError) as exc:raise ValidationError({name:'Photo upload failed; retry the save.'}) from exc
    patch=publication.snapshot(candidate,'place')
    override_request = getattr(candidate, '_location_override_request', None)
    if override_request:
        patch['location_override'] = {
            key: override_request[key] for key in ('city', 'district', 'reason', 'lat', 'lng')
        }
        patch['location_override']['actor_id'] = override_request['actor'].pk
    # Explicit values also cancel pending fields reverted to approved live values.
    if 'pricing_plans' in form.cleaned_data:
        plans=form.cleaned_data['pricing_plans']
        if plans or place.pricing_plan_records.exists():patch['pricing_plans']=plans
    if form.cleaned_data.get('nested_pricing'):
        patch['nested_pricing']=form.cleaned_data['nested_pricing']
    else:
        revision=VolunteerPlaceRevision.objects.filter(place=place,status__in=['draft','pending']).first()
        if revision and 'nested_pricing' in revision.payload:
            patch['nested_pricing']=revision.payload['nested_pricing']
    gallery=gallery_from_form(place,form)
    if gallery is not None:patch['gallery']=gallery
    if getattr(form,'cleaned_schedule_days',None) is not None:patch['structured_schedule']=form.cleaned_schedule_days
    return publication.propose(actor=actor,target_type='place',target_id=place.pk,patch=patch,schema_version=base['schema'],expected_version=base['source'],revision_version=base['candidate'],submit=submit,explicit_save=explicit_save)


@transaction.atomic
def create_from_form(*,actor,form,owner=None,submit=True):
    """New draft has no approved content; form values live in its candidate."""
    candidate=form.instance
    # Admin may exclude legacy name from ModelForm construction while its clean()
    # supplies a validated name (including the empty-draft display placeholder).
    if 'name' in form.cleaned_data:
        candidate.name=form.cleaned_data['name']
    raw=form.data.get('publication_token')
    if raw:
        try:token=signing.loads(raw,salt='publication-source')
        except signing.BadSignature:raise ValidationError('Invalid publication creation token.')
        if token['id'] is not None or token['schema']!=publication.SCHEMA_VERSION:raise ValidationError('Publication creation schema conflict.')
    if not candidate.category_id:
        from catalog.models import Category
        candidate.category=Category.objects.order_by('order','code').first()
    base=Place.objects.create(name=candidate.name,category_id=candidate.category_id,owner=owner,created_by=actor,status='draft',is_active=False)
    for name in ('photo','cover_photo'):
        value=getattr(candidate,name)
        if value and not value._committed:
            try:value.save(value.name,value.file,save=False)
            except (OSError,RuntimeError) as exc:raise ValidationError({name:'Photo upload failed; retry the save.'}) from exc
    candidate.pk=base.pk;candidate._state.adding=False;candidate._state.db=base._state.db
    patch=publication.snapshot(candidate,'place')
    if 'pricing_plans' in form.cleaned_data:patch['pricing_plans']=form.cleaned_data['pricing_plans']
    if form.cleaned_data.get('nested_pricing') and form.cleaned_data['nested_pricing'].get('activities'):
        patch['nested_pricing']=form.cleaned_data['nested_pricing']
    patch['structured_schedule']=getattr(form,'cleaned_schedule_days',[])
    gallery=gallery_from_form(base,form)
    if gallery is not None:patch['gallery']=gallery
    publication.propose(actor=actor,target_type='place',target_id=base.pk,patch=patch,schema_version=publication.SCHEMA_VERSION,expected_version=base.content_version,revision_version=0,submit=submit,explicit_save=True)
    base.refresh_from_db();return base


def candidate_for_edit(place):
    if not getattr(place,'pk',None):return place
    revision=VolunteerPlaceRevision.objects.filter(place=place,status__in=['draft','pending','rejected']).first()
    if revision is None:return place
    from catalog.services.volunteer_places import candidate_from_payload
    return candidate_from_payload(place,revision.payload)


def gallery_from_form(place,form):
    from catalog.models import PlacePhoto
    if 'gallery_images' not in form.cleaned_data:return None
    deleted=set(map(int,form.cleaned_data.get('delete_gallery_ids') or []))
    revision=VolunteerPlaceRevision.objects.filter(place=place,status__in=['draft','pending','rejected']).first()
    base=revision.payload.get('gallery',publication.snapshot(place,'place')['gallery']) if revision else publication.snapshot(place,'place')['gallery']
    rows=[dict(row) for row in base if row['id'] not in deleted]
    for file in form.cleaned_data.get('gallery_images') or []:
        photo=PlacePhoto(place=place,caption='',order=len(rows))
        try:
            photo.image.save(file.name,file,save=False)
        except (OSError,RuntimeError) as exc:
            raise ValidationError({'gallery_images':'Photo upload failed; retry the save.'}) from exc
        rows.append({'id':None,'image':photo.image.name,'caption':'','order':len(rows)})
    order=form.cleaned_data.get('gallery_order') or []
    positions={str(key):i for i,key in enumerate(order)}
    new_index=0
    for row in rows:
        key=f"saved:{row['id']}" if row['id'] is not None else f'new:{new_index}'
        if row['id'] is None:new_index+=1
        row['order']=positions.get(key,row['order'])
    return rows


@transaction.atomic
def save_admin_related(*,actor,place,formsets,uploads,submit):
    from catalog.models import PlacePhoto
    from catalog.services.image_uploads import normalize_uploaded_image
    place=publication.locked_target('place',place.pk);revision=VolunteerPlaceRevision.objects.select_for_update().filter(place=place).first()
    rows=revision.payload.get('gallery',publication.snapshot(place,'place')['gallery']) if revision and revision.status in {'draft','pending','rejected'} else publication.snapshot(place,'place')['gallery']
    rows=[dict(row) for row in rows];changed=False
    for formset in formsets:
        if formset.model is not PlacePhoto:continue
        for form in formset.forms:
            if not form.has_changed():continue
            changed=True;photo=form.instance;deleted=form.cleaned_data.get('DELETE',False)
            rows=[r for r in rows if r['id']!=photo.pk] if photo.pk else rows
            if deleted:continue
            photo=form.save(commit=False)
            if photo.image and not photo.image._committed:photo.image.save(photo.image.name,photo.image.file,save=False)
            if photo.image:rows.append({'id':photo.pk,'image':photo.image.name,'caption':photo.caption,'order':photo.order})
    for file in uploads:
        changed=True;file=normalize_uploaded_image(file);photo=PlacePhoto(place=place,order=len(rows));photo.image.save(file.name,file,save=False)
        rows.append({'id':None,'image':photo.image.name,'caption':'','order':len(rows)})
    if changed:
        return publication.propose(actor=actor,target_type='place',target_id=place.pk,patch={'gallery':rows},schema_version=1,expected_version=place.content_version,revision_version=revision.version if revision else 0,submit=submit,explicit_save=True)
    return revision


def save_admin_metadata(place,cleaned):
    # Platform-only curation/verification bookkeeping is separate from content.
    names={'is_home_recommended','home_recommended_order','is_verified','last_verified_at'}
    values={name:cleaned[name] for name in names if name in cleaned and cleaned[name]!=getattr(place,name)}
    if values:
        from django.db.models import F
        values['content_version']=F('content_version')+1
        Place.objects.filter(pk=place.pk).update(**values);place.refresh_from_db()


def validate_form_source(form):
    if form.instance.pk:
        try:source_version(form,Place.objects.get(pk=form.instance.pk))
        except ValidationError as exc:form.add_error(None,exc)
