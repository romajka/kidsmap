"""Stage 11 local pilot. Plans contain source IDs and fingerprints: keep outside Git."""
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from catalog.services.catalog_conversion import apply_plan, build_plan


class Command(BaseCommand):
    help = 'Plan or apply the conservative Task 33 conversion on isolated PostgreSQL'

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument('--dry-run', action='store_true')
        mode.add_argument('--apply', action='store_true')
        parser.add_argument('--plan', required=True)
        parser.add_argument('--batch-size', type=int, default=50)
        parser.add_argument('--max-batches', type=int)

    def handle(self, *args, **options):
        if not settings.TESTING:
            raise CommandError('Stage 11 command requires DJANGO_TESTING=1 and isolated test settings')
        raw_path = Path(options['plan']).expanduser()
        path = raw_path.resolve()
        if not path.is_relative_to('/tmp') or raw_path.is_symlink():
            raise CommandError('Plan must be a regular path under /tmp')
        if options['dry_run']:
            if path.exists():
                raise CommandError('Refusing to overwrite an existing plan')
            plan = build_plan()
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'w', encoding='utf-8') as output:
                json.dump(plan, output, ensure_ascii=False, separators=(',', ':'))
            counts = {}
            for entry in plan['entries']:
                key = entry['reason_code']
                counts[key] = counts.get(key, 0) + 1
            self.stdout.write(json.dumps({'digest': plan['digest'], 'entry_count': len(plan['entries']), 'by_reason': counts}, sort_keys=True))
            return
        if not path.is_file():
            raise CommandError('Existing plan file required')
        if not 1 <= options['batch_size'] <= 500 or (options['max_batches'] is not None and options['max_batches'] < 1):
            raise CommandError('Invalid batch limit')
        try:
            plan = json.loads(path.read_text(encoding='utf-8'))
            result = apply_plan(plan, batch_size=options['batch_size'], max_batches=options['max_batches'])
        except (ValueError, KeyError, TypeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, sort_keys=True))
