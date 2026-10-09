from dataclasses import dataclass
from types import SimpleNamespace
from datetime import datetime
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
    error_code: str = ""

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
        return EventActionResponse(ok=False, message=_("Ошибка в форме."), form=form, event=event, error_code=validation_code(exc))


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


def validation_code(exc):
    errors = [item for values in exc.error_dict.values() for item in values] if hasattr(exc, 'error_dict') else exc.error_list
    return 'stale_version' if any(getattr(item, 'code', None) == 'stale_version' for item in errors) else 'validation_error'


def entry_context(request, form, event=None, error_code=''):
    """UI inventory follows the current owner submission contract, not admin rules."""
    from catalog.services.locations import init_location_fields
    venues = list(form.fields['related_place'].queryset)
    for venue in venues:
        location = SimpleNamespace(initial={})
        init_location_fields(location, venue)
        venue.event_region = location.initial['region']
        venue.event_district = location.initial['district']
    requirements = [
        {'field': name, 'label': str(form.fields[name].label), 'physical': name == 'address'}
        for name in (*form.SUBMIT_REQUIRED_FIELDS, 'phone', 'address')
    ]
    requirements.insert(0, {'field': 'organizer_organization', 'oneOf': ['organizer_organization', 'organizer_specialist'], 'label': str(_('Организатор мероприятия'))})
    marker = request.session.pop('owner_event_explicit_save', None)
    identity = str(event.pk) if event else 'create'
    key = f'km-owner-event-v2:{request.user.pk}:{identity}'
    saved = bool(marker and event and marker.get('entity') == identity and marker.get('revision') == event.updated_at.isoformat())
    current = Event.objects.filter(pk=event.pk).first() if event and error_code == 'stale_version' else None
    return {'event_venues': venues, 'event_requirements': requirements, 'event_error_code': error_code,
            'event_recovery_key': key, 'event_recovery_clear_key': marker.get('key', '') if marker else '',
            'event_explicit_saved': saved, 'event_server_version': current.updated_at.isoformat() if current else (event.updated_at.isoformat() if event else ''),
            'event_current': current,
            'event_venue_unavailable': bool(form['related_place'].value() and not form.fields['related_place'].queryset.filter(pk=form['related_place'].value()).exists()) if str(form['related_place'].value() or '').isdigit() else bool(form['related_place'].value())}


from django import forms
from django.utils.dateparse import parse_datetime
from zoneinfo import ZoneInfo


class BakuDateTimeField(forms.DateTimeField):
    def to_python(self, value):
        if value in self.empty_values:
            return None
        if isinstance(value, str):
            try:
                value = parse_datetime(value)
            except ValueError:
                value = None
        if not isinstance(value, datetime):
            raise forms.ValidationError(_('Укажите дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ.'))
        return timezone.make_aware(value, ZoneInfo('Asia/Baku')) if timezone.is_naive(value) else value


class EventOccurrenceForm(forms.Form):
    expected_updated_at = forms.CharField(widget=forms.HiddenInput())
    reason = forms.CharField(label=_('Причина'), max_length=2000, widget=forms.Textarea(attrs={'class': 'field', 'rows': 3}))
    start_datetime = BakuDateTimeField(label=_('Новое начало (Asia/Baku)'), required=False, widget=forms.DateTimeInput(attrs={'class': 'field', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'))
    end_datetime = BakuDateTimeField(label=_('Новое окончание (Asia/Baku)'), required=False, widget=forms.DateTimeInput(attrs={'class': 'field', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'))

    def __init__(self, *args, reschedule=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.reschedule = reschedule
        for name in ('start_datetime', 'end_datetime'):
            self.fields[name].required = reschedule

    def clean(self):
        values = super().clean()
        start, end = values.get('start_datetime'), values.get('end_datetime')
        if self.reschedule and start and end and end <= start:
            self.add_error('end_datetime', _('Время окончания должно быть позже времени начала.'))
        return values


def change_occurrence(request, pk, reschedule=False):
    from django.core.exceptions import ValidationError
    from catalog.services import event_domain
    event = _managed_event(request, pk)
    form = EventOccurrenceForm(request.POST, reschedule=reschedule)
    if not form.is_valid():
        return EventActionResponse(False, _('Ошибка в форме.'), event, form)
    try:
        values = {'actor': request.user, 'event_id': pk, 'expected_updated_at': form.cleaned_data['expected_updated_at'], 'reason': form.cleaned_data['reason']}
        if reschedule:
            saved = event_domain.reschedule_event(**values, start_datetime=form.cleaned_data['start_datetime'], end_datetime=form.cleaned_data['end_datetime'])
        else:
            saved = event_domain.cancel_event(**values)
        return EventActionResponse(True, _('Мероприятие перенесено.') if reschedule else _('Мероприятие отменено.'), saved)
    except ValidationError as exc:
        messages = exc.messages if validation_code(exc) == 'stale_version' else [_('Действие отклонено: проверьте состояние мероприятия, причину и новый интервал. Начавшееся, прошедшее или отменённое мероприятие нельзя перенести; для него нужен новый ID.')]
        form.add_error(None, messages)
        return EventActionResponse(False, _('Ошибка в форме.'), event, form, validation_code(exc))
