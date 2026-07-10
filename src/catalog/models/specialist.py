from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.utils.text import slugify

class Region(models.Model):
    """Справочник городов/регионов Азербайджана (Баку, Сумгаит и т.д.)"""
    key = models.CharField(_("Ключ"), max_length=50, primary_key=True)
    name_ru = models.CharField(_("Название (RU)"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255)
    name_en = models.CharField(_("Название (EN)"), max_length=255)

    class Meta:
        ordering = ("name_ru",)
        verbose_name = _("Регион")
        verbose_name_plural = _("Регионы")

    def name_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru

    def __str__(self):
        return self.name_i18n()


class District(models.Model):
    """Справочник районов городов (например, Ясамальский р-н для Баку)"""
    key = models.CharField(_("Ключ"), max_length=50, primary_key=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="districts", verbose_name=_("Регион"))
    name_ru = models.CharField(_("Название (RU)"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255)
    name_en = models.CharField(_("Название (EN)"), max_length=255)

    class Meta:
        ordering = ("name_ru",)
        verbose_name = _("Район")
        verbose_name_plural = _("Районы")

    def name_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru

    def __str__(self):
        return f"{self.region} · {self.name_i18n()}"


class MetroStation(models.Model):
    """Справочник станций Бакинского метрополитена"""
    key = models.CharField(_("Ключ"), max_length=50, primary_key=True)
    name_ru = models.CharField(_("Название (RU)"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255)
    name_en = models.CharField(_("Название (EN)"), max_length=255)

    class Meta:
        ordering = ("name_ru",)
        verbose_name = _("Станция метро")
        verbose_name_plural = _("Станции метро")

    def name_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru

    def __str__(self):
        return self.name_i18n()


class SpecialistSpecialization(models.Model):
    """Изолированный справочник специализаций (логопеды, психологи и т.д.)"""
    code = models.CharField(_("Код"), max_length=50, unique=True)
    name = models.CharField(_("Название (системное)"), max_length=255)
    name_ru = models.CharField(_("Название (RU)"), max_length=255)
    name_az = models.CharField(_("Название (AZ)"), max_length=255)
    name_en = models.CharField(_("Название (EN)"), max_length=255)
    is_active = models.BooleanField(_("Активна"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "name_ru")
        verbose_name = _("Специализация")
        verbose_name_plural = _("Специализации")

    def name_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"name_{lang}", self.name_ru) or self.name_ru

    def __str__(self):
        return self.name_i18n()


class Specialist(models.Model):
    FORMAT_ONLINE = "online"
    FORMAT_OFFLINE = "offline"
    FORMAT_BOTH = "both"
    FORMAT_CHOICES = [
        (FORMAT_ONLINE, _("Только онлайн")),
        (FORMAT_OFFLINE, _("Только очно")),
        (FORMAT_BOTH, _("Онлайн и очно")),
    ]

    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending"
    STATUS_PUBLISHED = "published"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_DRAFT, _("Черновик")),
        (STATUS_PENDING, _("На модерации")),
        (STATUS_PUBLISHED, _("Опубликован")),
        (STATUS_REJECTED, _("Отклонено")),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_specialists",
        verbose_name=_("Владелец профиля"),
        null=True,
        blank=True
    )
    name = models.CharField(_("Имя и фамилия"), max_length=255)
    name_alt = models.CharField(
        _("Альтернативное имя / Транслитерация"), 
        max_length=255, 
        blank=True, 
        default="", 
        help_text=_("Например, латиница/кириллица для поиска")
    )
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    photo = models.FileField(_("Фото профиля"), upload_to="specialists/photos/", blank=True, null=True)
    
    bio_ru = models.TextField(_("О себе (RU)"), blank=True, default="")
    bio_az = models.TextField(_("О себе (AZ)"), blank=True, default="")
    bio_en = models.TextField(_("О себе (EN)"), blank=True, default="")
    
    specializations = models.ManyToManyField(
        SpecialistSpecialization, 
        related_name="specialists", 
        verbose_name=_("Специализации")
    )
    
    consultation_format = models.CharField(
        _("Формат работы"), 
        max_length=10, 
        choices=FORMAT_CHOICES, 
        default=FORMAT_BOTH
    )
    
    experience_years = models.PositiveSmallIntegerField(_("Стаж (лет)"), null=True, blank=True)
    age_from = models.PositiveSmallIntegerField(_("Возраст от"), null=True, blank=True)
    age_to = models.PositiveSmallIntegerField(_("Возраст до"), null=True, blank=True)
    
    # Языки консультации
    language_az = models.BooleanField(_("Азербайджанский"), default=False)
    language_ru = models.BooleanField(_("Русский"), default=False)
    language_en = models.BooleanField(_("Английский"), default=False)
    
    # Стоимость и продолжительность
    price_from = models.PositiveIntegerField(_("Стоимость от (AZN)"), null=True, blank=True)
    price_to = models.PositiveIntegerField(_("Стоимость до (AZN)"), null=True, blank=True)
    duration_minutes = models.PositiveSmallIntegerField(_("Продолжительность приема (минут)"), null=True, blank=True)

    # Образование и опыт (подробно)
    education_ru = models.TextField(_("Образование (RU)"), blank=True, default="")
    education_az = models.TextField(_("Образование (AZ)"), blank=True, default="")
    education_en = models.TextField(_("Образование (EN)"), blank=True, default="")
    
    experience_info_ru = models.TextField(_("Опыт работы (RU)"), blank=True, default="")
    experience_info_az = models.TextField(_("Опыт работы (AZ)"), blank=True, default="")
    experience_info_en = models.TextField(_("Опыт работы (EN)"), blank=True, default="")
    
    phone = models.CharField(_("Телефон"), max_length=50, blank=True, default="")
    whatsapp = models.CharField(_("WhatsApp"), max_length=50, blank=True, default="")
    instagram = models.CharField(_("Instagram"), max_length=255, blank=True)
    website = models.URLField(_("Сайт"), blank=True)
    
    # Детерминированные агрегированные поля
    rating_avg = models.FloatField(_("Средний рейтинг"), default=0, editable=False)
    rating_count = models.PositiveIntegerField(_("Количество отзывов"), default=0, editable=False)
    
    is_active = models.BooleanField(_("Активен"), default=True)
    is_verified = models.BooleanField(_("Проверен"), default=False)
    status = models.CharField(
        _("Статус модерации"), 
        max_length=16, 
        choices=STATUS_CHOICES, 
        default=STATUS_DRAFT, 
        db_index=True
    )
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Специалист")
        verbose_name_plural = _("Специалисты")

    def refresh_rating_stats(self):
        """Перерасчет рейтинга специалиста только на основе одобренных отзывов"""
        from django.db.models import Avg, Count
        stats = self.reviews.filter(
            is_approved=True, 
            status=SpecialistReview.STATUS_APPROVED
        ).aggregate(avg=Avg("rating"), cnt=Count("id"))
        
        self.rating_avg = float(stats.get("avg") or 0.0)
        self.rating_count = int(stats.get("cnt") or 0)
        self.save(update_fields=["rating_avg", "rating_count"])

    def bio_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"bio_{lang}", self.bio_ru) or self.bio_ru

    def education_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"education_{lang}", self.education_ru) or self.education_ru

    def experience_info_i18n(self, lang=None):
        lang = (lang or get_language() or "az").split("-")[0]
        return getattr(self, f"experience_info_{lang}", self.experience_info_ru) or self.experience_info_ru

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("specialist_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True) or "specialist"
            # Проверка на уникальность
            candidate = self.slug
            idx = 2
            while Specialist.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{self.slug}-{idx}"
                idx += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def age_display(self) -> str:
        if self.age_from is not None and self.age_to is not None:
            return f"{self.age_from}-{self.age_to}"
        if self.age_from is not None:
            return f"{self.age_from}+"
        if self.age_to is not None:
            return str(self.age_to)
        return ""


class SpecialistPracticeLocation(models.Model):
    specialist = models.ForeignKey(
        Specialist, 
        on_delete=models.CASCADE, 
        related_name="practice_locations", 
        verbose_name=_("Специалист")
    )
    
    place = models.ForeignKey(
        "catalog.Place", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name=_("Детский центр (KidsMap)")
    )
    
    address = models.CharField(_("Собственный адрес/кабинет"), max_length=255, blank=True)
    
    region = models.ForeignKey(Region, on_delete=models.PROTECT, verbose_name=_("Город / Регион"), null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, verbose_name=_("Район"), null=True, blank=True)
    metro = models.ForeignKey(MetroStation, on_delete=models.SET_NULL, verbose_name=_("Метро"), null=True, blank=True)
    
    lat = models.FloatField(_("Широта"), null=True, blank=True)
    lng = models.FloatField(_("Долгота"), null=True, blank=True)
    
    schedule = models.TextField(_("Расписание (текст)"), blank=True)
    price_per_session = models.PositiveIntegerField(_("Стоимость приема (AZN)"), null=True, blank=True)
    phone = models.CharField(_("Телефон для записи в филиале"), max_length=50, blank=True)
    
    is_primary = models.BooleanField(_("Основной адрес"), default=False)
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        verbose_name = _("Локация практики")
        verbose_name_plural = _("Локации практики")

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.specialist.consultation_format in [Specialist.FORMAT_OFFLINE, Specialist.FORMAT_BOTH]:
            if not self.place and not self.address:
                raise ValidationError(_("Укажите детский центр KidsMap или адрес собственного кабинета."))
            if not self.region:
                raise ValidationError(_("Укажите регион/город для очной практики."))

    def __str__(self):
        if self.place:
            return f"{self.specialist} @ {self.place}"
        return f"{self.specialist} @ {self.address}"


class SpecialistScheduleDay(models.Model):
    WEEKDAY_CHOICES = (
        ("mon", _("Понедельник")),
        ("tue", _("Вторник")),
        ("wed", _("Среда")),
        ("thu", _("Четверг")),
        ("fri", _("Пятница")),
        ("sat", _("Суббота")),
        ("sun", _("Воскресенье")),
    )

    practice_location = models.ForeignKey(
        SpecialistPracticeLocation, 
        on_delete=models.CASCADE, 
        related_name="schedule_days", 
        verbose_name=_("Локация практики")
    )
    weekday = models.CharField(_("День недели"), max_length=3, choices=WEEKDAY_CHOICES)
    is_closed = models.BooleanField(_("Закрыто"), default=True)
    is_24_hours = models.BooleanField(_("24 часа"), default=False)
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("День расписания специалиста")
        verbose_name_plural = _("Дни расписания специалиста")
        constraints = [
            models.UniqueConstraint(fields=("practice_location", "weekday"), name="unique_spec_schedule_weekday"),
        ]

    def __str__(self):
        return f"{self.practice_location} · {self.get_weekday_display()}"


class SpecialistScheduleInterval(models.Model):
    schedule_day = models.ForeignKey(
        SpecialistScheduleDay,
        on_delete=models.CASCADE,
        related_name="intervals",
        verbose_name=_("День расписания"),
    )
    start_time = models.TimeField(_("Начало"))
    end_time = models.TimeField(_("Окончание"))
    order = models.PositiveSmallIntegerField(_("Порядок"), default=0)

    class Meta:
        ordering = ("order", "id")
        verbose_name = _("Интервал расписания специалиста")
        verbose_name_plural = _("Интервалы расписания специалиста")

    def __str__(self):
        return f"{self.schedule_day} · {self.start_time:%H:%M}-{self.end_time:%H:%M}"


class SpecialistDocument(models.Model):
    TYPE_IDENTITY = "identity"
    TYPE_DIPLOMA = "diploma"
    TYPE_CERTIFICATE = "certificate"
    TYPE_CHOICES = [
        (TYPE_IDENTITY, _("Удостоверение личности (приватно)")),
        (TYPE_DIPLOMA, _("Диплом")),
        (TYPE_CERTIFICATE, _("Сертификат")),
    ]

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Проверен")),
        (STATUS_REJECTED, _("Отклонен")),
    ]

    specialist = models.ForeignKey(
        Specialist, 
        on_delete=models.CASCADE, 
        related_name="documents", 
        verbose_name=_("Специалист")
    )
    
    document_type = models.CharField(_("Тип документа"), max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(_("Название / Описание документа"), max_length=255)
    
    file = models.FileField(_("Файл документа"), upload_to="protected_docs/specialists/")
    
    status = models.CharField(_("Статус проверки"), max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_published = models.BooleanField(
        _("Показывать в профиле"), 
        default=False, 
        help_text=_("Разрешить публичный показ диплома/сертификата после прохождения проверки")
    )
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Документ специалиста")
        verbose_name_plural = _("Документы специалиста")

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.name}"

    @property
    def is_verified(self):
        return self.status == self.STATUS_APPROVED

    @property
    def is_public(self):
        return self.is_published


class SpecialistReview(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Одобрен")),
        (STATUS_REJECTED, _("Отклонен")),
    )

    specialist = models.ForeignKey(
        Specialist, 
        on_delete=models.CASCADE, 
        related_name="reviews", 
        verbose_name=_("Специалист")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="specialist_reviews",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True
    )
    author_name = models.CharField(_("Имя автора"), max_length=80)
    rating = models.PositiveSmallIntegerField(_("Оценка (1-5)"), default=5)
    text = models.TextField(_("Текст отзыва"))
    is_approved = models.BooleanField(_("Одобрен"), default=False)
    status = models.CharField(
        _("Статус модерации"), 
        max_length=16, 
        choices=STATUS_CHOICES, 
        default=STATUS_PENDING, 
        db_index=True
    )
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Отзыв о специалисте")
        verbose_name_plural = _("Отзывы о специалистах")
        constraints = [
            models.UniqueConstraint(fields=("specialist", "user"), name="unique_specialist_review_per_user")
        ]

    def __str__(self):
        return f"{self.specialist_id}:{self.rating}"

    def save(self, *args, **kwargs):
        self.is_approved = (self.status == self.STATUS_APPROVED)
        super().save(*args, **kwargs)
        self.specialist.refresh_rating_stats()

    def delete(self, *args, **kwargs):
        specialist = self.specialist
        super().delete(*args, **kwargs)
        specialist.refresh_rating_stats()
