from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext as _

from catalog.forms import OwnerSpecialistForm
from catalog.models import Specialist, SpecialistDocument, SpecialistPracticeLocation
from catalog.services import specialist_domain


@dataclass(slots=True)
class OwnerSpecialistResult:
    ok: bool
    message: str
    form: OwnerSpecialistForm | None = None
    specialist: Specialist | None = None


def _sync_primary_location(*, specialist: Specialist, form: OwnerSpecialistForm) -> None:
    consultation_format = form.cleaned_data.get("consultation_format")
    if consultation_format not in {Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH}:
        specialist.practice_locations.filter(is_active=True).update(is_active=False)
        return

    values = {
        'place_id': getattr(form.cleaned_data.get('location_place'), 'pk', None),
        'address': form.cleaned_data.get('location_address') or '',
        'region_id': getattr(form.cleaned_data.get('location_region'), 'pk', None),
        'district_id': getattr(form.cleaned_data.get('location_district'), 'pk', None),
        'metro_id': getattr(form.cleaned_data.get('location_metro'), 'pk', None),
    }
    location = specialist.practice_locations.select_for_update().filter(is_primary=True).first()
    if location is not None and any(getattr(location, key) != value for key, value in values.items()):
        location.is_primary = False
        location.is_active = False
        location.save(update_fields=['is_primary', 'is_active'])
        location = None
    if location is None:
        location = SpecialistPracticeLocation(specialist=specialist, is_primary=True, **values)
    location.is_active = True
    location.save()


def _create_pending_documents(*, user, specialist: Specialist, form: OwnerSpecialistForm) -> None:
    from catalog.services.specialist_documents import upload_document
    for uploaded_file in form.cleaned_data.get("documents") or []:
        upload_document(
            actor=user, specialist_id=specialist.pk,
            document_type=SpecialistDocument.TYPE_CERTIFICATE,
            name=getattr(uploaded_file, "name", "") or _("Документ"),
            uploaded_file=uploaded_file,
        )


def save_owner_specialist_profile(
    *,
    user,
    form: OwnerSpecialistForm,
    draft_save_only: bool,
    expected_updated_at: str | None = None,
    locations=None,
) -> OwnerSpecialistResult:
    with transaction.atomic():
        user = specialist_domain.lock_actor(user)
        is_new = form.instance.pk is None
        if not is_new:
            locked = Specialist.objects.select_for_update().get(pk=form.instance.pk)
            specialist_domain.require_person(user, locked)
            if expected_updated_at is not None and expected_updated_at != locked.updated_at.isoformat():
                from django.core.exceptions import ValidationError
                raise ValidationError(_("Запись изменилась. Обновите страницу."), code='stale_version')
            form.instance = locked
        # The controller may have validated already; rebind to the locked row.
        form.full_clean()
        if not form.is_valid():
            return OwnerSpecialistResult(ok=False, message=_("Проверьте поля формы."), form=form)
        if is_new and form.cleaned_data.get('documents'):
            form.add_error('documents', _("Документы может загрузить только подтверждённый специалист."))
            return OwnerSpecialistResult(ok=False, message=_("Проверьте поля формы."), form=form)
        specialist = form.save(commit=False)
        if is_new:
            specialist.owner = None
            specialist.created_by = user
            specialist.verified_person_user = None
            specialist.person_verified_at = None
        specialist.status = Specialist.STATUS_DRAFT if draft_save_only else Specialist.STATUS_PENDING
        specialist.save()
        form.save_m2m()
        locations = locations if locations is not None else getattr(form,'locations',None)
        if locations is not None:
            locations.instance=specialist
            locations.full_clean()
            if not locations.is_valid():
                from django.core.exceptions import ValidationError
                raise ValidationError(_('Проверьте места приёма.'))
            from catalog.forms_specialist_locations import save_practice_locations
            save_practice_locations(specialist=specialist,formset=locations)
        else:
            _sync_primary_location(specialist=specialist, form=form)
        _create_pending_documents(user=user, specialist=specialist, form=form)

    message = (
        _("Черновик профиля сохранён.")
        if draft_save_only
        else _("Профиль отправлен на модерацию. После проверки он появится в каталоге.")
    )
    return OwnerSpecialistResult(ok=True, message=message, form=form, specialist=specialist)
