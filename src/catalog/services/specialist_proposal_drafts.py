"""Explicit draft saves and idempotent sends under actor and draft locks."""
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import QueryDict
from django.utils import timezone
from django.utils.translation import gettext as _
from catalog.forms import OwnerSpecialistForm
from catalog.forms_specialist_locations import PracticeLocationForm,practice_location_formset
from catalog.models import Specialist,SpecialistProposalDraft
from catalog.services import specialist_domain
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile

PUBLIC_FIELDS=set(OwnerSpecialistForm.Meta.fields)-{'photo'}


def get_proposal(*,actor,draft_id):
    actor=specialist_domain.require_actor(actor)
    draft=SpecialistProposalDraft.objects.get(pk=draft_id)
    if draft.actor_id!=actor.pk:raise PermissionDenied
    return draft


def proposal_data(payload):
    result=QueryDict('',mutable=True)
    for key,values in payload.items():result.setlist(key,values)
    return result


def _payload(data):
    # No IDs, claims, consent, document metadata, tokens or arbitrary form keys.
    keys=set(PUBLIC_FIELDS)
    keys.update('locations-'+key for key in ('TOTAL_FORMS','INITIAL_FORMS','MIN_NUM_FORMS','MAX_NUM_FORMS'))
    for i in range(31):keys.update(f'locations-{i}-{key}' for key in (*PracticeLocationForm.Meta.fields,'DELETE'))
    return {key:data.getlist(key) for key in keys if key in data}


def proposal_forms(*,actor,data=None,files=None,submit=False,payload=None):
    if data is None:
        initial={key:(values if key=='specializations' else values[-1]) for key,values in (payload or {}).items() if key in PUBLIC_FIELDS and values}
        form=OwnerSpecialistForm(initial=initial,actor=actor,draft_save_only=True)
        # Checkbox values in HTTP are strings; do not turn 'false' into True.
        for key in ('language_az','language_ru','language_en'):
            if key in initial:form.initial[key]=str(initial[key]).lower() not in ('false','0','')
        rows=proposal_data(payload) if payload else None
    else:
        form=OwnerSpecialistForm(data,files,actor=actor,draft_save_only=not submit)
        rows=data
    locations=practice_location_formset(actor=actor,specialist=form.instance,data=rows,require_active=submit)
    form.locations=locations
    return form,locations


def save_proposal(*,actor,draft_id,expected_version,data,files,submit=False):
    new_photo=None
    try:
        with transaction.atomic():
            actor=specialist_domain.lock_actor(actor)
            draft=SpecialistProposalDraft.objects.select_for_update().filter(pk=draft_id).first()
            if draft and draft.actor_id!=actor.pk:raise PermissionDenied
            if draft and draft.submitted_at:
                if submit and draft.submitted_specialist_id:return draft  # A repeated send never creates a second person.
                raise ValidationError(_('Предложение уже отправлено.'))
            current=draft.version if draft else 0
            if str(current)!=str(expected_version):raise ValidationError(_('Запись изменилась. Обновите страницу.'),code='stale_version')
            form,locations=proposal_forms(actor=actor,data=data,files=files,submit=submit)
            if files.get('documents') or data.get('documents'):
                form.add_error('documents',_('Документы может загрузить только подтверждённый специалист.'))
            if not form.is_valid():
                error=ValidationError(_('Проверьте поля формы.'),code='invalid_form')
                error.form=form;error.locations=locations
                raise error
            draft=draft or SpecialistProposalDraft(pk=draft_id,actor=actor,version=0)
            old_photo=draft.photo.name
            uploaded=form.cleaned_data.get('photo')
            if uploaded:
                uploaded.seek(0)
                draft.photo.save(uploaded.name,uploaded,save=False)
                new_photo=draft.photo.name
                draft.photo_content_type=getattr(uploaded,'content_type','image/jpeg')
            elif data.get('photo-clear'):
                draft.photo='';draft.photo_content_type=''
            draft.payload=_payload(data);draft.version+=1
            if submit:
                # Temporary files stay outside public media until a valid send.
                if draft.photo and not uploaded:
                    with draft.photo.open('rb') as stream:
                        form.files['photo']=ContentFile(stream.read(),name='proposal.jpg')
                result=save_owner_specialist_profile(user=actor,form=form,draft_save_only=False,locations=locations)
                if not result.ok:
                    error=ValidationError(_('Проверьте поля формы.'),code='invalid_form');error.form=result.form;error.locations=locations
                    raise error
                draft.submitted_specialist=result.specialist;draft.submitted_at=timezone.now()
                draft.photo='';draft.photo_content_type=''
            draft.save()
            if old_photo and old_photo!=draft.photo.name:
                storage=draft.photo.storage
                transaction.on_commit(lambda:storage.delete(old_photo))
            if new_photo and new_photo!=draft.photo.name:
                storage=draft.photo.storage
                transaction.on_commit(lambda:storage.delete(new_photo))
            return draft
    except Exception:
        if new_photo:
            from catalog.private_storage import specialist_private_storage
            specialist_private_storage.delete(new_photo)
        raise
