"""Small display helpers for the place page."""
from django import template

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
    """'35 AZN / dərs' -> '35 ₼ / dərs': one currency sign across the page."""
    import re
    return re.sub(r'\s*\bAZN\b', ' ₼', str(value or '')).strip()


def _get(item, key):
    return item.get(key) if isinstance(item, dict) else getattr(item, key, None)


@register.filter
def first_open_row(rows, limit=2):
    """'Bazar ertəsi–Cümə 09:00–20:00 · Şənbə 10:00–14:00' — up to two open lines, never a closed one."""
    parts = []
    for row in rows or []:
        if not _get(row, 'is_closed') and _get(row, 'time'):
            parts.append(f"{_get(row, 'days') or ''} {_get(row, 'time')}".strip())
        if len(parts) >= int(limit):
            break
    return ' · '.join(parts)


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
