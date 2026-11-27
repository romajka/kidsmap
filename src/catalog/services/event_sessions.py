"""Display-only grouping of sessions: the same show, at the same venue, on the same day.

Organisers publish each showtime as its own Event ("Qaraca qız" at 12:00,
14:00 and 16:00). Lists show one card with the times; every time keeps its own
event page and ticket link. Nothing here writes data.
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from itertools import islice
import re
from urllib.parse import urlsplit

from django.db.models import Q
from django.utils import timezone

from .event_afisha import is_long_event
from .event_queries import BAKU, query_public_events
from .slugs import build_ascii_slug


def _title(event) -> str:
    names = (event.name_az, event.name_ru, event.name_en, event.name)
    return ' '.join(next((n for n in names if n), '').casefold().split())


def _venue(event):
    if event.event_format == 'online':
        return ('online',)
    if event.related_place_id:
        return ('place', event.related_place_id)
    snapshot = event.venue_snapshot if isinstance(event.venue_snapshot, dict) else {}
    label = ' '.join(str(snapshot.get('label') or event.venue_label or snapshot.get('address') or event.address or '').casefold().split())
    return ('venue', label) if label else ('event', event.pk)


def session_key(event):
    """Key shared by sessions of one show on one Baku day; None if never grouped."""
    if not event.start_datetime or not event.end_datetime or is_long_event(event):
        return None
    organizer = (event.organizer_organization_id, event.organizer_specialist_id)
    return (_title(event), organizer, _venue(event), event.start_datetime.astimezone(BAKU).date())


def _session(event, now):
    return {
        'event': event,
        'start': event.start_datetime,
        'end': event.end_datetime,
        'url': event.get_absolute_url(),
        'ended': event.end_datetime <= now,
        'cancelled': event.occurrence_state == 'cancelled',
    }


def group_sessions(events, *, now=None):
    """[{'event': lead, 'sessions': [...]}] in the order leads first appear.

    The lead is the first session in the incoming order (the list is already
    sorted for the surface); sessions are sorted by start time.
    """
    now = now or timezone.now()
    groups, by_key = [], {}
    for event in events:
        key = session_key(event)
        if key is not None and key in by_key:
            by_key[key]['sessions'].append(_session(event, now))
            continue
        group = {'event': event, 'sessions': [_session(event, now)]}
        groups.append(group)
        if key is not None:
            by_key[key] = group
    for group in groups:
        group['sessions'].sort(key=lambda item: (item['start'], item['event'].pk))
        group['multi'] = len(group['sessions']) > 1
    return groups


def sibling_sessions(event, *, now=None):
    """All public sessions of this event's show on its day, the event included."""
    key = session_key(event)
    now = now or timezone.now()
    if key is None:
        return [_session(event, now)]
    from catalog.models import Event
    day = key[-1]
    start = timezone.make_aware(datetime.combine(day, time.min), BAKU)
    candidates = (Event.objects.filter(status=Event.STATUS_PUBLISHED, deleted_at__isnull=True,
                                       start_datetime__gte=start, start_datetime__lt=start + timedelta(days=1))
                  .exclude(occurrence_state='cancelled')
                  .only('pk', 'slug', 'name', 'name_az', 'name_ru', 'name_en', 'start_datetime', 'end_datetime',
                        'event_format', 'related_place', 'venue_snapshot', 'venue_label', 'address',
                        'organizer_organization', 'organizer_specialist', 'occurrence_state', 'status',
                        'deleted_at'))
    sessions = [_session(other, now) for other in candidates if other.pk == event.pk or session_key(other) == key]
    if not any(item['event'].pk == event.pk for item in sessions):
        sessions.append(_session(event, now))
    sessions.sort(key=lambda item: (item['start'], item['event'].pk))
    return sessions


def _production_venue(event):
    snapshot = event.venue_snapshot if isinstance(event.venue_snapshot, dict) else {}
    address = snapshot.get('address') or event.address or ''
    return _venue(event), ' '.join(str(address).casefold().split())


def _production_sources(event):
    """Identify show pages supplied by the editor; a venue homepage proves nothing."""
    slugs = {build_ascii_slug(name, fallback='') for name in
             (event.name, event.name_az, event.name_ru, event.name_en) if name}
    urls = [event.website]
    if event.registration_method == 'link':
        urls.append(event.registration_url)
    sources = set()
    for value in urls:
        try:
            parsed = urlsplit(value or '')
            host = parsed.hostname
        except ValueError:
            continue
        if parsed.scheme not in ('https', 'http') or not host or parsed.username or parsed.password:
            continue
        path = parsed.path.rstrip('/')
        if host in ('iticket.az', 'www.iticket.az'):
            # The last numeric component is the individually ticketed showtime.
            match = re.fullmatch(r'/(?:(?:az|en|ru)/)?(events/[a-z0-9-]+/[a-z0-9-]+)(?:/[0-9]+)?', path)
            if match:
                sources.add(('iticket.az', '/' + match[1]))
        elif not parsed.query:
            parts = path.rsplit('/', 2)
            if len(parts) == 3 and parts[-2] in ('article', 'event', 'events', 'shows', 'productions', 'repertoire') and parts[-1] in slugs:
                sources.add((host, path))
    return sources


def other_show_dates(event, *, listed=(), now=None):
    """Nearest upcoming sessions with matching show source, venue, organizer and title."""
    key = session_key(event)
    sources = _production_sources(event) if key else set()
    if not sources:
        return []
    now = now or timezone.now()
    # Narrow to URLs with a common show path before parsing the exact host and path.
    source_filter = Q()
    for _, path in sources:
        source_filter |= Q(website__contains=path) | Q(registration_url__contains=path)
    candidates = (query_public_events(now=now).select_related(None)
                  .filter(source_filter, start_datetime__gt=now, event_format=event.event_format,
                          organizer_organization_id=event.organizer_organization_id,
                          organizer_specialist_id=event.organizer_specialist_id,
                          related_place_id=event.related_place_id)
                  .exclude(pk__in=[event.pk, *(slot['event'].pk for slot in listed)])
                  .only('name', 'name_az', 'name_ru', 'name_en', 'start_datetime', 'end_datetime',
                        'slug', 'languages', 'event_format', 'related_place_id', 'venue_snapshot',
                        'venue_label', 'address', 'organizer_organization_id', 'organizer_specialist_id',
                        'registration_method', 'registration_url', 'website'))
    venue = _production_venue(event)
    matched = (other for other in candidates.iterator() if not is_long_event(other)
               and _title(other) == key[0] and _production_venue(other) == venue
               and sources.intersection(_production_sources(other)))
    return list(islice(matched, 6))


def by_day(groups, *, now=None, first_day=None):
    """[{'day': date, 'groups': [...]}] for the phone "by day" agenda.

    A running event is listed under today; the rest under their Baku start day.
    """
    now = now or timezone.now()
    today = max(now.astimezone(BAKU).date(), first_day or now.astimezone(BAKU).date())
    days = {}
    for group in groups:
        start = group['event'].start_datetime.astimezone(BAKU).date()
        days.setdefault(max(start, today), []).append(group)
    return [{'day': day, 'groups': days[day]} for day in sorted(days)]
