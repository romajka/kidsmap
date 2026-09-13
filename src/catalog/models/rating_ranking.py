from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class RatingRankingCalibration(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Черновик")
        ACTIVE = "active", _("Активна")
        RETIRED = "retired", _("Архивная")

    version = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    prior_mean = models.DecimalField(max_digits=7, decimal_places=5)
    prior_weight = models.DecimalField(max_digits=9, decimal_places=4)
    population_review_count = models.PositiveIntegerField()
    population_place_count = models.PositiveIntegerField()
    population_rating_sum = models.PositiveBigIntegerField()
    population_rating_sum_squares = models.PositiveBigIntegerField()
    population_standard_deviation = models.DecimalField(max_digits=7, decimal_places=5)
    confidence_z = models.DecimalField(max_digits=6, decimal_places=4)
    margin_stars = models.DecimalField(max_digits=5, decimal_places=3)
    source_cutoff = models.DateTimeField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activated_rating_calibrations",
    )

    class Meta:
        ordering = ("-version",)
        verbose_name = _("Калибровка сортировки по рейтингу")
        verbose_name_plural = _("Калибровки сортировки по рейтингу")
        constraints = [
            models.UniqueConstraint(
                fields=("status",),
                condition=Q(status="active"),
                name="unique_active_rating_calibration",
            ),
            models.CheckConstraint(
                condition=Q(prior_mean__gte=1) & Q(prior_mean__lte=5),
                name="rating_calibration_mean_range",
            ),
            models.CheckConstraint(
                condition=Q(prior_weight__gt=0),
                name="rating_calibration_weight_positive",
            ),
            models.CheckConstraint(
                condition=Q(population_review_count__gte=30) & Q(population_place_count__gte=10),
                name="rating_calibration_population_minimum",
            ),
            models.CheckConstraint(
                condition=Q(population_rating_sum__gt=0) & Q(population_rating_sum_squares__gt=0),
                name="rating_calibration_sums_positive",
            ),
            models.CheckConstraint(
                condition=Q(population_standard_deviation__gte=0),
                name="rating_calibration_stddev_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(confidence_z__gt=0) & Q(margin_stars__gt=0),
                name="rating_calibration_policy_positive",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="draft", activated_at__isnull=True)
                    | Q(status__in=("active", "retired"), activated_at__isnull=False)
                ),
                name="rating_calibration_activation_time",
            ),
        ]

    def clean(self):
        errors = {}
        if self.status in {self.Status.ACTIVE, self.Status.RETIRED}:
            if self.activated_at is None:
                errors["activated_at"] = _("Для активной или архивной версии нужна дата активации.")
            if self.activated_by_id is None and self._state.adding:
                errors["activated_by"] = _("Для активации нужен ответственный пользователь.")
        elif self.activated_at is not None or self.activated_by_id is not None:
            errors["status"] = _("Черновик не может содержать данные активации.")
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values("status").first()
            if previous and previous["status"] in {self.Status.ACTIVE, self.Status.RETIRED}:
                if not getattr(self, "_allow_calibration_transition", False):
                    raise ValidationError(_("Активные и архивные калибровки неизменяемы."))
            if previous and previous["status"] != self.status:
                if not getattr(self, "_allow_calibration_transition", False):
                    raise ValidationError(_("Статус калибровки меняется только через сервис активации."))
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status in {self.Status.ACTIVE, self.Status.RETIRED}:
            raise ValidationError(_("Активные и архивные калибровки нельзя удалять."))
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"v{self.version} ({self.status})"
