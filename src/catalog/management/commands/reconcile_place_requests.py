"""Read-only by default; explicit snapshot-bound closure never grants ownership."""
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management.base import BaseCommand, CommandError

from catalog.models import PlaceOwnershipRequest
from catalog.services.place_request_reconciliation import apply_request, plan_request


class Command(BaseCommand):
    help = 'Classify redundant legacy place claims; explicit apply records an already fulfilled request without changing rights.'

    def add_arguments(self, parser):
        parser.add_argument('--request-id', dest='request_ids', action='append', type=int)
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--actor-id', type=int)
        parser.add_argument('--token')
        parser.add_argument('--note')

    def handle(self, *args, **options):
        ids = options['request_ids'] or []
        if any(pk < 1 for pk in ids) or not 1 <= options['limit'] <= 500:
            raise CommandError('Positive request IDs and a limit between 1 and 500 are required.')
        if options['apply']:
            if len(ids) != 1 or not options['actor_id'] or not options['token'] or not options['note']:
                raise CommandError('Apply requires one --request-id, --actor-id, --token and --note.')
            actor = get_user_model().objects.filter(pk=options['actor_id']).first()
            try:
                item = apply_request(actor=actor, request_id=ids[0], token=options['token'], note=options['note'])
            except (PermissionDenied, ValidationError, PlaceOwnershipRequest.DoesNotExist) as exc:
                raise CommandError('Reconciliation refused; reload the read-only plan and verify reviewer access.') from exc
            result = {'mode': 'applied', 'request_id': item.pk, 'status': item.status,
                      'ownership_changed': False, 'publication_changed': False}
        else:
            candidates = PlaceOwnershipRequest.objects.order_by('pk')
            candidates = candidates.filter(pk__in=ids) if ids else candidates.filter(status='PENDING', request_kind='CLAIM')
            selected = list(candidates.values_list('pk', flat=True)[:options['limit'] + 1])
            result = {'mode': 'dry_run', 'results': [plan_request(pk) for pk in selected[:options['limit']]],
                      'truncated': len(selected) > options['limit']}
        self.stdout.write(json.dumps(result, sort_keys=True))
