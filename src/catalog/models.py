import uuid

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


class UserProfile(models.Model):
    ROLE_USER = "USER"
    ROLE_OWNER = "OWNER"
    ROLE_CHOICES = [
        (ROLE_USER, _("Обычный пользователь")),
        (ROLE_OWNER, _("Владелец кружка / бизнеса")),
    ]
    OWNER_ROLE_MANAGER = "MANAGER"
    OWNER_ROLE_MODERATOR = "MODERATOR"
    OWNER_ROLE_EDITOR = "EDITOR"
    OWNER_ROLE_CHOICES = [
        (OWNER_ROLE_MANAGER, _("Owner manager")),
        (OWNER_ROLE_MODERATOR, _("Owner moderator")),
        (OWNER_ROLE_EDITOR, _("Owner editor")),
    ]

    OWNER_PERMISSION_VIEW_PLACES = "owner.places.view"
    OWNER_PERMISSION_EDIT_PLACES = "owner.places.edit"
    OWNER_PERMISSION_PUBLISH_PLACES = "owner.places.publish"
    OWNER_PERMISSION_VIEW_STATS = "owner.stats.view"
    OWNER_PERMISSION_MODERATE_REVIEWS = "owner.reviews.moderate"
    OWNER_PERMISSION_MANAGE_TEAM = "owner.team.manage"

    OWNER_PERMISSION_CHOICES = [
        (OWNER_PERMISSION_VIEW_PLACES, _("Просмотр своих карточек")),
        (OWNER_PERMISSION_EDIT_PLACES, _("Редактирование карточек")),
        (OWNER_PERMISSION_PUBLISH_PLACES, _("Публикация и перевод в черновик")),
        (OWNER_PERMISSION_VIEW_STATS, _("Просмотр статистики")),
        (OWNER_PERMISSION_MODERATE_REVIEWS, _("Модерация отзывов")),
        (OWNER_PERMISSION_MANAGE_TEAM, _("Управление участниками команды")),
    ]

    OWNER_ROLE_DEFAULT_PERMISSIONS = {
        OWNER_ROLE_MANAGER: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_EDIT_PLACES,
            OWNER_PERMISSION_PUBLISH_PLACES,
            OWNER_PERMISSION_VIEW_STATS,
            OWNER_PERMISSION_MODERATE_REVIEWS,
            OWNER_PERMISSION_MANAGE_TEAM,
        ),
        OWNER_ROLE_MODERATOR: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_VIEW_STATS,
            OWNER_PERMISSION_MODERATE_REVIEWS,
        ),
        OWNER_ROLE_EDITOR: (
            OWNER_PERMISSION_VIEW_PLACES,
            OWNER_PERMISSION_EDIT_PLACES,
        ),
    }

    GENDER_UNSPECIFIED = "U"
    GENDER_MALE = "M"
    GENDER_FEMALE = "F"
    GENDER_CHOICES = [
        (GENDER_UNSPECIFIED, _("Не указан")),
        (GENDER_MALE, _("Мужской")),
        (GENDER_FEMALE, _("Женский")),
    ]
    REGISTRATION_GENDER_CHOICES = [
        (GENDER_MALE, _("Мужской")),
        (GENDER_FEMALE, _("Женский")),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("Пользователь"),
    )
    role = models.CharField(
        _("Статус"),
        max_length=16,
        choices=ROLE_CHOICES,
        default=ROLE_USER,
        db_index=True,
    )
    owner_role = models.CharField(
        _("Роль владельца"),
        max_length=16,
        choices=OWNER_ROLE_CHOICES,
        default=OWNER_ROLE_MANAGER,
        help_text=_("Используется только для пользователей со статусом владельца."),
    )
    owner_permissions_override = models.JSONField(
        _("Переопределение прав владельца"),
        default=list,
        blank=True,
        help_text=_("Оставьте пустым, чтобы использовать права по умолчанию для роли владельца."),
    )
    phone = models.CharField(
        _("Телефон"),
        max_length=32,
        blank=True,
        default="",
    )
    gender = models.CharField(
        _("Пол"),
        max_length=1,
        choices=GENDER_CHOICES,
        default=GENDER_UNSPECIFIED,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлен"), auto_now=True)

    class Meta:
        verbose_name = _("Профиль пользователя")
        verbose_name_plural = _("Профили пользователей")

    def __str__(self):
        return f"{self.user}: {self.get_role_display()}"

    @classmethod
    def get_or_create_for_user(cls, user):
        profile, _ = cls.objects.get_or_create(user=user, defaults={"role": cls.ROLE_USER})
        return profile

    @property
    def is_owner(self) -> bool:
        return self.role == self.ROLE_OWNER

    @classmethod
    def owner_permission_codes(cls) -> set[str]:
        return {code for code, _ in cls.OWNER_PERMISSION_CHOICES}

    @classmethod
    def default_permissions_for_owner_role(cls, owner_role: str) -> set[str]:
        return set(
            cls.OWNER_ROLE_DEFAULT_PERMISSIONS.get(
                owner_role,
                cls.OWNER_ROLE_DEFAULT_PERMISSIONS[cls.OWNER_ROLE_EDITOR],
            )
        )

    def get_owner_permissions(self) -> set[str]:
        if self.role != self.ROLE_OWNER:
            return set()

        if self.owner_permissions_override:
            valid_codes = self.owner_permission_codes()
            return {
                code
                for code in self.owner_permissions_override
                if isinstance(code, str) and code in valid_codes
            }

        return self.default_permissions_for_owner_role(self.owner_role)

    def has_owner_permission(self, permission_code: str) -> bool:
        return permission_code in self.get_owner_permissions()


class UserEmailVerification(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_verification",
        verbose_name=_("Пользователь"),
    )
    email = models.EmailField(_("Email для подтверждения"), db_index=True)
    code_hash = models.CharField(_("Хэш кода"), max_length=255, blank=True, default="")
    expires_at = models.DateTimeField(_("Код действует до"), null=True, blank=True)
    resend_available_at = models.DateTimeField(_("Повторная отправка после"), null=True, blank=True)
    attempts_left = models.PositiveSmallIntegerField(_("Осталось попыток"), default=5)
    is_verified = models.BooleanField(_("Email подтвержден"), default=False, db_index=True)
    verified_at = models.DateTimeField(_("Дата подтверждения"), null=True, blank=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Подтверждение email")
        verbose_name_plural = _("Подтверждение email")
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.user} ({self.email})"


class PlaceOwnershipRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_APPROVED = "APPROVED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Одобрена")),
        (STATUS_REJECTED, _("Отклонена")),
    ]

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="ownership_requests",
        verbose_name=_("Кружок"),
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ownership_requests",
        verbose_name=_("Заявитель"),
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    note = models.TextField(
        _("Комментарий заявителя"),
        blank=True,
        default="",
    )
    moderation_note = models.TextField(
        _("Комментарий модератора"),
        blank=True,
        default="",
    )
    moderated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="moderated_ownership_requests",
        verbose_name=_("Модератор"),
        null=True,
        blank=True,
    )
    moderated_at = models.DateTimeField(_("Дата модерации"), null=True, blank=True)
    created_at = models.DateTimeField(_("Создана"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлена"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("place", "applicant"),
                condition=Q(status="PENDING"),
                name="unique_pending_ownership_request_per_user_place",
            ),
        ]
        verbose_name = _("Заявка на владение кружком")
        verbose_name_plural = _("Заявки на владение кружком")

    def __str__(self):
        return f"{self.place} ← {self.applicant} [{self.get_status_display()}]"

    @property
    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def apply_moderation(self, *, moderator, new_status: str, note: str = ""):
        if self.status != self.STATUS_PENDING:
            raise ValueError("Request is not pending")
        if new_status not in {self.STATUS_APPROVED, self.STATUS_REJECTED}:
            raise ValueError("Unsupported status transition")

        previous_status = self.status
        self.status = new_status
        self.moderated_by = moderator
        self.moderated_at = timezone.now()
        self.moderation_note = note or ""
        self.save(update_fields=["status", "moderated_by", "moderated_at", "moderation_note", "updated_at"])

        if new_status == self.STATUS_APPROVED and self.place.owner_id != self.applicant_id:
            self.place.owner = self.applicant
            self.place.save(update_fields=["owner", "updated_at"])

        PlaceOwnershipRequestAudit.log_event(
            ownership_request=self,
            actor=moderator,
            action=(
                PlaceOwnershipRequestAudit.ACTION_APPROVED
                if new_status == self.STATUS_APPROVED
                else PlaceOwnershipRequestAudit.ACTION_REJECTED
            ),
            from_status=previous_status,
            to_status=new_status,
            note=note or "",
        )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            PlaceOwnershipRequestAudit.log_event(
                ownership_request=self,
                actor=self.applicant,
                action=PlaceOwnershipRequestAudit.ACTION_CREATED,
                from_status="",
                to_status=self.status,
                note=self.note,
            )


class PlaceOwnershipRequestAudit(models.Model):
    ACTION_CREATED = "CREATED"
    ACTION_APPROVED = "APPROVED"
    ACTION_REJECTED = "REJECTED"
    ACTION_CHOICES = [
        (ACTION_CREATED, _("Создана")),
        (ACTION_APPROVED, _("Одобрена")),
        (ACTION_REJECTED, _("Отклонена")),
    ]

    ownership_request = models.ForeignKey(
        PlaceOwnershipRequest,
        on_delete=models.CASCADE,
        related_name="audit_entries",
        verbose_name=_("Заявка"),
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="ownership_request_audits",
        verbose_name=_("Кто выполнил"),
        null=True,
        blank=True,
    )
    action = models.CharField(_("Событие"), max_length=16, choices=ACTION_CHOICES)
    from_status = models.CharField(_("Статус до"), max_length=16, blank=True, default="")
    to_status = models.CharField(_("Статус после"), max_length=16, blank=True, default="")
    note = models.TextField(_("Комментарий"), blank=True, default="")
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _("Аудит заявки на владение")
        verbose_name_plural = _("Аудит заявок на владение")

    def __str__(self):
        return f"{self.ownership_request_id}: {self.get_action_display()}"

    @classmethod
    def log_event(
        cls,
        *,
        ownership_request: PlaceOwnershipRequest,
        actor,
        action: str,
        from_status: str = "",
        to_status: str = "",
        note: str = "",
    ):
        return cls.objects.create(
            ownership_request=ownership_request,
            actor=actor,
            action=action,
            from_status=from_status or "",
            to_status=to_status or "",
            note=note or "",
        )


class OwnerTeamMembership(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_members",
        verbose_name=_("Владелец команды"),
    )
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_memberships",
        verbose_name=_("Участник"),
    )
    role = models.CharField(
        _("Роль в команде"),
        max_length=16,
        choices=UserProfile.OWNER_ROLE_CHOICES,
        default=UserProfile.OWNER_ROLE_EDITOR,
        db_index=True,
    )
    is_active = models.BooleanField(_("Активна"), default=True, db_index=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_sent_memberships",
        verbose_name=_("Кто пригласил"),
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Участник команды владельца")
        verbose_name_plural = _("Участники команды владельца")
        constraints = [
            models.UniqueConstraint(fields=("owner", "member"), name="unique_owner_team_member"),
            models.CheckConstraint(condition=~Q(owner=models.F("member")), name="owner_team_member_not_owner"),
        ]
        ordering = ("owner_id", "member_id")

    def __str__(self):
        return f"{self.owner} -> {self.member} ({self.get_role_display()})"

    def get_permissions(self) -> set[str]:
        return UserProfile.default_permissions_for_owner_role(self.role)


class OwnerTeamInvitation(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ACCEPTED = "ACCEPTED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELED = "CANCELED"
    STATUS_CHOICES = [
        (STATUS_PENDING, _("Ожидает ответа")),
        (STATUS_ACCEPTED, _("Принято")),
        (STATUS_REJECTED, _("Отклонено")),
        (STATUS_CANCELED, _("Отменено")),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owner_team_invitations",
        verbose_name=_("Владелец команды"),
    )
    email = models.EmailField(_("Email приглашенного"), db_index=True)
    role = models.CharField(
        _("Роль в команде"),
        max_length=16,
        choices=UserProfile.OWNER_ROLE_CHOICES,
        default=UserProfile.OWNER_ROLE_EDITOR,
        db_index=True,
    )
    status = models.CharField(
        _("Статус"),
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    token = models.CharField(_("Токен приглашения"), max_length=64, unique=True, default="", blank=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_sent_invitations",
        verbose_name=_("Кто пригласил"),
        null=True,
        blank=True,
    )
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owner_team_received_invitations",
        verbose_name=_("Приглашенный пользователь"),
        null=True,
        blank=True,
    )
    responded_at = models.DateTimeField(_("Дата ответа"), null=True, blank=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        verbose_name = _("Приглашение в команду владельца")
        verbose_name_plural = _("Приглашения в команду владельца")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("owner", "email"),
                condition=Q(status="PENDING"),
                name="unique_pending_team_invitation_per_owner_email",
            ),
            models.CheckConstraint(condition=~Q(owner=models.F("invited_user")), name="owner_invited_user_not_owner"),
        ]

    def __str__(self):
        return f"{self.owner} -> {self.email} [{self.get_status_display()}]"

    @property
    def is_pending(self) -> bool:
        return self.status == self.STATUS_PENDING

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        self.email = (self.email or "").strip().lower()
        super().save(*args, **kwargs)


class PlaceChangeAudit(models.Model):
    SOURCE_OWNER_PANEL = "OWNER_PANEL"
    SOURCE_ADMIN = "ADMIN"
    SOURCE_SYSTEM = "SYSTEM"
    SOURCE_CHOICES = [
        (SOURCE_OWNER_PANEL, _("Кабинет владельца")),
        (SOURCE_ADMIN, _("Админка")),
        (SOURCE_SYSTEM, _("Система")),
    ]

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="change_audits",
        verbose_name=_("Кружок"),
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="place_change_audits",
        verbose_name=_("Кто изменил"),
        null=True,
        blank=True,
    )
    field_name = models.CharField(_("Поле"), max_length=64, db_index=True)
    old_value = models.TextField(_("Старое значение"), blank=True, default="")
    new_value = models.TextField(_("Новое значение"), blank=True, default="")
    source = models.CharField(
        _("Источник"),
        max_length=24,
        choices=SOURCE_CHOICES,
        default=SOURCE_OWNER_PANEL,
        db_index=True,
    )
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True)

    class Meta:
        verbose_name = _("Аудит изменения карточки")
        verbose_name_plural = _("Аудит изменений карточек")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.place_id}:{self.field_name}"


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
    home_hero_show_decor = models.BooleanField(_("Показывать декор в hero"), default=True)
    home_title_ru = models.CharField(_("Hero заголовок (RU)"), max_length=220, blank=True, default="")
    home_title_en = models.CharField(_("Hero заголовок (EN)"), max_length=220, blank=True, default="")
    home_title_az = models.CharField(_("Hero заголовок (AZ)"), max_length=220, blank=True, default="")
    home_subtitle_ru = models.CharField(_("Hero подзаголовок (RU)"), max_length=260, blank=True, default="")
    home_subtitle_en = models.CharField(_("Hero подзаголовок (EN)"), max_length=260, blank=True, default="")
    home_subtitle_az = models.CharField(_("Hero подзаголовок (AZ)"), max_length=260, blank=True, default="")
    home_search_label_ru = models.CharField(_("Hero подпись поиска (RU)"), max_length=220, blank=True, default="")
    home_search_label_en = models.CharField(_("Hero подпись поиска (EN)"), max_length=220, blank=True, default="")
    home_search_label_az = models.CharField(_("Hero подпись поиска (AZ)"), max_length=220, blank=True, default="")
    home_search_placeholder_ru = models.CharField(_("Hero placeholder поиска (RU)"), max_length=220, blank=True, default="")
    home_search_placeholder_en = models.CharField(_("Hero placeholder поиска (EN)"), max_length=220, blank=True, default="")
    home_search_placeholder_az = models.CharField(_("Hero placeholder поиска (AZ)"), max_length=220, blank=True, default="")
    home_cta_text_ru = models.CharField(_("Hero кнопка (RU)"), max_length=120, blank=True, default="")
    home_cta_text_en = models.CharField(_("Hero кнопка (EN)"), max_length=120, blank=True, default="")
    home_cta_text_az = models.CharField(_("Hero кнопка (AZ)"), max_length=120, blank=True, default="")
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

    def home_title_i18n(self, lang=None):
        return self._i18n_text("home_title", lang)

    def home_subtitle_i18n(self, lang=None):
        return self._i18n_text("home_subtitle", lang)

    def home_search_label_i18n(self, lang=None):
        return self._i18n_text("home_search_label", lang)

    def home_search_placeholder_i18n(self, lang=None):
        return self._i18n_text("home_search_placeholder", lang)

    def home_cta_text_i18n(self, lang=None):
        return self._i18n_text("home_cta_text", lang)

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
            contacts_text_ru="Свяжитесь с нами по почте: kidsmap.az@gmail.com",
            contacts_text_en="Contact us by email: kidsmap.az@gmail.com",
            contacts_text_az="Bizimlə e-poçt vasitəsilə əlaqə saxlayın: kidsmap.az@gmail.com",
            about_text_ru="KidsMap — каталог детских кружков и секций в Баку.",
            about_text_en="KidsMap is a catalog of kids clubs and courses in Baku.",
            about_text_az="KidsMap Bakıda uşaqlar üçün dərnək və kurs kataloqudur.",
            home_title_ru="Найдите кружок для ребёнка в Баку",
            home_title_en="Find a club for your child in Baku",
            home_title_az="Bakıda uşağınız üçün dərnək tapın",
            home_subtitle_ru="Спорт, творчество, музыка, образование — всё в одном месте.",
            home_subtitle_en="Sports, creativity, music, and education in one place.",
            home_subtitle_az="İdman, yaradıcılıq, musiqi, təhsil — hamısı bir yerdə.",
            home_search_label_ru="Искать кружок, курс или школу",
            home_search_label_en="Find a club, course, or school",
            home_search_label_az="Dərnək, kurs və ya məktəb axtarın",
            home_search_placeholder_ru="например english, ballet, lego",
            home_search_placeholder_en="for example english, ballet, lego",
            home_search_placeholder_az="məsələn english, ballet, lego",
            home_cta_text_ru="Начать поиск",
            home_cta_text_en="Start searching",
            home_cta_text_az="Axtarışa başla",
            empty_results_text_ru="Ничего не найдено.",
            empty_results_text_en="Nothing found.",
            empty_results_text_az="Heç nə tapılmadı.",
            footer_phone="+994 00 000 00 00",
            footer_email="kidsmap.az@gmail.com",
            footer_instagram="https://www.instagram.com/kidsmap.az/",
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


class FunnelEvent(models.Model):
    EVENT_CATALOG_SEARCH = "catalog_search"
    EVENT_CATALOG_FILTER = "catalog_filter"
    EVENT_PLACE_OPEN = "place_open"
    EVENT_CTA_CALL = "cta_call"
    EVENT_CTA_WHATSAPP = "cta_whatsapp"
    EVENT_CTA_INSTAGRAM = "cta_instagram"

    EVENT_CHOICES = (
        (EVENT_CATALOG_SEARCH, _("Поиск в каталоге")),
        (EVENT_CATALOG_FILTER, _("Применение фильтров")),
        (EVENT_PLACE_OPEN, _("Открытие карточки")),
        (EVENT_CTA_CALL, _("Клик: Позвонить")),
        (EVENT_CTA_WHATSAPP, _("Клик: WhatsApp")),
        (EVENT_CTA_INSTAGRAM, _("Клик: Instagram")),
    )

    event_type = models.CharField(_("Событие"), max_length=32, choices=EVENT_CHOICES, db_index=True)
    day = models.DateField(_("День"), default=timezone.localdate, db_index=True)
    path = models.CharField(_("Путь"), max_length=255, blank=True, default="")
    place = models.ForeignKey(
        Place,
        on_delete=models.SET_NULL,
        related_name="funnel_events",
        verbose_name=_("Кружок/курс"),
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="funnel_events",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    event_meta = models.JSONField(_("Данные"), default=dict, blank=True)
    created_at = models.DateTimeField(_("Создано"), auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("Событие воронки")
        verbose_name_plural = _("События воронки")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("day", "event_type")),
            models.Index(fields=("event_type", "created_at")),
        ]

    def __str__(self):
        return f"{self.day} / {self.event_type}"


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
