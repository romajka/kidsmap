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

    place = models.OneToOneField("catalog.Place", on_delete=models.CASCADE, related_name="volunteer_revision")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="volunteer_revisions")
    payload = models.JSONField(default=dict)
    base_snapshot = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    version = models.PositiveIntegerField(default=1)
    review_note = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_volunteer_revisions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Изменения волонтёра")
        verbose_name_plural = _("Изменения волонтёров")

    def __str__(self):
        return str(self.payload.get("name_az") or self.place_id)
