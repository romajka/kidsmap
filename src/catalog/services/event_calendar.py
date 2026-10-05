"""Bounded calendar presentation over actual Events from the shared reader."""
from calendar import Calendar
from datetime import date, timedelta
from urllib.parse import urlencode

from django.utils import timezone

from catalog.services.event_queries import BAKU, EventPeriod, _day, _midnight, parse_event_period, query_public_events

FILTER_KEYS = ('q', 'category', 'age_from', 'age_to', 'format', 'district', 'free', 'sort')
PERIOD_KEYS = ('month', 'date', 'date_from', 'date_to', 'date_filter')


def build_event_filter_options(*, language_code, selected_category='', selected_district=''):
    """Use public Event taxonomy and immutable districts, never Place inventory."""
    from catalog.models import Category
    from catalog.services.locations import get_location_translation

    public_events = query_public_events({}, period=EventPeriod(None, None))
    category_ids = public_events.order_by().values_list('category_id', flat=True).distinct()
    categories = []
    language = language_code.split('-')[0]
    for category in Category.objects.filter(pk__in=category_ids).order_by('order', 'code'):
        translated = str(getattr(category, 'name_' + language, '') or '').strip()
        az = str(category.name_az or '').strip()
        label = translated or (az + (' (AZ)' if language != 'az' else '')) or category.code
        categories.append({'value': category.code, 'label': label})
    selected_category = str(selected_category or '').strip()
    if selected_category and not any(option['value'] == selected_category for option in categories):
        categories.insert(0, {'value': selected_category, 'label': selected_category})

    district_values = {str(value).strip() for value in public_events.order_by()
        .values_list('venue_snapshot__district', flat=True).distinct() if isinstance(value, str) and value.strip()}
    if any(value.startswith('baku_') for value in district_values):
        district_values.add('baku')
    if selected_district:
        district_values.add(str(selected_district).strip())
    districts = [{'value': value, 'label': get_location_translation(value, language)}
                 for value in sorted(district_values, key=lambda value: (value != 'baku', value))]
    return {'categories': categories, 'districts': districts}


def build_event_calendar(params, events, *, now=None, path=''):
    """Dates select existing occurrences; this never generates Event objects.

    Canonical links carry only supported filters and periods, never list pages
    or arbitrary redirect inputs. An explicit day outside its month fails closed.
    """
    now = now or timezone.now()
    if timezone.is_naive(now):
        raise ValueError('Calendar requires aware now')
    today = now.astimezone(BAKU).date()
    clean = {key: str(params.get(key) or '').strip()
             for key in FILTER_KEYS + PERIOD_KEYS + ('view',)}
    filters = {key: clean[key] for key in FILTER_KEYS if clean[key]}

    def url(values):
        query = urlencode({key: value for key, value in values.items() if value})
        return path + ('?' + query if query else '')

    period = parse_event_period(clean, now=now, calendar=True)
    first = period.start.date() if period.valid else today.replace(day=1)
    selected = today if (today.year, today.month) == (first.year, first.month) else first
    valid = period.valid
    try:
        if clean['date']:
            selected = _day(clean['date'])
            valid = valid and (selected.year, selected.month) == (first.year, first.month)
        weeks_dates = Calendar(firstweekday=0).monthdatescalendar(first.year, first.month) if valid else []
    except (ValueError, OverflowError):
        valid = False
        weeks_dates = []

    month = first.strftime('%Y-%m')
    calendar_params = dict(filters, view='calendar', month=month, date=selected.isoformat())
    list_params = dict(filters, view='list', month=month)
    quick_urls = {key: url(dict(filters, view='list', date_filter=key))
                  for key in ('today', 'tomorrow', 'this_week', 'weekend')}
    free_params = {key: value for key, value in clean.items() if value}
    free_params['view'] = 'calendar' if clean['view'] == 'calendar' else 'list'
    if clean['free'] == '1':
        free_params.pop('free', None)
    else:
        free_params['free'] = '1'
    quick_urls['free'] = url(free_params)

    def adjacent_url(direction):
        try:
            target = (first-timedelta(days=1)).replace(day=1) if direction < 0 else period.end.date()
            return url(dict(filters, view='calendar', month=target.strftime('%Y-%m'), date=target.isoformat()))
        except (ValueError, OverflowError, AttributeError):
            return ''

    result = {
        'valid': valid, 'month': month, 'month_label': first,
        'selected_date': selected.isoformat(), 'weeks': [], 'days': [], 'selected_events': [],
        'prev_url': adjacent_url(-1) if valid else '',
        'next_url': adjacent_url(1) if valid else '',
        'list_url': url(list_params), 'calendar_url': url(calendar_params),
        'today_url': url(dict(filters, view='calendar', month=today.strftime('%Y-%m'), date=today.isoformat())),
        'quick_urls': quick_urls,
    }
    if not valid:
        return result
    actual_events = list(events)
    for dates in weeks_dates:
        row = []
        for day in dates:
            in_month = day.month == first.month and day.year == first.year
            start, end = _midnight(day), _midnight(day+timedelta(days=1))
            matches = [event for event in actual_events if in_month
                       and event.start_datetime is not None and event.end_datetime is not None
                       and event.start_datetime < end and event.end_datetime > start]
            item = {'iso': day.isoformat(), 'date': day, 'in_month': in_month,
                    'selected': day == selected, 'today': day == today,
                    'events': matches, 'count': len(matches),
                    'url': url(dict(filters, view='calendar', month=day.strftime('%Y-%m'), date=day.isoformat()))}
            row.append(item)
            if in_month:
                result['days'].append(item)
            if day == selected:
                result['selected_events'] = matches
        result['weeks'].append(row)
    return result
