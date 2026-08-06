"""Apply Level A safe auto-fixes to KidsMap.az.

Usage:
    python manage.py apply_seo_fixes --safe-only           # Dry-run mode (default, no changes made)
    python manage.py apply_seo_fixes --safe-only --apply   # Real execution of Level A safe fixes
    python manage.py apply_seo_fixes --safe-only --issue-id=12 --apply
"""

from django.core.management.base import BaseCommand

from catalog.services.seo_fix_engine import SEOFixEngine


class Command(BaseCommand):
    help = "Apply Level A safe auto-fixes to KidsMap.az (Default is dry-run, use --apply to execute)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--safe-only",
            action="store_true",
            default=True,
            help="Enforce Level A safe auto-fixes only (Level B and C require admin approval or manual review)",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Execute actual changes to database and cache (without --apply, runs in dry-run mode)",
        )
        parser.add_argument(
            "--issue-id",
            type=int,
            help="Target a specific SEOIssue ID",
        )

    def handle(self, *args, **options):
        dry_run = not options["apply"]
        engine = SEOFixEngine()

        mode_str = "[DRY-RUN MODE]" if dry_run else "[REAL EXECUTION MODE]"
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(f"APPLYING SAFE SEO FIXES {mode_str}")
        self.stdout.write(f"{'=' * 60}\n")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in DRY-RUN mode. No database or cache changes will be applied.\n"
                                   "Pass '--apply' to execute changes.\n")
            )

        changes = engine.apply_safe_fixes(dry_run=dry_run, issue_id=options["issue_id"])

        if not changes:
            self.stdout.write(self.style.SUCCESS("✓ No open Level A safe auto-fixable issues found to process."))
            self.stdout.write(f"{'=' * 60}\n")
            return

        self.stdout.write(f"PROCESSED {len(changes)} SAFE FIX(ES):\n")
        for change in changes:
            prefix = "[DRY-RUN]" if dry_run else f"[CHANGE #{change.pk or 'NEW'}]"
            self.stdout.write(self.style.SUCCESS(f"  {prefix} {change.change_summary}"))
            if change.old_value:
                self.stdout.write(f"     Old: {change.old_value[:80]}")
            if change.new_value:
                self.stdout.write(f"     New: {change.new_value[:80]}")
            if change.recheck_result:
                self.stdout.write(f"     Recheck: {change.recheck_result}")

        self.stdout.write(f"\n{'=' * 60}\n")
