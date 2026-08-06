"""Run comprehensive SEO audit on KidsMap.az.

Usage:
    python manage.py audit_seo
    python manage.py audit_seo --only-errors
    python manage.py audit_seo --url=/catalog/
    python manage.py audit_seo --place-id=10
    python manage.py audit_seo --language=ru
    python manage.py audit_seo --format=json
"""

import json

from django.core.management.base import BaseCommand

from catalog.models import SEOAuditRun
from catalog.services.seo_audit_engine import SEOAuditEngine


class Command(BaseCommand):
    help = "Run comprehensive SEO audit on KidsMap.az"

    def add_arguments(self, parser):
        parser.add_argument("--only-errors", action="store_true", help="Report critical errors only")
        parser.add_argument("--url", type=str, help="Audit a specific URL path")
        parser.add_argument("--place-id", type=int, help="Audit a specific place ID")
        parser.add_argument("--language", type=str, choices=["az", "ru", "en"], help="Target specific language")
        parser.add_argument("--page-type", type=str, help="Target specific page type")
        parser.add_argument("--format", type=str, choices=["text", "json"], default="text", help="Output format")
        parser.add_argument("--limit", type=int, help="Limit number of audited places")
        parser.add_argument("--external", action="store_true", help="Include external link verification")
        parser.add_argument("--skip-performance", action="store_true", help="Skip performance audits")

    def handle(self, *args, **options):
        engine = SEOAuditEngine()
        run = engine.run_audit(
            audit_type=SEOAuditRun.AUDIT_TYPE_FULL if not options["url"] else SEOAuditRun.AUDIT_TYPE_TECHNICAL,
            only_errors=options["only_errors"],
            target_url=options["url"],
            target_place_id=options["place_id"],
            target_language=options["language"],
            target_page_type=options["page_type"],
            limit=options["limit"],
            skip_performance=options["skip_performance"],
        )

        issues = run.issues.all()
        if options["format"] == "json":
            payload = {
                "run_id": run.pk,
                "status": run.status,
                "total_urls": run.total_urls,
                "error_count": run.error_count,
                "warning_count": run.warning_count,
                "auto_fix_count": run.auto_fix_count,
                "summary": run.summary_notes,
                "issues": [
                    {
                        "id": issue.pk,
                        "url": issue.url,
                        "issue_code": issue.issue_code,
                        "severity": issue.severity,
                        "level": issue.level,
                        "description": issue.description,
                        "current_value": issue.current_value,
                        "proposed_value": issue.proposed_value,
                    }
                    for issue in issues
                ],
            }
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        self.stdout.write(f"\n{'=' * 65}")
        self.stdout.write(f"SEO AUDIT REPORT (Run #{run.pk}) - {run.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"{'=' * 65}\n")
        self.stdout.write(f"Status: {run.status}")
        self.stdout.write(f"Tested URLs: {run.total_urls}")
        self.stdout.write(f"Critical Errors: {run.error_count}")
        self.stdout.write(f"Warnings: {run.warning_count}")
        self.stdout.write(f"Level A Safe Auto-Fixable: {run.auto_fix_count}\n")

        if not issues.exists():
            self.stdout.write(self.style.SUCCESS("✓ No SEO issues discovered! Site is healthy."))
            self.stdout.write(f"{'=' * 65}\n")
            return

        self.stdout.write(f"DISCOVERED ISSUES ({issues.count()}):")
        for issue in issues:
            level_tag = f"[{issue.level}]"
            sev_tag = f"[{issue.severity.upper()}]"
            if issue.severity == "critical":
                style = self.style.ERROR
            elif issue.severity == "warning":
                style = self.style.WARNING
            else:
                style = self.style.SUCCESS

            self.stdout.write(style(f"  {level_tag}{sev_tag} {issue.issue_code} @ {issue.url}"))
            self.stdout.write(f"     -> {issue.description}")
            if issue.current_value:
                self.stdout.write(f"     -> Current: {issue.current_value[:100]}")
            if issue.proposed_value:
                self.stdout.write(f"     -> Proposed: {issue.proposed_value[:100]}")

        self.stdout.write(f"\n{'=' * 65}\n")
