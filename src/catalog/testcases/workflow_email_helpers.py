"""Explicit mail policy setup for tests of existing immediate delivery contracts."""
from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone


def enable_delivery(test):
    from catalog.models import WorkflowEmailDeliveryPolicy
    WorkflowEmailDeliveryPolicy.objects.update_or_create(pk=1,
        defaults={'enabled': True, 'enabled_at': timezone.now() - timedelta(days=3)})
    # These legacy tests cover retry/content, not the collection window (tested separately).
    window = patch('catalog.services.workflow_email_policy.COLLECT_FOR', timedelta(0))
    window.start()
    test.addCleanup(window.stop)


def current_decision(user):
    from catalog.models import Organization, VolunteerPlaceRevision
    from catalog.services.workflow_notifications import emit
    organization = Organization.objects.create(owner=user, created_by=user, name_az='Synthetic current decision')
    revision = VolunteerPlaceRevision.objects.create(organization=organization, author=user, status='approved', version=2)
    return emit(kind='moderation_decision', entity_type='volunteer_revision', entity_id=revision.pk,
                version=revision.version, recipient_user=user,
                event_context={'decision': 'approved', 'target_type': 'organization', 'target_id': organization.pk})
