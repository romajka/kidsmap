from dataclasses import dataclass
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
    if not event.address:
        missing.append(_("адрес"))
    if not event.phone:
        missing.append(_("телефон"))
    if not event.description_az:
        missing.append(_("описание"))
    if not event.photo:
        missing.append(_("фото"))
    return missing

def create_event(request, data, files, draft_save_only: bool) -> EventActionResponse:
    if not request.user.is_authenticated:
        return EventActionResponse(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))

    form = OwnerEventForm(data=data, files=files, user=request.user, draft_save_only=draft_save_only)
    if form.is_valid():
        event = form.save(commit=False)
        event.owner = request.user
        event.status = Event.STATUS_DRAFT if draft_save_only else Event.STATUS_PENDING
        if not draft_save_only:
            event.rejection_reason = ""
            event.published_at = None
        event.save()
        message = _("Qaralama saxlanıldı.") if draft_save_only else _("Tədbir moderasiyaya göndərildi.")
        return EventActionResponse(ok=True, message=message, event=event)
    
    return EventActionResponse(ok=False, message=_("Ошибка в форме."), form=form)

def edit_event(request, pk: int, data, files, draft_save_only: bool) -> EventActionResponse:
    if not request.user.is_authenticated:
        return EventActionResponse(ok=False, message=_("Для доступа войдите в аккаунт и повторите действие."))

    event = get_object_or_404(Event, pk=pk, owner=request.user, deleted_at__isnull=True)
    if event.status in {Event.STATUS_PENDING, Event.STATUS_PUBLISHED} and request.method != "GET":
        return EventActionResponse(ok=False, message=_("Tədbir yalnız qaralama və ya rədd edildikdən sonra redaktə oluna bilər."))

    form = OwnerEventForm(data=data, files=files, instance=event, user=request.user, draft_save_only=draft_save_only)
    if form.is_valid():
        event = form.save(commit=False)
        if draft_save_only:
            event.status = Event.STATUS_DRAFT
        else:
            event.status = Event.STATUS_PENDING
            event.rejection_reason = ""
            event.published_at = None
        event.save()
        message = _("Qaralama saxlanıldı.") if draft_save_only else _("Tədbir moderasiyaya göndərildi.")
        return EventActionResponse(ok=True, message=message, event=event)

    return EventActionResponse(ok=False, message=_("Ошибка в форме."), form=form, event=event)

def submit_event_for_review(request, pk: int) -> EventActionResponse:
    event = get_object_or_404(Event, pk=pk, owner=request.user, deleted_at__isnull=True)
    if event.status == Event.STATUS_PENDING:
        return EventActionResponse(ok=False, message=_("Это мероприятие уже на модерации."))

    missing = _event_required_missing(event)
    if missing:
        msg = _("Заполните перед отправкой: %(fields)s.") % {"fields": ", ".join(str(item) for item in missing)}
        return EventActionResponse(ok=False, message=msg, event=event)

    event.status = Event.STATUS_PENDING
    event.rejection_reason = ""
    event.published_at = None
    event.save(update_fields=["status", "rejection_reason", "published_at", "updated_at"])
    return EventActionResponse(ok=True, message=_("Tədbir moderasiyaya göndərildi."), event=event)

def delete_event(request, pk: int) -> EventActionResponse:
    event = get_object_or_404(Event, pk=pk, owner=request.user, deleted_at__isnull=True)
    event.deleted_at = timezone.now()
    event.save(update_fields=["deleted_at", "updated_at"])
    return EventActionResponse(ok=True, message=_("Tədbir silindi."))
