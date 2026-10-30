"""Stable localized Place paths; reading a URL never writes or translates data."""
import re

from django.conf import settings
from django.db import connections
from django.urls import reverse
from django.utils.translation import override

from catalog.services.slugs import PUBLIC_SLUG_MAX_LENGTH, build_ascii_slug

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
        public_slug = getattr(place, f'public_slug_{language}', None)
        if getattr(place, 'uses_slug_only_urls', False) and public_slug:
            return reverse('place_detail', kwargs={'slug': public_slug})
        return reverse('place_detail', kwargs={'pk': place.pk, 'slug': place_slug_for_language(place, language)})


def place_paths_by_language(place) -> dict[str, str]:
    return {language: place_path_for_language(place, language) for language in PLACE_URL_LANGUAGES}


def build_place_public_slug(value, *, fallback='') -> str:
    slug = build_ascii_slug(str(value or '').replace('_', '-'), fallback=fallback)
    # Keep /123/ and /123-name/ unambiguously owned by the legacy routes.
    if re.match(r'^\d+(?:-|$)', slug):
        slug = f'place-{slug}'[:PUBLIC_SLUG_MAX_LENGTH].rstrip('-')
    return slug


def prepare_place_public_slugs(place, *, previous, update_fields, using) -> set[str]:
    """Reserve URLs at first publication, inside Place.save's transaction.

    NULL public slugs identify legacy rows or unpublished new drafts. Only the
    explicit new-place cohort may acquire a reservation. Saved reservations
    survive renames, soft deletion and stale/injected attributes.
    """
    fields = [f'public_slug_{language}' for language in PLACE_URL_LANGUAGES]
    for field in fields:
        setattr(place, field, getattr(previous, field, None))
    if previous is not None:
        place.uses_slug_only_urls = previous.uses_slug_only_urls
    elif place.is_temporary:
        place.uses_slug_only_urls = False

    def saved_value(field):
        source = previous if previous is not None and update_fields is not None and field not in update_fields else place
        return getattr(source, field)

    content_fields = {'status', 'name', 'name_az', 'name_ru', 'name_en'}
    if (not place.uses_slug_only_urls or saved_value('is_temporary')
            or saved_value('status') != place.STATUS_PUBLISHED
            or (update_fields is not None and not update_fields & content_fields)
            or all(getattr(place, field) for field in fields)):
        return set()

    # Different Place rows can publish the same name concurrently. A row lock
    # alone cannot serialize their reservations; the unique indexes also guard
    # direct SQL/imports that bypass save(). This lock lasts to transaction end.
    connection = connections[using]
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [1263359314])

    fallback = next((saved_value(field) for field in ('name_az', 'name_en', 'name_ru', 'name')
                     if saved_value(field)), 'place')
    distinctions = [saved_value('district'), saved_value('address')]
    changed = set()
    for language, field in zip(PLACE_URL_LANGUAGES, fields):
        if getattr(place, field):
            continue
        base = build_place_public_slug(saved_value(f'name_{language}')) or build_place_public_slug(fallback, fallback='place')
        candidates = [base]
        for value in distinctions:
            distinction = build_ascii_slug(str(value or '').replace('_', '-'), fallback='')
            if distinction:
                suffix = f'-{distinction[:30].rstrip("-")}'
                candidate = f'{base[:PUBLIC_SLUG_MAX_LENGTH - len(suffix)].rstrip("-")}{suffix}'
                if candidate not in candidates:
                    candidates.append(candidate)
        queryset = type(place).objects.using(using).exclude(pk=place.pk)
        candidate = candidates[0]
        for candidate in candidates:
            if not queryset.filter(**{field: candidate}).exists():
                break
        else:
            base = candidates[-1]
            index = 2
            while True:
                suffix = f'-{index}'
                candidate = f'{base[:PUBLIC_SLUG_MAX_LENGTH - len(suffix)].rstrip("-")}{suffix}'
                if not queryset.filter(**{field: candidate}).exists():
                    break
                index += 1
        setattr(place, field, candidate)
        changed.add(field)
    return changed


def place_publication_url_values(place) -> dict[str, str]:
    """URL values for the moderation service's SQL publication update.

    The caller owns the locked Place row inside its publication transaction.
    Reserve from approved names after applying the candidate, before exposing
    the published row; an ordinary model save is deliberately not required.
    """
    from copy import copy

    candidate = copy(place)
    candidate.status = place.STATUS_PUBLISHED
    changed = prepare_place_public_slugs(
        candidate, previous=place, update_fields=None, using=place._state.db or 'default')
    return {field: getattr(candidate, field) for field in changed}


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
