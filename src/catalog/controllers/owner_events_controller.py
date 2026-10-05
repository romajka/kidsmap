from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from catalog.models import Event
from catalog.forms import OwnerEventForm

@dataclass
class EventActionResponse:
    ok: bool
    message: str
    event: Event | None = None
    form: OwnerEventForm | None = None

def _event_required_missing(event: Event) -> list[str]:
    missing = []
    if not event.name_az:
        missing.append(_("название"))
    if not event.category:
        missing.append(_("категория"))
    if not event.start_datetime or not event.end_datetime:
        missing.append(_("дата и время"))
    if event.end_datetime and event.end_datetime <= timezone.now():
        missing.append(_("актуальная дата окончания"))
    if event.age_from is None or event.age_to is None:
        missing.append(_("возраст"))
    if not event.price_text:
        missing.append(_("цена"))
    if event.event_format != "online" and not event.address:
        missing.append(_("адрес"))
    if not event.phone:
        missing.append(_("телефон"))
    if not event.description_az:
        missing.append(_("описание"))
    if not event.photo:
        missing.append(_("фото"))
    return missing

def _managed_event(request, pk):
    from catalog.services.event_domain import require_manage_event
    event = get_object_or_404(Event, pk=pk, deleted_at__isnull=True)
    require_manage_event(request.user, event)
    return event


def _values(form):
    from catalog.services.event_domain import CONTENT_FIELDS, ORGANIZER_FIELDS
    event = form.save(commit=False)
    return {key: getattr(event, key) for key in CONTENT_FIELDS | ORGANIZER_FIELDS}


def _save_form(request, form, draft_save_only, event=None):
    from django.core.exceptions import ValidationError
    from catalog.services import event_domain
    if not form.is_valid():
        return EventActionResponse(ok=False, message=_("Ошибка в форме."), form=form, event=event)
    try:
        with transaction.atomic():
            if event is None:
                saved = event_domain.create_event(actor=request.user, values=_values(form))
            else:
                saved = event_domain.save_event(actor=request.user, event_id=event.pk, values=_values(form), expected_updated_at=form.cleaned_data.get('expected_updated_at'))
            if not draft_save_only:
                saved = event_domain.submit_event(actor=request.user, event_id=saved.pk, expected_updated_at=saved.updated_at.isoformat())
        return EventActionResponse(ok=True, message=_("Qaralama saxlanıldı.") if draft_save_only else _("Tədbir moderasiyaya göndərildi."), event=saved)
    except ValidationError as exc:
        form.add_error(None, exc.messages)
        return EventActionResponse(ok=False, message=_("Ошибка в форме."), form=form, event=event)


def create_event(request, data, files, draft_save_only: bool) -> EventActionResponse:
    form=OwnerEventForm(data=data, files=files, user=request.user, draft_save_only=draft_save_only)
    return _save_form(request, form, draft_save_only)


def edit_event(request, pk: int, data, files, draft_save_only: bool) -> EventActionResponse:
    event=_managed_event(request, pk)
    if event.status not in {'draft', 'rejected'}:
        return EventActionResponse(ok=False, message=_("Tədbir yalnız qaralama və ya rədd edildikdən sonra redaktə oluna bilər."), event=event)
    form=OwnerEventForm(data=data, files=files, instance=event, user=request.user, draft_save_only=draft_save_only)
    return _save_form(request, form, draft_save_only, event)


def submit_event_for_review(request, pk: int) -> EventActionResponse:
    from django.core.exceptions import ValidationError
    from catalog.services.event_domain import submit_event
    event=_managed_event(request, pk)
    missing=_event_required_missing(event)
    if missing:
        return EventActionResponse(ok=False, message=_("Заполните перед отправкой: %(fields)s.") % {'fields': ', '.join(str(item) for item in missing)}, event=event)
    try:
        saved=submit_event(actor=request.user, event_id=pk, expected_updated_at=request.POST.get('expected_updated_at'))
        return EventActionResponse(ok=True, message=_("Tədbir moderasiyaya göndərildi."), event=saved)
    except ValidationError as exc:
        return EventActionResponse(ok=False, message='; '.join(exc.messages), event=event)


def delete_event(request, pk: int) -> EventActionResponse:
    from django.core.exceptions import ValidationError
    from catalog.services.event_domain import delete_event as delete
    event=_managed_event(request, pk)
    try:
        delete(actor=request.user, event_id=pk, expected_updated_at=request.POST.get('expected_updated_at'))
        return EventActionResponse(ok=True, message=_("Tədbir silindi."), event=event)
    except ValidationError as exc:
        return EventActionResponse(ok=False, message='; '.join(exc.messages), event=event)
