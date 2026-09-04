from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext as _, get_language


MAX_PRICING_PLANS = 12
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


def _compat_to_canonical(raw):
    raw = dict(raw)
    for language in ("az", "ru", "en"):
        title_key = f"title_{language}"
        name_key = f"name_{language}"
        if not raw.get(title_key) and raw.get(name_key):
            raw[title_key] = raw[name_key]
    if not raw.get("lesson_format") and raw.get("format"):
        raw["lesson_format"] = raw["format"]
    payment_type = str(raw.get("payment_type") or raw.get("payment") or "").strip()
    if raw.get("package_sessions") and not raw.get("quantity"):
        raw["quantity"] = raw["package_sessions"]
        raw["quantity_unit"] = "lesson"
    mappings = {
        "per_lesson": {"product_type": "lesson", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "lesson"},
        "per_month": {"product_type": "membership", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1},
        "package": {"product_type": "lesson", "billing_mode": "one_time", "quantity": raw.get("package_sessions"), "quantity_unit": "lesson"},
        "per_visit": {"product_type": "visit", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "visit"},
        "entry_ticket": {"product_type": "admission", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "entry"},
    }
    for key, val in mappings.get(payment_type, {}).items():
        raw.setdefault(key, val)
    if "price_kind" not in raw:
        raw["price_kind"] = "free" if str(raw.get("price", "")).strip() in {"0", "0.0", "0.00"} else "exact"

    product_type = raw.get("product_type") or raw.get("editor_kind") or ""
    quantity = raw.get("quantity")
    quantity_unit = str(raw.get("quantity_unit") or "").strip()
    DEFAULT_UNITS = {
        "admission": "entry", "visit": "visit", "lesson": "lesson",
        "membership": "lesson", "course": "course", "camp": "camp_shift",
        "event": "event", "excursion": "event", "tour": "event", "rental": "hour",
    }
    if quantity not in (None, "") and not quantity_unit:
        raw["quantity_unit"] = DEFAULT_UNITS.get(product_type, "entry" if product_type == "admission" else "lesson")

    return raw


def _model_to_compat(plan):
    if plan.product_type == "membership" and plan.billing_mode == "recurring" and plan.billing_interval == "month" and plan.billing_interval_count == 1:
        return "per_month"
    if plan.product_type == "lesson" and plan.quantity_unit == "lesson" and (plan.quantity or 0) > 1:
        return "package"
    if plan.product_type == "lesson":
        return "per_lesson"
    if plan.product_type == "admission":
        return "entry_ticket"
    if plan.product_type == "visit":
        return "per_visit"
    return ""


PRICING_STORAGE_FIELDS = (
    "product_type", "lesson_format", "charge_role", "billing_mode", "billing_interval",
    "billing_interval_count", "billing_cycles", "price_kind", "price", "price_min", "price_max",
    "currency", "quantity", "quantity_unit", "sessions_per_week", "sessions_per_month", "is_unlimited",
    "validity_interval", "validity_interval_count", "valid_from", "valid_until", "audience_type",
    "age_from", "age_to", "min_people", "max_people", "day_type", "title_az", "title_ru", "title_en",
    "conditions_az", "conditions_ru", "conditions_en", "is_required", "is_active", "sort_order",
    "verified_at", "source_url",
)


def serialize_pricing_plan(plan, language=None):
    data = {"id": plan.pk}
    for field in PRICING_STORAGE_FIELDS:
        value = getattr(plan, field)
        if isinstance(value, Decimal):
            value = format(value, ".2f")
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        data[field] = value
    payment_type = _model_to_compat(plan)
    if payment_type:
        data["payment_type"] = payment_type
    if payment_type == "package":
        data["package_sessions"] = plan.quantity
    if language:
        data["title"] = plan.title_i18n(language)
        data["conditions"] = plan.conditions_i18n(language)
    return data


def serialize_pricing_plans(plans, language=None):
    return [serialize_pricing_plan(plan, language) for plan in plans]


def pricing_audit_summary(place):
    """Compact, stable audit value; the full tariff state remains in its table."""
    plans = list(place.pricing_plan_records.order_by("sort_order", "id"))
    if not plans:
        return "0 tariffs"
    parts = []
    for plan in plans[:5]:
        if plan.price_kind in {"exact", "free"}:
            amount = plan.price
        elif plan.price_kind in {"from", "range"}:
            amount = plan.price_min
        else:
            amount = None
        price = plan.price_kind if amount is None else f"{amount:g} {plan.currency}"
        state = "active" if plan.is_active else "inactive"
        parts.append(f"#{plan.pk or '-'} {plan.product_type}/{plan.charge_role} {price} {state}")
    suffix = f"; +{len(plans) - 5}" if len(plans) > 5 else ""
    return f"{len(plans)} tariffs: " + "; ".join(parts) + suffix


def normalize_pricing_plans(value, *, strict=True, allow_verified=False):
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
        raise ValidationError(_("Можно добавить не более 12 тарифов."))

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
                "name_az", "name_ru", "name_en", "format", "payment",
                "product_type", "price_kind", "price_min", "price_max", "billing_mode",
            }
            if not any(str(raw.get(key) or "").strip() for key in content_keys):
                if strict:
                    raise ValidationError({"product_type": _("Укажите тип тарифа.")})
                continue
            if {"name", "frequency"}.intersection(raw) and not {
                "product_type", "price_kind", "lesson_format", "payment_type", "title_az", "title_ru", "title_en"
            }.intersection(raw):
                legacy = _legacy_plan(raw, index)
                if legacy["price"]:
                    normalized.append(legacy)
                continue

            raw = _compat_to_canonical(raw)
            from catalog.models import PricingPlan
            values = {field: raw.get(field) for field in PRICING_STORAGE_FIELDS if field in raw}
            values.setdefault("charge_role", "primary")
            values.setdefault("billing_mode", "one_time")
            values.setdefault("price_kind", "exact")
            values.setdefault("currency", DEFAULT_CURRENCY)
            values.setdefault("audience_type", "all")
            values.setdefault("day_type", "any")
            values.setdefault("is_active", True)
            values.setdefault("sort_order", index)
            if not allow_verified:
                values.pop("verified_at", None)
            for price_field in ("price", "price_min", "price_max"):
                if values.get(price_field) not in (None, ""):
                    values[price_field] = Decimal(str(values[price_field]).replace(",", "."))
                else:
                    values[price_field] = None
            for int_field in ("billing_interval_count", "billing_cycles", "quantity", "sessions_per_week", "sessions_per_month", "validity_interval_count", "age_from", "age_to", "min_people", "max_people", "sort_order"):
                if values.get(int_field) not in (None, ""):
                    values[int_field] = int(values[int_field])
                elif int_field in values:
                    values[int_field] = None
            candidate = PricingPlan(**values)
            candidate.full_clean(exclude=("place",))
            clean = {}
            for field in PRICING_STORAGE_FIELDS:
                # Owners may edit tariff contents, but an omitted verification
                # marker must leave the staff-owned value untouched.
                if field == "verified_at" and not allow_verified:
                    continue
                val = getattr(candidate, field)
                if isinstance(val, Decimal):
                    val = format(val, ".2f")
                elif hasattr(val, "isoformat"):
                    val = val.isoformat()
                clean[field] = val
            payment_type = _model_to_compat(candidate)
            if payment_type:
                clean["payment_type"] = payment_type
            if payment_type == "package":
                clean["package_sessions"] = candidate.quantity
            if raw.get("id") not in (None, ""):
                clean["id"] = int(raw["id"])
            normalized.append(clean)
        except ValidationError as exc:
            if strict:
                if getattr(exc, "error_dict", None):
                    field_name = next(iter(exc.error_dict))
                    field_errors = exc.error_dict[field_name]
                    detail = field_errors[0].message if field_errors else str(exc)
                    message = _("поле %(field)s: %(detail)s") % {"field": field_name, "detail": detail}
                else:
                    message = exc.messages[0] if getattr(exc, "messages", None) else str(exc)
                raise ValidationError(
                    _("Тариф %(number)s: %(error)s"),
                    params={"number": index + 1, "error": message},
                )
            continue
        except (InvalidOperation, TypeError, ValueError) as exc:
            if strict:
                raise ValidationError(
                    _("Тариф %(number)s: неверный тип или формат значения (%(error)s)."),
                    params={"number": index + 1, "error": str(exc)},
                )
            continue
    return normalized


@transaction.atomic
def replace_place_pricing_plans(place, value, *, allow_verified=False):
    from catalog.models import PricingPlan
    plans = normalize_pricing_plans(value, allow_verified=allow_verified)
    existing = {item.pk: item for item in PricingPlan.objects.select_for_update().filter(place=place)}
    def fingerprint(item):
        getter = item.get if isinstance(item, dict) else lambda key: getattr(item, key)
        return tuple(str(getter(key) or "") for key in (
            "product_type", "charge_role", "billing_mode", "billing_interval",
            "billing_interval_count", "price_kind", "price", "price_min", "price_max",
            "currency", "quantity", "quantity_unit", "audience_type", "age_from", "age_to",
        ))
    by_fingerprint = {}
    for item in existing.values():
        by_fingerprint.setdefault(fingerprint(item), []).append(item)
    keep = set()
    for index, raw in enumerate(plans):
        plan_id = raw.pop("id", None)
        instance = existing.get(plan_id) if plan_id else None
        if instance is None:
            candidates = by_fingerprint.get(fingerprint(raw), [])
            instance = next((candidate for candidate in candidates if candidate.pk not in keep), None)
        if instance is None:
            instance = PricingPlan(place=place)
        elif instance.place_id != place.pk:
            raise ValidationError(_("Тариф не принадлежит этой карточке."))
        for field in PRICING_STORAGE_FIELDS:
            if field in raw:
                setattr(instance, field, raw[field])
        instance.sort_order = index
        instance.full_clean()
        instance._skip_legacy_sync = True
        instance.save()
        keep.add(instance.pk)
    for stale in PricingPlan.objects.filter(place=place).exclude(pk__in=keep):
        stale._skip_legacy_sync = True
        stale.delete()
    sync_legacy_price_fields(place.pk)
    return list(PricingPlan.objects.filter(place=place))


def _plan_bounds(plan):
    if plan.price_kind in {"exact", "free"} and plan.price is not None:
        return plan.price, plan.price
    if plan.price_kind == "from" and plan.price_min is not None:
        return plan.price_min, plan.price_min
    if plan.price_kind == "range" and plan.price_min is not None and plan.price_max is not None:
        return plan.price_min, plan.price_max
    return None


def sync_legacy_price_fields(place_id):
    from catalog.models import Place, PricingPlan
    plans = list(PricingPlan.objects.filter(place_id=place_id, is_active=True, charge_role="primary", currency="AZN"))
    bounds = [_plan_bounds(plan) for plan in plans]
    bounds = [item for item in bounds if item]
    values = {
        "price_from": min((item[0] for item in bounds), default=None),
        "price_to": max((item[1] for item in bounds), default=None),
        "price_per_lesson": None, "price_per_month": None, "price_per_8_lessons": None,
    }
    for plan in plans:
        bound = _plan_bounds(plan)
        if not bound:
            continue
        amount = bound[0]
        if plan.product_type == "lesson" and plan.billing_mode == "one_time" and plan.quantity == 1 and plan.quantity_unit == "lesson":
            values["price_per_lesson"] = min(filter(lambda x: x is not None, (values["price_per_lesson"], amount)), default=amount)
        if plan.product_type == "membership" and plan.billing_mode == "recurring" and plan.billing_interval == "month" and plan.billing_interval_count == 1:
            values["price_per_month"] = min(filter(lambda x: x is not None, (values["price_per_month"], amount)), default=amount)
        if plan.product_type == "lesson" and plan.billing_mode == "one_time" and plan.quantity == 8 and plan.quantity_unit == "lesson":
            values["price_per_8_lessons"] = min(filter(lambda x: x is not None, (values["price_per_8_lessons"], amount)), default=amount)
    Place.objects.filter(pk=place_id).update(**values)


def public_pricing_plans(value, language=None):
    """Safely normalize plans for display; invalid entries are hidden."""
    try:
        if hasattr(value, "all"):
            return serialize_pricing_plans(value.filter(is_active=True).order_by("sort_order", "id"), language)
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
        conditions = (
            plan.get(f"conditions_{lang}") or plan.get("conditions_az")
            or plan.get("conditions_ru") or plan.get("conditions_en") or ""
        )
        result.append(
            {
                **plan,
                "title": title,
                "format_label": format_label,
                "payment_label": payment_label,
                "conditions": conditions,
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
        if not plan.get("is_active", True) or plan.get("charge_role", "primary") != "primary":
            continue
        # Place.price_from/price_to are AZN fields. Other currencies stay in
        # their tariff rows and must never overwrite the card's AZN range.
        if (plan.get("currency") or DEFAULT_CURRENCY).upper() != DEFAULT_CURRENCY:
            continue
        try:
            if plan.get("price_kind") in {"exact", "free"}:
                low = high = Decimal(str(plan["price"]))
            elif plan.get("price_kind") == "from":
                low = high = Decimal(str(plan["price_min"]))
            elif plan.get("price_kind") == "range":
                low, high = Decimal(str(plan["price_min"])), Decimal(str(plan["price_max"]))
            else:
                continue
            prices.extend((low, high))
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


def build_public_price_summary(place, language="ru"):
    lang = (language or get_language() or "ru").split("-")[0]
    labels = {
        "ru": {
            "free": "Бесплатно",
            "free_entry": "Вход бесплатный",
            "events": "Цена зависит от мероприятия",
            "from": "От {value} ₼",
            "unknown": "Цена уточняется",
        },
        "az": {
            "free": "Pulsuz",
            "free_entry": "Giriş pulsuzdur",
            "events": "Qiymət tədbirdən asılıdır",
            "from": "{value} ₼-dən",
            "unknown": "Qiymət dəqiqləşdirilir",
        },
        "en": {
            "free": "Free",
            "free_entry": "Free admission",
            "events": "Price depends on event",
            "from": "From {value} ₼",
            "unknown": "Price on request",
        },
    }.get(lang, None)
    if labels is None:
        lang, labels = "ru", {
            "free": "Бесплатно",
            "free_entry": "Вход бесплатный",
            "events": "Цена зависит от мероприятия",
            "from": "От {value} ₼",
            "unknown": "Цена уточняется",
        }
    custom = (
        getattr(place, f"custom_price_badge_{lang}", "")
        or getattr(place, "custom_price_badge_ru", "")
        or getattr(place, "custom_price_badge_az", "")
    )
    custom = (custom or "").strip()
    if custom:
        return {"kind": "custom", "min_price": None, "max_price": None, "currency": "AZN", "label": custom, "source": "custom_override"}

    price_mode = getattr(place, "price_mode", "tariffs") or "tariffs"
    if price_mode == "free":
        return {"kind": "free", "min_price": Decimal("0"), "max_price": Decimal("0"), "currency": "AZN", "label": labels["free"], "source": "price_mode"}
    if price_mode == "free_entry_paid_services":
        return {"kind": "free_entry", "min_price": Decimal("0"), "max_price": None, "currency": "AZN", "label": labels["free_entry"], "source": "price_mode"}
    if price_mode == "events":
        return {"kind": "events", "min_price": None, "max_price": None, "currency": "AZN", "label": labels["events"], "source": "price_mode"}
    active_primary = []
    if getattr(place, "pk", None):
        active_primary = [
            plan for plan in place.pricing_plan_records.all()
            if plan.is_active and plan.charge_role == "primary"
        ]
    records = [plan for plan in active_primary if plan.currency == "AZN"]
    if records:
        free = [plan for plan in records if plan.price_kind == "free"]
        on_request = [plan for plan in records if plan.price_kind == "on_request"]
        paid = [(plan, _plan_bounds(plan)) for plan in records if plan.price_kind not in {"free", "on_request"}]
        paid = [(plan, bounds) for plan, bounds in paid if bounds and bounds[0] > 0]
        if free and not paid and not on_request:
            return {"kind": "free", "min_price": Decimal("0"), "max_price": Decimal("0"), "currency": "AZN", "label": labels["free"], "source": "pricing_plans"}
        if free and paid:
            maximum = max(item[1][1] for item in paid)
            minimum = Decimal("0")
            label = f"{format_price_amount(minimum)}–{format_price_amount(maximum)} ₼"
            return {"kind": "mixed", "min_price": minimum, "max_price": maximum, "currency": "AZN", "label": label, "source": "pricing_plans"}
        if paid:
            minimum = min(item[1][0] for item in paid)
            maximum = max(item[1][1] for item in paid)
            if minimum != maximum:
                label = f"{format_price_amount(minimum)}–{format_price_amount(maximum)} ₼"
                kind = "range"
            elif any(plan.price_kind == "from" for plan, _bounds in paid):
                label = labels["from"].format(value=format_price_amount(minimum))
                kind = "from"
            else:
                label = f"{format_price_amount(minimum)} ₼"
                kind = "exact"
            return {"kind": kind, "min_price": minimum, "max_price": maximum, "currency": "AZN", "label": label, "source": "pricing_plans"}
        return {"kind": "on_request", "min_price": None, "max_price": None, "currency": "AZN", "label": labels["unknown"], "source": "pricing_plans"}

    # Any active primary tariff ends the transition fallback. A foreign-currency
    # plan is still real pricing, but it cannot be folded into the AZN headline.
    if active_primary:
        return {"kind": "on_request", "min_price": None, "max_price": None, "currency": "AZN", "label": labels["unknown"], "source": "pricing_plans"}

    legacy_values = [value for value in (place.price_from, place.price_to) if value is not None]
    if legacy_values:
        minimum, maximum = min(legacy_values), max(legacy_values)
        if minimum == maximum == 0:
            kind, label = "free", labels["free"]
        elif minimum != maximum:
            kind, label = "range", f"{format_price_amount(minimum)}–{format_price_amount(maximum)} ₼"
        else:
            kind, label = "from", labels["from"].format(value=format_price_amount(minimum))
        return {"kind": kind, "min_price": minimum, "max_price": maximum, "currency": "AZN", "label": label, "source": "legacy_fallback"}
    return {"kind": "on_request", "min_price": None, "max_price": None, "currency": "AZN", "label": labels["unknown"], "source": "none"}


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
    from catalog.services.place_schedule import build_public_schedule_rows

    return build_public_schedule_rows(place, lang)


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
    canonical = build_public_price_summary(place, lang)
    if canonical["source"] in {"pricing_plans", "legacy_fallback", "price_mode"}:
        payment_type = None
        if canonical["source"] == "pricing_plans" and canonical["min_price"] is not None:
            matching = [
                plan for plan in place.pricing_plan_records.all()
                if plan.is_active and plan.charge_role == "primary" and plan.currency == "AZN"
                and _plan_bounds(plan) and _plan_bounds(plan)[0] == canonical["min_price"]
            ]
            if matching:
                payment_type = _model_to_compat(matching[0]) or None
        return {
            "amount": float(canonical["min_price"]) if canonical["min_price"] is not None else None,
            "max_amount": float(canonical["max_price"]) if canonical["max_price"] is not None else None,
            "payment_type": payment_type,
            "currency": canonical["currency"],
            "formatted": {"full": canonical["label"], "amount": canonical["label"], "unit": ""},
        }
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
        elif lang == "az":
            frequency_label = f"həftədə {lessons_per_week} dəfə"
        else:
            count = int(lessons_per_week)
            times = "time / week" if count == 1 else "times / week"
            frequency_label = f"{count} {times}"
    elif lessons_per_month:
        if lang == "ru":
            count = int(lessons_per_month)
            times = "раз в месяц" if (count % 10 == 1 and count % 100 != 11) else "раза в месяц"
            frequency_label = f"{count} {times}"
        elif lang == "az":
            frequency_label = f"ayda {lessons_per_month} dəfə"
        else:
            count = int(lessons_per_month)
            times = "time / month" if count == 1 else "times / month"
            frequency_label = f"{count} {times}"

    duration_label = ""
    if place.lesson_duration_minutes:
        duration_label = LOCALIZED_STRINGS[lang]["minutes"].format(count=place.lesson_duration_minutes)

    from catalog.services.place_schedule import (
        build_open_status,
        build_public_schedule_week,
        schedule_mode_label,
        schedule_mode_note,
    )

    schedule_mode = getattr(place, "schedule_mode", "regular") or "regular"
    strings = dict(LOCALIZED_STRINGS[lang])
    if schedule_mode == "events":
        event_heading = {
            "az": ("Qiymət və tədbirlər", "Biletlər və yaxın tədbirlərin vaxtı"),
            "ru": ("Цена и мероприятия", "Билеты и даты ближайших событий"),
            "en": ("Price and events", "Tickets and upcoming event dates"),
        }[lang]
        strings["title"], strings["subtitle"] = event_heading
    is_working_hours = place.category_id in ["PARK", "BEACH", "FUN", "CAMP", "WATERPARK", "ZOO"]

    if schedule_mode != "regular":
        schedule_type_label = schedule_mode_label(place, lang)
    elif is_working_hours:
        schedule_type_label = LOCALIZED_STRINGS[lang]["schedule_working_hours"]
    else:
        schedule_type_label = LOCALIZED_STRINGS[lang]["schedule_label"]

    schedule_rows = build_compact_schedule_rows(place, lang)
    schedule_week = build_public_schedule_week(place, lang)
    open_status = build_open_status(place, lang)
    public_schedule_note = schedule_mode_note(place, lang) or LOCALIZED_STRINGS[lang]["schedule_note"]

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
            cnt = int(plan["package_sessions"])
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
            elif lang == "az":
                details_list.append(f"həftədə {sess_w} dəfə")
            else:
                count = int(sess_w)
                times = "time / week" if count == 1 else "times / week"
                details_list.append(f"{count} {times}")
        elif sess_m:
            if lang == "ru":
                count = int(sess_m)
                times = "раз в месяц" if (count % 10 == 1 and count % 100 != 11) else "раза в месяц"
                details_list.append(f"{count} {times}")
            elif lang == "az":
                details_list.append(f"ayda {sess_m} dəfə")
            else:
                count = int(sess_m)
                times = "time / month" if count == 1 else "times / month"
                details_list.append(f"{count} {times}")

        details_str = " · ".join(details_list)

        plan_price_val = plan.get("price")
        plan_price_str = ""
        currency = plan.get("currency") or DEFAULT_CURRENCY
        if plan.get("price_kind") == "free":
            plan_price_str = LOCALIZED_STRINGS[lang]["free"]
        elif plan.get("price_kind") == "on_request":
            plan_price_str = LOCALIZED_STRINGS[lang]["price_unknown"]
        elif plan.get("price_kind") == "from" and plan.get("price_min") is not None:
            plan_price_str = LOCALIZED_STRINGS[lang]["from"] + " " + format_price_amount(plan["price_min"]) + " " + currency
        elif plan.get("price_kind") == "range" and plan.get("price_min") is not None and plan.get("price_max") is not None:
            plan_price_str = f"{format_price_amount(plan['price_min'])}–{format_price_amount(plan['price_max'])} {currency}"
        elif plan_price_val is not None:
            price_float = float(plan_price_val)
            price_display = str(int(price_float)) if price_float.is_integer() else f"{price_float:.2f}"
            unit = LOCALIZED_STRINGS[lang].get(plan.get("payment_type"), "")
            plan_price_str = f"{price_display} {currency}" + (f" / {unit}" if unit else "")

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
                msg = f"Salam! «{place_name}» üzrə «{title_str}» tarifi ilə maraqlanıram. Zəhmət olmasa, ətraflı məlumat verə bilərsiniz?"
            elif lang == "en":
                msg = f"Hello! I am interested in the '{title_str}' plan at '{place_name}'. Could you please provide more details?"
            else:
                msg = f"Здравствуйте! Меня интересует тариф «{title_str}» в «{place_name}». Подскажите, пожалуйста, подробнее."

            import urllib.parse
            whatsapp_url = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

        group_keys = {
            "admission": "admission", "visit": "visits", "lesson": "lessons",
            "membership": "memberships", "course": "courses", "camp": "camps",
            "event": "events", "excursion": "events", "tour": "events", "rental": "rental",
            "addon": "additional", "registration_fee": "additional", "deposit": "additional",
        }
        group_labels = {
            "ru": {"admission": "Входные билеты", "visits": "Разовые посещения", "lessons": "Занятия и пакеты", "memberships": "Абонементы", "courses": "Курсы", "camps": "Лагеря", "events": "События и экскурсии", "rental": "Аренда", "additional": "Дополнительные платежи"},
            "az": {"admission": "Giriş biletləri", "visits": "Birdəfəlik ziyarətlər", "lessons": "Dərslər və paketlər", "memberships": "Abunəliklər", "courses": "Kurslar", "camps": "Düşərgələr", "events": "Tədbirlər və ekskursiyalar", "rental": "İcarə", "additional": "Əlavə ödənişlər"},
            "en": {"admission": "Admission", "visits": "Single visits", "lessons": "Lessons and packages", "memberships": "Memberships", "courses": "Courses", "camps": "Camps", "events": "Events and excursions", "rental": "Rental", "additional": "Additional payments"},
        }
        group_key = group_keys.get(plan.get("product_type"), "additional")
        plans_processed.append({
            "title": plan.get("title"),
            "details": plan.get("conditions") or details_str,
            "price_str": plan_price_str,
            "fully_matches": fully_matches,
            "lesson_format": plan.get("lesson_format"),
            "payment_type": plan.get("payment_type"),
            "whatsapp_url": whatsapp_url,
            "group_key": group_key,
            "group_label": group_labels[lang][group_key],
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
        "schedule_week": schedule_week,
        "open_status": open_status,
        "schedule_type_label": schedule_type_label,
        "schedule_note": public_schedule_note,
        "lesson_format": lesson_format,
        "format_label": format_label,
        "frequency": frequency_label,
        "duration": duration_label,
        "strings": strings,
    }
