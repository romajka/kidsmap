"""Explicit service-mail activation; never modifies authentication email settings."""
import json

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import WorkflowEmailDeliveryPolicy
from catalog.services.workflow_email_delivery import preview


class Command(BaseCommand):
    help = 'Preview service mail policy; --enable starts with a fresh cutoff, --disable stops delivery.'

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument('--enable', action='store_true')
        group.add_argument('--disable', action='store_true')

    def handle(self, *args, **options):
        if options['enable'] or options['disable']:
            with transaction.atomic():
                item, _ = WorkflowEmailDeliveryPolicy.objects.get_or_create(pk=1)
                item = WorkflowEmailDeliveryPolicy.objects.select_for_update().get(pk=item.pk)
                if options['enable'] and not item.enabled:
                    item.enabled_at = timezone.now()
                    item.enabled = True
                    item.save(update_fields=['enabled', 'enabled_at'])
                elif options['disable']:
                    item.enabled = False
                    item.save(update_fields=['enabled'])
        item = WorkflowEmailDeliveryPolicy.objects.filter(pk=1).first()
        report = preview()
        report['enabled_at'] = item.enabled_at.isoformat() if item and item.enabled_at else None
        self.stdout.write(json.dumps(report, sort_keys=True))
