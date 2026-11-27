"""Search copy and structured facts derived from the published event occurrence."""

from django.utils.translation import override

from catalog.services import event_languages
from catalog.services.event_afisha import is_long_event, ru_plural
from catalog.services.event_collections import format_day
from catalog.services.event_queries import BAKU
from catalog.services.locations import (
    AZERBAIJAN_REGIONS_MAP, BAKU_DISTRICTS_MAP, _normalize_location_segment, normalize_to_key,
)


def venue_geography(venue, language):
    """Match whole administrative names from the approved venue snapshot."""
    key = normalize_to_key(venue.get("district"))
    regions = {key} if key in AZERBAIJAN_REGIONS_MAP else set()
    if key in BAKU_DISTRICTS_MAP:
        regions.add("baku")
    explicit_cities = {"baku"}
    for segment in str(venue.get("address") or "").split(","):
        normalized, identity = _normalize_location_segment(segment, language)
        kind, _, key = identity.partition(":")
        if kind == "region":
            regions.add(key)
            if normalized.casefold().endswith((" şəhəri", " город", " city")):
                explicit_cities.add(key)
        elif kind == "district" and normalized.casefold().endswith((" rayonu", " район", " district")):
            regions.add("baku")
    if len(regions) != 1:
        return {}
    key = regions.pop()
    # The taxonomy combines cities and administrative regions. Use locality
    # only when supported by the address or the Baku district hierarchy.
    field = "addressLocality" if key in explicit_cities else "addressRegion"
    return {field: AZERBAIJAN_REGIONS_MAP[key][language], "addressCountry": "AZ"}


def ticket_offer(event):
    if event.occurrence_state == "cancelled" or event.has_ended:
        return None
    if event.price_mode == "free":
        amount = "0"
    elif event.price_mode in {"fixed", "from", "range"} and event.price_amount is not None:
        amount = str(event.price_amount)
    else:
        return None
    if not event.price_currency:
        return None
    offer = {"@type": "Offer", "price": amount, "priceCurrency": event.price_currency}
    if event.price_mode in {"from", "range"}:
        spec = {"@type": "PriceSpecification", "minPrice": amount, "priceCurrency": event.price_currency}
        if event.price_mode == "range" and event.price_amount_max is not None:
            spec["maxPrice"] = str(event.price_amount_max)
        offer["priceSpecification"] = spec
    if event.registration_method == "link":
        url = event.registration["url"]
        if url:
            offer["url"] = url
    return offer


def _age_line(event, language):
    age = event.age_display
    if not age:
        return ""
    if language == "az":
        return f"Yaş — {age}"
    if language == "en":
        return f"Ages {age}"
    low, high = event.age_from, event.age_to
    if low is not None and high is not None:
        bounds = str(low) if low == high else f"{low}–{high}"
        label = f"{bounds} {ru_plural(high, 'год', 'года', 'лет')}"
    elif low == 0:
        label = "с рождения"
    else:
        bound = high if low is None else low
        prefix = "до" if low is None else "от"
        label = f"{prefix} {bound} {ru_plural(bound, 'года', 'лет', 'лет')}"
    return f"Возраст — {label}"


def occurrence_copy(event, language, venue, geography, online):
    name = event.name_i18n(language)
    start = event.start_datetime.astimezone(BAKU)
    end = event.end_datetime.astimezone(BAKU)
    date = format_day(start, language)
    if start.date() == end.date():
        when = f"{date}, {start:%H:%M}"
    elif is_long_event(event):
        when = f"{date} – {format_day(end, language)}"
    else:
        when = f"{date}, {start:%H:%M} – {format_day(end, language)}, {end:%H:%M}"

    if online:
        area = {"az": "onlayn", "ru": "онлайн", "en": "online"}[language]
    elif geography.get("addressLocality") == AZERBAIJAN_REGIONS_MAP["baku"][language]:
        area = {"az": "Bakıda", "ru": "в Баку", "en": "in Baku"}[language]
    else:
        area = geography.get("addressLocality") or geography.get("addressRegion", "")
    separator = " — " if area in geography.values() else " "
    area_suffix = separator + area if area and area.casefold() not in name.casefold() else ""
    headline = name.strip() + area_suffix
    label = (venue.get("label") or "").strip() if not online else ""
    venue_for_title = label if label.casefold() not in name.casefold() else ""
    tail = ", ".join(filter(None, (venue_for_title, when)))
    title = f"{headline} — {tail} | KidsMap"

    if event.occurrence_state == "cancelled":
        status = {"az": "Ləğv edilib", "ru": "Отменено", "en": "Cancelled"}[language]
    elif event.has_ended:
        status = {"az": "Başa çatıb", "ru": "Завершено", "en": "Ended"}[language]
    elif event.occurrence_state == "rescheduled":
        status = {"az": "Vaxtı dəyişdirilib", "ru": "Перенесено", "en": "Rescheduled"}[language]
    else:
        status = ""

    where = label or (venue.get("address") if not online else "")
    first_sentence = f"{headline} — {when}"
    if where:
        first_sentence += f" ({where})"
    first_sentence += "."
    if status:
        first_sentence = f"{status}. {first_sentence}"
    details = []
    with override(language):
        price = event.price_display if event.price_mode != "unknown" else ""
        if price:
            details.append({"az": "Qiymət", "ru": "Стоимость", "en": "Admission"}[language] + f" — {price}")
        age_line = _age_line(event, language)
        if age_line:
            details.append(age_line)
    languages = event_languages.present(event.languages, language)
    if languages:
        names = []
        for item in languages:
            name = item["name"]
            if language == "ru" or (language == "az" and item["code"] != "az"):
                name = name.replace("İ", "i").lower()
            names.append(name)
        spoken = ", ".join(names)
        details.append({"az": "Tədbirin dili", "ru": "Язык проведения", "en": "Event language"}[language] + f" — {spoken}")
    summary = " ".join([first_sentence, *(fact + "." for fact in details)])
    return title, summary, [item["code"] for item in languages]
