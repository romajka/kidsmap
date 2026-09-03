from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import time

from django.utils import timezone
from django.utils.translation import get_language, gettext as _, override


WEEKDAY_ORDER = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
WEEKDAY_CHOICES = tuple((value, value) for value in WEEKDAY_ORDER)

FULL_DAY_LABELS = {
    "mon": "Понедельник",
    "tue": "Вторник",
    "wed": "Среда",
    "thu": "Четверг",
    "fri": "Пятница",
    "sat": "Суббота",
    "sun": "Воскресенье",
}

SHORT_DAY_LABELS = {
    "mon": "Пн",
    "tue": "Вт",
    "wed": "Ср",
    "thu": "Чт",
    "fri": "Пт",
    "sat": "Сб",
    "sun": "Вс",
}

SCHEDULE_MODE_COPY = {
    "ru": {
        "regular": "Расписание",
        "always_open": "Круглосуточно",
        "by_appointment": "По предварительной записи",
        "variable": "Переменное расписание",
        "events": "Ближайшие мероприятия",
        "variable_default": "Расписание меняется. Уточняйте актуальное время у организации.",
        "events_empty": "Ближайшие мероприятия пока не добавлены.",
        "regular_note": "Актуальное время лучше уточнить перед посещением.",
        "always_open_note": "Открыто круглосуточно 24/7.",
    },
    "az": {
        "regular": "Cədvəl",
        "always_open": "Günün 24 saatı",
        "by_appointment": "Əvvəlcədən qeydiyyatla",
        "variable": "Dəyişən cədvəl",
        "events": "Yaxın tədbirlər",
        "variable_default": "Cədvəl dəyişir. Aktual vaxtı təşkilatdan dəqiqləşdirin.",
        "events_empty": "Yaxın tədbirlər hələ əlavə edilməyib.",
        "regular_note": "Ziyarətdən əvvəl aktual vaxtı dəqiqləşdirmək məsləhətdir.",
        "always_open_note": "24/7 açıqdır, fasiləsiz.",
    },
    "en": {
        "regular": "Schedule",
        "always_open": "Round the clock / 24/7",
        "by_appointment": "By appointment",
        "variable": "Variable schedule",
        "events": "Upcoming events",
        "variable_default": "The schedule changes. Confirm the current time with the organization.",
        "events_empty": "No upcoming events have been added yet.",
        "regular_note": "Confirm the current time before visiting.",
        "always_open_note": "Open 24/7, without breaks.",
    },
}

FULL_DAY_LABELS_I18N = {
    "ru": FULL_DAY_LABELS,
    "az": {
        "mon": "Bazar ertəsi",
        "tue": "Çərşənbə axşamı",
        "wed": "Çərşənbə",
        "thu": "Cümə axşamı",
        "fri": "Cümə",
        "sat": "Şənbə",
        "sun": "Bazar",
    },
    "en": {
        "mon": "Monday",
        "tue": "Tuesday",
        "wed": "Wednesday",
        "thu": "Thursday",
        "fri": "Friday",
        "sat": "Saturday",
        "sun": "Sunday",
    },
}

SHORT_DAY_LABELS_I18N = {
    "ru": SHORT_DAY_LABELS,
    "az": {
        "mon": "B.e",
        "tue": "Ç.a",
        "wed": "Çər",
        "thu": "C.a",
        "fri": "Cümə",
        "sat": "Şən",
        "sun": "Bazar",
    },
    "en": {
        "mon": "Mon",
        "tue": "Tue",
        "wed": "Wed",
        "thu": "Thu",
        "fri": "Fri",
        "sat": "Sat",
        "sun": "Sun",
    },
}

OPEN_STATUS_COPY = {
    "ru": {"open": "Сегодня открыто", "closed": "Сегодня закрыто", "today": "сегодня"},
    "az": {"open": "Bu gün açıqdır", "closed": "Bu gün bağlıdır", "today": "bu gün"},
    "en": {"open": "Open today", "closed": "Closed today", "today": "today"},
}

EVENT_MONTHS = {
    "ru": ("января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"),
    "az": ("yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avqust", "sentyabr", "oktyabr", "noyabr", "dekabr"),
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
}


def _schedule_lang(language=None) -> str:
    lang = (language or get_language() or "ru").split("-")[0]
    return lang if lang in SCHEDULE_MODE_COPY else "ru"


def schedule_mode_label(place, language=None) -> str:
    lang = _schedule_lang(language)
    mode = getattr(place, "schedule_mode", "regular") or "regular"
    return SCHEDULE_MODE_COPY[lang].get(mode, SCHEDULE_MODE_COPY[lang]["regular"])


def schedule_mode_note(place, language=None) -> str:
    lang = _schedule_lang(language)
    mode = getattr(place, "schedule_mode", "regular") or "regular"
    custom_note = ""
    if hasattr(place, "schedule_note_i18n"):
        custom_note = (place.schedule_note_i18n(lang) or "").strip()
    if custom_note:
        return custom_note
    if mode == "variable":
        return SCHEDULE_MODE_COPY[lang]["variable_default"]
    if mode == "regular":
        return SCHEDULE_MODE_COPY[lang]["regular_note"]
    return ""


def _format_event_date(value, lang: str) -> str:
    local_value = timezone.localtime(value) if timezone.is_aware(value) else value
    month = EVENT_MONTHS[lang][local_value.month - 1]
    if lang == "en":
        return f"{month} {local_value.day}"
    return f"{local_value.day} {month}"


def _upcoming_place_events(place, limit=3):
    if not getattr(place, "pk", None) or not getattr(place, "events", None):
        return []
    from catalog.services.features import is_events_section_enabled

    if not is_events_section_enabled():
        return []
    now = timezone.now()
    prefetched = getattr(place, "_prefetched_objects_cache", {}).get("events")
    if prefetched is not None:
        candidates = [
            event for event in prefetched
            if event.status == "published"
            and event.deleted_at is None
            and event.start_datetime is not None
            and event.end_datetime is not None
            and event.end_datetime >= now
        ]
        return sorted(candidates, key=lambda event: (event.start_datetime, event.id))[:limit]
    return list(
        place.events.filter(
            status="published",
            deleted_at__isnull=True,
            start_datetime__isnull=False,
            end_datetime__gte=now,
        ).order_by("start_datetime", "id")[:limit]
    )


def build_default_schedule_payload() -> list[dict[str, object]]:
    return [
        {
            "weekday": weekday,
            "is_closed": True,
            "is_24_hours": False,
            "intervals": [],
        }
        for weekday in WEEKDAY_ORDER
    ]


def parse_schedule_payload(raw_value) -> list[dict[str, object]]:
    if isinstance(raw_value, list):
        return raw_value
    if isinstance(raw_value, dict):
        return raw_value.get("days") or build_default_schedule_payload()

    text = str(raw_value or "").strip()
    if not text:
        return build_default_schedule_payload()

    try:
        payload = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return build_default_schedule_payload()

    if isinstance(payload, dict):
        return payload.get("days") or build_default_schedule_payload()
    if isinstance(payload, list):
        return payload
    return build_default_schedule_payload()


def dump_schedule_payload(days: list[dict[str, object]]) -> str:
    return json.dumps(days, ensure_ascii=False)


def is_meaningful_schedule(days: list[dict[str, object]]) -> bool:
    for day in days or []:
        if day.get("is_24_hours"):
            return True
        if not day.get("is_closed") and (day.get("intervals") or []):
            return True
    return False


def weekday_full_label(weekday: str, language=None) -> str:
    lang = _schedule_lang(language)
    return FULL_DAY_LABELS_I18N.get(lang, FULL_DAY_LABELS_I18N["ru"]).get(weekday, weekday)


def weekday_short_label(weekday: str, language=None) -> str:
    lang = _schedule_lang(language)
    return SHORT_DAY_LABELS_I18N.get(lang, SHORT_DAY_LABELS_I18N["ru"]).get(weekday, weekday)


def _coerce_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_time(raw_value: str) -> time | None:
    text = str(raw_value or "").strip()
    if not text:
        return None
    try:
        hours, minutes = text.split(":", 1)
        hour_value = int(hours)
        minute_value = int(minutes)
        if hour_value < 0 or hour_value > 23 or minute_value < 0 or minute_value > 59:
            return None
        return time(hour=hour_value, minute=minute_value)
    except (TypeError, ValueError):
        return None


def _format_time(value: time) -> str:
    return value.strftime("%H:%M")


def _localized_closed_label(language=None) -> str:
    lang = _schedule_lang(language)
    if lang == "az":
        return "Bağlıdır"
    if lang == "en":
        return "Closed"
    return "Закрыто"


def _localized_around_clock_label(language=None) -> str:
    lang = _schedule_lang(language)
    if lang == "az":
        return "24 saat"
    if lang == "en":
        return "24 hours"
    return "Круглосуточно"


@dataclass(slots=True)
class ScheduleValidationResult:
    days: list[dict[str, object]]
    errors: dict[str, list[str]]

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_schedule_payload(raw_value) -> ScheduleValidationResult:
    raw_days = parse_schedule_payload(raw_value)
    indexed_raw = {}
    for item in raw_days:
        if not isinstance(item, dict):
            continue
        weekday = str(item.get("weekday") or "").strip()
        if weekday in WEEKDAY_ORDER and weekday not in indexed_raw:
            indexed_raw[weekday] = item

    normalized_days: list[dict[str, object]] = []
    errors: dict[str, list[str]] = {}

    for weekday in WEEKDAY_ORDER:
        day_payload = indexed_raw.get(weekday, {})
        is_closed = _coerce_bool(day_payload.get("is_closed", True))
        is_24_hours = _coerce_bool(day_payload.get("is_24_hours", False))
        raw_intervals = day_payload.get("intervals") or []
        normalized_intervals: list[dict[str, str]] = []
        parsed_intervals: list[tuple[time, time]] = []
        day_errors: list[str] = []

        if is_closed:
            is_24_hours = False
            raw_intervals = []
        elif is_24_hours:
            raw_intervals = []
        else:
            for raw_interval in raw_intervals:
                if not isinstance(raw_interval, dict):
                    continue
                start_raw = str(raw_interval.get("start") or "").strip()
                end_raw = str(raw_interval.get("end") or "").strip()
                if not start_raw and not end_raw:
                    continue
                if not start_raw or not end_raw:
                    day_errors.append(_("Для интервала укажите и начало, и конец."))
                    continue

                start_value = _parse_time(start_raw)
                end_value = _parse_time(end_raw)
                if start_value is None or end_value is None:
                    day_errors.append(_("Время должно быть в формате HH:MM."))
                    continue
                if start_value == end_value:
                    day_errors.append(_("Начало и конец интервала не должны совпадать."))
                    continue
                if start_value > end_value:
                    day_errors.append(_("Интервал не может переходить через полночь. Разделите его на два дня."))
                    continue

                parsed_intervals.append((start_value, end_value))

            parsed_intervals.sort(key=lambda item: (item[0], item[1]))
            deduplicated: list[tuple[time, time]] = []
            seen = set()
            for item in parsed_intervals:
                key = (_format_time(item[0]), _format_time(item[1]))
                if key in seen:
                    continue
                seen.add(key)
                deduplicated.append(item)
            parsed_intervals = deduplicated

            previous_end: time | None = None
            for start_value, end_value in parsed_intervals:
                if previous_end is not None and start_value < previous_end:
                    day_errors.append(_("Интервалы одного дня не должны пересекаться."))
                    break
                previous_end = end_value

            normalized_intervals = [
                {"start": _format_time(start_value), "end": _format_time(end_value)}
                for start_value, end_value in parsed_intervals
            ]
            if not normalized_intervals and not day_errors:
                day_errors.append(_("Добавьте хотя бы один интервал, отметьте «24 часа» или закройте день."))

        normalized_days.append(
            {
                "weekday": weekday,
                "is_closed": is_closed,
                "is_24_hours": is_24_hours,
                "intervals": normalized_intervals,
            }
        )
        if day_errors:
            errors[weekday] = day_errors

    return ScheduleValidationResult(days=normalized_days, errors=errors)


def serialize_place_schedule(place) -> list[dict[str, object]]:
    if not getattr(place, "pk", None) or not getattr(place, "schedule_days", None):
        return build_default_schedule_payload()

    days_by_weekday = {}
    for day in place.schedule_days.all():
        intervals = [
            {
                "start": interval.start_time.strftime("%H:%M"),
                "end": interval.end_time.strftime("%H:%M"),
            }
            for interval in day.intervals.all()
        ]
        days_by_weekday[day.weekday] = {
            "weekday": day.weekday,
            "is_closed": day.is_closed,
            "is_24_hours": day.is_24_hours,
            "intervals": intervals,
        }

    return [days_by_weekday.get(weekday, build_default_schedule_payload()[index]) for index, weekday in enumerate(WEEKDAY_ORDER)]


def sync_place_schedule(place, days: list[dict[str, object]]) -> None:
    from catalog.models import PlaceScheduleDay, PlaceScheduleInterval

    place.schedule_days.all().delete()
    if not is_meaningful_schedule(days):
        return

    created_days: dict[str, PlaceScheduleDay] = {}
    for order, day in enumerate(days):
        created_day = PlaceScheduleDay.objects.create(
            place=place,
            weekday=day["weekday"],
            is_closed=bool(day["is_closed"]),
            is_24_hours=bool(day["is_24_hours"]),
            order=order,
        )
        created_days[created_day.weekday] = created_day

    interval_objects: list[PlaceScheduleInterval] = []
    for day in days:
        schedule_day = created_days[day["weekday"]]
        for order, interval in enumerate(day.get("intervals") or []):
            start_value = _parse_time(interval.get("start"))
            end_value = _parse_time(interval.get("end"))
            if start_value is None or end_value is None:
                continue
            interval_objects.append(
                PlaceScheduleInterval(
                    schedule_day=schedule_day,
                    start_time=start_value,
                    end_time=end_value,
                    order=order,
                )
            )
    if interval_objects:
        PlaceScheduleInterval.objects.bulk_create(interval_objects)


def schedule_signature(day: dict[str, object]) -> tuple:
    intervals = tuple((item["start"], item["end"]) for item in (day.get("intervals") or []))
    return (bool(day.get("is_closed")), bool(day.get("is_24_hours")), intervals)


def build_schedule_rows(days: list[dict[str, object]], language=None) -> list[dict[str, object]]:
    lang = _schedule_lang(language)
    if not is_meaningful_schedule(days):
        return []

    rows: list[dict[str, object]] = []
    current_group: list[dict[str, object]] = []
    current_signature: tuple | None = None

    def flush_group():
        nonlocal current_group, current_signature
        if not current_group:
            return
        first_weekday = current_group[0]["weekday"]
        last_weekday = current_group[-1]["weekday"]
        if len(current_group) == 1:
            day_label = weekday_full_label(first_weekday, lang)
        else:
            day_label = f"{weekday_full_label(first_weekday, lang)}–{weekday_full_label(last_weekday, lang)}"

        if current_group[0]["is_closed"]:
            lines = [_localized_closed_label(lang)]
        elif current_group[0]["is_24_hours"]:
            lines = [_localized_around_clock_label(lang)]
        else:
            lines = [f"{item['start']}–{item['end']}" for item in current_group[0]["intervals"]]
        rows.append({
            "days": day_label,
            "lines": lines,
            "is_closed": current_group[0]["is_closed"],
            "is_24_hours": current_group[0]["is_24_hours"],
        })
        current_group = []
        current_signature = None

    for day in days:
        signature = schedule_signature(day)
        if current_signature is None or signature == current_signature:
            current_group.append(day)
            current_signature = signature
            continue
        flush_group()
        current_group.append(day)
        current_signature = signature

    flush_group()
    return rows


def build_schedule_summary(days: list[dict[str, object]], language=None) -> str:
    return "\n".join(
        f"{row['days']}  {'; '.join(row['lines'])}"
        for row in build_schedule_rows(days, language)
    )


def build_public_schedule_rows(place, language=None, *, event_limit=3) -> list[dict[str, object]]:
    """Build one public row shape for weekly, variable and event schedules."""
    lang = _schedule_lang(language)
    mode = getattr(place, "schedule_mode", "regular") or "regular"
    copy = SCHEDULE_MODE_COPY[lang]

    if mode == "always_open":
        text = copy["always_open"]
        return [{"days": "", "time": text, "lines": [text], "is_closed": False, "url": ""}]

    if mode == "by_appointment":
        text = copy["by_appointment"]
        return [{"days": "", "time": text, "lines": [text], "is_closed": False, "url": ""}]

    if mode == "variable":
        text = schedule_mode_note(place, lang)
        return [{"days": "", "time": text, "lines": [text], "is_closed": False, "url": ""}]

    if mode == "events":
        events = _upcoming_place_events(place, event_limit)
        if not events:
            text = copy["events_empty"]
            return [{"days": "", "time": text, "lines": [text], "is_closed": False, "url": ""}]
        rows = []
        for event in events:
            starts_at = timezone.localtime(event.start_datetime) if timezone.is_aware(event.start_datetime) else event.start_datetime
            event_text = f"{starts_at:%H:%M} · {event.name_i18n(lang)}"
            rows.append({
                "days": _format_event_date(event.start_datetime, lang),
                "time": event_text,
                "lines": [event_text],
                "is_closed": False,
                "url": event.get_absolute_url(),
            })
        return rows

    if getattr(place, "has_structured_schedule", False):
        weekly_rows = build_schedule_rows(serialize_place_schedule(place), lang)
        public_rows = []
        all_day_label = "24h" if lang == "en" else ("24 saat" if lang == "az" else "круглосуточно")
        for row in weekly_rows:
            lines = [all_day_label] if row["is_24_hours"] else row["lines"]
            public_rows.append({**row, "lines": lines, "time": ", ".join(lines), "url": ""})
        return public_rows

    legacy_text = (getattr(place, "schedule", "") or "").strip()
    if legacy_text:
        return [{"days": "", "time": legacy_text, "lines": [legacy_text], "is_closed": False, "url": ""}]
    return []


def build_public_schedule_summary(place, language=None) -> str:
    rows = build_public_schedule_rows(place, language)
    return "\n".join(
        f"{row['days']}  {row['time']}".strip()
        for row in rows
        if row.get("time")
    )


def _today_weekday_key() -> str:
    return WEEKDAY_ORDER[timezone.localdate().weekday()]


def _day_display_lines(day: dict[str, object], language=None) -> list[str]:
    lang = _schedule_lang(language)
    if day["is_closed"]:
        return [_localized_closed_label(lang)]
    if day["is_24_hours"]:
        return [_localized_around_clock_label(lang)]
    return [f"{item['start']}–{item['end']}" for item in day.get("intervals") or []]


def build_public_schedule_week(place, language=None) -> list[dict[str, object]]:
    """Seven per-day cells for the detail card grid; empty when there is no weekly schedule.

    Reads the same prefetched ``schedule_days__intervals`` as the grouped rows,
    so it costs no extra query on the place detail page.
    """
    mode = getattr(place, "schedule_mode", "regular") or "regular"
    if mode != "regular" or not getattr(place, "has_structured_schedule", False):
        return []

    lang = _schedule_lang(language)
    labels = SHORT_DAY_LABELS_I18N[lang]
    today = _today_weekday_key()
    cells = []
    for day in serialize_place_schedule(place):
        weekday = day["weekday"]
        cells.append(
            {
                "weekday": weekday,
                "label": labels.get(weekday, weekday),
                "lines": _day_display_lines(day, lang),
                "is_closed": bool(day["is_closed"]),
                "is_24_hours": bool(day["is_24_hours"]),
                "is_today": weekday == today,
            }
        )
    return cells


def build_open_status(place, language=None) -> dict[str, object]:
    """Whether the place is open right now, for the "open today" marker.

    Returns an empty dict when the schedule cannot answer the question, so the
    template can simply skip the marker instead of guessing.
    """
    mode = getattr(place, "schedule_mode", "regular") or "regular"
    if mode == "always_open":
        lang = _schedule_lang(language)
        time_text = _localized_around_clock_label(lang)
        return {"is_open": True, "label": OPEN_STATUS_COPY[lang]["open"], "time": time_text}
    if mode != "regular" or not getattr(place, "has_structured_schedule", False):
        return {}

    lang = _schedule_lang(language)
    today = _today_weekday_key()
    day = next(
        (item for item in serialize_place_schedule(place) if item["weekday"] == today),
        None,
    )
    if day is None:
        return {}

    lines = _day_display_lines(day, lang)

    if day["is_closed"]:
        return {"is_open": False, "label": OPEN_STATUS_COPY[lang]["closed"], "time": ""}
    if day["is_24_hours"]:
        return {"is_open": True, "label": OPEN_STATUS_COPY[lang]["open"], "time": lines[0] if lines else ""}

    now = timezone.localtime().time()
    is_open = False
    for interval in day.get("intervals") or []:
        start_value = _parse_time(interval.get("start"))
        end_value = _parse_time(interval.get("end"))
        if start_value is None or end_value is None:
            continue
        if end_value <= start_value:
            # Interval runs past midnight.
            if now >= start_value or now < end_value:
                is_open = True
                break
        elif start_value <= now < end_value:
            is_open = True
            break

    if not lines:
        return {}
    return {
        "is_open": is_open,
        "label": OPEN_STATUS_COPY[lang]["open" if is_open else "closed"],
        "time": " · ".join(lines),
    }
