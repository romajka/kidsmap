"""Generate summary SEO health and audit reports for KidsMap.az.

Usage:
    python manage.py seo_report
    python manage.py seo_report --format=json
    python manage.py seo_report --format=markdown
"""

import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import SEOAuditRun, SEOChange, SEOIssue


class Command(BaseCommand):
    help = "Generate summary SEO health and audit report for KidsMap.az"

    def add_arguments(self, parser):
        parser.add_argument("--format", type=str, choices=["text", "json", "markdown"], default="text", help="Output format")

    def handle(self, *args, **options):
        latest_run = SEOAuditRun.objects.filter(status=SEOAuditRun.STATUS_COMPLETED).order_by("-finished_at").first()

        open_issues = SEOIssue.objects.filter(status=SEOIssue.STATUS_OPEN)
        critical_count = open_issues.filter(severity=SEOIssue.SEVERITY_CRITICAL).count()
        warning_count = open_issues.filter(severity=SEOIssue.SEVERITY_WARNING).count()

        level_a_count = open_issues.filter(level=SEOIssue.LEVEL_A).count()
        level_b_count = open_issues.filter(level=SEOIssue.LEVEL_B).count()
        level_c_count = open_issues.filter(level=SEOIssue.LEVEL_C).count()

        recent_changes = SEOChange.objects.filter(is_rolled_back=False).order_by("-applied_at")[:10]

        if options["format"] == "json":
            payload = {
                "generated_at": timezone.now().isoformat(),
                "latest_audit_run": {
                    "id": latest_run.pk if latest_run else None,
                    "started_at": latest_run.started_at.isoformat() if latest_run else None,
                    "total_urls": latest_run.total_urls if latest_run else 0,
                },
                "open_issues_summary": {
                    "total_open": open_issues.count(),
                    "critical": critical_count,
                    "warning": warning_count,
                    "level_a_safe_fixable": level_a_count,
                    "level_b_approval_required": level_b_count,
                    "level_c_manual_review_only": level_c_count,
                },
                "recent_changes_count": recent_changes.count(),
            }
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        if options["format"] == "markdown":
            self.stdout.write("# KidsMap SEO Health Report\n")
            self.stdout.write(f"**Report Generated:** {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if latest_run:
                self.stdout.write(f"- **Last Completed Audit:** #{latest_run.pk} at {latest_run.finished_at.strftime('%Y-%m-%d %H:%M')}")
                self.stdout.write(f"- **Total URLs Checked:** {latest_run.total_urls}\n")

            self.stdout.write("## Open Issues Breakdown")
            self.stdout.write(f"- **Critical Errors:** {critical_count}")
            self.stdout.write(f"- **Warnings:** {warning_count}")
            self.stdout.write(f"- **Level A (Safe Auto-Fix):** {level_a_count}")
            self.stdout.write(f"- **Level B (Approval Required):** {level_b_count}")
            self.stdout.write(f"- **Level C (Manual Review Only):** {level_c_count}\n")

            self.stdout.write("## Actions & Recommendations")
            if level_a_count > 0:
                self.stdout.write(f"- Run `python manage.py apply_seo_fixes --safe-only --apply` to resolve {level_a_count} safe Level A issue(s).")
            if level_b_count > 0:
                self.stdout.write(f"- Review {level_b_count} Level B proposal(s) in Admin Dashboard `/admin/catalog/seoissue/`.")
            if level_c_count > 0:
                self.stdout.write(f"- Manually review {level_c_count} Level C data quality issue(s).")
            return

        # Text format
        self.stdout.write(f"\n{'=' * 65}")
        self.stdout.write(f"KIDSMAP SEO HEALTH REPORT - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"{'=' * 65}\n")
        if latest_run:
            self.stdout.write(f"Last Completed Audit: Run #{latest_run.pk} ({latest_run.finished_at.strftime('%Y-%m-%d %H:%M')})")
            self.stdout.write(f"Total Scanned URLs:   {latest_run.total_urls}\n")

        self.stdout.write(f"OPEN ISSUES ({open_issues.count()} total):")
        self.stdout.write(f"  • Critical Errors:             {critical_count}")
        self.stdout.write(f"  • Warnings:                    {warning_count}")
        self.stdout.write(f"  • Level A (Safe Auto-Fixable): {level_a_count}")
        self.stdout.write(f"  • Level B (Approval Required): {level_b_count}")
        self.stdout.write(f"  • Level C (Manual Review Only):{level_c_count}\n")

        if recent_changes.exists():
            self.stdout.write("RECENT APPLIED CHANGES:")
            for change in recent_changes:
                self.stdout.write(f"  • #{change.pk}: {change.change_summary} [{change.applied_at.strftime('%Y-%m-%d %H:%M')}]")

        self.stdout.write(f"\n{'=' * 65}\n")
