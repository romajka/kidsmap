"""Private working copies. These rows never participate in publication queries."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class ServerDraft(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='server_drafts')
    target_type = models.CharField(max_length=24)
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    materialized_place = models.ForeignKey('catalog.Place', on_delete=models.PROTECT, null=True, blank=True, related_name='origin_drafts')
    schema_version = models.PositiveIntegerField(default=1)
    source_version = models.PositiveBigIntegerField(default=0)
    version = models.PositiveBigIntegerField(default=1)
    fields = models.JSONField(default=dict)
    photo_name = models.CharField(max_length=255, blank=True, default='')
    saved_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(version__gte=1, schema_version__gte=1), name='server_draft_positive_versions'),
            models.CheckConstraint(condition=Q(target_id__isnull=True, source_version=0) | Q(target_id__isnull=False, source_version__gte=1), name='server_draft_source_for_target'),
        ]
        indexes = [models.Index(fields=['actor', 'target_type', 'target_id'], name='catalog_ser_actor_i_76e27e_idx')]
