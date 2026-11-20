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
