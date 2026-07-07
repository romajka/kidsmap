from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import time

from django.utils.translation import gettext as _


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


def weekday_full_label(weekday: str) -> str:
    return str(_(FULL_DAY_LABELS.get(weekday, weekday)))


def weekday_short_label(weekday: str) -> str:
    return str(_(SHORT_DAY_LABELS.get(weekday, weekday)))


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


def build_schedule_rows(days: list[dict[str, object]]) -> list[dict[str, object]]:
    if not days:
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
            day_label = weekday_full_label(first_weekday)
        else:
            day_label = f"{weekday_full_label(first_weekday)}-{weekday_full_label(last_weekday)}"

        if current_group[0]["is_closed"]:
            lines = [str(_("Закрыто"))]
        elif current_group[0]["is_24_hours"]:
            lines = [str(_("24 часа"))]
        else:
            lines = [f"{item['start']}-{item['end']}" for item in current_group[0]["intervals"]]
        rows.append({"days": day_label, "lines": lines})
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


def build_schedule_summary(days: list[dict[str, object]]) -> str:
    return "\n".join(
        f"{row['days']}  {'; '.join(row['lines'])}"
        for row in build_schedule_rows(days)
    )
