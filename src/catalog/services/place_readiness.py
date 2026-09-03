"""Single source of truth for "can this place card be published?".

Before this module the answer was computed in five independent places: the
admin form checklist, the admin sidebar summary, ``place_quality_check``, the
catalog visibility filter and a client-side ``CHECKLIST_CONFIG`` in
``kidsmap_place_form.js``. They disagreed, which is how a card could show
"100% filled" and still be refused at publish time.

Everything that answers the readiness question now goes through
:func:`evaluate_place_readiness`. It takes a snapshot (built either from a
saved ``Place`` or from unsaved admin form data) so the same rules apply to a
stored card and to the form the editor is looking at right now.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Callable

from django.utils.translation import gettext_lazy as _


# Quality target for a description. It blocks nothing: neither publication nor
# catalog visibility depend on it, so a card that passes every requirement here
# is reachable on the site.
MIN_DESCRIPTION_LENGTH = 120

# Form sections of the admin change form, used as scroll targets.
SECTION_BASICS = "basics"
SECTION_PRICING = "pricing"
SECTION_LOCATION = "location"
SECTION_MEDIA = "media"


@dataclass(frozen=True)
class PlaceReadinessData:
    """Normalized card values the readiness rules operate on."""

    name_az: str = ""
    name_texts: tuple[str, ...] = ()
    description_az: str = ""
    description_texts: tuple[str, ...] = ()
    category_code: str = ""
    subcategory_id: int | None = None
    subcategory_category_code: str = ""
    district: str = ""
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    age_from: int | None = None
    age_to: int | None = None
    age_open_ended: bool = False
    # Only tariffs (including a "free" one) count as a price. The legacy
    # ``price_*`` columns are kept separately: they still drive the public
    # catalog for old cards, but they no longer satisfy this requirement.
    has_priced_plan: bool = False
    has_legacy_price: bool = False
    has_custom_price_badge: bool = False
    phone1: str = ""
    schedule_mode: str = "regular"
    schedule_has_structured: bool = False
    schedule_text: str = ""
    has_main_photo: bool = False
    has_cover_photo_only: bool = False


@dataclass(frozen=True)
class ReadinessRequirement:
    """One of the twelve things a card needs before it can go public."""

    code: str
    label: str
    section: str
    field: str
    anchor: str
    check: Callable[[PlaceReadinessData], tuple[str, str] | None]
    # Mirrored by the browser so live progress uses the same rule.
    client_check: str = ""


@dataclass(frozen=True)
class ReadinessIssue:
    code: str
    section: str
    field: str
    anchor: str
    label: str
    message: str
    quality_code: str
    blocking: bool = True


@dataclass(frozen=True)
class ReadinessItem:
    requirement: ReadinessRequirement
    issue: ReadinessIssue | None = None

    @property
    def code(self) -> str:
        return self.requirement.code

    @property
    def label(self) -> str:
        return str(self.requirement.label)

    @property
    def is_complete(self) -> bool:
        return self.issue is None


@dataclass(frozen=True)
class PlaceReadiness:
    items: tuple[ReadinessItem, ...] = dataclass_field(default_factory=tuple)
    #: Non-blocking quality hints. They never change ``percentage`` or ``is_ready``.
    advice: tuple[ReadinessIssue, ...] = dataclass_field(default_factory=tuple)

    @property
    def issues(self) -> tuple[ReadinessIssue, ...]:
        return tuple(item.issue for item in self.items if item.issue is not None)

    @property
    def required_count(self) -> int:
        return len(self.items)

    @property
    def completed_count(self) -> int:
        return sum(1 for item in self.items if item.is_complete)

    @property
    def percentage(self) -> int:
        if not self.items:
            return 0
        return round(self.completed_count / self.required_count * 100)

    @property
    def is_ready(self) -> bool:
        return not self.issues

    @property
    def quality_codes(self) -> tuple[str, ...]:
        return tuple(issue.quality_code for issue in self.issues)


def _text(value) -> str:
    return (value or "").strip() if isinstance(value, str) else ""


def _contains_test_content(value: str) -> bool:
    from catalog.services.content_quality import contains_test_content

    return contains_test_content(value)


def _check_name(data: PlaceReadinessData):
    if not _text(data.name_az):
        return ("missing_name", _("Укажите название на азербайджанском."))
    if any(_contains_test_content(value) for value in data.name_texts):
        return ("test_content", _("Уберите из названия тестовый текст вроде «test» или «lorem»."))
    return None


def _check_description(data: PlaceReadinessData):
    """Publication needs a real description, not a long one.

    ``MIN_DESCRIPTION_LENGTH`` is a quality target, not a model constraint, so
    a short description is reported as advice instead of blocking the card.
    """

    description = _text(data.description_az)
    if not description:
        return ("missing_description", _("Добавьте описание на азербайджанском."))
    if any(_contains_test_content(value) for value in data.description_texts):
        return ("test_content", _("Уберите из описания тестовый текст вроде «test» или «lorem»."))
    return None


def _check_category(data: PlaceReadinessData):
    if not _text(data.category_code):
        return ("missing_category", _("Выберите категорию места."))
    return None


def _check_subcategory(data: PlaceReadinessData):
    if data.subcategory_id is None:
        return ("missing_subcategory", _("Выберите подкатегорию выбранной категории."))
    if (
        data.subcategory_category_code
        and data.category_code
        and data.subcategory_category_code != data.category_code
    ):
        return (
            "subcategory_mismatch",
            _("Подкатегория относится к другой категории — выберите подходящую."),
        )
    return None


def _check_region(data: PlaceReadinessData):
    if not _text(data.district):
        return ("missing_region", _("Выберите город или регион, а для Баку — район."))
    return None


def _check_address(data: PlaceReadinessData):
    address = _text(data.address)
    if not address:
        return ("missing_address", _("Укажите адрес: улицу и дом или понятный ориентир."))
    if _contains_test_content(address):
        return ("test_content", _("Уберите из адреса тестовый текст вроде «test» или «lorem»."))
    return None


def _check_coordinates(data: PlaceReadinessData):
    if data.lat is None or data.lng is None:
        return (
            "missing_coordinates",
            _("Поставьте точку на карте или обновите координаты по адресу. Адрес координаты не заменяет."),
        )
    if not (-90 <= data.lat <= 90) or not (-180 <= data.lng <= 180):
        return ("invalid_coordinates", _("Координаты вне допустимого диапазона — поставьте точку на карте заново."))
    return None


def _check_age(data: PlaceReadinessData):
    if data.age_from is None:
        return ("missing_age", _("Укажите возраст «от»."))
    if data.age_to is None and not data.age_open_ended:
        return (
            "missing_age_to",
            _("Укажите возраст «до» или включите «Без верхней границы возраста»."),
        )
    if data.age_to is not None and data.age_to < data.age_from:
        return ("invalid_age_range", _("Возраст «до» не может быть меньше возраста «от»."))
    return None


def _check_price(data: PlaceReadinessData):
    if data.has_priced_plan or data.has_custom_price_badge:
        return None
    if data.has_legacy_price:
        # The old scalar price still shows on the site, but the card cannot be
        # re-published until it is migrated into a tariff.
        return (
            "legacy_price_not_migrated",
            _("Перенесите существующую цену в тарифы или укажите, что место бесплатное."),
        )
    return (
        "missing_price",
        _("Добавьте хотя бы один заполненный тариф или выберите вариант «Бесплатно» / «Бесплатный вход»."),
    )


def _check_phone(data: PlaceReadinessData):
    if not _text(data.phone1):
        return ("missing_phone", _("Укажите телефон. Instagram и сайт его не заменяют."))
    return None


def _check_schedule(data: PlaceReadinessData):
    if _contains_test_content(data.schedule_text):
        return ("test_content", _("Уберите из расписания тестовый текст вроде «test» или «lorem»."))
    # Only the weekly mode carries per-day hours. "By appointment", "variable"
    # and "by events" describe the schedule through the chosen mode itself, so
    # the mode is the answer — an upcoming event is not required.
    if data.schedule_mode != "regular":
        return None
    if data.schedule_has_structured:
        return None
    if data.schedule_text:
        # The old free-text field is not editable in the current form.
        return (
            "legacy_schedule_not_migrated",
            _("Перенесите расписание из старого текстового поля в редактор дней: откройте дни и укажите время."),
        )
    return ("missing_schedule", _("Откройте минимум один день и добавьте время работы."))


def _check_photo(data: PlaceReadinessData):
    """Only the card's own main image counts.

    Gallery photos never substitute for it. There is no stored placeholder to
    exclude: an empty card renders the placeholder in the template, so an empty
    ``photo`` simply fails here. ``cover_photo`` is accepted as a temporary
    bridge because ``Place.public_image_file`` still falls back to it as the
    real main image of older cards.
    """

    if not data.has_main_photo:
        return ("missing_photo", _("Загрузите главное фото. Фотографии галереи его не заменяют."))
    return None


PLACE_READINESS_REQUIREMENTS: tuple[ReadinessRequirement, ...] = (
    ReadinessRequirement(
        code="name",
        label=_("Название (AZ)"),
        section=SECTION_BASICS,
        field="name_az",
        anchor="id_name_az",
        check=_check_name,
        client_check="name",
    ),
    ReadinessRequirement(
        code="description",
        label=_("Описание (AZ)"),
        section=SECTION_BASICS,
        field="description_az",
        anchor="id_description_az",
        check=_check_description,
        client_check="description",
    ),
    ReadinessRequirement(
        code="category",
        label=_("Категория"),
        section=SECTION_BASICS,
        field="category",
        anchor="id_category",
        check=_check_category,
        client_check="category",
    ),
    ReadinessRequirement(
        code="subcategory",
        label=_("Подкатегория"),
        section=SECTION_BASICS,
        field="subcategory",
        anchor="id_subcategory",
        check=_check_subcategory,
        client_check="subcategory",
    ),
    ReadinessRequirement(
        code="region",
        label=_("Город / регион"),
        section=SECTION_LOCATION,
        field="region",
        anchor="id_region",
        check=_check_region,
        client_check="region",
    ),
    ReadinessRequirement(
        code="address",
        label=_("Адрес"),
        section=SECTION_LOCATION,
        field="address",
        anchor="id_address",
        check=_check_address,
        client_check="address",
    ),
    ReadinessRequirement(
        code="coordinates",
        label=_("Точка на карте"),
        section=SECTION_LOCATION,
        field="lat",
        anchor="id_lat",
        check=_check_coordinates,
        client_check="coordinates",
    ),
    ReadinessRequirement(
        code="age",
        label=_("Возраст"),
        section=SECTION_PRICING,
        field="age_from",
        anchor="id_age_from",
        check=_check_age,
        client_check="age",
    ),
    ReadinessRequirement(
        code="price",
        label=_("Цена"),
        section=SECTION_PRICING,
        field="pricing_plans",
        anchor="[data-tariff-editor]",
        check=_check_price,
        client_check="price",
    ),
    ReadinessRequirement(
        code="phone",
        label=_("Телефон"),
        section=SECTION_LOCATION,
        field="phone1",
        anchor="id_phone1",
        check=_check_phone,
        client_check="phone",
    ),
    ReadinessRequirement(
        code="schedule",
        label=_("Расписание"),
        section=SECTION_LOCATION,
        field="structured_schedule",
        anchor="admin-place-schedule",
        check=_check_schedule,
        client_check="schedule",
    ),
    ReadinessRequirement(
        code="photo",
        label=_("Главное фото"),
        section=SECTION_MEDIA,
        field="photo",
        anchor="id_photo",
        check=_check_photo,
        client_check="photo",
    ),
)


def _advice_short_description(data: PlaceReadinessData) -> ReadinessIssue | None:
    description = _text(data.description_az)
    if not description or len(description) >= MIN_DESCRIPTION_LENGTH:
        return None
    return ReadinessIssue(
        code="description_length",
        section=SECTION_BASICS,
        field="description_az",
        anchor="id_description_az",
        label=str(_("Описание (AZ)")),
        message=str(
            _("Рекомендуем не менее %(count)s символов — короткое описание хуже работает в поиске.")
            % {"count": MIN_DESCRIPTION_LENGTH}
        ),
        quality_code="description_length",
        blocking=False,
    )


def _advice_cover_photo_as_main(data: PlaceReadinessData) -> ReadinessIssue | None:
    if not data.has_cover_photo_only:
        return None
    return ReadinessIssue(
        code="cover_photo_as_main",
        section=SECTION_MEDIA,
        field="photo",
        anchor="id_photo",
        label=str(_("Главное фото")),
        message=str(_("Сейчас как главное используется резервное фото — загрузите основное изображение карточки.")),
        quality_code="cover_photo_as_main",
        blocking=False,
    )


# Quality advice: shown to the editor, never counted in the twelve and never a
# reason to refuse publication.
PLACE_READINESS_ADVICE = (
    _advice_short_description,
    _advice_cover_photo_as_main,
)


def evaluate_readiness(data: PlaceReadinessData) -> PlaceReadiness:
    """Apply every requirement to *data*. The only place rules are decided."""

    items = []
    for requirement in PLACE_READINESS_REQUIREMENTS:
        failure = requirement.check(data)
        issue = None
        if failure is not None:
            quality_code, message = failure
            issue = ReadinessIssue(
                code=requirement.code,
                section=requirement.section,
                field=requirement.field,
                anchor=requirement.anchor,
                label=str(requirement.label),
                message=str(message),
                quality_code=quality_code,
            )
        items.append(ReadinessItem(requirement=requirement, issue=issue))
    advice = tuple(filter(None, (check(data) for check in PLACE_READINESS_ADVICE)))
    return PlaceReadiness(items=tuple(items), advice=advice)


LEGACY_PRICE_FIELDS = (
    "price_from",
    "price_to",
    "price_per_lesson",
    "price_per_month",
    "price_per_8_lessons",
)


def _has_legacy_price(place_or_instance) -> bool:
    """The pre-tariff scalar price.

    It still feeds the public catalog so old published cards keep showing a
    price, but it does not satisfy the readiness requirement: the card has to
    be migrated to a tariff (or marked free) before it can be published again.
    """

    return any(
        getattr(place_or_instance, field_name, None) is not None
        for field_name in LEGACY_PRICE_FIELDS
    )


def _place_schedule_is_structured(place) -> bool:
    if getattr(place, "pk", None) is None:
        return False
    from catalog.services.place_schedule import is_meaningful_schedule, serialize_place_schedule

    return is_meaningful_schedule(serialize_place_schedule(place))


def readiness_data_from_place(place) -> PlaceReadinessData:
    """Build a snapshot from a stored (or fully populated) ``Place``."""

    subcategory = place.subcategory if getattr(place, "subcategory_id", None) else None
    subcategory_category_code = ""
    if subcategory is not None and getattr(subcategory, "category_id", None):
        subcategory_category_code = getattr(subcategory.category, "code", "") or ""

    schedule_text = (getattr(place, "schedule", "") or "").strip()
    has_structured = _place_schedule_is_structured(place)
    from catalog.services.content_quality import _place_has_pricing_plan_price

    photo = getattr(place, "photo", None)
    cover_photo = getattr(place, "cover_photo", None)

    return PlaceReadinessData(
        name_az=getattr(place, "name_az", "") or "",
        name_texts=tuple(
            getattr(place, field_name, "") or ""
            for field_name in ("name", "name_az", "name_ru", "name_en")
        ),
        description_az=getattr(place, "description_az", "") or "",
        description_texts=tuple(
            getattr(place, field_name, "") or ""
            for field_name in ("description_az", "description_ru", "description_en")
        ),
        category_code=getattr(place, "category_id", "") or "",
        subcategory_id=getattr(place, "subcategory_id", None),
        subcategory_category_code=subcategory_category_code,
        district=getattr(place, "district", "") or "",
        address=getattr(place, "address", "") or "",
        lat=getattr(place, "lat", None),
        lng=getattr(place, "lng", None),
        age_from=getattr(place, "age_from", None),
        age_to=getattr(place, "age_to", None),
        age_open_ended=bool(getattr(place, "age_open_ended", False)),
        has_priced_plan=_place_has_pricing_plan_price(place),
        has_legacy_price=_has_legacy_price(place),
        has_custom_price_badge=bool(
            (getattr(place, "custom_price_badge_az", "") or "").strip()
            or (getattr(place, "custom_price_badge_ru", "") or "").strip()
            or (getattr(place, "custom_price_badge_en", "") or "").strip()
        ),
        phone1=getattr(place, "phone1", "") or "",
        schedule_mode=getattr(place, "schedule_mode", "regular") or "regular",
        schedule_has_structured=has_structured,
        schedule_text=schedule_text,
        has_main_photo=bool(photo) or bool(cover_photo),
        has_cover_photo_only=bool(cover_photo) and not bool(photo),
    )


def evaluate_place_readiness(place) -> PlaceReadiness:
    """Readiness of a stored place card."""

    return evaluate_readiness(readiness_data_from_place(place))


def _form_value(form, cleaned, field_name, instance):
    """Prefer the submitted value, fall back to what is already stored."""

    if field_name in cleaned:
        return cleaned.get(field_name)
    if instance is not None:
        return getattr(instance, field_name, None)
    return None


def readiness_data_from_form(form, instance=None) -> PlaceReadinessData:
    """Build a snapshot from a bound place form before anything is saved.

    The editor must see the same verdict the server will give, so this reads
    submitted values rather than the stored row: tariffs come from the posted
    payload (it replaces the stored plans on save) and the schedule from the
    validated editor days.
    """

    cleaned = getattr(form, "cleaned_data", None) or {}
    instance = instance if instance is not None else getattr(form, "instance", None)

    def text(field_name: str) -> str:
        return _text(_form_value(form, cleaned, field_name, instance))

    category = _form_value(form, cleaned, "category", instance)
    category_code = getattr(category, "code", None) or (category if isinstance(category, str) else "") or ""
    if not category_code and instance is not None:
        category_code = getattr(instance, "category_id", "") or ""

    subcategory = cleaned.get("subcategory") if "subcategory" in cleaned else None
    if subcategory is None and "subcategory" not in cleaned and instance is not None:
        subcategory = instance.subcategory if getattr(instance, "subcategory_id", None) else None
    subcategory_category_code = ""
    if subcategory is not None and getattr(subcategory, "category_id", None):
        subcategory_category_code = getattr(subcategory.category, "code", "") or ""

    plans = cleaned.get("pricing_plans")
    if not isinstance(plans, list):
        plans = getattr(instance, "pricing_plans", None) or []
    from catalog.services.content_quality import _mapping_has_public_price

    has_priced_plan = any(_mapping_has_public_price(plan) for plan in plans)
    # Legacy scalar prices are not editable in this form. They are reported so
    # the editor is told to migrate them, never as a satisfied requirement.
    has_legacy_price = instance is not None and _has_legacy_price(instance)
    has_custom_price_badge = bool(
        text("custom_price_badge_az") or text("custom_price_badge_ru") or text("custom_price_badge_en")
    )

    schedule_mode = cleaned.get("schedule_mode") or getattr(instance, "schedule_mode", "regular") or "regular"
    schedule_days = getattr(form, "cleaned_schedule_days", None)
    if schedule_days is None:
        schedule_days = []
    from catalog.services.place_schedule import is_meaningful_schedule

    schedule_text = text("schedule")
    schedule_has_structured = is_meaningful_schedule(schedule_days)

    photo = _form_value(form, cleaned, "photo", instance)
    cover_photo = _form_value(form, cleaned, "cover_photo", instance)

    return PlaceReadinessData(
        name_az=text("name_az"),
        name_texts=tuple(text(field_name) for field_name in ("name", "name_az", "name_ru", "name_en")),
        description_az=text("description_az"),
        description_texts=tuple(
            text(field_name) for field_name in ("description_az", "description_ru", "description_en")
        ),
        category_code=category_code,
        subcategory_id=getattr(subcategory, "pk", None),
        subcategory_category_code=subcategory_category_code,
        district=text("district"),
        address=text("address"),
        lat=_coerce_coordinate(_form_value(form, cleaned, "lat", instance)),
        lng=_coerce_coordinate(_form_value(form, cleaned, "lng", instance)),
        age_from=_coerce_int(_form_value(form, cleaned, "age_from", instance)),
        age_to=_coerce_int(_form_value(form, cleaned, "age_to", instance)),
        age_open_ended=bool(_form_value(form, cleaned, "age_open_ended", instance)),
        has_priced_plan=has_priced_plan,
        has_legacy_price=has_legacy_price,
        has_custom_price_badge=has_custom_price_badge,
        phone1=text("phone1"),
        schedule_mode=schedule_mode,
        schedule_has_structured=schedule_has_structured,
        schedule_text=schedule_text,
        has_main_photo=bool(photo) or bool(cover_photo),
        has_cover_photo_only=bool(cover_photo) and not bool(photo),
    )


def _coerce_coordinate(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def evaluate_form_readiness(form, instance=None) -> PlaceReadiness:
    """Readiness of the card as currently filled in the admin form."""

    return evaluate_readiness(readiness_data_from_form(form, instance))


def format_readiness_issues(readiness: PlaceReadiness) -> str:
    """"Возраст — укажите ...; Цена — ..." for a single-line message."""

    return "; ".join(f"{issue.label} — {issue.message}" for issue in readiness.issues)


def publication_blocked_message(readiness: PlaceReadiness) -> str:
    """Never say only "the card is not ready": always say what is missing."""

    return str(
        _(
            "Карточка не может быть опубликована. Заполнено %(done)s из %(total)s обязательных пунктов. "
            "Необходимо заполнить: %(issues)s"
        )
        % {
            "done": readiness.completed_count,
            "total": readiness.required_count,
            "issues": format_readiness_issues(readiness),
        }
    )
