"""Display editorial sections found in existing event copy without changing it."""
import re
from urllib.parse import urlsplit

from django import template
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

register = template.Library()
validate_web_url = URLValidator(schemes=['https', 'http'])
URL = re.compile(r"""https?://[^\s<>"']+""", re.IGNORECASE)
SCHEDULE = re.compile(
    r'^(?:Источник расписания\b|Programme and times from\b|Tamaşa haqqında məlumat və cədvəl\b)',
    re.IGNORECASE,
)
PHOTO = re.compile(
    r'^(?:На обложке\b|The cover shows\b|Üz qabığında\b|(?:Фото|Photo|Foto)\s*[:—])',
    re.IGNORECASE,
)


def _web_host(url):
    try:
        validate_web_url(url)
        parsed = urlsplit(url)
        if parsed.username is None and parsed.password is None:
            return parsed.hostname
    except (ValidationError, ValueError):
        pass
    return ''


def _link_parts(text):
    """URLs keep their original destination. Text around them stays autoescaped."""
    parts = []
    end = 0
    for match in URL.finditer(text):
        url = match.group().rstrip('.,;:')
        host = _web_host(url)
        if not host:
            continue
        parts.append({'text': text[end:match.start()]})
        parts.append({'url': url, 'host': host})
        end = match.start() + len(url)
    parts.append({'text': text[end:]})
    return parts


def _has_photo_credits(parts):
    return (
        any(piece.get('host') == 'commons.wikimedia.org' and '/wiki/File:' in piece['url'] for piece in parts)
        and any(piece.get('host') == 'creativecommons.org' and '/licenses/' in piece['url'] for piece in parts)
    )


@register.filter
def event_story(value):
    paragraphs, sources = [], []
    for paragraph in re.split(r'\n[ \t]*\n', str(value or '').replace('\r\n', '\n').strip()):
        if not paragraph:
            continue
        parts = _link_parts(paragraph)
        if (SCHEDULE.match(paragraph) and any('url' in part for part in parts)
                or PHOTO.match(paragraph) and _has_photo_credits(parts)):
            sources.append(parts)
        else:
            paragraphs.append(paragraph)
    return {'paragraphs': paragraphs, 'sources': sources}


@register.filter
def event_caption(value):
    caption = str(value or '').strip()
    title, divider, rest = caption.partition(' — ')
    if divider:
        parts = _link_parts(rest)
        if _has_photo_credits(parts):
            return {'title': title, 'credits': parts}
    return {'title': caption, 'credits': []}


@register.filter
def is_iticket_url(url):
    return _web_host(str(url or '')) == 'iticket.az'


@register.simple_tag
def event_card_facts(event):
    """Phase/when/remaining for afisha cards and countdowns (display only)."""
    from catalog.services.event_afisha import card_facts
    return card_facts(event)


@register.simple_tag
def event_more(event):
    """Upcoming events shown under an event page (same organizer/venue first)."""
    from catalog.models import Event
    from catalog.services.event_afisha import more_events_for
    if not isinstance(event, Event):
        return {'events': [], 'same_source': False}
    return more_events_for(event)


@register.simple_tag
def event_poster(event):
    """Poster facts (urls, orientation, focus, colour) for a card or hero; None without a photo."""
    from catalog.services.event_images import poster
    return poster(event)


@register.simple_tag
def sessions_label(count, language):
    """'3 seans' / '3 сеанса' / '3 sessions'."""
    count = int(count or 0)
    if language == 'en':
        return f'{count} session' + ('' if count == 1 else 's')
    if language == 'ru':
        from catalog.services.event_afisha import ru_plural
        return f'{count} ' + ru_plural(count, 'сеанс', 'сеанса', 'сеансов')
    return f'{count} seans'


@register.simple_tag
def day_month(value, language):
    """'29 noyabr' / '29 ноября' / '29 November' in Baku time."""
    if not value:
        return ''
    from django.utils import translation
    from django.utils.formats import date_format
    from catalog.services.event_queries import BAKU
    local = value.astimezone(BAKU)
    with translation.override(language):
        if language == 'ru':
            return date_format(local, 'j E')
        text = date_format(local, 'j F')
    return text.lower() if language == 'az' else text


@register.simple_tag
def day_heading(day, language):
    """'Bazar, 29 noyabr' / 'Воскресенье, 29 ноября' / 'Sunday, 29 November' for a date."""
    from django.utils import translation
    from django.utils.formats import date_format
    with translation.override(language):
        text = date_format(day, 'l, j E' if language == 'ru' else 'l, j F')
    if language == 'az':
        weekday, _, rest = text.partition(', ')
        return f'{weekday}, {rest.lower()}'
    return text



@register.simple_tag
def event_gallery_items(event, items=None):
    """Gallery photos with poster facts; reuses the view's list when it is given."""
    if items is not None and items != '':
        return items
    from catalog.services.event_images import gallery
    return gallery(event)
