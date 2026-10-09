"""Durable previews/receipts. Neither ownership nor permission authority."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class OrganizationConnectionOperation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    organization = models.ForeignKey('catalog.Organization', on_delete=models.PROTECT)
    action = models.CharField(max_length=8, choices=[('connect', 'connect'), ('detach', 'detach')])
    relationship_kind = models.CharField(max_length=16)
    status = models.CharField(max_length=12, default='preview')
    idempotency_key = models.UUIDField(null=True, blank=True)
    fingerprint = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['actor', 'idempotency_key'], condition=Q(idempotency_key__isnull=False), name='org_connection_actor_key_unique'),
            models.CheckConstraint(condition=Q(action__in=['connect', 'detach']), name='org_connection_action_known'),
            models.CheckConstraint(condition=Q(status__in=['preview', 'running', 'completed']), name='org_connection_status_known'),
            models.CheckConstraint(condition=Q(relationship_kind__in=['business', 'informational']), name='org_connection_kind_known'),
        ]


class OrganizationConnectionItem(models.Model):
    operation = models.ForeignKey(OrganizationConnectionOperation, on_delete=models.CASCADE, related_name='items')
    place = models.ForeignKey('catalog.Place', on_delete=models.PROTECT)
    snapshot = models.JSONField(default=dict)
    decision = models.CharField(max_length=24)
    result = models.CharField(max_length=24, blank=True, default='')
    request = models.ForeignKey('catalog.OrganizationPlaceRequest', null=True, blank=True, on_delete=models.SET_NULL)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['place_id']
        constraints = [models.UniqueConstraint(fields=['operation', 'place'], name='org_connection_place_unique')]
