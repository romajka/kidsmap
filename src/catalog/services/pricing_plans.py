from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _, get_language


MAX_PRICING_PLANS = 20
DEFAULT_CURRENCY = "AZN"
LESSON_FORMATS = {"group", "individual", "open_visit"}
PAYMENT_TYPES = {"per_lesson", "per_month", "package", "per_visit", "entry_ticket"}

_FORMAT_LABELS = {
    "az": {"group": "Qrup", "individual": "Fərdi", "open_visit": "Sərbəst ziyarət"},
    "ru": {"group": "Групповые", "individual": "Индивидуальные", "open_visit": "Свободное посещение"},
    "en": {"group": "Group", "individual": "Individual", "open_visit": "Open visit"},
}
_PAYMENT_LABELS = {
    "az": {"per_lesson": "dərs üçün", "per_month": "ay üçün", "package": "paket", "per_visit": "ziyarət üçün", "entry_ticket": "giriş bileti"},
    "ru": {"per_lesson": "за занятие", "per_month": "за месяц", "package": "пакет", "per_visit": "за посещение", "entry_ticket": "входной билет"},
    "en": {"per_lesson": "per lesson", "per_month": "per month", "package": "package", "per_visit": "per visit", "entry_ticket": "entry ticket"},
}


def _as_int(value, field_name, *, required=False):
    if value in (None, ""):
        if required:
            raise ValidationError(_("Укажите количество занятий в пакете."))
        return None
    if isinstance(value, bool):
        raise ValidationError(_("Количество занятий должно быть положительным целым числом."))
    try:
        result = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(_("Количество занятий должно быть положительным целым числом."))
    if result <= 0:
        raise ValidationError(_("Количество занятий должно быть больше нуля."))
    return result


def _as_price(value):
    if value in (None, ""):
        raise ValidationError(_("Укажите цену тарифа."))
    try:
        price = Decimal(str(value).strip().replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(_("Цена должна быть корректным числом."))
    if price < 0:
        raise ValidationError(_("Цена не может быть отрицательной."))
    return format(price.quantize(Decimal("0.01")), "f")


def _legacy_plan(plan, index):
    return {
        "lesson_format": "",
        "sessions_per_week": None,
        "sessions_per_month": None,
        "payment_type": "",
        "package_sessions": None,
        "price": _as_price(plan.get("price")) if str(plan.get("price") or "").strip() else "",
        "currency": DEFAULT_CURRENCY,
        "title_az": "",
        "title_ru": str(plan.get("name") or "").strip()[:120],
        "title_en": "",
        "is_active": True,
        "sort_order": index,
        "_legacy_frequency": str(plan.get("frequency") or "").strip()[:120],
    }


def normalize_pricing_plans(value, *, strict=True):
    """Return storage-ready plans without mutating the supplied value.

    Legacy {name, price, frequency} entries are accepted and converted only in
    the returned value, so callers can use this result on an explicit save.
    """
    if isinstance(value, str):
        try:
            value = json.loads(value or "[]")
        except (TypeError, ValueError, json.JSONDecodeError):
            raise ValidationError(_("Проверьте список тарифов."))
    if value in (None, ""):
        value = []
    if not isinstance(value, list):
        raise ValidationError(_("Проверьте список тарифов."))
    if len(value) > MAX_PRICING_PLANS:
        raise ValidationError(_("Можно добавить не более 20 тарифов."))

    normalized = []
    for index, raw in enumerate(value):
        try:
            if not isinstance(raw, dict):
                if strict:
                    raise ValidationError(_("Некорректный формат тарифа."))
                continue
            content_keys = {
                "lesson_format", "sessions_per_week", "sessions_per_month", "payment_type",
                "package_sessions", "price", "title_az", "title_ru", "title_en", "name", "frequency",
            }
            if not any(str(raw.get(key) or "").strip() for key in content_keys):
                continue
            if {"name", "price", "frequency"}.intersection(raw) and not {
                "lesson_format", "payment_type", "title_az", "title_ru", "title_en"
            }.intersection(raw):
                legacy = _legacy_plan(raw, index)
                if legacy["price"]:
                    normalized.append(legacy)
                continue

            lesson_format = str(raw.get("lesson_format") or "").strip()
            payment_type = str(raw.get("payment_type") or "").strip()
            currency = str(raw.get("currency") or DEFAULT_CURRENCY).strip().upper()[:3] or DEFAULT_CURRENCY
            if lesson_format and lesson_format not in LESSON_FORMATS:
                raise ValidationError(_("Неизвестный формат занятия."))
            if payment_type and payment_type not in PAYMENT_TYPES:
                raise ValidationError(_("Неизвестный тип оплаты."))
            if not lesson_format and not payment_type and not raw.get("price"):
                continue
            if not lesson_format or not payment_type:
                raise ValidationError(_("Укажите формат занятия и тип оплаты тарифа."))
            package_sessions = _as_int(raw.get("package_sessions"), "package_sessions", required=payment_type == "package")
            normalized.append(
                {
                    "lesson_format": lesson_format,
                    "sessions_per_week": _as_int(raw.get("sessions_per_week"), "sessions_per_week"),
                    "sessions_per_month": _as_int(raw.get("sessions_per_month"), "sessions_per_month"),
                    "payment_type": payment_type,
                    "package_sessions": package_sessions,
                    "price": _as_price(raw.get("price")),
                    "currency": currency,
                    "title_az": str(raw.get("title_az") or "").strip()[:120],
                    "title_ru": str(raw.get("title_ru") or "").strip()[:120],
                    "title_en": str(raw.get("title_en") or "").strip()[:120],
                    "is_active": bool(raw.get("is_active", True)),
                    "sort_order": max(0, int(str(raw.get("sort_order")).strip())) if raw.get("sort_order") not in (None, "") and str(raw.get("sort_order")).strip().isdigit() else index,
                }
            )
        except ValidationError as exc:
            if strict:
                message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
                raise ValidationError(
                    _("Тариф %(number)s: %(error)s"),
                    params={"number": index + 1, "error": message},
                )
            continue
    return normalized


def public_pricing_plans(value, language=None):
    """Safely normalize plans for display; invalid entries are hidden."""
    try:
        plans = normalize_pricing_plans(value, strict=False)
    except ValidationError:
        return []
    lang = (language or get_language() or "az").split("-")[0]
    if lang not in _FORMAT_LABELS:
        lang = "ru"
    result = []
    for plan in sorted(plans, key=lambda item: (item.get("sort_order", 0),)):
        if not plan.get("is_active", True):
            continue
        frequency = plan.pop("_legacy_frequency", "")
        format_label = _FORMAT_LABELS[lang].get(plan.get("lesson_format"), "")
        payment_label = _PAYMENT_LABELS[lang].get(plan.get("payment_type"), frequency)
        title = (
            plan.get(f"title_{lang}")
            or plan.get("title_az")
            or plan.get("title_ru")
            or plan.get("title_en")
            or " · ".join(part for part in (format_label, payment_label) if part)
        )
        result.append(
            {
                **plan,
                "title": title,
                "format_label": format_label,
                "payment_label": payment_label,
            }
        )
    return result


def active_pricing_plan_range(value):
    """Return the canonical min/max price for active tariffs, if any."""
    try:
        plans = normalize_pricing_plans(value, strict=False)
    except ValidationError:
        return None

    prices = []
    for plan in plans:
        if not plan.get("is_active", True) or plan.get("price") in (None, ""):
            continue
        # Place.price_from/price_to are AZN fields. Other currencies stay in
        # their tariff rows and must never overwrite the card's AZN range.
        if (plan.get("currency") or DEFAULT_CURRENCY).upper() != DEFAULT_CURRENCY:
            continue
        try:
            prices.append(Decimal(str(plan["price"])))
        except (InvalidOperation, TypeError, ValueError):
            continue
    if not prices:
        return None
    return min(prices), max(prices)


def has_azn_pricing_plans(value):
    """Whether valid AZN tariff rows exist, including inactive rows."""
    try:
        plans = normalize_pricing_plans(value, strict=False)
    except ValidationError:
        return False
    return any(
        (plan.get("currency") or DEFAULT_CURRENCY).upper() == DEFAULT_CURRENCY
        for plan in plans
    )


def format_price_amount(value) -> str:
    amount = Decimal(str(value))
    if amount == amount.to_integral_value():
        return str(int(amount))
    return format(amount.normalize(), "f")


LOCALIZED_STRINGS = {
    "az": {
        "title": "Qiymət və dərslər",
        "subtitle": "Format, tezlik və ödəniş variantları",
        "price_label": "Qiymət",
        "from": "",
        "suffix_den": "dən",
        "per_lesson_under": "bir dərs üçün",
        "per_visit_under": "bir ziyarət üçün",
        "entry_ticket_under": "giriş bileti",
        "per_month_under": "bir ay üçün",
        "package_under": "paket üçün",
        "per_lesson": "dərs",
        "per_visit": "ziyarət",
        "entry_ticket": "giriş bileti",
        "per_month": "ay",
        "package": "paket",
        "schedule_label": "Dərs cədvəli",
        "schedule_working_hours": "İş saatları",
        "schedule_by_appointment": "Razılaşma ilə",
        "schedule_note": "Dərs vaxtını təşkilatla dəqiqləşdirin",
        "tariffs": "Tariflər",
        "show_all": "Bütün tarifləri göstər",
        "hide_all": "Tarifləri gizlət",
        "price_unknown": "Qiymət təşkilatla dəqiqləşdirilir",
        "free": "Pulsuz",
        "group": "Qrup",
        "individual": "Fərdi",
        "open_visit": "Sərbəst ziyarət",
        "sessions_per_week": "həftədə {count} dəfə",
        "sessions_per_month": "ayda {count} dəfə",
        "minutes": "{count} dəqiqə",
    },
    "ru": {
        "title": "Цена и занятия",
        "subtitle": "Формат, частота и варианты оплаты",
        "price_label": "Цена",
        "from": "от",
        "suffix_den": "",
        "per_lesson_under": "за занятие",
        "per_visit_under": "за посещение",
        "entry_ticket_under": "входной билет",
        "per_month_under": "в месяц",
        "package_under": "за пакет",
        "per_lesson": "занятие",
        "per_visit": "посещение",
        "entry_ticket": "входной билет",
        "per_month": "месяц",
        "package": "пакет",
        "schedule_label": "Расписание занятий",
        "schedule_working_hours": "Рабочие часы",
        "schedule_by_appointment": "Занятия по предварительной записи",
        "schedule_note": "Время занятий уточняйте у организации",
        "tariffs": "Тарифы",
        "show_all": "Показать все тарифы",
        "hide_all": "Скрыть тарифы",
        "price_unknown": "Цена уточняется у организации",
        "free": "Бесплатно",
        "group": "Групповые",
        "individual": "Индивидуальные",
        "open_visit": "Свободное посещение",
        "sessions_per_week": "{count} раза в неделю",
        "sessions_per_month": "{count} раз в месяц",
        "minutes": "{count} минут",
    },
    "en": {
        "title": "Price and classes",
        "subtitle": "Format, frequency and payment options",
        "price_label": "Price",
        "from": "from",
        "suffix_den": "",
        "per_lesson_under": "per lesson",
        "per_visit_under": "per visit",
        "entry_ticket_under": "entry ticket",
        "per_month_under": "per month",
        "package_under": "per package",
        "per_lesson": "lesson",
        "per_visit": "visit",
        "entry_ticket": "entry ticket",
        "per_month": "month",
        "package": "package",
        "schedule_label": "Class schedule",
        "schedule_working_hours": "Working hours",
        "schedule_by_appointment": "Classes by appointment",
        "schedule_note": "Please check the class schedule with the organization",
        "tariffs": "Pricing plans",
        "show_all": "Show all pricing plans",
        "hide_all": "Hide pricing plans",
        "price_unknown": "Price is specified by organization",
        "free": "Free",
        "group": "Group",
        "individual": "Individual",
        "open_visit": "Open visit",
        "sessions_per_week": "{count} / week",
        "sessions_per_month": "{count} / month",
        "minutes": "{count} minutes",
    }
}


def build_compact_schedule_rows(place, lang="ru"):
    from catalog.services.place_schedule import serialize_place_schedule, schedule_signature
    days = serialize_place_schedule(place)
    
    has_structured = False
    if getattr(place, "pk", None) and getattr(place, "schedule_days", None):
        has_structured = place.schedule_days.exists()
    
    if not has_structured:
        txt = (place.schedule or "").strip()
        if txt:
            return [{"days": "", "time": txt, "is_closed": False}]
        return []
        
    az_day_labels = {
        "mon": "Bazar ertəsi",
        "tue": "Çərşənbə axşamı",
        "wed": "Çərşənbə",
        "thu": "Cümə axşamı",
        "fri": "Cümə",
        "sat": "Şənbə",
        "sun": "Bazar",
    }
    ru_day_labels = {
        "mon": "Понедельник",
        "tue": "Вторник",
        "wed": "Среда",
        "thu": "Четверг",
        "fri": "Пятница",
        "sat": "Суббота",
        "sun": "Воскресенье",
    }
    en_day_labels = {
        "mon": "Monday",
        "tue": "Tuesday",
        "wed": "Wednesday",
        "thu": "Thursday",
        "fri": "Friday",
        "sat": "Saturday",
        "sun": "Sunday",
    }
    
    day_labels = az_day_labels if lang == "az" else (en_day_labels if lang == "en" else ru_day_labels)
    
    groups = []
    current_group = []
    current_sig = None
    
    for day in days:
        sig = schedule_signature(day)
        if current_sig is None or sig == current_sig:
            current_group.append(day)
            current_sig = sig
        else:
            groups.append(current_group)
            current_group = [day]
            current_sig = sig
    if current_group:
        groups.append(current_group)
        
    rows = []
    for g in groups:
        first_day = g[0]["weekday"]
        last_day = g[-1]["weekday"]
        
        if len(g) == 1:
            days_str = day_labels.get(first_day)
        else:
            days_str = f"{day_labels.get(first_day)}–{day_labels.get(last_day)}"
            
        if g[0]["is_closed"]:
            time_str = "Bağlıdır" if lang == "az" else ("Closed" if lang == "en" else "Закрыто")
        elif g[0]["is_24_hours"]:
            time_str = "24h" if lang == "en" else ("24 saat" if lang == "az" else "круглосуточно")
        else:
            time_str = ", ".join(f"{interval['start']}–{interval['end']}" for interval in g[0]["intervals"])
            
        rows.append({"days": days_str, "time": time_str, "is_closed": g[0]["is_closed"]})
        
    return rows


def _format_starting_price(amount, payment_type, lang, currency=DEFAULT_CURRENCY):
    amount_str = str(int(amount)) if amount.is_integer() else f"{amount:.2f}"
    strings = LOCALIZED_STRINGS.get(lang, LOCALIZED_STRINGS["ru"])
    currency = currency or DEFAULT_CURRENCY
    if lang == "az":
        amount_display = f"{amount_str} {currency}-{strings['suffix_den']}"
    else:
        amount_display = f"{strings['from']} {amount_str} {currency}"
    # The headline is intentionally payment-neutral: the same place can offer
    # lessons, monthly subscriptions and packages. Exact terms live in tariffs.
    return {"full": amount_display, "amount": amount_display, "unit": ""}


def format_price_range(minimum, maximum, lang, currency=DEFAULT_CURRENCY):
    strings = LOCALIZED_STRINGS.get(lang, LOCALIZED_STRINGS["ru"])
    minimum_value = Decimal(str(minimum))
    maximum_value = Decimal(str(maximum))
    if minimum_value == maximum_value == 0:
        text = strings["free"]
    elif minimum_value == maximum_value:
        text = f"{format_price_amount(minimum_value)} {currency}"
    else:
        text = f"{format_price_amount(minimum_value)}–{format_price_amount(maximum_value)} {currency}"
    return {"full": text, "amount": text, "unit": ""}


def get_starting_price(place, public_plans, lang):
    # A complete admin range is explicit content and must not be overwritten
    # by a narrower set of detailed tariffs (for example 3–50 vs 3–15).
    tariff_range = active_pricing_plan_range(place.pricing_plans)
    stored_range = (
        Decimal(str(place.price_from)),
        Decimal(str(place.price_to)),
    ) if place.price_from is not None and place.price_to is not None else None
    if stored_range is not None and stored_range != tariff_range:
        minimum = place.price_from
        maximum = place.price_to
        return {
            "amount": float(minimum),
            "max_amount": float(maximum),
            "payment_type": None,
            "currency": DEFAULT_CURRENCY,
            "formatted": format_price_range(minimum, maximum, lang),
        }

    priced_plans = [plan for plan in public_plans if plan.get("price") not in (None, "")]
    if priced_plans:
        min_plan = min(priced_plans, key=lambda item: Decimal(str(item["price"])))
        max_plan = max(priced_plans, key=lambda item: Decimal(str(item["price"])))
        minimum = Decimal(str(min_plan["price"]))
        maximum = Decimal(str(max_plan["price"]))
        currency = min_plan.get("currency", DEFAULT_CURRENCY)
        return {
            "amount": float(minimum),
            "max_amount": float(maximum),
            "payment_type": min_plan.get("payment_type"),
            "currency": currency,
            "formatted": format_price_range(minimum, maximum, lang, currency),
        }

    # Manual range is the fallback source for cards without active tariffs.
    if place.price_from is not None or place.price_to is not None:
        minimum = place.price_from if place.price_from is not None else place.price_to
        maximum = place.price_to if place.price_to is not None else minimum
        return {
            "amount": float(minimum),
            "max_amount": float(maximum),
            "payment_type": "per_month",
            "currency": DEFAULT_CURRENCY,
            "formatted": format_price_range(minimum, maximum, lang),
        }

    if has_azn_pricing_plans(place.pricing_plans):
        price_unknown = LOCALIZED_STRINGS.get(lang, LOCALIZED_STRINGS["ru"])["price_unknown"]
        return {
            "amount": None,
            "max_amount": None,
            "payment_type": None,
            "currency": DEFAULT_CURRENCY,
            "formatted": {"full": price_unknown, "amount": price_unknown, "unit": ""},
        }

    legacy_prices = [
        (place.price_per_lesson, "per_lesson"),
        (place.price_per_month, "per_month"),
        (place.price_per_8_lessons, "package"),
    ]
    legacy_prices = [(price, kind) for price, kind in legacy_prices if price is not None]
    if legacy_prices:
        minimum, payment_type = min(legacy_prices, key=lambda item: item[0])
        maximum = max(price for price, _kind in legacy_prices)
        return {
            "amount": float(minimum),
            "max_amount": float(maximum),
            "payment_type": payment_type,
            "currency": DEFAULT_CURRENCY,
            "formatted": format_price_range(minimum, maximum, lang),
        }

    price_unknown = LOCALIZED_STRINGS.get(lang, LOCALIZED_STRINGS["ru"])["price_unknown"]
    return {
        "amount": None,
        "max_amount": None,
        "payment_type": None,
        "currency": "AZN",
        "formatted": {"full": price_unknown, "amount": price_unknown, "unit": ""},
    }


def build_pricing_summary(place, lang="ru"):
    lang = (lang or "ru").split("-")[0]
    if lang not in ["az", "ru", "en"]:
        lang = "ru"
        
    plans = public_pricing_plans(place.pricing_plans, lang)
    starting_price = get_starting_price(place, plans, lang)
    has_price = starting_price["amount"] is not None

    selected_plan = next(
        (
            plan
            for plan in plans
            if plan.get("price") not in (None, "")
            and float(plan["price"]) == starting_price["amount"]
            and plan.get("payment_type") == starting_price["payment_type"]
        ),
        None,
    )
    lesson_format = (
        selected_plan.get("lesson_format", "")
        if selected_plan
        else (place.lesson_format or (plans[0].get("lesson_format", "") if plans else ""))
    )
        
    format_label = ""
    if lesson_format:
        format_label = LOCALIZED_STRINGS[lang].get(lesson_format, "")
        
    lessons_per_week = selected_plan.get("sessions_per_week") if selected_plan else place.lessons_per_week
    lessons_per_month = selected_plan.get("sessions_per_month") if selected_plan else place.lessons_per_month
    if not selected_plan and not lessons_per_week and not lessons_per_month and plans:
        lessons_per_week = plans[0].get("sessions_per_week")
        lessons_per_month = plans[0].get("sessions_per_month")
        
    frequency_label = ""
    if lessons_per_week:
        if lang == "ru":
            count = int(lessons_per_week)
            times = "раз в неделю" if (count % 10 == 1 and count % 100 != 11) else "раза в неделю"
            frequency_label = f"{count} {times}"
        else:
            frequency_label = LOCALIZED_STRINGS[lang]["sessions_per_week"].format(count=lessons_per_week)
    elif lessons_per_month:
        frequency_label = LOCALIZED_STRINGS[lang]["sessions_per_month"].format(count=lessons_per_month)
        
    duration_label = ""
    if place.lesson_duration_minutes:
        duration_label = LOCALIZED_STRINGS[lang]["minutes"].format(count=place.lesson_duration_minutes)
        
    schedule_text = (place.schedule or "").lower()
    by_appt_markers = ["договор", "запис", "appoint", "razılaş", "rezer", "təyin"]
    is_by_appt = any(marker in schedule_text for marker in by_appt_markers)
    is_working_hours = place.category_id in ["PARK", "BEACH", "FUN", "CAMP", "WATERPARK", "ZOO"]
    
    if is_by_appt:
        schedule_type_label = LOCALIZED_STRINGS[lang]["schedule_by_appointment"]
    elif is_working_hours:
        schedule_type_label = LOCALIZED_STRINGS[lang]["schedule_working_hours"]
    else:
        schedule_type_label = LOCALIZED_STRINGS[lang]["schedule_label"]
        
    schedule_rows = build_compact_schedule_rows(place, lang)
    
    plans_processed = []
    for plan in plans:
        fully_matches = False
        if has_price and plan.get("price") is not None:
            plan_price = float(plan.get("price"))
            if plan_price == starting_price["amount"] and plan.get("payment_type") == starting_price["payment_type"]:
                # Check format/sessions match parameter chips if present
                fully_matches = True
                
        details_list = []
        if plan.get("package_sessions"):
            cnt = plan["package_sessions"]
            if lang == "ru":
                if cnt % 10 == 1 and cnt % 100 != 11:
                    unit_sess = "занятие"
                elif cnt % 10 in [2, 3, 4] and cnt % 100 not in [12, 13, 14]:
                    unit_sess = "занятия"
                else:
                    unit_sess = "занятий"
                details_list.append(f"{cnt} {unit_sess}")
            elif lang == "az":
                details_list.append(f"{cnt} dərs")
            else:
                details_list.append(f"{cnt} sessions" if cnt > 1 else f"{cnt} session")
        
        sess_w = plan.get("sessions_per_week")
        sess_m = plan.get("sessions_per_month")
        if sess_w:
            if lang == "ru":
                count = int(sess_w)
                times = "раз в неделю" if (count % 10 == 1 and count % 100 != 11) else "раза в неделю"
                details_list.append(f"{count} {times}")
            else:
                details_list.append(LOCALIZED_STRINGS[lang]["sessions_per_week"].format(count=sess_w))
        elif sess_m:
            details_list.append(LOCALIZED_STRINGS[lang]["sessions_per_month"].format(count=sess_m))
            
        details_str = " · ".join(details_list)
        
        plan_price_val = plan.get("price")
        plan_price_str = ""
        if plan_price_val is not None:
            price_float = float(plan_price_val)
            price_display = str(int(price_float)) if price_float.is_integer() else f"{price_float:.2f}"
            unit = LOCALIZED_STRINGS[lang][plan.get("payment_type")]
            currency = plan.get("currency") or DEFAULT_CURRENCY
            plan_price_str = f"{price_display} {currency} / {unit}"
            
        whatsapp_url = ""
        if place.phone1:
            clean_phone = place.phone1.replace(" ", "").replace("+", "")
            clean_phone = "".join(c for c in clean_phone if c.isdigit())
            if clean_phone.startswith("0") and not clean_phone.startswith("994"):
                clean_phone = "994" + clean_phone[1:]
            
            title_str = plan.get("title") or ""
            place_name = (
                (place.name_az or place.name or "").strip()
                if lang == "az"
                else (
                    (place.name_en or place.name or "").strip()
                    if lang == "en"
                    else (place.name_ru or place.name or "").strip()
                )
            )
            
            if lang == "az":
                msg = f"Salam! '{place_name}' təşkilatındakı '{title_str}' tarifi ilə maraqlanıram. Ətraflı məlumat verə bilərsiniz?"
            elif lang == "en":
                msg = f"Hello! I am interested in the '{title_str}' tariff at '{place_name}'. Could you please provide more details?"
            else:
                msg = f"Здравствуйте! Меня интересует тариф «{title_str}» в «{place_name}». Подскажите, пожалуйста, подробнее."
            
            import urllib.parse
            whatsapp_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

        plans_processed.append({
            "title": plan.get("title"),
            "details": details_str,
            "price_str": plan_price_str,
            "fully_matches": fully_matches,
            "lesson_format": plan.get("lesson_format"),
            "payment_type": plan.get("payment_type"),
            "whatsapp_url": whatsapp_url
        })
        
    return {
        "has_price": has_price,
        "amount": starting_price["amount"],
        "max_amount": starting_price["max_amount"],
        "payment_type": starting_price["payment_type"],
        "currency": starting_price["currency"],
        "formatted_price": starting_price["formatted"]["full"],
        "formatted_price_amount": starting_price["formatted"]["amount"],
        "formatted_price_unit": starting_price["formatted"]["unit"],
        "plans": plans_processed,
        "schedule_rows": schedule_rows,
        "schedule_type_label": schedule_type_label,
        "schedule_note": LOCALIZED_STRINGS[lang]["schedule_note"],
        "lesson_format": lesson_format,
        "format_label": format_label,
        "frequency": frequency_label,
        "duration": duration_label,
        "strings": LOCALIZED_STRINGS[lang],
    }
