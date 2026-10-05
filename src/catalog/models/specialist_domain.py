"""Person claims and explicit, historical organization employment consent."""
from django.conf import settings
from django.db import models
from django.db.models import Q, F


class SpecialistClaim(models.Model):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'
    STATUSES = ((PENDING, 'Pending'), (APPROVED, 'Approved'),
                (REJECTED, 'Rejected'), (WITHDRAWN, 'Withdrawn'))

    specialist = models.ForeignKey('catalog.Specialist', on_delete=models.PROTECT,
                                   related_name='person_claims')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                  on_delete=models.SET_NULL, related_name='specialist_claims')
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    version = models.PositiveIntegerField(default=1)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True, default='')
    previous_legacy_owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                              on_delete=models.SET_NULL, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('specialist', 'applicant'),
                                    condition=Q(status='pending', applicant__isnull=False),
                                    name='spec_claim_pending_applicant'),
            models.CheckConstraint(condition=Q(status__in=('pending', 'approved', 'rejected', 'withdrawn')),
                                   name='spec_claim_valid_status'),
            models.CheckConstraint(condition=Q(version__gte=1), name='spec_claim_positive_version'),
        ]


class SpecialistEmployment(models.Model):
    PENDING = 'pending'
    ACTIVE = 'active'
    CANCELLED = 'cancelled'
    STATUSES = ((PENDING, 'Pending'), (ACTIVE, 'Active'), (CANCELLED, 'Cancelled'))

    specialist = models.ForeignKey('catalog.Specialist', on_delete=models.PROTECT,
                                   related_name='employment_links')
    organization = models.ForeignKey('catalog.Organization', on_delete=models.PROTECT,
                                     related_name='specialist_employments')
    role = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    # Consent is bound to these identities, not an invitation, location or grant.
    person_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                    on_delete=models.SET_NULL, related_name='+')
    organization_owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                           on_delete=models.SET_NULL, related_name='+')
    organization_ownership_version = models.PositiveBigIntegerField(default=0)
    person_confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                            on_delete=models.SET_NULL, related_name='+')
    person_confirmed_at = models.DateTimeField(null=True, blank=True)
    organization_confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                                  on_delete=models.SET_NULL, related_name='+')
    organization_confirmed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                                   on_delete=models.SET_NULL, related_name='+')
    cancelled_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='+')
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('specialist', 'organization', 'role', 'start_date', 'end_date'),
                condition=Q(status__in=('pending', 'active')), nulls_distinct=False,
                name='spec_employment_exact_open_unique'),
            models.CheckConstraint(condition=Q(end_date__isnull=True) | Q(end_date__gte=F('start_date')),
                                   name='spec_employment_valid_period'),
            models.CheckConstraint(condition=~Q(role=''), name='spec_employment_role_required'),
            models.CheckConstraint(condition=Q(status__in=('pending', 'active', 'cancelled')),
                                   name='spec_employment_valid_status'),
            models.CheckConstraint(condition=Q(version__gte=1), name='spec_employment_positive_ver'),
            models.CheckConstraint(
                condition=~Q(status='active') | Q(person_confirmed_at__isnull=False,
                                                organization_confirmed_at__isnull=False),
                name='spec_employment_active_consents'),
        ]


class SpecialistEmploymentEvent(models.Model):
    employment = models.ForeignKey(SpecialistEmployment, on_delete=models.PROTECT,
                                   related_name='history')
    action = models.CharField(max_length=32)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                              on_delete=models.SET_NULL, related_name='+')
    version = models.PositiveIntegerField()
    role = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id',)
