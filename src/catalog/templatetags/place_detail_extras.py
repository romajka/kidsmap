"""Small display helpers for the place page."""
import re

from django import template
from django.utils.html import format_html_join
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def uniform_week(week):
    """'10:00–22:30' when all seven days are open with the same hours, else ''."""
    days = list(week or [])
    if len(days) != 7 or any(getattr(d, 'is_closed', None) or (isinstance(d, dict) and d.get('is_closed')) for d in days):
        return ''
    lines = [tuple((d.get('lines') if isinstance(d, dict) else getattr(d, 'lines', None)) or ()) for d in days]
    if not lines[0] or any(item != lines[0] for item in lines):
        return ''
    return ', '.join(lines[0])


@register.filter
def money(value):
    """Display the manat sign visually and expose its ISO code to screen readers."""
    parts = re.split(r'\s*(?:\bAZN\b|₼)', str(value or ''))
    currency = mark_safe(' <span aria-hidden="true">₼</span><span class="visually-hidden">AZN</span>')
    return format_html_join(currency, '{}', ((part,) for part in parts))


def _get(item, key):
    return item.get(key) if isinstance(item, dict) else getattr(item, key, None)


@register.filter
def first_open_row(rows):
    """'Bazar ertəsi–Şənbə 09:00–20:00' — the first open line of the schedule, never a closed one."""
    for row in rows or []:
        if not _get(row, 'is_closed') and _get(row, 'time'):
            days = _get(row, 'days') or ''
            return f"{days} {_get(row, 'time')}".strip()
    return ''


@register.filter
def next_open_day(week):
    """'Cümə · 15:00–18:00' — the next open day after today, for a place that is closed today."""
    days = list(week or [])
    today = next((i for i, d in enumerate(days) if _get(d, 'is_today')), None)
    if today is None:
        return ''
    for step in range(1, len(days) + 1):
        day = days[(today + step) % len(days)]
        lines = _get(day, 'lines') or []
        if not _get(day, 'is_closed') and lines:
            return f"{_get(day, 'label')} · {lines[0]}"
    return ''
