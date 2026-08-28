"""Deterministic quality checks required before a place is marked verified."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import re


AZERBAIJAN_BOUNDS = (38.3, 41.9, 44.7, 50.8)
WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}


@dataclass(frozen=True)
class PlaceCardIssue:
    code: str
    field: str
    message: str


@dataclass
class PlaceCardValidationResult:
    errors: list[PlaceCardIssue] = field(default_factory=list)
    warnings: list[PlaceCardIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


def _decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _plan_minimum(plan):
    value = getattr(plan, "price", None) if not isinstance(plan, dict) else plan.get("price")
    kind = getattr(plan, "price_kind", "") if not isinstance(plan, dict) else plan.get("price_kind", "")
    if kind in {"exact", "free"}:
        return _decimal(value)
    if kind in {"from", "range"}:
        value = getattr(plan, "price_min", None) if not isinstance(plan, dict) else plan.get("price_min")
        return _decimal(value)
    # Legacy JSON plans have just `price`.
    return _decimal(value)


def _active_primary_prices(place):
    prices = []
    for plan in place.pricing_plans or []:
        active = getattr(plan, "is_active", True) if not isinstance(plan, dict) else plan.get("is_active", True)
        role = getattr(plan, "charge_role", "primary") if not isinstance(plan, dict) else plan.get("charge_role", "primary")
        if not active or role != "primary":
            continue
        price = _plan_minimum(plan)
        if price is not None:
            prices.append(price)
    return prices


def _has_photo(place) -> bool:
    if place.photo or place.cover_photo:
        return True
    return bool(place.pk and place.gallery.exists())


def _language_warning(text: str, expected: str) -> bool:
    """Deliberately conservative: names, brands and addresses do not trigger it."""
    text = (text or "").strip()
    words = re.findall(r"[A-Za-zА-Яа-яЁёƏəĞğİıÖöŞşÇçÜü]+", text)
    if len(words) < 8:
        return False
    cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
    az_specific = len(re.findall(r"[ƏəĞğİıÖöŞşÇçÜü]", text))
    english_words = len(re.findall(r"\b(?:the|and|with|for|from|our|your|children|lessons|school|open)\b", text, re.I))
    if expected == "ru":
        return cyrillic < 20 and (az_specific >= 3 or english_words >= 3)
    if expected == "az":
        return cyrillic >= 20 or english_words >= 3
    return cyrillic >= 20 or az_specific >= 3


def validate_place_card(place) -> PlaceCardValidationResult:
    result = PlaceCardValidationResult()
    error, warning = result.errors.append, result.warnings.append

    if place.age_from is not None and place.age_to is not None and place.age_from > place.age_to:
        error(PlaceCardIssue("AGE_RANGE_INVALID", "age_to", "Возраст «до» не может быть меньше возраста «от»."))

    if not _has_photo(place):
        error(PlaceCardIssue("MISSING_PHOTO", "photo", "Добавьте хотя бы одну фотографию."))

    if place.lat is None or place.lng is None:
        error(PlaceCardIssue("MISSING_COORDINATES", "lat", "Укажите координаты места."))
    else:
        try:
            lat, lng = float(place.lat), float(place.lng)
        except (TypeError, ValueError):
            error(PlaceCardIssue("INVALID_COORDINATES", "lat", "Координаты должны быть числами."))
        else:
            if not -90 <= lat <= 90 or not -180 <= lng <= 180:
                error(PlaceCardIssue("INVALID_COORDINATES", "lat", "Координаты находятся вне допустимого диапазона."))
            elif not (AZERBAIJAN_BOUNDS[0] <= lat <= AZERBAIJAN_BOUNDS[1] and AZERBAIJAN_BOUNDS[2] <= lng <= AZERBAIJAN_BOUNDS[3]):
                warning(PlaceCardIssue("COORDINATES_OUTSIDE_AZERBAIJAN", "lat", "Координаты находятся за пределами Азербайджана. Проверьте точку на карте."))
            else:
                from catalog.services.district_geometry import district_for_coordinates
                from catalog.services.locations import normalize_to_key

                selected_district = normalize_to_key(place.district)
                actual_district = district_for_coordinates(lat, lng)
                if selected_district.startswith("baku_") and actual_district and selected_district != actual_district:
                    warning(PlaceCardIssue(
                        "DISTRICT_COORDINATE_MISMATCH",
                        "district",
                        "Указанный район не соответствует координатам места.",
                    ))

    has_phone = any((phone or "").strip() for phone in (place.phone1, place.phone2, place.phone3))
    if not has_phone and not (place.instagram or "").strip() and not (place.website or "").strip():
        error(PlaceCardIssue("MISSING_CONTACT", "phone1", "Укажите хотя бы один контакт."))

    prices = _active_primary_prices(place)
    if prices:
        minimum = min(prices)
        displayed = _decimal(place.price_from)
        if displayed != minimum:
            error(PlaceCardIssue("PRICE_MISMATCH", "pricing_plans", f"Минимальная цена карточки — {displayed if displayed is not None else 'не указана'} AZN, а минимальный основной тариф — {minimum} AZN."))
        if displayed == 0 and any(price > 0 for price in prices):
            error(PlaceCardIssue("FREE_PRICE_MISMATCH", "pricing_plans", "Карточка отмечена как бесплатная, хотя есть платный основной тариф."))

    days = list(place.schedule_days.prefetch_related("intervals").all()) if place.pk else []
    for day in days:
        if day.weekday not in WEEKDAYS:
            error(PlaceCardIssue("INVALID_SCHEDULE_DAY", "structured_schedule", "В расписании указан неизвестный день недели."))
        intervals = list(day.intervals.all())
        if (day.is_closed or day.is_24_hours) and intervals:
            error(PlaceCardIssue("SCHEDULE_CONFLICT", "structured_schedule", "Закрытый день или режим 24/7 не должен содержать интервалы работы."))
        seen = set()
        for interval in intervals:
            pair = (interval.start_time, interval.end_time)
            if pair in seen:
                error(PlaceCardIssue("DUPLICATE_SCHEDULE_INTERVAL", "structured_schedule", "В расписании есть дублирующийся интервал."))
            seen.add(pair)
            if interval.start_time >= interval.end_time:
                error(PlaceCardIssue("INVALID_SCHEDULE_INTERVAL", "structured_schedule", "Время начала должно быть раньше времени окончания."))

    for lang in ("az", "ru", "en"):
        for field_name in (f"name_{lang}", f"description_{lang}", f"extra_conditions_{lang}", f"additional_info_{lang}"):
            if _language_warning(getattr(place, field_name, ""), lang):
                warning(PlaceCardIssue("LANGUAGE_MIX", field_name, f"В поле {field_name} возможно присутствует текст на другом языке."))

    return result
