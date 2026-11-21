"""Suggest the language for events that have none yet (dry run by default).

    python manage.py suggest_event_languages            # print suggestions only
    python manage.py suggest_event_languages --apply    # save the confident ones

A guess is made only from explicit signals; everything else is listed as
"manual" for a moderator (admin → Events → filter «Язык проведения: Не указан»).
"""
import re

from django.core.management.base import BaseCommand

from catalog.models import Event
from catalog.services.event_languages import normalize

# Venue names that state the stage language.
VENUE_HINTS = (
    (re.compile(r'rus\s+dram|русск\w*\s+драм|russian\s+drama', re.I), 'ru'),
)
# Explicit mentions in the organizer's own text.
TEXT_HINTS = (
    (re.compile(r'на\s+русском|rus\s+dilində|in\s+russian', re.I), 'ru'),
    (re.compile(r'на\s+азербайджанском|azərbaycan\s+dilində|in\s+azerbaijani', re.I), 'az'),
    (re.compile(r'на\s+английском|ingilis\s+dilində|in\s+english', re.I), 'en'),
    (re.compile(r'на\s+турецком|türk\s+dilində|in\s+turkish', re.I), 'tr'),
)


def suggest(event):
    venue = event.venue_snapshot if isinstance(event.venue_snapshot, dict) else {}
    venue_text = ' '.join(str(venue.get(key) or '') for key in ('label', 'address')) + ' ' + (event.address or '')
    text = ' '.join(str(getattr(event, field, '') or '') for field in (
        'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'description_en'))
    found, reasons = set(), []
    for pattern, code in TEXT_HINTS:
        if pattern.search(text):
            found.add(code)
            reasons.append('text mentions ' + code)
    if not found:
        for pattern, code in VENUE_HINTS:
            if pattern.search(venue_text):
                found.add(code)
                reasons.append('venue ' + code)
    return normalize(found), ', '.join(reasons)


class Command(BaseCommand):
    help = 'Suggest Event.languages for events without a language; --apply saves confident guesses.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Save confident suggestions.')

    def handle(self, *args, apply=False, **options):
        events = Event.objects.filter(languages='', deleted_at__isnull=True).order_by('start_datetime')
        saved = manual = 0
        for event in events:
            value, why = suggest(event)
            name = event.name_ru or event.name_az or event.name
            if not value:
                manual += 1
                self.stdout.write(f'manual  #{event.pk} {name}')
                continue
            self.stdout.write(f'{value:<7} #{event.pk} {name}  ({why})')
            if apply:
                # Only the language column changes; no save() side effects.
                Event.objects.filter(pk=event.pk, languages='').update(languages=value)
                saved += 1
        self.stdout.write(self.style.SUCCESS(
            f'{"saved" if apply else "suggested"}: {saved if apply else events.count() - manual}, manual: {manual}'))
