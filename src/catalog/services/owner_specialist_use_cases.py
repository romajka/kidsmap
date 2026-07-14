from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext as _

from catalog.forms import OwnerSpecialistForm
from catalog.models import Specialist, SpecialistDocument, SpecialistPracticeLocation


@dataclass(slots=True)
class OwnerSpecialistResult:
    ok: bool
    message: str
    form: OwnerSpecialistForm | None = None
    specialist: Specialist | None = None


def _sync_primary_location(*, specialist: Specialist, form: OwnerSpecialistForm) -> None:
    consultation_format = form.cleaned_data.get("consultation_format")
    if consultation_format not in {Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH}:
        specialist.practice_locations.all().delete()
        return

    location = specialist.practice_locations.filter(is_primary=True).first()
    if location is None:
        location = SpecialistPracticeLocation(specialist=specialist, is_primary=True)

    location.place = form.cleaned_data.get("location_place")
    location.address = form.cleaned_data.get("location_address") or ""
    location.region = form.cleaned_data.get("location_region")
    location.district = form.cleaned_data.get("location_district")
    location.metro = form.cleaned_data.get("location_metro")
    location.price_per_session = form.cleaned_data.get("price_from")
    location.phone = form.cleaned_data.get("phone") or form.cleaned_data.get("whatsapp") or ""
    location.is_active = True
    location.save()


def _create_pending_documents(*, specialist: Specialist, form: OwnerSpecialistForm) -> None:
    for uploaded_file in form.cleaned_data.get("documents") or []:
        SpecialistDocument.objects.create(
            specialist=specialist,
            document_type=SpecialistDocument.TYPE_CERTIFICATE,
            name=getattr(uploaded_file, "name", "") or _("Документ"),
            file=uploaded_file,
            status=SpecialistDocument.STATUS_PENDING,
            is_published=False,
        )


def save_owner_specialist_profile(
    *,
    user,
    form: OwnerSpecialistForm,
    draft_save_only: bool,
) -> OwnerSpecialistResult:
    if not form.is_valid():
        return OwnerSpecialistResult(ok=False, message=_("Проверьте поля формы."), form=form)

    with transaction.atomic():
        specialist = form.save(commit=False)
        if specialist.pk is None:
            specialist.owner = user
        specialist.status = Specialist.STATUS_DRAFT if draft_save_only else Specialist.STATUS_PENDING
        specialist.save()
        form.save_m2m()
        _sync_primary_location(specialist=specialist, form=form)
        _create_pending_documents(specialist=specialist, form=form)

    message = (
        _("Черновик профиля сохранён.")
        if draft_save_only
        else _("Профиль отправлен на модерацию. После проверки он появится в каталоге.")
    )
    return OwnerSpecialistResult(ok=True, message=message, form=form, specialist=specialist)
