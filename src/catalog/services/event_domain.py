"""D09 organizer-only, versioned Event mutations and immutable approved venue facts."""
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from catalog.models import Event, Organization, Specialist, Place
from catalog.services.staff_roles import is_volunteer

CONTENT_FIELDS=frozenset({'name','name_az','name_ru','name_en','description_az','description_ru','description_en','category_id','start_datetime','end_datetime','age_from','age_to','price_text','related_place_id','address','district','metro','lat','lng','phone','instagram','website','photo','moderation_note','event_format','venue_label'})
ORGANIZER_FIELDS=frozenset({'organizer_organization_id','organizer_specialist_id'})


def _actor(actor,lock=False):
    if not getattr(actor,'is_authenticated',False) or not getattr(actor,'pk',None):
        raise PermissionDenied('Active account required.')
    qs=get_user_model().objects
    if lock:qs=qs.select_for_update()
    fresh=qs.filter(pk=actor.pk,is_active=True).first()
    if fresh is None or is_volunteer(fresh):raise PermissionDenied('Active account required.')
    return fresh


def _organizer(event,lock=False):
    org_id=event.organizer_organization_id;person_id=event.organizer_specialist_id
    if bool(org_id)==bool(person_id):raise ValidationError('Exactly one organizer is required.')
    qs=Organization.objects if org_id else Specialist.objects
    if lock:qs=qs.select_for_update()
    organizer=qs.filter(pk=org_id or person_id).first()
    if organizer is None:raise PermissionDenied('Organizer unavailable.')
    if org_id:
        if organizer.archived_at or not organizer.owner_id:raise PermissionDenied('Organizer unavailable.')
        owner=organizer.owner_id
    else:
        if not organizer.is_active or not organizer.verified_person_user_id or not organizer.person_verified_at:
            raise PermissionDenied('Confirmed independent person required.')
        owner=organizer.verified_person_user_id
    if not get_user_model().objects.filter(pk=owner,is_active=True).exists():
        raise PermissionDenied('Organizer account unavailable.')
    return organizer,owner


def can_manage_event(actor,event):
    try:
        actor=_actor(actor)
        fresh=Event.objects.get(pk=event.pk,deleted_at__isnull=True)
        _,owner=_organizer(fresh)
        return owner==actor.pk
    except (PermissionDenied,ValidationError,Event.DoesNotExist):return False


def require_manage_event(actor,event):
    if not can_manage_event(actor,event):raise PermissionDenied('Event organizer permission required.')


def _version(event,expected):
    if isinstance(expected,datetime):value=expected
    elif isinstance(expected,str):
        try:value=datetime.fromisoformat(expected)
        except ValueError:value=None
    else:value=None
    if value is None or timezone.is_naive(value) or value!=event.updated_at:
        raise ValidationError(_('Событие изменилось. Обновите страницу перед сохранением.'),code='stale_version')


def _locked(actor,event_id,expected,review=False):
    actor=_actor(actor,lock=True)
    if review and (not actor.is_staff or not actor.has_perm('catalog.change_event')):
        raise PermissionDenied('KidsMap event publication permission required.')
    before=Event.objects.get(pk=event_id,deleted_at__isnull=True)
    _,owner=_organizer(before,lock=True)
    event=Event.objects.select_for_update().get(pk=event_id,deleted_at__isnull=True)
    if (event.organizer_organization_id,event.organizer_specialist_id)!=(before.organizer_organization_id,before.organizer_specialist_id):
        raise ValidationError('Organizer changed; reload.',code='stale_version')
    if not review and owner!=actor.pk:raise PermissionDenied('Event organizer permission required.')
    _version(event,expected)
    return actor,event


def capture_venue_snapshot(event):
    if event.event_format=='online':return {}
    source=event;label=event.venue_label
    # Unresolved historical snapshots never borrow today's Place location.
    if event.organizer_resolution=='resolved' and event.related_place_id:
        place=Place.objects.filter(pk=event.related_place_id,deleted_at__isnull=True,is_active=True).first()
        if place is None:raise ValidationError('Venue unavailable.')
        _, owner = _organizer(event)
        if place.status != 'published' and place.owner_id != owner:
            raise PermissionDenied('A public venue or the organizer own venue is required.')
        source=place;label=place.name_az or place.name
    return {'label':label or '', 'address':source.address or '', 'district':source.district or '',
            'metro':source.metro or '', 'lat':str(source.lat) if source.lat is not None else None,
            'lng':str(source.lng) if source.lng is not None else None}


def _validate(event,publication=False):
    _, owner = _organizer(event)
    if event.event_format == 'physical' and event.related_place_id:
        venue = Place.objects.filter(pk=event.related_place_id, deleted_at__isnull=True, is_active=True).first()
        if venue is None or (venue.status != 'published' and venue.owner_id != owner):
            raise PermissionDenied('A public venue or the organizer own venue is required.')
    if event.event_format not in {'physical','online'}:raise ValidationError('Unknown event format.')
    for value in (event.start_datetime,event.end_datetime):
        if value is not None and (not isinstance(value,datetime) or timezone.is_naive(value)):
            raise ValidationError('Aware event dates are required.')
    if bool(event.start_datetime)!=bool(event.end_datetime):raise ValidationError('Both dates are required.')
    if event.start_datetime and event.end_datetime<=event.start_datetime:raise ValidationError('End must follow start.')
    if publication:
        if not event.name_az or not event.category_id or not event.description_az or not event.start_datetime:
            raise ValidationError('Name, category, description and dates are required for publication.')
        if event.event_format=='physical' and not capture_venue_snapshot(event).get('address'):
            raise ValidationError('A real physical address is required.')


def _save(event):
    previous=event.updated_at
    event.save()
    epoch=max(timezone.now(),previous+timedelta(microseconds=1)) if previous else timezone.now()
    Event.objects.filter(pk=event.pk).update(updated_at=epoch)
    event.refresh_from_db()
    return event


@transaction.atomic
def create_event(*,actor,values):
    actor=_actor(actor,lock=True)
    if not isinstance(values,dict) or set(values)-(CONTENT_FIELDS|ORGANIZER_FIELDS):
        raise ValidationError('Unsupported Event create fields.')
    event=Event(**values,owner=actor,organizer_resolution='resolved',status='draft')
    _,owner=_organizer(event,lock=True)
    if owner!=actor.pk:raise PermissionDenied('Organizer permission required.')
    _validate(event)
    return _save(event)


@transaction.atomic
def save_event(*,actor,event_id,values,expected_updated_at):
    _,event=_locked(actor,event_id,expected_updated_at)
    if not isinstance(values,dict) or set(values)-(CONTENT_FIELDS|ORGANIZER_FIELDS):
        raise ValidationError('Unsupported Event edit fields.')
    if event.status not in {'draft','rejected'}:raise ValidationError('Only draft or rejected content can be edited.')
    for field in ORGANIZER_FIELDS:
        if field in values and values[field]!=getattr(event,field):raise ValidationError('Organizer cannot be reassigned through editing.')
    for field,value in values.items():setattr(event,field,value)
    _validate(event)
    return _save(event)


@transaction.atomic
def submit_event(*,actor,event_id,expected_updated_at):
    _,event=_locked(actor,event_id,expected_updated_at)
    if event.status not in {'draft','rejected'}:raise ValidationError('Only draft or rejected Event can be submitted.')
    _validate(event,publication=True)
    event.status='pending';event.rejection_reason=''
    return _save(event)


@transaction.atomic
def publish_event(*,actor,event_id,expected_updated_at):
    _,event=_locked(actor,event_id,expected_updated_at,review=True)
    if event.related_place_id:Place.objects.select_for_update().get(pk=event.related_place_id)
    _validate(event,publication=True)
    if not event.venue_snapshot:
        event.venue_snapshot=capture_venue_snapshot(event)
    event.status='published';event.rejection_reason='';event.published_at=event.published_at or timezone.now()
    return _save(event)


def _facts(event):
    return {'start_datetime':event.start_datetime.isoformat() if event.start_datetime else None,
            'end_datetime':event.end_datetime.isoformat() if event.end_datetime else None,
            'venue_snapshot':event.venue_snapshot,'event_format':event.event_format,'occurrence_state':event.occurrence_state}


def _occurrence(event,actor,before,kind,reason):
    from catalog.models import EventOccurrenceChange
    event.occurrence_version+=1
    event._allow_occurrence_change=True
    event=_save(event)
    EventOccurrenceChange.objects.create(event=event,actor=actor,kind=kind,reason=str(reason or '')[:2000],
                                         before=before,after=_facts(event),version=event.occurrence_version)
    return event


@transaction.atomic
def cancel_event(*,actor,event_id,expected_updated_at,reason):
    actor,event=_locked(actor,event_id,expected_updated_at)
    if event.occurrence_state=='cancelled':raise ValidationError('Event already cancelled.')
    if not isinstance(reason,str) or not reason.strip():raise ValidationError('Cancellation reason required.')
    before=_facts(event);event.occurrence_state='cancelled'
    return _occurrence(event,actor,before,'cancel',reason)


@transaction.atomic
def reschedule_event(*,actor,event_id,start_datetime,end_datetime,expected_updated_at,reason):
    actor,event=_locked(actor,event_id,expected_updated_at)
    if not event.start_datetime or event.start_datetime<=timezone.now():raise ValidationError('Started or past occurrence needs a new Event ID.')
    if event.occurrence_state=='cancelled':raise ValidationError('Cancelled occurrence cannot be rescheduled.')
    if not isinstance(reason,str) or not reason.strip():raise ValidationError('Reschedule reason required.')
    if not isinstance(start_datetime,datetime) or timezone.is_naive(start_datetime) or start_datetime<=timezone.now():
        raise ValidationError('A future aware start is required.')
    before=_facts(event);event.start_datetime=start_datetime;event.end_datetime=end_datetime;event.occurrence_state='rescheduled'
    _validate(event)
    return _occurrence(event,actor,before,'reschedule',reason)


@transaction.atomic
def delete_event(*,actor,event_id,expected_updated_at):
    _,event=_locked(actor,event_id,expected_updated_at)
    event.deleted_at=timezone.now()
    return _save(event)


def lock_event_for_response(*,actor,event_id):
    """Caller owns an atomic block; lock authority before Event/review rows."""
    before=Event.objects.get(pk=event_id,deleted_at__isnull=True)
    _,event=_locked(actor,event_id,before.updated_at)
    return event
