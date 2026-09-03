"""Read the old free-text ``Place.schedule`` into structured weekday rows.

The parser is deliberately strict: it converts a text only when every word in
it is a weekday, a separator or a time range. Anything it does not fully
understand — "по договорённости", an extra clause about a workshop — is left
untouched and reported for manual review. Guessing a schedule would put wrong
opening hours on a public card.
"""

from __future__ import annotations

import re
import unicodedata

from catalog.services.place_schedule import WEEKDAY_ORDER


# Azerbaijani cards are stored both with and without diacritics, so every
# lookup happens on a folded form.
_FOLD = str.maketrans({
    "ə": "e", "ç": "c", "ş": "s", "ğ": "g", "ı": "i", "ö": "o", "ü": "u",
    "İ": "i", "Ə": "e", "Ç": "c", "Ş": "s", "Ğ": "g", "Ö": "o", "Ü": "u",
    "ё": "е",
})

# Diacritics carry meaning: "Ç.a" is Tuesday and "C.a" is Thursday, and both
# fold to the same ASCII string. So matching happens on the written form first,
# and the folded table below deliberately omits that pair — a card that spells
# days without diacritics keeps its ambiguity and goes to manual review.
EXACT_DAY_TOKENS: tuple[tuple[str, str], ...] = (
    ("bazar ertəsi", "mon"),
    ("çərşənbə axşamı", "tue"),
    ("cümə axşamı", "thu"),
    ("çərşənbə", "wed"),
    ("cümə", "fri"),
    ("şənbə", "sat"),
    ("bazar", "sun"),
    ("b.e", "mon"),
    ("ç.a", "tue"),
    ("çər", "wed"),
    ("c.a", "thu"),
    ("şən", "sat"),
    ("понедельник", "mon"),
    ("вторник", "tue"),
    ("среда", "wed"),
    ("среду", "wed"),
    ("четверг", "thu"),
    ("пятница", "fri"),
    ("пятницу", "fri"),
    ("суббота", "sat"),
    ("субботу", "sat"),
    ("воскресенье", "sun"),
    ("пн", "mon"),
    ("вт", "tue"),
    ("ср", "wed"),
    ("чт", "thu"),
    ("пт", "fri"),
    ("сб", "sat"),
    ("вс", "sun"),
    ("monday", "mon"),
    ("tuesday", "tue"),
    ("wednesday", "wed"),
    ("thursday", "thu"),
    ("friday", "fri"),
    ("saturday", "sat"),
    ("sunday", "sun"),
    ("mon", "mon"),
    ("tue", "tue"),
    ("wed", "wed"),
    ("thu", "thu"),
    ("fri", "fri"),
    ("sat", "sat"),
    ("sun", "sun"),
)

# Folded spellings that stay unique without diacritics.
FOLDED_DAY_TOKENS: tuple[tuple[str, str], ...] = (
    ("bazar ertesi", "mon"),
    ("cersenbe axsami", "tue"),
    ("cume axsami", "thu"),
    ("cersenbe", "wed"),
    ("cume", "fri"),
    ("senbe", "sat"),
    ("bazar", "sun"),
    ("b.e", "mon"),
    ("cer", "wed"),
    ("sen", "sat"),
)

EVERY_DAY_PHRASES = (
    "hər gün",
    "her gun",
    "каждый день",
    "ежедневно",
    "every day",
    "everyday",
    "daily",
    "7 gün",
    "7 gun",
    "без выходных",
)

_TIME_RANGE_RE = re.compile(
    r"(?P<sh>\d{1,2})[:.](?P<sm>\d{2})\s*[-–—]\s*(?P<eh>\d{1,2})[:.](?P<em>\d{2})"
)


def _normalize(value: str) -> str:
    """Lowercase and unify dashes and spaces, keeping diacritics intact."""

    text = unicodedata.normalize("NFC", value or "").lower()
    text = text.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip()


def _fold(value: str) -> str:
    return _normalize(value).translate(_FOLD)


def _parse_day_spec(spec: str) -> tuple[list[str], str]:
    """Turn "пн-сб" or "b.e, cume" into weekday keys."""

    text = spec.strip(" .:,;")
    if not text:
        return [], "не указаны дни"

    for phrase in EVERY_DAY_PHRASES:
        if text == phrase or text.translate(_FOLD) == phrase.translate(_FOLD):
            return list(WEEKDAY_ORDER), ""

    # Split on list separators, keeping ranges ("пн-пт") intact.
    parts = re.split(r"\s*(?:,|\bvə\b|\bve\b|\bи\b|\band\b|&)\s*", text)
    weekdays: list[str] = []
    for part in parts:
        part = part.strip(" .:;")
        if not part:
            continue
        if "-" in part:
            left, _, right = part.partition("-")
            start, reason = _single_day(left)
            if reason:
                return [], reason
            end, reason = _single_day(right)
            if reason:
                return [], reason
            start_index = WEEKDAY_ORDER.index(start)
            end_index = WEEKDAY_ORDER.index(end)
            if end_index < start_index:
                return [], f"диапазон дней «{part}» идёт в обратную сторону"
            weekdays.extend(WEEKDAY_ORDER[start_index:end_index + 1])
            continue
        day, reason = _single_day(part)
        if reason:
            return [], reason
        weekdays.append(day)

    if not weekdays:
        return [], "не указаны дни"
    return weekdays, ""


AZ_DIACRITICS = "əçşğıöü"


def _single_day(token: str) -> tuple[str, str]:
    text = token.strip(" .:;")
    if not text:
        return "", "пустое название дня"
    # Written without diacritics, "C.a" is either Ç.a (Tuesday) or C.a
    # (Thursday). Refuse rather than pick one.
    if text.translate(_FOLD).replace(".", "") == "ca" and not any(ch in AZ_DIACRITICS for ch in text):
        return "", f"«{token.strip()}» без диакритики: это может быть вторник (Ç.a) или четверг (C.a)"
    for label, weekday in EXACT_DAY_TOKENS:
        if text == label or text.replace(".", "") == label.replace(".", ""):
            return weekday, ""
    folded = text.translate(_FOLD)
    for label, weekday in FOLDED_DAY_TOKENS:
        if folded == label or folded.replace(".", "") == label.replace(".", ""):
            return weekday, ""
    return "", f"непонятное название дня «{token.strip()}»"


def parse_legacy_schedule(raw_text: str) -> tuple[list[dict] | None, str]:
    """Return a schedule payload for *raw_text*, or the reason it is unclear."""

    text = _normalize(raw_text)
    if not text:
        return None, "пустое расписание"

    matches = list(_TIME_RANGE_RE.finditer(text))
    if not matches:
        return None, "нет времени работы в тексте"

    intervals_by_day: dict[str, list[dict]] = {}
    cursor = 0
    for index, match in enumerate(matches):
        day_spec = text[cursor:match.start()]
        cursor = match.end()

        if index > 0:
            # Between two clauses only a separator may stand.
            day_spec = day_spec.lstrip(" ;,.")
        weekdays, reason = _parse_day_spec(day_spec)
        if reason:
            return None, reason

        start = f"{int(match.group('sh')):02d}:{match.group('sm')}"
        end = f"{int(match.group('eh')):02d}:{match.group('em')}"
        if start >= end:
            return None, f"интервал {start}-{end} не читается однозначно"
        for weekday in weekdays:
            intervals_by_day.setdefault(weekday, []).append({"start": start, "end": end})

    tail = text[cursor:].strip(" ;,.")
    if tail:
        return None, f"остался неразобранный текст «{tail[:40]}»"

    payload = [
        {
            "weekday": weekday,
            "is_closed": weekday not in intervals_by_day,
            "is_24_hours": False,
            "intervals": intervals_by_day.get(weekday, []),
        }
        for weekday in WEEKDAY_ORDER
    ]
    return payload, ""


def describe_payload(payload: list[dict]) -> str:
    """Short human summary used in the migration report."""

    parts = []
    for day in payload:
        if day["is_closed"]:
            continue
        hours = ", ".join(f"{item['start']}-{item['end']}" for item in day["intervals"])
        parts.append(f"{day['weekday']} {hours}")
    return "; ".join(parts) if parts else "все дни закрыты"
