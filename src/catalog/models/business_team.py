"""Business grants are distinct from platform staff and concrete legacy teams."""
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone
from catalog.services.place_access import PLACE_ROLE_CHOICES


def invitation_expiry():
    return timezone.now() + timedelta(days=7)


class OrganizationGrant(models.Model):
    organization = models.ForeignKey('catalog.Organization', on_delete=models.CASCADE, related_name='team_grants')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization_team_grants')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organization_memberships')
    base_ownership_version = models.PositiveBigIntegerField()
    role = models.CharField(max_length=16, choices=PLACE_ROLE_CHOICES, default='EDITOR')
    actions = models.JSONField(default=list)
    scope = models.CharField(max_length=24, choices=[('selected_places','Selected places'),('all_network','All network')], default='selected_places')
    selected_places = models.ManyToManyField('catalog.Place', blank=True, related_name='selected_organization_grants')
    is_active = models.BooleanField(default=True, db_index=True)
    version = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization','member'], name='org_team_member_unique'),
            models.CheckConstraint(condition=~Q(owner=F('member')), name='org_team_not_owner'),
            models.CheckConstraint(condition=Q(version__gte=1,base_ownership_version__gte=1), name='org_team_versions_positive'),
            models.CheckConstraint(condition=Q(scope__in=['selected_places','all_network']), name='org_team_scope_known'),
        ]


class OrganizationTeamInvitation(models.Model):
    organization = models.ForeignKey('catalog.Organization', on_delete=models.CASCADE, related_name='team_invitations')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_organization_team_invitations')
    email = models.EmailField()
    role = models.CharField(max_length=16, choices=PLACE_ROLE_CHOICES, default='EDITOR')
    actions = models.JSONField(default=list)
    scope = models.CharField(max_length=24, choices=[('selected_places','Selected places'),('all_network','All network')])
    selected_place_ids = models.JSONField(default=list)
    scope_snapshot = models.JSONField(default=dict)
    base_ownership_version = models.PositiveBigIntegerField()
    base_grant_version = models.PositiveBigIntegerField(null=True, blank=True)
    status = models.CharField(max_length=16, default='PENDING', choices=[(s,s) for s in ('PENDING','ACCEPTED','REJECTED','CANCELED')])
    expires_at = models.DateTimeField(default=invitation_expiry)
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['organization','email'], condition=Q(status='PENDING'), name='org_team_pending_email_unique'),
            models.CheckConstraint(condition=Q(base_ownership_version__gte=1), name='org_invite_base_positive'),
            models.CheckConstraint(condition=Q(status__in=['PENDING','ACCEPTED','REJECTED','CANCELED']), name='org_invite_status_known'),
            models.CheckConstraint(condition=Q(scope__in=['selected_places','all_network']), name='org_invite_scope_known'),
        ]
