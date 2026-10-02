"""Service-only workflow inbox and durable email intents, separate from subscriptions."""
from django.conf import settings
from django.db import models
from django.db.models import Q


class WorkflowNotification(models.Model):
    event_kind = models.CharField(max_length=48)
    entity_type = models.CharField(max_length=48)
    entity_id = models.PositiveBigIntegerField()
    entity_version = models.PositiveBigIntegerField()
    recipient_key = models.CharField(max_length=80)
    recipient_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='workflow_notifications')
    recipient_email = models.EmailField(blank=True, default='')
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event_kind', 'entity_type', 'entity_id',
                'entity_version', 'recipient_key'], name='workflow_event_recipient_unique'),
            models.CheckConstraint(condition=Q(entity_id__gte=1, entity_version__gte=1),
                name='workflow_event_positive_identity'),
        ]
        indexes = [models.Index(fields=['recipient_user', '-created_at'], name='workflow_inbox_user_created')]


class EmailOutbox(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        RETRY = 'retry'
        SENT = 'sent'
        SUPPRESSED = 'suppressed'
        FAILED = 'failed'

    notification = models.OneToOneField(WorkflowNotification, on_delete=models.CASCADE,
        related_name='email_outbox')
    recipient_email = models.EmailField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=32, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(attempts__lte=5), name='workflow_outbox_attempt_cap')]
        indexes = [models.Index(fields=['status', 'next_attempt_at', 'id'], name='workflow_outbox_due')]
