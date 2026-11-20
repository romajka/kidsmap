"""Shared presentation facts for the public afisha (home block, list, calendar).

Every surface reads the same public Event query, so counters on the home page,
the afisha header and the calendar always agree. Nothing here writes data.
"""
from datetime import timedelta

from django.utils import timezone

from catalog.services.event_queries import BAKU, EventPeriod, query_public_events

# An occurrence longer than a day (exhibitions, seasonal parks) is shown as a
# running period, not as a time slot repeated on every calendar day.
LONG_EVENT_THRESHOLD = timedelta(hours=24)
QUICK_PERIODS = ('today', 'tomorrow', 'weekend', 'this_week')


def is_long_event(event) -> bool:
    start, end = getattr(event, 'start_datetime', None), getattr(event, 'end_datetime', None)
    return bool(start and end and end - start > LONG_EVENT_THRESHOLD)


def _when(event, now):
    """today / tomorrow / weekend / later, by the event's first relevant Baku day."""
    today = now.astimezone(BAKU).date()
    start = event.start_datetime.astimezone(BAKU).date()
    day = max(start, today) if event.start_datetime <= now else start
    if day == today:
        return 'today'
    if day == today + timedelta(days=1):
        return 'tomorrow'
    if day.weekday() >= 5 and (day - today).days < 7:
        return 'weekend'
    return 'later'


def card_facts(event, *, now=None):
    """Display-only facts for one event card/timer (never mutates the event)."""
    now = now or timezone.now()
    start, end = getattr(event, 'start_datetime', None), getattr(event, 'end_datetime', None)
    zero = {'d': 0, 'h': 0, 'm': 0, 's': 0}
    state = getattr(event, 'occurrence_state', '')
    if state == 'cancelled':
        phase = 'cancelled'
    elif getattr(event, 'has_ended', False) or (end and end <= now):
        phase = 'ended'
    elif not start or not end:
        return {'phase': 'unknown', 'when': '', 'long': False, 'remaining': zero}
    elif start <= now:
        phase = 'running'
    elif start - now <= timedelta(hours=24):
        phase = 'soon'
    else:
        phase = 'upcoming'
    remaining = zero
    if phase in ('running', 'soon', 'upcoming'):
        target = end if phase == 'running' else start
        seconds = max(int((target - now).total_seconds()), 0)
        remaining = {'d': seconds // 86400, 'h': seconds % 86400 // 3600,
                     'm': seconds % 3600 // 60, 's': seconds % 60}
    return {
        'phase': phase,
        'when': _when(event, now) if phase in ('running', 'soon', 'upcoming') else '',
        'long': is_long_event(event),
        'remaining': remaining,
        'timer': bool(start and end) and phase not in ('cancelled', 'ended'),
    }


def build_event_quick_stats(*, now=None):
    """Counts for quick chips; the same reader and periods as the afisha filters."""
    now = now or timezone.now()
    stats = {key: query_public_events({'date_filter': key}, now=now).count() for key in QUICK_PERIODS}
    stats['total'] = query_public_events({}, period=EventPeriod(now, None), now=now).count()
    stats['running'] = query_public_events({}, period=EventPeriod(now, now + timedelta(seconds=1)), now=now).count()
    stats['past'] = query_past_events({}, now=now).count()
    return stats


def upcoming_events_for_home(*, limit=4, now=None):
    """Nearest attendable events: starting soonest first, running exhibitions after."""
    now = now or timezone.now()
    events = list(query_public_events({}, now=now)[:60])
    upcoming = [event for event in events if event.start_datetime > now]
    running = [event for event in events if event.start_datetime <= now]
    upcoming.sort(key=lambda event: (event.start_datetime, event.pk))
    running.sort(key=lambda event: (event.end_datetime, event.pk))
    return (upcoming + running)[:limit]


def ru_plural(count: int, one: str, few: str, many: str) -> str:
    """Russian plural form: 1 мероприятие, 3 мероприятия, 11 мероприятий."""
    n = abs(int(count)) % 100
    if 11 <= n <= 14:
        return many
    n %= 10
    return one if n == 1 else few if 2 <= n <= 4 else many


def ru_events_label(count: int) -> str:
    return f"{count} " + ru_plural(count, 'мероприятие', 'мероприятия', 'мероприятий')


PAST_WINDOW = timedelta(days=365)


def query_past_events(params=None, *, now=None):
    """Afisha history: events that already ended in the last year, newest first.

    Uses the same public reader and filters (search, category, age, district,
    format, free) as the live feed; cancelled occurrences are not history.
    """
    from catalog.services.event_calendar import PERIOD_KEYS
    now = now or timezone.now()
    clean = {key: value for key, value in dict((params or {}).items()).items() if key not in PERIOD_KEYS}
    return (query_public_events(clean, period=EventPeriod(now - PAST_WINDOW, now), now=now)
            .filter(end_datetime__lte=now)
            .order_by('-end_datetime', '-pk'))


def more_events_for(event, *, limit=3, now=None):
    """Upcoming events to offer on an event page: same organizer or venue first."""
    now = now or timezone.now()
    candidates = list(query_public_events({}, now=now).exclude(pk=event.pk)[:80])

    def same_source(other):
        return any(getattr(event, field, None) and getattr(event, field, None) == getattr(other, field, None)
                   for field in ('organizer_organization_id', 'organizer_specialist_id', 'related_place_id'))

    upcoming = [other for other in candidates if other.start_datetime > now]
    running = [other for other in candidates if other.start_datetime <= now]
    ordered = sorted(upcoming, key=lambda other: (not same_source(other), other.start_datetime, other.pk))
    ordered += sorted(running, key=lambda other: (not same_source(other), other.end_datetime, other.pk))
    picked = ordered[:limit]
    return {'events': picked, 'same_source': bool(picked) and same_source(picked[0])}


def _coordinate(value, low, high):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not (low <= number <= high) or abs(number) < 0.001:
        return None
    return round(number, 6)


def event_map_points(*, language_code='az', now=None, limit=200):
    """Pins for the map: attendable physical events with an approved venue location.

    Coordinates come only from the approved venue snapshot, the same source the
    event page shows; online events and address-only venues get no pin.
    """
    from django.utils.formats import date_format
    from django.utils import translation
    now = now or timezone.now()
    language = (language_code or 'az').split('-')[0]
    points = []
    with translation.override(language):
        for event in query_public_events({}, now=now)[:limit]:
            if event.event_format == 'online':
                continue
            venue = event.public_venue(language)
            lat = _coordinate(venue.get('lat'), -90, 90)
            lng = _coordinate(venue.get('lng'), -180, 180)
            if lat is None or lng is None:
                continue
            facts = card_facts(event, now=now)
            start = event.start_datetime.astimezone(BAKU)
            end = event.end_datetime.astimezone(BAKU)
            points.append({
                'id': event.pk,
                'name': event.name_i18n(language),
                'url': event.get_absolute_url(),
                'lat': lat, 'lng': lng,
                'start': start.isoformat(), 'end': end.isoformat(),
                'phase': facts['phase'], 'when': facts['when'], 'long': facts['long'],
                'day': start.day, 'month': date_format(start, 'b').rstrip('.'),
                'end_day': end.day, 'end_month': date_format(end, 'b').rstrip('.'),
                'weekday': date_format(start, 'D'),
                'time': f"{start:%H:%M}–{end:%H:%M}",
                'image': event.photo.url if event.photo else '',
                'price': event.price_display or '',
                'free': bool(event.is_free),
                'category': event.get_category_display() or '',
                'age': event.age_display or '',
                'languages': [item['short'] for item in event.language_list],
                'language_names': [item['name'] for item in event.language_list],
                'venue': venue.get('label') or '',
                'address': venue.get('address') or '',
            })
    return points
