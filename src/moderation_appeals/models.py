from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Appeal(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        SECOND_REVIEW = "second_review", "Second review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    appellant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    kind = models.CharField(max_length=60)
    source_id = models.PositiveBigIntegerField()
    source_version = models.CharField(max_length=180)
    title = models.TextField()
    original_reason = models.TextField(blank=True)
    original_decided_at = models.DateTimeField(null=True)
    original_reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    # Retain attribution if a staff account is later removed, without retaining
    # their name or email. A missing original actor is never assumed independent.
    original_reviewer_key = models.PositiveBigIntegerField(null=True)
    permission = models.CharField(max_length=120)
    explanation = models.TextField(max_length=4000)
    evidence_url = models.URLField(max_length=2000, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=Status, default=Status.SUBMITTED)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    reviewer_key = models.PositiveBigIntegerField(null=True)
    claimed_at = models.DateTimeField(null=True)
    final_reason = models.TextField(max_length=4000, blank=True)
    resolved_at = models.DateTimeField(null=True)

    class Meta:
        ordering = ("-submitted_at", "-pk")
        default_permissions = ()
        indexes = [models.Index(fields=("permission", "status", "submitted_at"), name="appeal_queue_by_scope")]
        constraints = [
            models.UniqueConstraint(fields=("kind", "source_id", "source_version"), name="appeal_unique_decision"),
            models.CheckConstraint(
                condition=Q(reviewer_key__isnull=True) | (
                    Q(original_reviewer_key__isnull=False) & ~Q(original_reviewer_key=F("reviewer_key"))
                    & ~Q(appellant_id=F("reviewer_key"))
                ), name="appeal_independent_reviewer",
            ),
            models.CheckConstraint(
                condition=Q(status="submitted", reviewer_key__isnull=True, claimed_at__isnull=True,
                            resolved_at__isnull=True, final_reason="")
                | Q(status="second_review", reviewer_key__isnull=False, claimed_at__isnull=False,
                    resolved_at__isnull=True, final_reason="")
                | (Q(status__in=("approved", "rejected"), reviewer_key__isnull=False,
                     claimed_at__isnull=False, resolved_at__isnull=False) & ~Q(final_reason="")),
                name="appeal_valid_lifecycle",
            ),
        ]


class AppealAssignment(models.Model):
    """Who held the independent review, including handover after access loss."""

    appeal = models.ForeignKey(Appeal, on_delete=models.CASCADE, related_name="assignments")
    reviewer_key = models.PositiveBigIntegerField()
    assigned_at = models.DateTimeField()

    class Meta:
        ordering = ("assigned_at", "pk")
        default_permissions = ()
