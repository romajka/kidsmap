"""Operational conversion ledger; no private source payloads are stored here."""
from django.db import models
from django.db.models import Q


class ConversionRun(models.Model):
    plan_digest = models.CharField(max_length=64, unique=True)
    rule_version = models.PositiveIntegerField()
    entry_count = models.PositiveIntegerField()
    baseline_counts = models.JSONField(default=dict)
    checkpoint = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(checkpoint__gte=0), name='conversion_run_checkpoint_nonnegative')]


class ConversionMapping(models.Model):
    source_type = models.CharField(max_length=32)
    source_id = models.PositiveBigIntegerField()
    rule_version = models.PositiveIntegerField()
    piece_key = models.CharField(max_length=48)
    source_version = models.PositiveBigIntegerField(null=True, blank=True)
    source_fingerprint = models.CharField(max_length=64)
    target_type = models.CharField(max_length=32, blank=True)
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    state = models.CharField(max_length=16, choices=[('applied', 'applied'), ('manual_review', 'manual_review')])
    reason_code = models.CharField(max_length=48)
    run = models.ForeignKey(ConversionRun, on_delete=models.PROTECT, related_name='mappings')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('source_type', 'source_id', 'rule_version', 'piece_key'), name='conversion_piece_unique'),
            models.CheckConstraint(condition=(Q(state='applied', target_id__isnull=False) & ~Q(target_type='')) | Q(state='manual_review', target_type='', target_id__isnull=True), name='conversion_mapping_target_state'),
        ]
        indexes = [models.Index(fields=('state', 'reason_code'), name='conversion_review_idx')]
