"""Bounded spelling variants for discovery, never inferred suitability.

Keep literal brand names. Expand only whole known activity terms, not words
inside arbitrary sentences. A leisure pool is not a swimming lesson.
"""
import re
import unicodedata

from django.db.models import Q


# Reviewed activity names: (whole queries that trigger the group, substrings
# searched for). Outputs are word stems so that inflected forms match
# ("плавания", "шахматная"), and never a generic word that could reach an
# unrelated card ("rəsm" is also part of "rəsmi"). A pool, a park or a venue is
# deliberately not an equivalent of a lesson.
_ACTIVITIES = (
    (('плавание', 'swimming', 'swim', 'üzgüçülük', 'uzguculuk'),
     ('плавани', 'swimming', 'üzgüçülük', 'uzguculuk')),
    (('шахматы', 'chess', 'şahmat', 'shahmat', 'sahmat'),
     ('шахмат', 'chess', 'şahmat')),
    (('робототехника', 'robotics', 'robototexnika'),
     ('робототехник', 'robotic', 'robototexnika')),
    (('танцы', 'танец', 'dance', 'dancing', 'rəqs', 'reqs'),
     ('танц', 'dance', 'rəqs')),
    (('футбол', 'football', 'futbol', 'soccer'),
     ('футбол', 'football', 'futbol')),
    (('английский', 'английский язык', 'english', 'ingilis', 'ingilis dili'),
     ('английск', 'english', 'ingilis')),
    (('гимнастика', 'gymnastics', 'gimnastika'),
     ('гимнаст', 'gymnast', 'gimnastika')),
    (('бокс', 'boxing', 'boks'),
     ('бокс', 'boxing', 'boks')),
    (('каратэ', 'карате', 'karate'),
     ('карат', 'karate')),
    (('дзюдо', 'judo', 'cüdo', 'cudo'),
     ('дзюдо', 'judo', 'cüdo')),
    (('теннис', 'tennis', 'tenis'),
     ('теннис', 'tennis', 'tenis')),
    (('музыка', 'music', 'musiqi'),
     ('музык', 'music', 'musiqi')),
    (('программирование', 'programming', 'coding', 'proqramlaşdırma', 'proqramlasdirma'),
     ('программирован', 'programming', 'coding', 'proqramlaşdırma')),
    (('логопед', 'speech therapist', 'speech therapy', 'loqoped'),
     ('логопед', 'speech therap', 'loqoped')),
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
        for triggers, equivalents in _ACTIVITIES:
            if any(term in triggers for term in variants):
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
