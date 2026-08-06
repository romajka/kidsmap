from django.core.management import call_command
from django.test import TestCase

from catalog.models import Place, SEOAuditRun, SEOChange, SEOIssue
from catalog.services.seo_audit_engine import SEOAuditEngine
from catalog.services.seo_fix_engine import SEOFixEngine
from catalog.testcases.utils import create_quality_place


class TestSEOAuditSystem(TestCase):
    def setUp(self):
        self.quality_place = create_quality_place(
            name="SEO Quality Club",
            name_az="SEO Keyfiyyətli Məkan",
            category="EDU",
            status=Place.STATUS_PUBLISHED,
        )

    def test_audit_engine_runs_and_creates_audit_run_record(self):
        engine = SEOAuditEngine(environment="test")
        run = engine.run_audit(limit=5)

        self.assertIsNotNone(run.pk)
        self.assertEqual(run.status, SEOAuditRun.STATUS_COMPLETED)
        self.assertGreaterEqual(run.total_urls, 1)

    def test_level_classification_of_issues(self):
        engine = SEOAuditEngine(environment="test")
        run = engine.run_audit(limit=5)

        issues = SEOIssue.objects.filter(audit_run=run)
        for issue in issues:
            if issue.level == SEOIssue.LEVEL_A:
                self.assertTrue(issue.is_auto_fixable)
                self.assertFalse(issue.requires_approval)
            elif issue.level == SEOIssue.LEVEL_B:
                self.assertTrue(issue.requires_approval)
                self.assertFalse(issue.is_auto_fixable)
            elif issue.level == SEOIssue.LEVEL_C:
                self.assertFalse(issue.is_auto_fixable)
                self.assertFalse(issue.requires_approval)

    def test_draft_places_are_excluded_from_sitemap_checks(self):
        draft_place = create_quality_place(
            name="Draft Place",
            name_az="Qaralama Məkan",
            category="EDU",
            status=Place.STATUS_DRAFT,
        )

        engine = SEOAuditEngine(environment="test")
        run = engine.run_audit(limit=10)

        sitemap_unwanted_issues = SEOIssue.objects.filter(audit_run=run, issue_code="sitemap_unwanted_urls")
        for issue in sitemap_unwanted_issues:
            self.assertNotIn(draft_place.get_absolute_url(), issue.current_value)

    def test_dry_run_safe_fixes_makes_zero_database_changes(self):
        # Create an artificial Level A issue
        issue = SEOIssue.objects.create(
            url="/sitemap.xml",
            issue_code="sitemap_duplicate_urls",
            severity=SEOIssue.SEVERITY_WARNING,
            level=SEOIssue.LEVEL_A,
            description="Duplicate sitemap test",
            status=SEOIssue.STATUS_OPEN,
            is_auto_fixable=True,
        )

        engine = SEOFixEngine()
        changes = engine.apply_safe_fixes(dry_run=True, issue_id=issue.pk)

        self.assertEqual(len(changes), 1)
        self.assertTrue(changes[0].change_summary.startswith("[DRY-RUN]"))
        self.assertEqual(SEOChange.objects.count(), 0)

        # Issue remains open in dry-run
        issue.refresh_from_db()
        self.assertEqual(issue.status, SEOIssue.STATUS_OPEN)

    def test_safe_fixes_only_applies_level_a_and_ignores_level_b_and_c(self):
        issue_a = SEOIssue.objects.create(
            url="/sitemap.xml",
            issue_code="sitemap_missing_published_places",
            severity=SEOIssue.SEVERITY_WARNING,
            level=SEOIssue.LEVEL_A,
            description="Missing published places in sitemap",
            status=SEOIssue.STATUS_OPEN,
            is_auto_fixable=True,
        )

        issue_b = SEOIssue.objects.create(
            url="/catalog/",
            issue_code="title_too_short",
            severity=SEOIssue.SEVERITY_WARNING,
            level=SEOIssue.LEVEL_B,
            description="Short title proposal",
            status=SEOIssue.STATUS_OPEN,
            requires_approval=True,
        )

        issue_c = SEOIssue.objects.create(
            url=self.quality_place.get_absolute_url(),
            issue_code="place_missing_coordinates",
            severity=SEOIssue.SEVERITY_WARNING,
            level=SEOIssue.LEVEL_C,
            description="Coordinates missing manual review",
            status=SEOIssue.STATUS_OPEN,
            place=self.quality_place,
        )

        engine = SEOFixEngine()
        changes = engine.apply_safe_fixes(dry_run=False)

        # Only Level A issue should be fixed
        issue_a.refresh_from_db()
        issue_b.refresh_from_db()
        issue_c.refresh_from_db()

        self.assertEqual(issue_a.status, SEOIssue.STATUS_FIXED)
        self.assertEqual(issue_b.status, SEOIssue.STATUS_OPEN)
        self.assertEqual(issue_c.status, SEOIssue.STATUS_OPEN)

        self.assertEqual(SEOChange.objects.count(), 1)

    def test_rollback_seo_change_restores_issue_state(self):
        issue = SEOIssue.objects.create(
            url=self.quality_place.get_absolute_url(),
            issue_code="place_detail_non_200",
            severity=SEOIssue.SEVERITY_WARNING,
            level=SEOIssue.LEVEL_A,
            description="Recalculate ratings auto-fix",
            status=SEOIssue.STATUS_OPEN,
            is_auto_fixable=True,
            place=self.quality_place,
        )

        engine = SEOFixEngine()
        changes = engine.apply_safe_fixes(dry_run=False, issue_id=issue.pk)
        self.assertEqual(len(changes), 1)

        change = changes[0]
        self.assertFalse(change.is_rolled_back)

        # Rollback
        rolled_back_change = engine.rollback_change(change.pk)
        self.assertTrue(rolled_back_change.is_rolled_back)

        issue.refresh_from_db()
        self.assertEqual(issue.status, SEOIssue.STATUS_OPEN)

    def test_management_commands_execution(self):
        # Test audit_seo
        call_command("audit_seo", limit=2, format="json")

        # Test apply_seo_fixes dry-run
        call_command("apply_seo_fixes", safe_only=True)

        # Test audit_internal_links
        call_command("audit_internal_links", limit_places=2)

        # Test audit_schema
        call_command("audit_schema")

        # Test seo_report
        call_command("seo_report", format="markdown")
