from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy


class VolunteerPlaceRevision(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Черновик")
        PENDING = "pending", pgettext_lazy("volunteer admin", "На проверке")
        APPROVED = "approved", _("Одобрено")
        REJECTED = "rejected", _("Нужны исправления")
        DECLINED = "declined", _("Отклонено")

    place = models.OneToOneField("catalog.Place", on_delete=models.CASCADE, null=True, blank=True, related_name="volunteer_revision")
    organization = models.OneToOneField("catalog.Organization", on_delete=models.CASCADE, null=True, blank=True, related_name="content_revision")
    program = models.OneToOneField("catalog.Program", on_delete=models.CASCADE, null=True, blank=True, related_name="content_revision")
    activity = models.OneToOneField("catalog.Activity", on_delete=models.CASCADE, null=True, blank=True, related_name="content_revision")
    offering_group = models.OneToOneField("catalog.OfferingGroup", on_delete=models.CASCADE, null=True, blank=True, related_name="content_revision")
    schema_version = models.PositiveIntegerField(default=1)
    base_content_version = models.PositiveBigIntegerField(default=1)
    dependencies = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="volunteer_revisions")
    payload = models.JSONField(default=dict)
    base_snapshot = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    version = models.PositiveIntegerField(default=1)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_volunteer_revisions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    needs_changes_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        from catalog.services.moderation_sla import prepare_moderation_save
        prepare_moderation_save(self, kwargs)
        super().save(*args, **kwargs)

    class Meta:
        constraints = [models.CheckConstraint(condition=(
            models.Q(place__isnull=False, organization__isnull=True, program__isnull=True, activity__isnull=True, offering_group__isnull=True)
            | models.Q(place__isnull=True, organization__isnull=False, program__isnull=True, activity__isnull=True, offering_group__isnull=True)
            | models.Q(place__isnull=True, organization__isnull=True, program__isnull=False, activity__isnull=True, offering_group__isnull=True)
            | models.Q(place__isnull=True, organization__isnull=True, program__isnull=True, activity__isnull=False, offering_group__isnull=True)
            | models.Q(place__isnull=True, organization__isnull=True, program__isnull=True, activity__isnull=True, offering_group__isnull=False)
        ), name="publication_revision_one_target"), models.CheckConstraint(condition=models.Q(schema_version__gte=1, base_content_version__gte=1), name="publication_revision_versions_positive")]
        verbose_name = _("Изменения волонтёра")
        verbose_name_plural = _("Изменения волонтёров")

    def __str__(self):
        return str(self.payload.get("name_az") or self.place_id)
