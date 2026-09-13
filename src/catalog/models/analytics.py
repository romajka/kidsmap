from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class AnalyticsActorExclusion(models.Model):
    REASON_STAFF_TEST = "staff_test"
    REASON_SUSPECTED_ABUSE = "suspected_abuse"
    REASON_PRIVACY = "privacy"
    REASON_CHOICES = (
        (REASON_STAFF_TEST, _("Тестовый или служебный аккаунт")),
        (REASON_SUSPECTED_ABUSE, _("Подозрение на накрутку")),
        (REASON_PRIVACY, _("Исключение по приватности")),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analytics_exclusions")
    reason_code = models.CharField(max_length=32, choices=REASON_CHOICES)
    actor_key_hash = models.CharField(max_length=80, blank=True, default="")
    starts_at = models.DateTimeField(default=timezone.now, db_index=True)
    ends_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="created_analytics_exclusions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=("user", "starts_at", "ends_at"), name="analytics_excl_active_idx")]
        verbose_name = _("Исключение из аналитики")
        verbose_name_plural = _("Исключения из аналитики")

    def is_active_at(self, value=None):
        value = value or timezone.now()
        return self.starts_at <= value and (self.ends_at is None or self.ends_at > value)


class AnalyticsIngressDaily(models.Model):
    day = models.DateField(default=timezone.localdate, unique=True)
    accepted_count = models.PositiveBigIntegerField(default=0)
    rejected_count = models.PositiveBigIntegerField(default=0)
    rate_limited_count = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Дневное качество аналитики")
        verbose_name_plural = _("Дневное качество аналитики")
