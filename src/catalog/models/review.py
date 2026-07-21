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

from .place import Place


class PlaceReview(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Одобрен")),
        (STATUS_REJECTED, _("Отклонен")),
    )

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
    contains_profanity = models.BooleanField(_("Содержит скрытую лексику"), default=False)
    likes_count = models.PositiveIntegerField(_("Лайки"), default=0)
    dislikes_count = models.PositiveIntegerField(_("Дизлайки"), default=0)
    is_approved = models.BooleanField(_("Одобрен"), default=True)
    status = models.CharField(_("Статус модерации"), max_length=16, choices=STATUS_CHOICES, default=STATUS_APPROVED, db_index=True)
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("place", "user"),
                name="unique_place_review_per_user",
            ),
        ]
        verbose_name = _("Отзыв по кружку")
        verbose_name_plural = _("Отзывы по кружкам")

    def __str__(self):
        return f"{self.place_id}:{self.rating}"

    @property
    def popularity_score(self) -> int:
        return int(self.likes_count) - int(self.dislikes_count)

    def refresh_reaction_stats(self):
        stats = self.reactions.aggregate(
            likes=Count("id", filter=Q(value=1)),
            dislikes=Count("id", filter=Q(value=-1)),
        )
        self.likes_count = int(stats.get("likes") or 0)
        self.dislikes_count = int(stats.get("dislikes") or 0)
        self.save(update_fields=["likes_count", "dislikes_count"])

    def save(self, *args, **kwargs):
        self.is_anonymous = False
        if self.status == self.STATUS_APPROVED:
            self.is_approved = True
        elif self.status in {self.STATUS_PENDING, self.STATUS_REJECTED}:
            self.is_approved = False
        self.rating = min(max(int(self.rating or 1), 1), 5)
        super().save(*args, **kwargs)
        self.place.refresh_rating_stats()

    def delete(self, *args, **kwargs):
        place = self.place
        super().delete(*args, **kwargs)
        place.refresh_rating_stats()


    @property
    def author_name_i18n(self) -> str:
        return self.author_name or str(_("Гость"))

    @property
    def text_i18n(self) -> str:
        return self.text or ""


def sync_place_rating_stats(place_ids):
    """Recalculate rating_avg and rating_count for a list of Place IDs."""
    ids = {pid for pid in place_ids if pid}
    if not ids:
        return
    for place in Place.objects.filter(pk__in=ids):
        place.refresh_rating_stats()


@receiver(post_save, sender=PlaceReview)
def _on_place_review_saved(sender, instance, **kwargs):
    if instance.place_id:
        instance.place.refresh_rating_stats()


@receiver(post_delete, sender=PlaceReview)
def _on_place_review_deleted(sender, instance, **kwargs):
    if instance.place_id:
        instance.place.refresh_rating_stats()



class PlaceReviewReaction(models.Model):
    VALUE_DISLIKE = -1
    VALUE_LIKE = 1
    VALUE_CHOICES = (
        (VALUE_LIKE, _("Лайк")),
        (VALUE_DISLIKE, _("Дизлайк")),
    )

    review = models.ForeignKey(
        PlaceReview,
        on_delete=models.CASCADE,
        related_name="reactions",
        verbose_name=_("Отзыв"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="place_review_reactions",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    session_key_unique = models.CharField(max_length=64, null=True, blank=True, editable=False)
    value = models.SmallIntegerField(_("Реакция"), choices=VALUE_CHOICES, default=VALUE_LIKE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("review", "session_key_unique"),
                name="unique_place_review_reaction_per_session",
            ),
            models.UniqueConstraint(
                fields=("review", "user"),
                name="unique_place_review_reaction_per_user",
            ),
        ]
        verbose_name = _("Реакция на отзыв по кружку")
        verbose_name_plural = _("Реакции на отзывы по кружкам")

    def save(self, *args, **kwargs):
        self.value = self.VALUE_LIKE if int(self.value or self.VALUE_LIKE) > 0 else self.VALUE_DISLIKE
        self.session_key_unique = (self.session_key or "").strip() or None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "session_key" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"session_key_unique"}
        super().save(*args, **kwargs)
        self.review.refresh_reaction_stats()

    def delete(self, *args, **kwargs):
        review = self.review
        super().delete(*args, **kwargs)
        review.refresh_reaction_stats()


class SiteReview(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = (
        (STATUS_PENDING, _("На модерации")),
        (STATUS_APPROVED, _("Одобрен")),
        (STATUS_REJECTED, _("Отклонен")),
    )

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
    contains_profanity = models.BooleanField(_("Содержит скрытую лексику"), default=False)
    likes_count = models.PositiveIntegerField(_("Лайки"), default=0)
    dislikes_count = models.PositiveIntegerField(_("Дизлайки"), default=0)
    is_approved = models.BooleanField(_("Одобрен"), default=True)
    status = models.CharField(_("Статус модерации"), max_length=16, choices=STATUS_CHOICES, default=STATUS_APPROVED, db_index=True)
    rejection_reason = models.TextField(_("Причина отклонения"), blank=True, default="")
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user",),
                name="unique_site_review_per_user",
            ),
        ]
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")

    def __str__(self):
        who = self.author_name or _("Гость")
        return f"{who}: {self.rating}"

    _AUTHOR_NAME_TRANSLATIONS = {
        "Наталья М.": {
            "az": "Nataliya M.",
            "en": "Natalia M.",
        },
        "Рамин А.": {
            "az": "Ramin A.",
            "en": "Ramin A.",
        },
    }

    _TEXT_TRANSLATIONS = {
        "Хороший каталог, особенно полезны карта и быстрые фильтры по категориям.": {
            "az": "Yaxşı kataloqdur, xüsusilə xəritə və kateqoriyalar üzrə sürətli filtrlər faydalıdır.",
            "en": "A good catalog, especially useful for the map and quick category filters.",
        },
        "Сайт помогает быстро находить новые кружки в Баку, интерфейс понятный.": {
            "az": "Sayt Bakıda yeni dərnəkləri tez tapmağa kömək edir, interfeys aydındır.",
            "en": "The site helps you quickly find new clubs in Baku, and the interface is easy to understand.",
        },
    }

    @staticmethod
    def _localized_demo_value(raw_value: str, translations: dict[str, dict[str, str]]) -> str:
        language = (get_language() or "ru").split("-", 1)[0]
        if language == "ru":
            return raw_value
        return translations.get(raw_value, {}).get(language, raw_value)

    @property
    def author_name_i18n(self) -> str:
        raw_value = str(_(self.author_name or "Гость"))
        return self._localized_demo_value(raw_value, self._AUTHOR_NAME_TRANSLATIONS)

    @property
    def text_i18n(self) -> str:
        raw_value = str(_(self.text or ""))
        return self._localized_demo_value(raw_value, self._TEXT_TRANSLATIONS)

    @property
    def popularity_score(self) -> int:
        return int(self.likes_count) - int(self.dislikes_count)

    def refresh_reaction_stats(self):
        stats = self.reactions.aggregate(
            likes=Count("id", filter=Q(value=1)),
            dislikes=Count("id", filter=Q(value=-1)),
        )
        self.likes_count = int(stats.get("likes") or 0)
        self.dislikes_count = int(stats.get("dislikes") or 0)
        self.save(update_fields=["likes_count", "dislikes_count"])

    def save(self, *args, **kwargs):
        self.is_anonymous = False
        if self.status == self.STATUS_APPROVED:
            self.is_approved = True
        elif self.status in {self.STATUS_PENDING, self.STATUS_REJECTED}:
            self.is_approved = False
        self.rating = min(max(int(self.rating or 1), 1), 5)
        super().save(*args, **kwargs)


class SiteReviewReaction(models.Model):
    VALUE_DISLIKE = -1
    VALUE_LIKE = 1
    VALUE_CHOICES = (
        (VALUE_LIKE, _("Лайк")),
        (VALUE_DISLIKE, _("Дизлайк")),
    )

    review = models.ForeignKey(
        SiteReview,
        on_delete=models.CASCADE,
        related_name="reactions",
        verbose_name=_("Отзыв о сайте"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="site_review_reactions",
        verbose_name=_("Пользователь"),
        null=True,
        blank=True,
    )
    session_key = models.CharField(_("Сессия"), max_length=64, blank=True, default="", db_index=True)
    session_key_unique = models.CharField(max_length=64, null=True, blank=True, editable=False)
    value = models.SmallIntegerField(_("Реакция"), choices=VALUE_CHOICES, default=VALUE_LIKE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(_("Обновлено"), auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("review", "session_key_unique"),
                name="unique_site_review_reaction_per_session",
            ),
            models.UniqueConstraint(
                fields=("review", "user"),
                name="unique_site_review_reaction_per_user",
            ),
        ]
        verbose_name = _("Реакция на отзыв о сайте")
        verbose_name_plural = _("Реакции на отзывы о сайте")

    def save(self, *args, **kwargs):
        self.value = self.VALUE_LIKE if int(self.value or self.VALUE_LIKE) > 0 else self.VALUE_DISLIKE
        self.session_key_unique = (self.session_key or "").strip() or None
        update_fields = kwargs.get("update_fields")
        if update_fields is not None and "session_key" in update_fields:
            kwargs["update_fields"] = set(update_fields) | {"session_key_unique"}
        super().save(*args, **kwargs)
        self.review.refresh_reaction_stats()

    def delete(self, *args, **kwargs):
        review = self.review
        super().delete(*args, **kwargs)
        review.refresh_reaction_stats()
