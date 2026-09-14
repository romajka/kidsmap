"""Stable localized Place paths; reading a URL never writes or translates data."""
from django.conf import settings
from django.urls import reverse
from django.utils.translation import override

from catalog.services.slugs import build_ascii_slug

PLACE_URL_LANGUAGES = ('az', 'ru', 'en')


def normalized_place_language(language):
    code = str(language or settings.LANGUAGE_CODE).lower().split('-', 1)[0]
    return code if code in PLACE_URL_LANGUAGES else 'az'


def place_slug_for_language(place, language: str) -> str:
    if getattr(settings, 'LOCALIZED_PLACE_URLS_ENABLED', False):
        localized = getattr(place, f'slug_{normalized_place_language(language)}', '')
        if localized:
            return localized
    return place.slug


def place_path_for_language(place, language: str) -> str:
    language = normalized_place_language(language)
    with override(language):
        return reverse('place_detail', kwargs={'pk': place.pk, 'slug': place_slug_for_language(place, language)})


def place_paths_by_language(place) -> dict[str, str]:
    return {language: place_path_for_language(place, language) for language in PLACE_URL_LANGUAGES}


def populate_missing_place_slugs(place, *, update_fields=None, previous=None) -> set[str]:
    """Called under the save transaction/row lock; ignore caller-supplied slugs.

    For partial saves, names outside update_fields come from the locked row,
    never from possibly unsaved attributes on the instance.
    """
    changed = set()
    for language in PLACE_URL_LANGUAGES:
        field = f'slug_{language}'
        name_field = f'name_{language}'
        saved = getattr(previous, field, '') if previous is not None else ''
        value = saved
        if not value:
            if previous is not None and language == 'az':
                # Very old slugs may predate the 60-character generator.
                # Keep the legacy fallback instead of truncating a live URL.
                value = previous.slug if len(previous.slug) <= 60 else ''
            else:
                source = previous if previous is not None and update_fields is not None and name_field not in update_fields else place
                value = build_ascii_slug(getattr(source, name_field, ''), fallback='')
        setattr(place, field, value)
        if value != saved:
            changed.add(field)
    return changed
