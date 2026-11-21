"""Report (and, with --apply, repair) organization data that breaks the rules.

Read-only by default. Repairs are limited to what is safe to do without a
human decision:

* published_without_approval -> moved back to draft (it was never public);
  with --approve-legacy it is approved instead, for rows staff already vetted.
* public_without_slug -> a readable URL is reserved.

Stale branch links and organizations without an owner are only reported: a
link must be confirmed again by its owners, never restored automatically.
"""
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from catalog.services import organization_state


class Command(BaseCommand):
    help = 'Diagnose organizations: unapproved "published" rows, missing slugs, stale branch links, missing owners.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Apply the safe repairs (default: dry run).')
        parser.add_argument('--approve-legacy', action='store_true',
                            help='With --apply: approve legacy published rows instead of returning them to draft.')
        parser.add_argument('--json', action='store_true', help='Print issues as JSON.')

    def handle(self, *args, apply=False, approve_legacy=False, json=False, **options):
        if approve_legacy and not apply:
            raise CommandError('--approve-legacy needs --apply.')
        from django.utils.translation import override
        with override('ru'):
            issues = organization_state.diagnose()
        if json:
            self.stdout.write(_dumps(issues))
        else:
            self._print(issues)
        if not apply:
            if issues:
                self.stdout.write(self.style.WARNING('Dry run: nothing changed. Re-run with --apply to repair.'))
            return
        fixed = self._repair(issues, approve_legacy=approve_legacy)
        self.stdout.write(self.style.SUCCESS(f'Repaired: {fixed}.'))

    def _print(self, issues):
        if not issues:
            self.stdout.write(self.style.SUCCESS('No organization issues found.'))
            return
        by_code = {}
        for row in issues:
            by_code.setdefault(row['code'], []).append(row)
        for code, rows in by_code.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f'{code} ({len(rows)})'))
            for row in rows:
                extra = ''
                if 'place_id' in row:
                    extra = f" place #{row['place_id']}: {row['reason']}"
                if row.get('has_pending_review'):
                    extra = ' (has a pending review — left for the moderator)'
                self.stdout.write(f"  #{row['organization_id']} {row['name']}{extra}")

    @transaction.atomic
    def _repair(self, issues, *, approve_legacy):
        from catalog.models import Organization
        fixed = 0
        for row in issues:
            if row['code'] == 'published_without_approval' and not row.get('has_pending_review'):
                query = Organization.objects.select_for_update().filter(
                    pk=row['organization_id'], status='published', approved_at__isnull=True, archived_at__isnull=True)
                org = query.first()
                if org is None:
                    continue
                if approve_legacy:
                    query.update(approved_at=timezone.now())
                    org.refresh_from_db()
                    organization_state.assign_public_slug(org)
                else:
                    query.update(status='draft')
                fixed += 1
            elif row['code'] == 'public_without_slug':
                org = Organization.objects.select_for_update().filter(pk=row['organization_id'], slug__isnull=True).first()
                if org is not None and organization_state.is_public(org):
                    organization_state.assign_public_slug(org)
                    fixed += 1
        return fixed


def _dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)
