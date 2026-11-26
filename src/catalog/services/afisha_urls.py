"""Localized afisha URL segment: /tedbirler/ (az), /ru/afisha/, /en/events/.

Django resolves and reverses i18n routes per active language, so one lazy
route string gives every language its own path without .po entries.
"""
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import get_language, override

AFISHA_SEGMENTS = {'az': 'tedbirler', 'ru': 'afisha', 'en': 'events'}
AFISHA_LANGUAGES = tuple(AFISHA_SEGMENTS)
# Old (pre-2026-11) segment shared by every language.
LEGACY_SEGMENT = 'events'


def afisha_language(language=None) -> str:
    code = str(language or get_language() or 'az').lower().split('-', 1)[0]
    return code if code in AFISHA_SEGMENTS else 'az'


def afisha_segment(language=None) -> str:
    return AFISHA_SEGMENTS[afisha_language(language)]


def localized_route_paths(view_name):
    paths = {}
    for language in AFISHA_LANGUAGES:
        with override(language):
            paths[language] = reverse(view_name)
    return paths


def _route(suffix: str) -> str:
    return f'{afisha_segment()}/{suffix}'


afisha_route = lazy(_route, str)
