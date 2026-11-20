"""Allocation rules for public event paths, also used by migration 0161."""
import re
import unicodedata
from itertools import count, product
from string import ascii_lowercase

from catalog.services.slugs import PUBLIC_SLUG_MAX_LENGTH, build_ascii_slug


def event_slug_base(value):
    text = unicodedata.normalize('NFKC', str(value or ''))
    words = re.sub(r'[\d_]+', ' ', text)
    return build_ascii_slug(words, fallback='tedbir')


def available_event_slug(base, is_taken):
    if not is_taken(base):
        return base
    for length in count(1):
        for letters in product(ascii_lowercase, repeat=length):
            suffix = '-' + ''.join(letters)
            candidate = base[:PUBLIC_SLUG_MAX_LENGTH - len(suffix)].rstrip('-') + suffix
            if not is_taken(candidate):
                return candidate
