import uuid
from functools import lru_cache

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_delete, post_save
from django.conf import settings
from django.utils.translation import gettext as translate
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver
from catalog.taxonomy_data import CATEGORIES

def _localized_free_label(lang: str | None = None) -> str:
    normalized_lang = (lang or get_language() or settings.LANGUAGE_CODE or "az").split("-")[0]
    if normalized_lang == "az":
        return "Pulsuz"
    if normalized_lang == "en":
        return "Free"
    return "Бесплатно"


class Place(models.Model):
    LESSON_FORMAT_GROUP = "group"
    LESSON_FORMAT_INDIVIDUAL = "individual"
    LESSON_FORMAT_CHOICES = [
        (LESSON_FORMAT_GROUP, _("Групповые")),
        (LESSON_FORMAT_INDIVIDUAL, _("Индивидуальные")),
    ]
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PUBLISHED = "published"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, _("Черновик")),
        (STATUS_PENDING, _("На модерации")),
        (STATUS_PUBLISHED, _("Опубликовано")),
        (STATUS_REJECTED, _("Отклонено")),
    ]

    CATEGORY_CHOICES = [(item["code"], _(item["ru"])) for item in CATEGORIES]

    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, blank=True, default="", unique=True)
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    description_ru = models.TextField(_("Описание (RU)"), blank=True, default="")
    description_en = models.TextField(_("Описание (EN)"), blank=True, default="")
    description_az = models.TextField(_("Описание (AZ)"), blank=True, default="")
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        db_column="category",
        to_field="code",
        verbose_name=_("Категория"),
    )
    subcategory = models.ForeignKey(
        "catalog.Subcategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Подкатегория"),
    )

    age_from = models.PositiveSmallIntegerField(_("Возраст от"), null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(_("Возраст до"), null=True, blank=True)
    age_open_ended = models.BooleanField(
        _("Без верхней границы возраста"),
        default=False,
        help_text=_("Например: 3+; для всех возрастов укажите возраст «от» 0."),
    )
    offers_adult_classes = models.BooleanField(_("Также есть занятия для взрослых"), default=False)

    district = models.CharField(_("Регион / район"), max_length=100, blank=True)
    metro = models.CharField(_("Метро"), max_length=100, blank=True)
    address = models.CharField(_("Адрес"), max_length=255, blank=True)

    phone1 = models.CharField(_("Телефон 1"), max_length=50, blank=True)
    phone2 = models.CharField(_("Дополнительный телефон"), max_length=50, blank=True, default="")
    phone3 = models.CharField(_("Ещё один телефон"), max_length=50, blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_places",
        verbose_name=_("Владелец карточки"),
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_places",
        verbose_name=_("Кто добавил"),
        null=True,
        blank=True,
    )
    cover_photo = models.FileField(_("Фото для шапки"), upload_to="places/covers/", blank=True, null=True)
    photo = models.FileField(_("Фото"), upload_to="places/", blank=True, null=True)
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)
    website = models.URLField(_("Сайт"), blank=True)
    schedule = models.TextField(_("Расписание"), blank=True)
    lesson_duration_minutes = models.PositiveSmallIntegerField(_("Длительность урока (мин)"), null=True, blank=True)
    lesson_format = models.CharField(_("Формат занятий"), max_length=16, choices=LESSON_FORMAT_CHOICES, blank=True, default="")
    lessons_per_week = models.PositiveSmallIntegerField(_("Занятий в неделю"), null=True, blank=True)
    lessons_per_month = models.PositiveSmallIntegerField(_("Занятий в месяц"), null=True, blank=True)
    pricing_plans_legacy = models.JSONField(_("Старые тарифы JSON"), default=list, blank=True, db_column="pricing_plans")
    is_temporary = models.BooleanField(_("Временное мероприятие"), default=False)
    temporary_start = models.DateTimeField(_("Начало мероприятия"), null=True, blank=True)
    temporary_end = models.DateTimeField(_("Окончание мероприятия"), null=True, blank=True)
    lat = models.FloatField(_("Широта"), null=True, blank=True)
    lng = models.FloatField(_("Долгота"), null=True, blank=True)

    price_from = models.DecimalField(_("Цена от"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_to = models.DecimalField(_("Цена до"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_lesson = models.DecimalField(_("Цена за 1 урок"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(_("Цена за месяц"), max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_8_lessons = models.DecimalField(_("Цена за 8 уроков"), max_digits=10, decimal_places=2, null=True, blank=True)
    extra_conditions = models.TextField(_("Дополнительные условия"), blank=True)
    additional_info = models.TextField(_("Дополнительная информация"), blank=True)
    extra_conditions_az = models.TextField(_("Дополнительные условия (AZ)"), blank=True, default="")
    extra_conditions_ru = models.TextField(_("Дополнительные условия (RU)"), blank=True, default="")
    extra_conditions_en = models.TextField(_("Дополнительные условия (EN)"), blank=True, default="")
    additional_info_az = models.TextField(_("Дополнительная информация (AZ)"), blank=True, default="")
    additional_info_ru = models.TextField(_("Дополнительная информация (RU)"), blank=True, default="")
    additional_info_en = models.TextField(_("Дополнительная информация (EN)"), blank=True, default="")
    likes_count = models.PositiveIntegerField(_("Лайки"), default=0)
    rating_avg = models.FloatField(_("Средний рейтинг"), default=0)
    rating_count = models.PositiveIntegerField(_("Количество отзывов"), default=0)
    is_home_recommended = models.BooleanField(
        _("Показывать в рекомендациях на главной"),
        default=False,
        db_index=True,
    )
    home_recommended_order = models.PositiveSmallIntegerField(
        _("Порядок в рекомендациях"),
        default=0,
        help_text=_("Меньшее число показывается раньше. На главной выводятся максимум четыре места."),
    )

    is_active = models.BooleanField(_("Активно"), default=True)
    is_verified = models.BooleanField(_("Проверено"), default=False)
    status = models.CharField(_("Статус модерации"), max_length=16, choices=STATUS_CHOICES, default=STATUS_PUBLISHED, db_index=True)
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    last_verified_at = models.DateTimeField(_("Информация проверена"), null=True, blank=True, db_index=True)
    published_at = models.DateTimeField(_("Опубликовано"), null=True, blank=True, db_index=True)
    deleted_at = models.DateTimeField(_("Удалено"), null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="deleted_places",
        verbose_name=_("Удалил"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or settings.LANGUAGE_CODE or "az"
        return lang.split("-")[0]

    def __init__(self, *args, **kwargs):
        category = kwargs.get("category")
        if isinstance(category, str):
            kwargs["category_id"] = kwargs.pop("category")

        subcategory = kwargs.get("subcategory")
        if isinstance(subcategory, str):
            kwargs["subcategory_id"] = kwargs.pop("subcategory")

        super().__init__(*args, **kwargs)

    def name_i18n(self, lang=None):
        lang = self._normalize_lang(lang)
        if lang == "en":
            return self.name_en or self.name_ru or self.name
        if lang == "az":
            return self.name_az or self.name_ru or self.name
        return self.name_ru or self.name

    def description_i18n(self, lang=None):
        lang = self._normalize_lang(lang)
        return getattr(self, f"description_{lang}", "") or ""

    def address_i18n(self, lang=None):
        from catalog.services.locations import localize_address_text

        return localize_address_text(self.address, self._normalize_lang(lang))

    def district_i18n(self, lang=None):
        if not self.district:
            return ""
        from catalog.services.locations import get_location_translation

        return get_location_translation(self.district, self._normalize_lang(lang))

    def metro_i18n(self, lang=None):
        if not self.metro:
            return ""
        with_translation = str(translate(self.metro))
        return with_translation or self.metro

    def instagram_url(self):
        value = (self.instagram or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith(("instagram.com/", "www.instagram.com/")):
            return f"https://{value}"
        if "instagram.com/" in value:
            return f"https://{value.lstrip('/')}"
        return f"https://instagram.com/{value.lstrip('@')}"

    def website_url(self):
        value = (self.website or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        return f"https://{value}"

    def gallery_files(self):
        files = []
        seen = set()

        def add_file(file_field):
            if file_field and getattr(file_field, "name", ""):
                name = file_field.name
                if name not in seen:
                    seen.add(name)
                    files.append(file_field)

        add_file(self.photo)
        if not files:
            add_file(self.cover_photo)
        for item in self.gallery.order_by("order", "id"):
            add_file(item.image)
        return files

    @property
    def age_display(self) -> str:
        if self.age_from is not None and self.age_to is not None:
            return f"{self.age_from}–{self.age_to}"
        if self.age_from is not None:
            return f"{self.age_from}+"
        if self.age_to is not None:
            return str(self.age_to)
        return ""

    def clean(self):
        super().clean()
        errors = {}
        if self.age_from is not None and self.age_to is not None and self.age_from > self.age_to:
            errors["age_to"] = _("Возраст «до» не может быть меньше возраста «от».")
        if self.offers_adult_classes and (self.age_from is None or (self.age_to is None and not self.age_open_ended)):
            errors["offers_adult_classes"] = _(
                "Сначала укажите детский возрастной диапазон. Место не может быть только для взрослых."
            )
        if errors:
            raise ValidationError(errors)

    @property
    def pricing_plans(self):
        pending = getattr(self, "_pending_pricing_plans", None)
        if pending is not None:
            return pending
        if not self.pk:
            return self.pricing_plans_legacy or []
        from catalog.services.pricing_plans import serialize_pricing_plans
        plans = list(self.pricing_plan_records.all())
        return serialize_pricing_plans(plans) if plans else (self.pricing_plans_legacy or [])

    @pricing_plans.setter
    def pricing_plans(self, value):
        self._pending_pricing_plans = value or []

    @property
    def price_range_display(self) -> str:
        from catalog.services.pricing_plans import build_public_price_summary
        return build_public_price_summary(self, self._normalize_lang(None))["label"]

    @property
    def lesson_duration_display(self) -> str:
        if not self.lesson_duration_minutes:
            return ""
        return _("%(minutes)s мин") % {"minutes": self.lesson_duration_minutes}

    @property
    def card_price_badge(self) -> str:
        return self.price_range_display

    @property
    def card_price_badge_label(self) -> str:
        return ""

    @property
    def card_price_badge_value(self) -> str:
        return self.price_range_display

    @property
    def card_price_badge_currency(self) -> str:
        return ""

    @property
    def pricing_options(self) -> list[tuple[str, str]]:
        from catalog.services.pricing_plans import format_price_amount
        options: list[tuple[str, str]] = []
        if self.price_per_lesson is not None:
            options.append((str(_("1 урок")), _localized_free_label(self._normalize_lang(None)) if self.price_per_lesson == 0 else f"{format_price_amount(self.price_per_lesson)} AZN"))
        if self.price_per_month is not None:
            options.append((str(_("1 месяц")), _localized_free_label(self._normalize_lang(None)) if self.price_per_month == 0 else f"{format_price_amount(self.price_per_month)} AZN"))
        if self.price_per_8_lessons is not None:
            options.append((str(_("8 уроков")), _localized_free_label(self._normalize_lang(None)) if self.price_per_8_lessons == 0 else f"{format_price_amount(self.price_per_8_lessons)} AZN"))
        if self.price_range_display:
            options.append((str(_("Диапазон цены")), self.price_range_display))
        return options

    @property
    def phone_numbers(self) -> list[str]:
        """Unique non-empty phone numbers in the order shown to visitors."""
        numbers: list[str] = []
        for phone in (self.phone1, self.phone2, self.phone3):
            normalized = (phone or "").strip()
            if normalized and normalized not in numbers:
                numbers.append(normalized)
        return numbers

    def _localized_text(self, prefix: str, lang: str | None = None) -> str:
        language = self._normalize_lang(lang)
        localized = getattr(self, f"{prefix}_{language}", "") or ""
        if localized:
            return localized
        return (getattr(self, prefix, "") or "") if language == "ru" else ""

    def extra_conditions_i18n(self, lang: str | None = None) -> str:
        return self._localized_text("extra_conditions", lang)

    def additional_info_i18n(self, lang: str | None = None) -> str:
        return self._localized_text("additional_info", lang)

    @property
    def has_more_details(self) -> bool:
        return any(
            (
                self.address,
                self.phone1,
                self.phone2,
                self.phone3,
                self.instagram,
                self.website,
                self.has_schedule_content,
                self.lesson_duration_minutes is not None,
                self.price_per_lesson is not None,
                self.price_per_month is not None,
                self.price_per_8_lessons is not None,
                self.lesson_format,
                self.lessons_per_week is not None,
                self.lessons_per_month is not None,
                self.pricing_plans,
                self.extra_conditions,
                self.additional_info,
                self.extra_conditions_az,
                self.extra_conditions_ru,
                self.extra_conditions_en,
                self.additional_info_az,
                self.additional_info_ru,
                self.additional_info_en,
                self.price_from is not None,
                self.price_to is not None,
            )
        )

    @property
    def has_structured_schedule(self) -> bool:
        if not getattr(self, "pk", None):
            return False
        return self.schedule_days.exists()

    @property
    def has_schedule_content(self) -> bool:
        return self.has_structured_schedule or bool((self.schedule or "").strip())

    @property
    def schedule_rows(self) -> list[dict[str, object]]:
        if not self.has_structured_schedule:
            return []
        from catalog.services.place_schedule import build_schedule_rows, serialize_place_schedule

        return build_schedule_rows(serialize_place_schedule(self))

    @property
    def schedule_summary(self) -> str:
        if self.has_structured_schedule:
            from catalog.services.place_schedule import build_schedule_summary, serialize_place_schedule

            return build_schedule_summary(serialize_place_schedule(self))
        return (self.schedule or "").strip()

    @property
    def has_coordinates(self) -> bool:
        return self.lat is not None and self.lng is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_public(self) -> bool:
        return self.is_active and self.status == self.STATUS_PUBLISHED and not self.is_deleted

    @property
    def publication_state(self) -> str:
        if self.is_deleted:
            return "deleted"
        if self.is_public:
            return "published"
        if self.status == self.STATUS_PENDING:
            return "pending"
        if self.status == self.STATUS_REJECTED:
            return "rejected"
        if self.status == self.STATUS_PUBLISHED and not self.is_active:
            return "unpublished"
        return "draft"

    @property
    def is_map_ready(self) -> bool:
        return self.is_public and self.has_coordinates

    @property
    def map_readiness_reason(self) -> str:
        if self.is_deleted:
            return "deleted"
        if not self.has_coordinates:
            return "missing_coordinates"
        if not self.is_active:
            return "inactive"
        return "ready"

    def soft_delete(self, *, deleted_by=None) -> bool:
        if self.is_deleted and not self.is_active and self.deleted_by_id == getattr(deleted_by, "pk", None):
            return False

        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.is_active = False
        self.save(update_fields=["deleted_at", "deleted_by", "is_active", "updated_at"])
        return True

    def restore_from_deleted(self, *, activate: bool = False) -> bool:
        if not self.is_deleted and (self.is_active or not activate):
            return False

        self.deleted_at = None
        self.deleted_by = None
        self.is_active = bool(activate)
        self.save(update_fields=["deleted_at", "deleted_by", "is_active", "updated_at"])
        return True

    def __str__(self):
        return self.name_i18n()

    def get_category_display(self):
        if not self.category_id:
            return ""
        return str(self.category)

    @property
    def category_code(self):
        return self.category_id

    def get_absolute_url(self):
        return reverse("place_detail", kwargs={"pk": self.pk, "slug": self.slug})

    def _build_unique_slug(self):
        from catalog.services.slugs import build_unique_ascii_slug

        source = self.name_az or self.name_en or self.name_ru or self.name or "place"
        return build_unique_ascii_slug(
            Place,
            source,
            fallback="place",
            instance_pk=self.pk,
        )

    def save(self, *args, **kwargs):
        pending_pricing = getattr(self, "_pending_pricing_plans", None)
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "pricing_plans" in update_fields:
            concrete_fields = set(update_fields) - {"pricing_plans"}
            if concrete_fields:
                kwargs["update_fields"] = concrete_fields
            else:
                kwargs.pop("update_fields")
        if not self.slug:
            self.slug = self._build_unique_slug()
        if self.district:
            from catalog.services.locations import normalize_to_key
            self.district = normalize_to_key(self.district)
        super().save(*args, **kwargs)
        if pending_pricing is not None:
            from catalog.services.pricing_plans import replace_place_pricing_plans
            replace_place_pricing_plans(self, pending_pricing)
            del self._pending_pricing_plans

    def refresh_rating_stats(self):
        from catalog.services.content_quality import public_review_queryset
        stats = public_review_queryset(self.reviews.all()).aggregate(avg=Avg("rating"), cnt=Count("id"))
        self.rating_avg = float(stats.get("avg") or 0.0)
        self.rating_count = int(stats.get("cnt") or 0)
        self.save(update_fields=["rating_avg", "rating_count"])

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Постоянное место")
        verbose_name_plural = _("Постоянные места")


class PlacePhoto(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="gallery", verbose_name=_("Место"))
    image = models.FileField(_("Фото"), upload_to="places/gallery/")
    caption = models.CharField(_("Подпись"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("Фото галереи")
        verbose_name_plural = _("Фото галереи")

    def __str__(self):
        return f"{self.place.name_i18n()} #{self.order}"


class PlaceScheduleDay(models.Model):
    WEEKDAY_CHOICES = (
        ("mon", _("Понедельник")),
        ("tue", _("Вторник")),
        ("wed", _("Среда")),
        ("thu", _("Четверг")),
        ("fri", _("Пятница")),
        ("sat", _("Суббота")),
        ("sun", _("Воскресенье")),
    )

    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="schedule_days", verbose_name=_("Место"))
    weekday = models.CharField(_("День недели"), max_length=3, choices=WEEKDAY_CHOICES)
    is_closed = models.BooleanField(_("Закрыто"), default=True)
    is_24_hours = models.BooleanField(_("24 часа"), default=False)
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("День расписания")
        verbose_name_plural = _("Дни расписания")
        constraints = [
            models.UniqueConstraint(fields=("place", "weekday"), name="unique_place_schedule_weekday"),
        ]

    def __str__(self):
        return f"{self.place} · {self.get_weekday_display()}"


class PlaceScheduleInterval(models.Model):
    schedule_day = models.ForeignKey(
        PlaceScheduleDay,
        on_delete=models.CASCADE,
        related_name="intervals",
        verbose_name=_("День расписания"),
    )
    start_time = models.TimeField(_("Начало"))
    end_time = models.TimeField(_("Окончание"))
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("Интервал расписания")
        verbose_name_plural = _("Интервалы расписания")

    def __str__(self):
        return f"{self.schedule_day} · {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class Event(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PUBLISHED = "published"
    STATUS_REJECTED = "rejected"
    STATUS_EXPIRED = "expired"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_DRAFT, _("Черновик")),
        (STATUS_PENDING, _("На модерации")),
        (STATUS_PUBLISHED, _("Опубликовано")),
        (STATUS_REJECTED, _("Отклонено")),
        (STATUS_EXPIRED, _("Завершено")),
        (STATUS_CANCELLED, _("Отменено")),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_events",
        verbose_name=_("Владелец мероприятия"),
        null=True,
        blank=True,
    )
    related_place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="events",
        verbose_name=_("Связанное место"),
        null=True,
        blank=True,
    )
    name = models.CharField(_("Название"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, blank=True, default="")
    name_az = models.CharField(_("Название (AZ)"), max_length=255, blank=True, default="")
    name_ru = models.CharField(_("Название (RU)"), max_length=255, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=255, blank=True, default="")
    description_az = models.TextField(_("Описание (AZ)"), blank=True, default="")
    description_ru = models.TextField(_("Описание (RU)"), blank=True, default="")
    description_en = models.TextField(_("Описание (EN)"), blank=True, default="")
    category = models.ForeignKey(
        "catalog.Category",
        on_delete=models.PROTECT,
        db_column="category",
        to_field="code",
        verbose_name=_("Категория"),
    )
    start_datetime = models.DateTimeField(_("Начало мероприятия"), null=True, blank=True, db_index=True)
    end_datetime = models.DateTimeField(_("Окончание мероприятия"), null=True, blank=True, db_index=True)
    age_from = models.PositiveSmallIntegerField(_("Возраст от"), null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(_("Возраст до"), null=True, blank=True)
    price_text = models.CharField(_("Цена"), max_length=120, blank=True, default="")
    district = models.CharField(_("Регион / район"), max_length=100, blank=True, default="")
    metro = models.CharField(_("Метро"), max_length=100, blank=True, default="")
    address = models.CharField(_("Адрес"), max_length=255, blank=True, default="")
    lat = models.DecimalField(_("Широта"), max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(_("Долгота"), max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(_("Телефон / WhatsApp"), max_length=50, blank=True, default="")
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True, default="")
    website = models.URLField(_("Сайт"), max_length=255, blank=True, default="")
    photo = models.FileField(_("Основное фото"), upload_to="events/", blank=True, null=True)
    moderation_note = models.TextField(_("Комментарий для модерации"), blank=True, default="")
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    status = models.CharField(_("Статус модерации"), max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT, db_index=True)
    published_at = models.DateTimeField(_("Опубликовано"), null=True, blank=True, db_index=True)
    deleted_at = models.DateTimeField(_("Удалено"), null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or settings.LANGUAGE_CODE or "az"
        return lang.split("-")[0]

    def __init__(self, *args, **kwargs):
        category = kwargs.get("category")
        if isinstance(category, str):
            kwargs["category_id"] = kwargs.pop("category")

        super().__init__(*args, **kwargs)

    def name_i18n(self, lang=None):
        lang = self._normalize_lang(lang)
        if lang == "en":
            return self.name_en or self.name_az or self.name_ru or self.name
        if lang == "ru":
            return self.name_ru or self.name_az or self.name_en or self.name
        return self.name_az or self.name_ru or self.name_en or self.name

    def description_i18n(self, lang=None):
        lang = self._normalize_lang(lang)
        return getattr(self, f"description_{lang}", "") or ""

    def address_i18n(self, lang=None):
        from catalog.services.locations import localize_address_text

        return localize_address_text(self.address, self._normalize_lang(lang))

    @property
    def has_coordinates(self):
        return self.lat is not None and self.lng is not None

    @property
    def age_display(self) -> str:
        if self.age_from is not None and self.age_to is not None:
            return f"{self.age_from}-{self.age_to}"
        if self.age_from is not None:
            return f"{self.age_from}+"
        if self.age_to is not None:
            return str(self.age_to)
        return ""

    @property
    def price_display(self) -> str:
        return (self.price_text or "").strip()

    @property
    def has_ended(self) -> bool:
        return bool(self.end_datetime and self.end_datetime < timezone.now())

    @property
    def is_running_now(self) -> bool:
        if not self.start_datetime or not self.end_datetime:
            return False
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    @property
    def effective_status(self) -> str:
        if self.status == self.STATUS_PUBLISHED and self.has_ended:
            return self.STATUS_EXPIRED
        return self.status

    @property
    def is_public(self) -> bool:
        return (
            self.status == self.STATUS_PUBLISHED
            and not self.deleted_at
            and bool(self.start_datetime)
            and bool(self.end_datetime)
            and not self.has_ended
        )

    def instagram_url(self):
        value = (self.instagram or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith(("instagram.com/", "www.instagram.com/")):
            return f"https://{value}"
        if "instagram.com/" in value:
            return f"https://{value.lstrip('/')}"
        return f"https://instagram.com/{value.lstrip('@')}"

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"pk": self.pk, "slug": self.slug})

    def _build_unique_slug(self):
        from catalog.services.slugs import build_unique_ascii_slug

        source = self.name_az or self.name_ru or self.name_en or self.name or "event"
        return build_unique_ascii_slug(
            Event,
            source,
            fallback="event",
            instance_pk=self.pk,
        )

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.name_az or self.name_ru or self.name_en or _("Мероприятие")
        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_i18n()

    def get_category_display(self):
        if not self.category_id:
            return ""
        return str(self.category)

    @property
    def category_code(self):
        return self.category_id

    class Meta:
        ordering = ("start_datetime", "-created_at")
        indexes = [
            models.Index(fields=("status", "start_datetime")),
            models.Index(fields=("owner", "status")),
            models.Index(fields=("end_datetime",)),
        ]
        verbose_name = _("Мероприятие")
        verbose_name_plural = _("Мероприятия")


class EventPhoto(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="gallery", verbose_name=_("Мероприятие"))
    image = models.FileField(_("Фото"), upload_to="events/gallery/")
    caption = models.CharField(_("Подпись"), max_length=255, blank=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("Фото мероприятия")
        verbose_name_plural = _("Фотографии мероприятия")

    def __str__(self):
        return f"{self.event.name_i18n()} #{self.order}"


class PlaceLike(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="place_likes", verbose_name=_("Место"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="place_likes",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("place", "session_key"),
                condition=models.Q(user__isnull=True) & ~models.Q(session_key=""),
                name="unique_place_like_per_session",
            ),
            models.UniqueConstraint(
                fields=("place", "user"),
                name="unique_place_like_per_user",
            ),
        ]
        verbose_name = _("Лайк")
        verbose_name_plural = _("Лайки")

    def save(self, *args, **kwargs):
        self.session_key = (self.session_key or "").strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.place_id}:{self.session_key}"


class PlaceReviewsByClub(Place):
    class Meta:
        proxy = True
        verbose_name = _("Рейтинг места")
        verbose_name_plural = _("Рейтинги мест")
