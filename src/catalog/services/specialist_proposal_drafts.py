"""Explicit draft saves and idempotent sends under actor and draft locks."""
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models.fields.files import FieldFile
from django.http import QueryDict
from django.utils import timezone
from django.utils.translation import gettext as _
from catalog.forms import OwnerSpecialistForm
from catalog.forms_specialist_locations import PracticeLocationForm,practice_location_formset
from catalog.models import Specialist,SpecialistProposalDraft
from catalog.services import specialist_domain
from catalog.services.specialist_proposal_documents import qualification_formset, save_qualifications, transfer_confirmed_qualifications
from catalog.services.specialist_formats import legacy_format_codes, profile_format_codes
from catalog.services.owner_specialist_use_cases import save_owner_specialist_profile

PUBLIC_FIELDS=set(OwnerSpecialistForm.Meta.fields)-{'photo'}
MULTI_FIELDS = {'specializations', 'visit_districts', 'session_formats'}


def _legacy_proposal_formats(payload):
    scalar = (payload.get('consultation_format') or [''])[-1]
    codes = list(legacy_format_codes(scalar))
    if 'office' in codes:
        # Older drafts can be incomplete. Only mark an office automatically when
        # the author supplied an active, identified practice location.
        def last(prefix, field):
            return (payload.get(prefix + field) or [''])[-1]

        for index in range(31):
            prefix = f'locations-{index}-'
            active = last(prefix, 'is_active') in ('on', 'true', '1', True)
            deleted = last(prefix, 'DELETE') in ('on', 'true', '1', True)
            identified = last(prefix, 'place') or last(prefix, 'address').strip()
            if active and not deleted and last(prefix, 'region') and identified:
                break
        else:
            codes.remove('office')
    return codes


def get_proposal(*,actor,draft_id):
    actor=specialist_domain.require_actor(actor)
    draft=SpecialistProposalDraft.objects.get(pk=draft_id)
    if draft.actor_id!=actor.pk:raise PermissionDenied
    return draft


def proposal_data(payload):
    result=QueryDict('',mutable=True)
    for key,values in payload.items():result.setlist(key,values)
    return result


def saved_profile_subject(draft):
    # Earlier proposals did not carry a subject. They were proposals for other people.
    values = draft.payload.get('profile_subject') or []
    return 'self' if values and values[-1] == 'self' else 'other'


def _payload(data):
    # Subject is an application intent, never identity proof or authority.
    # No authority IDs, consent, document metadata or arbitrary form keys.
    # Location IDs are accepted only through the parent-scoped validated formset.
    keys=set(PUBLIC_FIELDS) | {'profile_subject', 'photo-clear'}
    keys.update('locations-'+key for key in ('TOTAL_FORMS','INITIAL_FORMS','MIN_NUM_FORMS','MAX_NUM_FORMS'))
    for i in range(31):keys.update(f'locations-{i}-{key}' for key in (*PracticeLocationForm.Meta.fields,'id','DELETE'))
    return {key:data.getlist(key) for key in keys if key in data}


def proposal_forms(*,actor,data=None,files=None,submit=False,payload=None,draft=None):
    specialist = None
    if draft is not None and draft.submitted_specialist_id and not draft.submitted_at:
        specialist = Specialist.objects.get(pk=draft.submitted_specialist_id)
        specialist_domain.require_proposal_revision(actor, specialist, draft)
    if data is None:
        payload = payload or {}
        initial = {key: (values if key in MULTI_FIELDS else values[-1])
                   for key, values in payload.items() if key in PUBLIC_FIELDS and values}
        if payload:
            initial['session_formats'] = (
                payload['session_formats'] if 'session_formats' in payload else _legacy_proposal_formats(payload)
            )
            initial['visit_region'] = (payload.get('visit_region') or [''])[-1]
            initial['visit_districts'] = payload.get('visit_districts', [])
            initial['visit_citywide'] = (payload.get('visit_citywide') or [''])[-1] in ('on', 'true', '1', True)
        form=OwnerSpecialistForm(initial=initial,instance=specialist,actor=actor,draft_save_only=True)
        if (payload or {}).get('photo-clear'):
            form.initial['photo'] = False
        # Checkbox values in HTTP are strings; do not turn 'false' into True.
        for key in ('language_az','language_ru','language_en'):
            if key in initial:form.initial[key]=str(initial[key]).lower() not in ('false','0','')
        rows=proposal_data(payload) if payload else None
    else:
        form=OwnerSpecialistForm(data,files,instance=specialist,actor=actor,draft_save_only=not submit)
        rows=data
    locations=practice_location_formset(actor=actor,specialist=form.instance,data=rows,require_active=submit,
                                        proposal_draft=draft if specialist else None)
    form.locations=locations
    return form,locations


def save_proposal(*,actor,draft_id,expected_version,data,files,submit=False):
    new_photo=None
    created_documents = []
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
            if draft and draft.payload.get('photo-clear') and not files.get('photo'):
                data = data.copy()
                data['photo-clear'] = 'on'
            subject = saved_profile_subject(draft) if draft else data.get('profile_subject', 'other')
            if subject not in ('self', 'other'):
                raise ValidationError(_('Выберите, чей профиль вы добавляете.'))
            if draft and draft.submitted_specialist_id:
                # Actor -> draft -> person, matching moderator return lock order.
                person = Specialist.objects.select_for_update().get(pk=draft.submitted_specialist_id)
                specialist_domain.require_proposal_revision(actor, person, draft)
            form,locations=proposal_forms(actor=actor,data=data,files=files,submit=submit,draft=draft)
            if files.get('documents') or data.get('documents'):
                form.add_error('documents',_('Документы может загрузить только подтверждённый специалист.'))
            form.qualification_formset = qualification_formset(draft=draft, subject=subject, data=data, files=files)
            if form.qualification_formset.is_bound and not form.qualification_formset.is_valid():
                form.add_error(None, _('Проверьте дипломы и сертификаты.'))
            if not form.is_valid():
                error=ValidationError(_('Проверьте поля формы.'),code='invalid_form')
                error.form=form;error.locations=locations
                raise error
            draft=draft or SpecialistProposalDraft(pk=draft_id,actor=actor,version=0)
            old_photo=draft.photo.name
            uploaded=form.cleaned_data.get('photo')
            if isinstance(uploaded, FieldFile) and uploaded._committed:
                uploaded = None
            if uploaded:
                uploaded.seek(0)
                draft.photo.save(uploaded.name,uploaded,save=False)
                new_photo=draft.photo.name
                draft.photo_content_type=getattr(uploaded,'content_type','image/jpeg')
            elif data.get('photo-clear'):
                draft.photo='';draft.photo_content_type=''
            draft.payload = _payload(form.data)
            draft.payload['session_formats'] = list(form.cleaned_data.get('session_formats') or ())
            # Keep the projection readable to older clients. Visits have no scalar equivalent.
            draft.payload['consultation_format'] = [form.instance.consultation_format]
            draft.payload['visit_citywide'] = ['on'] if form.cleaned_data.get('visit_citywide') else []
            draft.payload['profile_subject'] = [subject]
            draft.version += 1
            if submit:
                # Temporary files stay outside public media until a valid send.
                if draft.photo and not uploaded:
                    with draft.photo.open('rb') as stream:
                        form.files['photo']=ContentFile(stream.read(),name='proposal.jpg')
                result=save_owner_specialist_profile(user=actor,form=form,draft_save_only=False,locations=locations,
                                                     proposal_draft=draft if draft.submitted_specialist_id else None)
                if not result.ok:
                    error=ValidationError(_('Проверьте поля формы.'),code='invalid_form');error.form=result.form;error.locations=locations
                    raise error
                draft.submitted_specialist=result.specialist;draft.submitted_at=timezone.now()
                if subject == 'self' and not result.specialist.verified_person_user_id:
                    specialist_domain.request_claim(actor=actor, specialist_id=result.specialist.pk)
                draft.photo='';draft.photo_content_type=''
            draft.save()
            save_qualifications(draft=draft, formset=form.qualification_formset, created_paths=created_documents)
            if submit and subject == 'self':
                transfer_confirmed_qualifications(draft.submitted_specialist)
            if old_photo and old_photo!=draft.photo.name:
                storage=draft.photo.storage
                transaction.on_commit(lambda: storage.delete(old_photo), robust=True)
            if new_photo and new_photo!=draft.photo.name:
                storage=draft.photo.storage
                transaction.on_commit(lambda: storage.delete(new_photo), robust=True)
            return draft
    except Exception:
        from catalog.private_storage import specialist_private_storage
        for filename in created_documents:
            specialist_private_storage.delete(filename)
        if new_photo:
            specialist_private_storage.delete(new_photo)
        raise


def _revision_payload(specialist, subject):
    """Snapshot current public fields and stable location IDs; retain private files."""
    data = QueryDict('', mutable=True)
    data['profile_subject'] = subject
    for name in PUBLIC_FIELDS:
        if name in ('specializations', 'visit_districts'):
            related = getattr(specialist, name)
            data.setlist(name, [str(pk) for pk in related.values_list('pk', flat=True)])
        elif name == 'session_formats':
            data.setlist(name, list(profile_format_codes(specialist)))
        elif name == 'visit_region':
            data[name] = str(specialist.visit_region_id or '')
        else:
            value = getattr(specialist, name)
            data[name] = ('on' if value else '') if isinstance(value, bool) else '' if value is None else str(value)
    rows = list(specialist.practice_locations.order_by('pk'))
    data.update({'locations-TOTAL_FORMS':str(len(rows)), 'locations-INITIAL_FORMS':str(len(rows)),
                 'locations-MIN_NUM_FORMS':'0', 'locations-MAX_NUM_FORMS':'30'})
    for index, row in enumerate(rows):
        data[f'locations-{index}-id'] = str(row.pk)
        for name in PracticeLocationForm.Meta.fields:
            field = row._meta.get_field(name)
            value = getattr(row, field.attname)
            data[f'locations-{index}-{name}'] = ('on' if value else '') if isinstance(value, bool) else '' if value is None else str(value)
    return _payload(data)


@transaction.atomic
def return_for_revision(*, actor, specialist_id, comment=''):
    """Reopen the original application, without granting ownership or copying docs.

    ``comment`` is what the author must fix; it is stored as the profile's
    moderation reason and sent with the author's notification.
    """
    from catalog.services.staff_roles import is_volunteer
    actor = specialist_domain.require_actor(actor)
    author_id = Specialist.objects.values_list('created_by_id', flat=True).get(pk=specialist_id)
    users = specialist_domain._lock_users([actor.pk, author_id])
    actor = users[actor.pk]
    if not actor.is_staff or is_volunteer(actor) or not actor.has_perm('catalog.change_specialist'):
        raise PermissionDenied
    draft = SpecialistProposalDraft.objects.select_for_update().filter(
        submitted_specialist_id=specialist_id, actor_id=author_id,
    ).order_by('-updated_at').first()
    person = Specialist.objects.select_for_update().get(pk=specialist_id)
    if person.created_by_id != author_id:
        raise ValidationError(_('Запись изменилась. Обновите страницу.'), code='stale_version')
    if person.status != Specialist.STATUS_PENDING:
        raise ValidationError(_('На доработку можно вернуть только анкету на проверке.'))
    from catalog.services import specialist_moderation
    reason = (comment or '').strip()[:specialist_moderation.REASON_LIMIT] or specialist_moderation.default_reason(
        specialist_moderation.NEEDS_CHANGES)
    person.status = Specialist.STATUS_DRAFT
    person.is_active = False
    person.rejection_reason = reason
    person.save(update_fields=['status', 'is_active', 'rejection_reason', 'updated_at'])
    specialist_moderation.reopen_author_draft(person)
    specialist_moderation.notify_decision(person, specialist_moderation.NEEDS_CHANGES, reason, actor=actor)
    return person
