import re
import uuid
from functools import lru_cache

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg, Count, Q
from django.db.models.signals import post_delete, post_save
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver

def _localize_public_address(raw_value: str, lang: str) -> str:
    value = (raw_value or "").strip()
    if not value:
        return ""

    normalized_lang = (lang or settings.LANGUAGE_CODE or "az").split("-")[0]
    if normalized_lang == "ru":
        return value

    common_replacements = {
        "Баку": "Baku" if normalized_lang == "en" else "Bakı",
        "Ясамал": "Yasamal",
        "Школьная": "School" if normalized_lang == "en" else "Məktəb",
        "Ататюрка": "Ataturk" if normalized_lang == "en" else "Atatürk",
        "Гусейна Джавида": "Huseyn Javid" if normalized_lang == "en" else "Hüseyn Cavid",
    }
    for source, target in common_replacements.items():
        value = value.replace(source, target)

    if normalized_lang == "en":
        replacements = [
            (r"\bул\.\s*", "St. "),
            (r"\bулица\s+", ""),
            (r"\bпр\.\s*", "Ave. "),
            (r"\bпроспект\s+", ""),
        ]
    else:
        replacements = [
            (r"\bул\.\s*", "küç. "),
            (r"\bулица\s+", ""),
            (r"\bпр\.\s*", "prospekti "),
            (r"\bпроспект\s+", ""),
        ]

    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)

    return re.sub(r"\s{2,}", " ", value).strip(" ,")


class Place(models.Model):
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

    CATEGORY_CHOICES = [
        ("SPRT", _("Спорт")),
        ("ART", _("Творчество")),
        ("MUS", _("Музыка и сцена")),
        ("EDU", _("Образование")),
        ("TECH", _("Технологии")),
        ("FUN", _("Развлечения и досуг")),
        ("CAMP", _("Лагеря")),
    ]

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

    district = models.CharField(_("Регион / район"), max_length=100, blank=True)
    metro = models.CharField(_("Метро"), max_length=100, blank=True)
    address = models.CharField(_("Адрес"), max_length=255, blank=True)

    phone1 = models.CharField(_("Телефон 1"), max_length=50, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_places",
        verbose_name=_("Владелец карточки"),
        null=True,
        blank=True,
    )
    cover_photo = models.FileField(_("Фото для шапки"), upload_to="places/covers/", blank=True, null=True)
    photo = models.FileField(_("Фото"), upload_to="places/", blank=True, null=True)
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)
    website = models.URLField(_("Сайт"), blank=True)
    schedule = models.TextField(_("Расписание"), blank=True)
    lesson_duration_minutes = models.PositiveSmallIntegerField(_("Длительность урока (мин)"), null=True, blank=True)
    is_temporary = models.BooleanField(_("Временное мероприятие"), default=False)
    temporary_start = models.DateTimeField(_("Начало мероприятия"), null=True, blank=True)
    temporary_end = models.DateTimeField(_("Окончание мероприятия"), null=True, blank=True)
    lat = models.FloatField(_("Широта"), null=True, blank=True)
    lng = models.FloatField(_("Долгота"), null=True, blank=True)

    price_from = models.IntegerField(_("Цена от"), null=True, blank=True)
    price_to = models.IntegerField(_("Цена до"), null=True, blank=True)
    price_per_lesson = models.PositiveIntegerField(_("Цена за 1 урок"), null=True, blank=True)
    price_per_month = models.PositiveIntegerField(_("Цена за месяц"), null=True, blank=True)
    price_per_8_lessons = models.PositiveIntegerField(_("Цена за 8 уроков"), null=True, blank=True)
    extra_conditions = models.TextField(_("Дополнительные условия"), blank=True)
    additional_info = models.TextField(_("Дополнительная информация"), blank=True)
    likes_count = models.PositiveIntegerField(_("Лайки"), default=0)
    rating_avg = models.FloatField(_("Средний рейтинг"), default=0)
    rating_count = models.PositiveIntegerField(_("Количество отзывов"), default=0)

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
        if lang == "en":
            return self.description_en or self.description_ru or ""
        if lang == "az":
            return self.description_az or self.description_ru or ""
        return self.description_ru or ""

    def address_i18n(self, lang=None):
        return _localize_public_address(self.address, self._normalize_lang(lang))

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
            return f"{self.age_from}-{self.age_to}"
        if self.age_from is not None:
            return f"{self.age_from}+"
        if self.age_to is not None:
            return str(self.age_to)
        return ""

    @property
    def price_range_display(self) -> str:
        if self.price_from is not None and self.price_to is not None:
            if self.price_from == self.price_to:
                return f"{self.price_from} AZN"
            return f"{self.price_from}-{self.price_to} AZN"
        if self.price_from is not None:
            return f"{self.price_from} AZN"
        if self.price_to is not None:
            return f"{self.price_to} AZN"
        return ""

    @property
    def lesson_duration_display(self) -> str:
        if not self.lesson_duration_minutes:
            return ""
        return _("%(minutes)s мин") % {"minutes": self.lesson_duration_minutes}

    @property
    def card_price_badge(self) -> str:
        if self.price_per_lesson is not None:
            return _("1 урок · %(price)s AZN") % {"price": self.price_per_lesson}
        if self.price_from is not None:
            return _("от %(price)s AZN") % {"price": self.price_from}
        if self.price_to is not None:
            return _("до %(price)s AZN") % {"price": self.price_to}
        return ""

    @property
    def card_price_badge_label(self) -> str:
        if self.price_per_lesson is not None:
            return str(_("1 урок"))
        if self.price_from is not None:
            return str(_("от"))
        if self.price_to is not None:
            return str(_("до"))
        return ""

    @property
    def card_price_badge_value(self) -> str:
        if self.price_per_lesson is not None:
            return str(self.price_per_lesson)
        if self.price_from is not None:
            return str(self.price_from)
        if self.price_to is not None:
            return str(self.price_to)
        return ""

    @property
    def card_price_badge_currency(self) -> str:
        if self.card_price_badge:
            return "AZN"
        return ""

    @property
    def pricing_options(self) -> list[tuple[str, str]]:
        options: list[tuple[str, str]] = []
        if self.price_per_lesson is not None:
            options.append((str(_("1 урок")), f"{self.price_per_lesson} AZN"))
        if self.price_per_month is not None:
            options.append((str(_("1 месяц")), f"{self.price_per_month} AZN"))
        if self.price_per_8_lessons is not None:
            options.append((str(_("8 уроков")), f"{self.price_per_8_lessons} AZN"))
        if self.price_range_display:
            options.append((str(_("Диапазон цены")), self.price_range_display))
        return options

    @property
    def has_more_details(self) -> bool:
        return any(
            (
                self.address,
                self.phone1,
                self.instagram,
                self.website,
                self.schedule,
                self.lesson_duration_minutes is not None,
                self.price_per_lesson is not None,
                self.price_per_month is not None,
                self.price_per_8_lessons is not None,
                self.extra_conditions,
                self.additional_info,
                self.price_from is not None,
                self.price_to is not None,
            )
        )

    @property
    def has_coordinates(self) -> bool:
        return self.lat is not None and self.lng is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_map_ready(self) -> bool:
        return self.is_active and self.status == self.STATUS_PUBLISHED and not self.is_deleted and self.has_coordinates

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
        source = self.name_ru or self.name or self.name_en or self.name_az or "place"
        base = slugify(source, allow_unicode=True) or "place"
        candidate = base
        idx = 2
        while Place.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base}-{idx}"
            idx += 1
        return candidate

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._build_unique_slug()
        super().save(*args, **kwargs)

    def refresh_rating_stats(self):
        # We import PlaceReview inside to prevent circular dependency if Review is moved to review.py
        # Actually PlaceReview is now in review.py. We need to be careful.
        # But `self.reviews.filter(...)` works perfectly because of related_name!
        from .review import PlaceReview
        stats = self.reviews.filter(is_approved=True, status=PlaceReview.STATUS_APPROVED).aggregate(avg=Avg("rating"), cnt=Count("id"))
        self.rating_avg = float(stats.get("avg") or 0)
        self.rating_count = int(stats.get("cnt") or 0)
        self.save(update_fields=["rating_avg", "rating_count"])

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Место")
        verbose_name_plural = _("Места")


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
    address = models.CharField(_("Адрес"), max_length=255, blank=True, default="")
    phone = models.CharField(_("Телефон / WhatsApp"), max_length=50, blank=True, default="")
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True, default="")
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
        if lang == "en":
            return self.description_en or self.description_az or self.description_ru or ""
        if lang == "ru":
            return self.description_ru or self.description_az or self.description_en or ""
        return self.description_az or self.description_ru or self.description_en or ""

    def address_i18n(self, lang=None):
        return _localize_public_address(self.address, self._normalize_lang(lang))

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
        source = self.name_az or self.name_ru or self.name_en or self.name or "event"
        base = slugify(source, allow_unicode=True) or "event"
        candidate = base
        idx = 2
        while Event.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base}-{idx}"
            idx += 1
        return candidate

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
                condition=~Q(session_key=""),
                name="unique_place_like_per_session",
            ),
            models.UniqueConstraint(
                fields=("place", "user"),
                condition=Q(user__isnull=False),
                name="unique_place_like_per_user",
            ),
        ]
        verbose_name = _("Лайк")
        verbose_name_plural = _("Лайки")

    def __str__(self):
        return f"{self.place_id}:{self.session_key}"


class PlaceReviewsByClub(Place):
    class Meta:
        proxy = True
        verbose_name = _("Рейтинг места")
        verbose_name_plural = _("Рейтинги мест")
