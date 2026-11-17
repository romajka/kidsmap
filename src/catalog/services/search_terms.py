"""Bounded spelling variants for discovery, never inferred suitability.

Keep literal brand names. Expand only whole known activity terms, not words
inside arbitrary sentences. A leisure pool is not a swimming lesson.
"""
import re
import unicodedata

from django.db.models import Q


_ACTIVITIES = (
    ('плавание', 'swimming', 'üzgüçülük', 'uzguculuk'),
    ('шахматы', 'chess', 'şahmat', 'shahmat'),
    ('робототехника', 'robotics', 'robototexnika'),
)
_DIGRAPHS = {
    'shch': 'щ', 'sch': 'щ', 'zh': 'ж', 'kh': 'х', 'ts': 'ц',
    'ch': 'ч', 'sh': 'ш', 'yu': 'ю', 'ya': 'я', 'yo': 'ё',
}
_LETTERS = str.maketrans({
    'a': 'а', 'b': 'б', 'c': 'ц', 'd': 'д', 'e': 'е', 'f': 'ф',
    'g': 'г', 'h': 'х', 'i': 'и', 'j': 'й', 'k': 'к', 'l': 'л',
    'm': 'м', 'n': 'н', 'o': 'о', 'p': 'п', 'q': 'к', 'r': 'р',
    's': 'с', 't': 'т', 'u': 'у', 'v': 'в', 'w': 'в', 'x': 'кс',
    'y': 'ы', 'z': 'з',
})
_LATIN_QUERY = re.compile(r"[a-z][a-z0-9 '\-]*\Z")
_TRANSLIT_PART = re.compile('|'.join(_DIGRAPHS) + '|[a-z]')


def query_variants(query):
    """Preserve the input and add a small deterministic set of equivalents."""
    literal = (query or '').strip()
    if not literal:
        return ()
    normalized = ' '.join(unicodedata.normalize('NFC', literal).split()).casefold()
    variants = [literal, normalized]
    # Avoid multiplying very long user input into a large SQL expression.
    if len(normalized) <= 120:
        if len(normalized) >= 3 and _LATIN_QUERY.fullmatch(normalized):
            transliterated = _TRANSLIT_PART.sub(
                lambda m: _DIGRAPHS.get(m[0], m[0].translate(_LETTERS)), normalized)
            variants.append(transliterated)
        for equivalents in _ACTIVITIES:
            if any(term in equivalents for term in variants):
                variants.extend(equivalents)
                break
        # SQLite's LIKE is ASCII-only; keep initial capitals discoverable in
        # local/test data too. PostgreSQL handles Unicode case-insensitivity.
        variants += [term.capitalize() for term in tuple(variants)]
    return tuple(dict.fromkeys(variants))


def text_query(query, fields):
    """OR text variants inside a single entity's existing filter boundary."""
    result = Q(pk__in=[])
    for term in query_variants(query):
        for field in fields:
            result |= Q(**{field + '__icontains': term})
    return result
