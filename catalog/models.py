from django.db import models
from django.db.models import Avg, Count, Q
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.utils.text import slugify
from django.urls import reverse
from django.utils import timezone


class Place(models.Model):
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
    category = models.CharField(_("Категория"), max_length=10, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(_("Подкатегория"), max_length=255, blank=True)

    age_from = models.PositiveSmallIntegerField(_("Возраст от"), null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(_("Возраст до"), null=True, blank=True)

    district = models.CharField(_("Район"), max_length=100, blank=True)
    metro = models.CharField(_("Метро"), max_length=100, blank=True)
    address = models.CharField(_("Адрес"), max_length=255, blank=True)

    phone1 = models.CharField(_("Телефон 1"), max_length=50, blank=True)
    cover_photo = models.FileField(_("Фото для шапки"), upload_to="places/covers/", blank=True, null=True)
    photo = models.FileField(_("Фото"), upload_to="places/", blank=True, null=True)
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)
    website = models.URLField(_("Сайт"), blank=True)
    schedule = models.TextField(_("Расписание"), blank=True)
    is_temporary = models.BooleanField(_("Временное мероприятие"), default=False)
    temporary_start = models.DateTimeField(_("Начало мероприятия"), null=True, blank=True)
    temporary_end = models.DateTimeField(_("Окончание мероприятия"), null=True, blank=True)
    lat = models.FloatField(_("Широта"), null=True, blank=True)
    lng = models.FloatField(_("Долгота"), null=True, blank=True)

    price_from = models.IntegerField(_("Цена от"), null=True, blank=True)
    price_to = models.IntegerField(_("Цена до"), null=True, blank=True)
    likes_count = models.PositiveIntegerField(_("Лайки"), default=0)
    rating_avg = models.FloatField(_("Средний рейтинг"), default=0)
    rating_count = models.PositiveIntegerField(_("Количество отзывов"), default=0)

    is_active = models.BooleanField(_("Активно"), default=True)
    is_verified = models.BooleanField(_("Проверено"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or "ru"
        return lang.split("-")[0]

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

        add_file(self.cover_photo)
        add_file(self.photo)
        for item in self.gallery.order_by("order", "id"):
            add_file(item.image)
        return files

    def __str__(self):
        return self.name_i18n()

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
        stats = self.reviews.filter(is_approved=True).aggregate(avg=Avg("rating"), cnt=Count("id"))
        self.rating_avg = float(stats.get("avg") or 0)
        self.rating_count = int(stats.get("cnt") or 0)
        self.save(update_fields=["rating_avg", "rating_count"])

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Кружок/курс")
        verbose_name_plural = _("Кружки и курсы")


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


class PlaceReview(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="reviews", verbose_name=_("Место"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="place_reviews",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    author_name = models.CharField(_("Имя"), max_length=80, blank=True)
    is_anonymous = models.BooleanField(_("Анонимно"), default=False)
    rating = models.PositiveSmallIntegerField(_("Оценка"), default=5)
    text = models.TextField(_("Отзыв"))
    is_approved = models.BooleanField(_("Одобрен"), default=True)
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("place", "user"),
                condition=Q(user__isnull=False),
                name="unique_place_review_per_user",
            ),
        ]
        verbose_name = _("Отзыв по кружку")
        verbose_name_plural = _("Отзывы по кружкам")

    def __str__(self):
        return f"{self.place_id}:{self.rating}"

    def save(self, *args, **kwargs):
        self.rating = min(max(int(self.rating or 1), 1), 5)
        super().save(*args, **kwargs)
        self.place.refresh_rating_stats()

    def delete(self, *args, **kwargs):
        place = self.place
        super().delete(*args, **kwargs)
        place.refresh_rating_stats()


class SiteReview(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="site_reviews",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    author_name = models.CharField(_("Имя"), max_length=80, blank=True)
    is_anonymous = models.BooleanField(_("Анонимно"), default=False)
    rating = models.PositiveSmallIntegerField(_("Оценка"), default=5)
    text = models.TextField(_("Отзыв"), blank=True)
    is_approved = models.BooleanField(_("Одобрен"), default=True)
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                condition=Q(user__isnull=False),
                name="unique_site_review_per_user",
            ),
        ]
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")

    def __str__(self):
        who = _("Аноним") if self.is_anonymous else (self.author_name or _("Гость"))
        return f"{who}: {self.rating}"

    def save(self, *args, **kwargs):
        self.rating = min(max(int(self.rating or 1), 1), 5)
        super().save(*args, **kwargs)


class SiteSettings(models.Model):
    brand_name = models.CharField(_("Название бренда"), max_length=120, default="KidsMap")
    logo = models.FileField(
        _("Логотип"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется SVG или PNG, размер 256x256 px (минимум 128x128), до 500 KB."),
    )
    site_background_image = models.FileField(
        _("Фон сайта"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1920x1080 px, до 2 MB."),
    )
    home_hero_image = models.FileField(
        _("Фон главного баннера"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется JPG/WebP 1600x500 px, до 1 MB."),
    )
    contacts_text_ru = models.TextField(_("Контакты (RU)"), blank=True, default="")
    contacts_text_en = models.TextField(_("Контакты (EN)"), blank=True, default="")
    contacts_text_az = models.TextField(_("Контакты (AZ)"), blank=True, default="")
    about_text_ru = models.TextField(_("О проекте (RU)"), blank=True, default="")
    about_text_en = models.TextField(_("О проекте (EN)"), blank=True, default="")
    about_text_az = models.TextField(_("О проекте (AZ)"), blank=True, default="")
    empty_results_text_ru = models.CharField(_("Текст пустого результата (RU)"), max_length=255, blank=True, default="")
    empty_results_text_en = models.CharField(_("Текст пустого результата (EN)"), max_length=255, blank=True, default="")
    empty_results_text_az = models.CharField(_("Текст пустого результата (AZ)"), max_length=255, blank=True, default="")
    empty_results_image = models.FileField(
        _("Картинка пустого результата"),
        upload_to="site/",
        blank=True,
        null=True,
        help_text=_("Рекомендуется PNG/WebP 600x400 px, до 500 KB."),
    )
    footer_phone = models.CharField(_("Телефон в футере"), max_length=60, blank=True, default="")
    footer_email = models.EmailField(_("Email в футере"), blank=True, default="")
    footer_instagram = models.CharField(_("Instagram в футере"), max_length=255, blank=True, default="")
    footer_whatsapp = models.CharField(_("WhatsApp ссылка в футере"), max_length=255, blank=True, default="")
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    def _normalize_lang(self, lang):
        if not lang:
            lang = get_language() or "ru"
        return lang.split("-")[0]

    def _i18n_text(self, prefix, lang):
        lang = self._normalize_lang(lang)
        if lang == "en":
            return (getattr(self, f"{prefix}_en", "") or getattr(self, f"{prefix}_ru", "")).strip()
        if lang == "az":
            return (getattr(self, f"{prefix}_az", "") or getattr(self, f"{prefix}_ru", "")).strip()
        return getattr(self, f"{prefix}_ru", "").strip()

    def contacts_text_i18n(self, lang=None):
        return self._i18n_text("contacts_text", lang)

    def about_text_i18n(self, lang=None):
        return self._i18n_text("about_text", lang)

    def empty_results_text_i18n(self, lang=None):
        return self._i18n_text("empty_results_text", lang)

    def footer_instagram_url(self):
        value = (self.footer_instagram or "").strip()
        if not value:
            return ""
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith(("instagram.com/", "www.instagram.com/")):
            return f"https://{value}"
        if "instagram.com/" in value:
            return f"https://{value.lstrip('/')}"
        return f"https://instagram.com/{value.lstrip('@')}"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.order_by("id").first()
        if obj:
            return obj
        return cls.objects.create(
            brand_name="KidsMap",
            contacts_text_ru="Свяжитесь с нами по почте: kidsmap@example.com",
            contacts_text_en="Contact us by email: kidsmap@example.com",
            contacts_text_az="Bizimlə e-poçt vasitəsilə əlaqə saxlayın: kidsmap@example.com",
            about_text_ru="KidsMap — каталог детских кружков и секций в Баку.",
            about_text_en="KidsMap is a catalog of kids clubs and courses in Baku.",
            about_text_az="KidsMap Bakıda uşaqlar üçün dərnək və kurs kataloqudur.",
            empty_results_text_ru="Ничего не найдено.",
            empty_results_text_en="Nothing found.",
            empty_results_text_az="Heç nə tapılmadı.",
            footer_phone="+994 00 000 00 00",
            footer_email="kidsmap@example.com",
            footer_instagram="kidsmap",
        )

    class Meta:
        verbose_name = _("Настройка сайта")
        verbose_name_plural = _("Настройка сайта")

    def __str__(self):
        return self.brand_name or "Site settings"


class SiteBrandingSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Лого и бренд")
        verbose_name_plural = _("Лого и бренд")


class SiteAboutSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("О проекте")
        verbose_name_plural = _("О проекте")


class SiteContactsSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Контакты")
        verbose_name_plural = _("Контакты")


class SiteFooterSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Футер и соцсети")
        verbose_name_plural = _("Футер и соцсети")


class SiteEmptyStateSettings(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Пустой результат")
        verbose_name_plural = _("Пустой результат")


class SiteAnalytics(SiteSettings):
    class Meta:
        proxy = True
        verbose_name = _("Статистика")
        verbose_name_plural = _("Статистика")


class SiteVisit(models.Model):
    day = models.DateField(_("День"), db_index=True)
    session_key = models.CharField(_("Сессия"), max_length=64, db_index=True)
    hits = models.PositiveIntegerField(_("Просмотры"), default=1)
    first_path = models.CharField(_("Первый путь"), max_length=255, blank=True, default="")
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Посещение")
        verbose_name_plural = _("Посещения")
        constraints = [
            models.UniqueConstraint(
                fields=("day", "session_key"),
                name="unique_site_visit_per_day_session",
            ),
        ]
        ordering = ("-day", "-hits")

    def __str__(self):
        return f"{self.day} / {self.session_key} / {self.hits}"

    @classmethod
    def today(cls):
        return timezone.localdate()


class CatalogContentSettings(models.Model):
    districts_json = models.JSONField(_("Районы (JSON)"), default=list, blank=True)
    metro_stations_json = models.JSONField(_("Станции метро (JSON)"), default=list, blank=True)
    seo_pages_json = models.JSONField(_("SEO страницы (JSON)"), default=dict, blank=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.order_by("id").first()
        if obj:
            return obj
        return cls.objects.create()

    def districts(self):
        if isinstance(self.districts_json, list) and self.districts_json:
            return self.districts_json
        from .content_data import BAKU_DISTRICTS

        return BAKU_DISTRICTS

    def metro_stations(self):
        if isinstance(self.metro_stations_json, list) and self.metro_stations_json:
            return self.metro_stations_json
        from .content_data import BAKU_METRO_STATIONS

        return BAKU_METRO_STATIONS

    def seo_pages(self):
        if isinstance(self.seo_pages_json, dict) and self.seo_pages_json:
            return self.seo_pages_json
        from .content_data import SEO_LANDING_PAGES

        return SEO_LANDING_PAGES

    class Meta:
        verbose_name = _("Контент каталога")
        verbose_name_plural = _("Контент каталога")

    def __str__(self):
        return _("Контент каталога")


class PlaceReviewsByClub(Place):
    class Meta:
        proxy = True
        verbose_name = _("Рейтинг кружка")
        verbose_name_plural = _("Рейтинг кружков")
