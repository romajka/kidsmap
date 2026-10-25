"""Validate profile-shaped Instagram input, without checking account existence."""
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.utils.translation import get_language


_HANDLE = re.compile(r'[A-Za-z0-9_.]+', re.ASCII)
_HOSTS = {'instagram.com', 'www.instagram.com'}
# These URL routes lead to content/navigation, not a profile page.
_NON_PROFILE_ROUTES = {'p', 'reel', 'reels', 'stories', 'explore', 'accounts', 'direct'}


def instagram_error():
    messages = {
        'ru': 'Укажите имя профиля Instagram, например @kidsmap, или ссылку https://instagram.com/kidsmap.',
        'az': 'Instagram profil adını, məsələn @kidsmap, və ya https://instagram.com/kidsmap keçidini daxil edin.',
        'en': 'Enter an Instagram profile name, such as @kidsmap, or a link like https://instagram.com/kidsmap.',
    }
    return ValidationError(messages.get((get_language() or 'az').split('-')[0], messages['en']),
                           code='invalid_instagram')


def validate_instagram_profile(value):
    """Preserve accepted input; do not invent a username or repair an old link.

    A bare dotted name is treated as a handle, not guessed to be a domain.
    The grammar is local input validation, not a claim about account existence
    or Instagram's current username length/availability rules.
    """
    if not isinstance(value, str):
        raise instagram_error()
    if not value:
        return value
    if any(char.isspace() or unicodedata.category(char) in {'Cc', 'Cf', 'Cs'} for char in value):
        raise instagram_error()
    candidate = value
    if candidate.lower().startswith(('instagram.com/', 'www.instagram.com/')):
        candidate = 'https://' + candidate
    if '://' in candidate:
        try:
            parsed = urlsplit(candidate)
            if (parsed.scheme.lower() not in {'http', 'https'}
                    or parsed.netloc.lower() not in _HOSTS
                    or parsed.username or parsed.password):
                raise ValueError
            handle = parsed.path.removeprefix('/').removesuffix('/')
            if not _HANDLE.fullmatch(handle) or handle.lower() in _NON_PROFILE_ROUTES:
                raise ValueError
        except ValueError as exc:
            raise instagram_error() from exc
    elif not _HANDLE.fullmatch(candidate.removeprefix('@')):
        raise instagram_error()
    return value


def instagram_profile_url(value):
    """Build a link for accepted input; keep the profile path/query case intact."""
    validate_instagram_profile(value)
    if not value:
        return ''
    candidate = value
    if candidate.lower().startswith(('instagram.com/', 'www.instagram.com/')):
        candidate = 'https://' + candidate
    if '://' in candidate:
        parsed = urlsplit(candidate)
        return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(),
                           parsed.path, parsed.query, parsed.fragment))
    return 'https://instagram.com/' + candidate.removeprefix('@')
