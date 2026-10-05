"""One public Event reader for list and calendar; no pagination or venue inference."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import re
from zoneinfo import ZoneInfo

from django.db.models import F, Q
from django.utils import timezone
from catalog.models import Event

BAKU = ZoneInfo('Asia/Baku')


@dataclass(frozen=True)
class EventPeriod:
    start: datetime | None
    end: datetime | None
    valid: bool = True


def _day(value):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(value)):
        raise ValueError('Use YYYY-MM-DD')
    return date.fromisoformat(value)


def _midnight(value):
    return datetime.combine(value, time.min, tzinfo=BAKU)


def _month(value):
    if not re.fullmatch(r'\d{4}-\d{2}', str(value)):
        raise ValueError('Use YYYY-MM')
    start = date.fromisoformat(value + '-01')
    end = date(start.year + (start.month == 12), start.month % 12 + 1, 1)
    return EventPeriod(_midnight(start), _midnight(end))


def parse_event_period(params, *, now=None, calendar=False):
    """Inputs are inclusive local dates; database periods are [start,end).

    Invalid explicit input fails closed. Default list includes ongoing events;
    default calendar covers the whole local month, even with a selected day.
    """
    now = now or timezone.now()
    if timezone.is_naive(now):
        raise ValueError('Event query requires aware now')
    today = now.astimezone(BAKU).date()
    get = lambda key: str(params.get(key) or '').strip()
    try:
        if calendar:
            month = get('month')
            if get('date'):
                selected = _day(get('date'))
                month = month or selected.strftime('%Y-%m')
            return _month(month or today.strftime('%Y-%m'))
        if get('date'):
            selected = _day(get('date'))
            return EventPeriod(_midnight(selected), _midnight(selected + timedelta(days=1)))
        if get('month'):
            return _month(get('month'))
        if get('date_from') or get('date_to'):
            start = _day(get('date_from')) if get('date_from') else None
            end = _day(get('date_to')) if get('date_to') else None
            if start and end and start > end:
                raise ValueError('Reversed date range')
            return EventPeriod(_midnight(start) if start else None,
                               _midnight(end + timedelta(days=1)) if end else None)
        quick = get('date_filter')
        if quick in {'today', 'tomorrow'}:
            start = today + timedelta(days=quick == 'tomorrow')
            return EventPeriod(_midnight(start), _midnight(start + timedelta(days=1)))
        if quick == 'this_week':
            return EventPeriod(_midnight(today), _midnight(today + timedelta(days=7-today.weekday())))
        if quick == 'weekend':
            start = today + timedelta(days=(5-today.weekday()) % 7) if today.weekday() != 6 else today-timedelta(days=1)
            return EventPeriod(_midnight(start), _midnight(start+timedelta(days=2)))
    except (ValueError, OverflowError):
        return EventPeriod(None, None, valid=False)
    return EventPeriod(now, None)


def query_public_events(params=None, *, period=None, now=None, calendar=False):
    from catalog.services.features import is_events_section_enabled
    params = params or {}
    period = period or parse_event_period(params, now=now, calendar=calendar)
    if not period.valid or not is_events_section_enabled():
        return Event.objects.none()
    qs = Event.objects.filter(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True,
        start_datetime__isnull=False, end_datetime__gt=F('start_datetime'))
    if period.start is not None:
        qs = qs.filter(end_datetime__gt=period.start)
    if period.end is not None:
        qs = qs.filter(start_datetime__lt=period.end)
    get = lambda key: str(params.get(key) or '').strip()
    q = get('q')[:500]
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(name_az__icontains=q) | Q(name_ru__icontains=q)
            | Q(name_en__icontains=q) | Q(description_az__icontains=q) | Q(description_ru__icontains=q)
            | Q(description_en__icontains=q) | Q(venue_snapshot__address__icontains=q))
    if get('category'):
        qs = qs.filter(category_id=get('category'))
    district = get('district')
    if district:
        if district.lower() == 'baku':
            qs = qs.filter(Q(venue_snapshot__district__iexact='baku') | Q(venue_snapshot__district__startswith='baku_'))
        else:
            qs = qs.filter(venue_snapshot__district=district)
    event_format = get('format')
    if event_format:
        if event_format not in {'physical', 'online'}:
            return Event.objects.none()
        qs = qs.filter(event_format=event_format)
    ages = {}
    for key in ('age_from', 'age_to'):
        value = get(key)
        if value.isascii() and value.isdigit() and len(value) < 4 and 0 <= int(value) <= 120:
            ages[key] = int(value)
    if ages:
        qs = qs.exclude(age_from__isnull=True, age_to__isnull=True)
    if 'age_from' in ages:
        qs = qs.filter(Q(age_to__gte=ages['age_from']) | Q(age_to__isnull=True))
    if 'age_to' in ages:
        qs = qs.filter(Q(age_from__lte=ages['age_to']) | Q(age_from__isnull=True))
    if get('free') == '1':
        qs = qs.filter(Q(price_text__iexact='pulsuz') | Q(price_text__iexact='free')
            | Q(price_text__iexact='бесплатно') | Q(price_text='0') | Q(price_text__iexact='0 AZN'))
    # Unknown/mixed textual prices and venue likes are not comparable Event rankings.
    ordering = ('-created_at', 'pk') if get('sort') == 'new' else ('start_datetime', 'pk')
    return qs.select_related('related_place', 'organizer_organization', 'organizer_specialist').order_by(*ordering)
