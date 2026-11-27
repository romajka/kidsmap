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


# Hosts that only ever carry photo credits (author page, licence text).
CREDIT_HOSTS = {'commons.wikimedia.org', 'upload.wikimedia.org', 'creativecommons.org'}
LICENSE = re.compile(r'^(?:CC[\s-]|CC0\b|Public domain\b|Ictimai\b|Общественное достояние\b)', re.IGNORECASE)
# "Tamaşanın dili — Azərbaycan dili." repeats the language badge in the hero.
LANGUAGE_LINE = re.compile(
    r'^(?:Tamaşanın dili|Tədbirin dili|Язык спектакля|Язык мероприятия|Language of the (?:show|event))\s*[—:–-]\s*\S',
    re.IGNORECASE)
# A paragraph that is mostly links (a "source: … https://…" line) is a reference, not story.
SOURCE_TEXT_LIMIT = 160


def _plain_text(parts):
    return ''.join(piece.get('text', '') for piece in parts)


def _is_source_line(paragraph, parts):
    urls = [piece for piece in parts if 'url' in piece and piece['host'] not in CREDIT_HOSTS]
    if not urls:
        return False
    if SCHEDULE.match(paragraph):
        return True
    rest = re.sub(r'[\s·•|,;:—–-]+', ' ', _plain_text(parts)).strip()
    return len(rest) <= SOURCE_TEXT_LIMIT


def _source_links(sources):
    """One link per website, in the order they first appear; photo-credit hosts left out."""
    links, seen = [], set()
    for parts in sources:
        for piece in parts:
            host = piece.get('host')
            if not host or host in CREDIT_HOSTS:
                continue
            label = host[4:] if host.startswith('www.') else host
            if label in seen:
                continue
            seen.add(label)
            links.append({'url': piece['url'], 'label': label})
    return links


@register.filter
def event_story(value):
    paragraphs, sources, credits = [], [], []
    for paragraph in re.split(r'\n[ \t]*\n', str(value or '').replace('\r\n', '\n').strip()):
        if not paragraph:
            continue
        parts = _link_parts(paragraph)
        if PHOTO.match(paragraph) and _has_photo_credits(parts):
            credits.append(parts)
        elif _is_source_line(paragraph, parts):
            sources.append(parts)
        elif LANGUAGE_LINE.match(paragraph) and len(paragraph) <= 80:
            continue
        else:
            paragraphs.append(paragraph)
    return {
        'paragraphs': paragraphs,
        'sources': sources + credits,
        'links': _source_links(sources),
        'credits': credits,
    }


def _credit(parts):
    """{'author', 'license', 'file_url', 'license_url'} from "Author · CC BY-SA 4.0 · links"."""
    tokens = [t.strip() for t in re.split(r'[·•|]', _plain_text(parts)) if t.strip(' .,;—–-')]
    license_name = next((t for t in tokens if LICENSE.match(t)), '')
    # every named creator stays (photographer, "retouch: …"): CC licences require it
    author = ' · '.join(t for t in tokens if t != license_name and not re.fullmatch(r'\(?\d{4}\)?', t))
    file_url = next((p['url'] for p in parts if p.get('host') == 'commons.wikimedia.org'), '')
    license_url = next((p['url'] for p in parts if p.get('host') == 'creativecommons.org'), '')
    return {'author': author, 'license': license_name, 'file_url': file_url, 'license_url': license_url}


@register.filter
def event_caption(value):
    caption = str(value or '').strip()
    for divider in (' — ', ' · '):
        title, found, rest = caption.partition(divider)
        if found:
            parts = _link_parts(rest)
            if _has_photo_credits(parts):
                return {'title': title.strip(), 'credits': parts, 'credit': _credit(parts)}
    return {'title': caption, 'credits': [], 'credit': None}


AZ_LETTERS = re.compile(r'[əğıöüşçƏĞİÖÜŞÇ]')
CYRILLIC = re.compile(r'[а-яёА-ЯЁ]')


@register.filter
def caption_for(title, language):
    """"Kukla Teatrı / Театр кукол / Puppet Theatre (2015)" -> the part in the page's language."""
    title = str(title or '').strip()
    pieces = [p.strip() for p in title.split(' / ') if p.strip()]
    if len(pieces) < 2:
        return title
    year = re.search(r'\s*\(\d{4}\)$', pieces[-1])
    pieces = [re.sub(r'\s*\(\d{4}\)$', '', p) for p in pieces]
    if language == 'ru':
        pick = next((p for p in pieces if CYRILLIC.search(p)), None)
    elif language == 'az':
        pick = next((p for p in pieces if AZ_LETTERS.search(p)), None) or next(
            (p for p in pieces if not CYRILLIC.search(p)), None)
    else:
        latin = [p for p in pieces if not CYRILLIC.search(p) and not AZ_LETTERS.search(p)]
        pick = latin[-1] if latin else None
    return pick or title


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
def event_duration(event, language):
    """'1 saat' / '1 час 30 мин' / '1 h 30 min' for a same-day event up to 8 hours; '' otherwise."""
    start, end = getattr(event, 'start_datetime', None), getattr(event, 'end_datetime', None)
    if not start or not end or end <= start:
        return ''
    minutes = int((end - start).total_seconds() // 60)
    if minutes > 8 * 60:
        return ''
    h, m = divmod(minutes, 60)
    if language == 'ru':
        from catalog.services.event_afisha import ru_plural
        hours = f'{h} ' + ru_plural(h, 'час', 'часа', 'часов') if h else ''
        return (f'{h} ч {m} мин' if h else f'{m} мин') if m else hours
    if language == 'en':
        return ' '.join(x for x in (f'{h} h' if h else '', f'{m} min' if m else '') if x)
    return ' '.join(x for x in (f'{h} saat' if h else '', f'{m} dəq' if m else '') if x)


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
