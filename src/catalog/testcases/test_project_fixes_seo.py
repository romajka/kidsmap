"""Behavioral regressions for the approved October 2026 SEO repairs."""
from unittest.mock import patch
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse

from catalog.models import SEOAuditRun, SEOChange, SEOIssue
from catalog.services.seo_audit_engine import SEOAuditEngine
from catalog.services.seo_fix_engine import SEOFixEngine
from catalog.testcases.utils import create_quality_place


class _FormParser(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.forms = []
        self.current_form = None
        self.action_selects = []
        self.feed(content.decode())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current_form = {**attrs, "fields": {}}
            self.forms.append(self.current_form)
        elif tag == "input" and self.current_form is not None:
            self.current_form["fields"][attrs.get("name")] = attrs.get("value")
        elif tag == "select" and attrs.get("name") == "action":
            self.action_selects.append(attrs)

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None


class SEOAdminBoundaryTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.staff = users.objects.create_user(username="seo_staff", is_staff=True)
        self.admin = users.objects.create_superuser(username="seo_admin", email="seo@example.test", password="synthetic")
        self.run = SEOAuditRun.objects.create(status="completed")

    def endpoint(self, name):
        return reverse("admin:catalog_seoauditrun_" + name)

    def test_staff_without_model_permissions_cannot_dispatch_custom_actions(self):
        self.client.force_login(self.staff)
        for action in ("run_now", "apply_fixes_now", "clear_history_now"):
            with self.subTest(action=action):
                self.assertEqual(self.client.post(self.endpoint(action)).status_code, 403)
        self.assertTrue(SEOAuditRun.objects.filter(pk=self.run.pk).exists())

    def test_superuser_get_never_dispatches_mutation(self):
        self.client.force_login(self.admin)
        for action in ("run_now", "apply_fixes_now", "clear_history_now"):
            with self.subTest(action=action):
                self.assertEqual(self.client.get(self.endpoint(action)).status_code, 405)
        self.assertTrue(SEOAuditRun.objects.filter(pk=self.run.pk).exists())

    def test_clear_history_requires_all_cascaded_delete_permissions(self):
        self.staff.user_permissions.add(Permission.objects.get(codename="delete_seoauditrun"))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.endpoint("clear_history_now")).status_code, 403)
        self.assertTrue(SEOAuditRun.objects.filter(pk=self.run.pk).exists())

    def test_running_audit_requires_permission_to_reconcile_old_issues(self):
        self.staff.user_permissions.add(*Permission.objects.filter(codename__in=("add_seoauditrun", "add_seoissue")))
        self.client.force_login(self.staff)
        self.assertEqual(self.client.post(self.endpoint("run_now")).status_code, 403)

    def test_authorized_staff_can_create_and_reconcile_audit(self):
        self.staff.user_permissions.add(*Permission.objects.filter(codename__in=("add_seoauditrun", "add_seoissue", "change_seoissue")))
        self.client.force_login(self.staff)
        with patch.object(SEOAuditEngine, "_get_page", return_value=HttpResponse(status=503)):
            self.assertEqual(self.client.post(self.endpoint("run_now")).status_code, 302)
        self.assertEqual(SEOAuditRun.objects.filter(status="completed").count(), 2)

    def test_csrf_protects_mutations_and_authorized_post_clears_history(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.endpoint("clear_history_now")).status_code, 403)
        response = client.get(reverse("admin:catalog_seoauditrun_changelist"))
        parser = _FormParser(response.content)
        form = next((form for form in parser.forms if form.get("action") == self.endpoint("clear_history_now")), None)
        self.assertIsNotNone(form)
        self.assertEqual(form.get("method", "").lower(), "post")
        token = form["fields"]["csrfmiddlewaretoken"]
        self.assertEqual(client.post(self.endpoint("clear_history_now"), {"csrfmiddlewaretoken": token}).status_code, 302)
        self.assertFalse(SEOAuditRun.objects.exists())

    def test_report_opens_and_escapes_issue_content(self):
        SEOIssue.objects.create(audit_run=self.run, url="/catalog/", issue_code="<b>code</b>", description='<img src=x onerror="alert(1)">')
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:catalog_seoauditrun_change", args=[self.run.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;img src=x onerror=")
        self.assertNotContains(response, '<img src=x onerror="alert(1)">')

    def test_view_only_staff_has_no_mutating_issue_or_change_actions(self):
        self.staff.user_permissions.add(*Permission.objects.filter(codename__in=("view_seoissue", "view_seochange")))
        self.client.force_login(self.staff)
        for model in ("seoissue", "seochange"):
            response = self.client.get(reverse(f"admin:catalog_{model}_changelist"))
            self.assertEqual(response.status_code, 200)
            parser = _FormParser(response.content)
            self.assertEqual(parser.action_selects, [])


class SEOAuditRetentionTests(TestCase):
    def issue(self, **kwargs):
        return SEOIssue.objects.create(url="/untested/", issue_code="missing_canonical", description="Existing observation", **kwargs)

    def test_partial_sitemap_audit_preserves_unrelated_and_orphan_history(self):
        issue = self.issue()
        engine = SEOAuditEngine(environment="test")
        with patch.object(engine, "_get_page", return_value=HttpResponse("unavailable", status=503)):
            engine.run_audit(audit_type="sitemap")
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_failed_audit_preserves_old_issues(self):
        issue = self.issue()
        engine = SEOAuditEngine(environment="test")
        with patch.object(engine, "_audit_sitemap_and_robots", side_effect=RuntimeError("synthetic scanner failure")):
            with self.assertRaises(RuntimeError):
                engine.run_audit()
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_successful_target_resolves_only_verified_missing_invariant(self):
        run = SEOAuditRun.objects.create()
        verified = SEOIssue.objects.create(audit_run=run, url="/checked/", language="az", issue_code="missing_canonical", description="Old missing canonical")
        unrelated = self.issue()
        engine = SEOAuditEngine(environment="test")
        with patch.object(engine, "_get_page", return_value=HttpResponse('<link rel="canonical" href="https://example.test/checked/">')):
            engine.run_audit(target_url="/checked/")
        verified.refresh_from_db()
        unrelated.refresh_from_db()
        self.assertEqual(verified.status, "resolved")
        self.assertEqual(unrelated.status, "open")

    def test_non_200_does_not_resolve_unchecked_metadata(self):
        issue = SEOIssue.objects.create(url="/checked/", language="az", issue_code="missing_canonical", description="Still unknown")
        engine = SEOAuditEngine(environment="test")
        with patch.object(engine, "_get_page", return_value=HttpResponse(status=404)):
            engine.run_audit(target_url="/checked/")
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_only_errors_filter_does_not_resolve_still_present_warning(self):
        issue = SEOIssue.objects.create(url="/checked/", language="az", issue_code="missing_canonical", description="Still missing", severity="warning")
        engine = SEOAuditEngine(environment="test")
        with patch.object(engine, "_get_page", return_value=HttpResponse("<title>A long enough title</title>")):
            engine.run_audit(target_url="/checked/", only_errors=True)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")


class SEOFixTruthTests(TestCase):
    def issue(self, code="missing_canonical", **kwargs):
        return SEOIssue.objects.create(url="/checked/", issue_code=code, description="Synthetic invariant", level="A", is_auto_fixable=True, **kwargs)

    def test_http_200_with_missing_canonical_remains_open(self):
        issue = self.issue()
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse("<title>Title</title>")):
            changes = engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")
        self.assertIn("missing_canonical", changes[0].recheck_result)
        self.assertFalse(changes[0].is_reversible)

    def test_http_404_cannot_be_fixed_metadata(self):
        issue = self.issue()
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse(status=404)):
            engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_invalid_sitemap_response_does_not_resolve_unchecked_duplicates(self):
        issue = self.issue("sitemap_duplicate_urls")
        issue.url = "/sitemap.xml"
        issue.save(update_fields=["url"])
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse("not XML")):
            engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_auto_fix_never_applies_an_issue_requiring_approval(self):
        issue = self.issue(requires_approval=True)
        self.assertEqual(SEOFixEngine().apply_safe_fixes(dry_run=False), [])
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")
        self.assertFalse(SEOChange.objects.exists())

    def test_supported_cache_refresh_marks_fixed_only_after_invariant_passes(self):
        issue = self.issue()
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse('<link rel="canonical" href="https://example.test/checked/">')):
            changes = engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "fixed")
        self.assertEqual(len(changes), 1)
        with self.assertRaises(ValueError):
            engine.rollback_change(changes[0].pk)

    def test_unsupported_issue_neither_changes_database_nor_claims_success(self):
        issue = self.issue("unknown_new_rule")
        changes = SEOFixEngine().apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")
        self.assertEqual(changes, [])
        self.assertFalse(SEOChange.objects.exists())

    def test_recheck_keeps_original_schema_page_type(self):
        issue = self.issue("missing_schema_json_ld", page_type="home")
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse('<link rel="canonical" href="https://example.test/">')):
            engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_invalid_schema_is_not_verified_when_all_schema_disappears(self):
        issue = self.issue("invalid_json_ld", page_type="home")
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse("<title>No schema anymore</title>")):
            engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_empty_breadcrumb_cannot_be_verified_against_invalid_json(self):
        issue = self.issue("empty_breadcrumb_schema", page_type="home")
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse('<script type="application/ld+json">invalid</script>')):
            engine.apply_safe_fixes(dry_run=False)
        issue.refresh_from_db()
        self.assertEqual(issue.status, "open")

    def test_metadata_repair_does_not_recalculate_unrelated_place_ratings(self):
        place = create_quality_place()
        type(place).objects.filter(pk=place.pk).update(rating_count=9, rating_avg=4.5)
        self.issue("invalid_json_ld", place=place)
        engine = SEOFixEngine()
        with patch.object(engine.client, "get", return_value=HttpResponse('<script type="application/ld+json">invalid</script>')):
            engine.apply_safe_fixes(dry_run=False)
        place.refresh_from_db()
        self.assertEqual((place.rating_count, place.rating_avg), (9, 4.5))


class SEOLegacyRollbackTests(TestCase):
    def setUp(self):
        self.place = create_quality_place()
        self.issue = SEOIssue.objects.create(url="/checked/", place=self.place, issue_code="invalid_json_ld", description="Legacy repair", status="fixed")
        self.change = SEOChange.objects.create(issue=self.issue, change_summary="Historical rating recalculation", old_value="rating_count=9, rating_avg=4.5", new_value="rating_count=0, rating_avg=0.0")

    def test_legacy_rating_rollback_restores_exact_captured_values(self):
        SEOFixEngine().rollback_change(self.change.pk)
        self.place.refresh_from_db()
        self.issue.refresh_from_db()
        self.assertEqual((self.place.rating_count, self.place.rating_avg), (9, 4.5))
        self.assertEqual(self.issue.status, "open")
        with self.assertRaises(ValueError):
            SEOFixEngine().rollback_change(self.change.pk)

    def test_rollback_refuses_to_overwrite_intervening_rating_updates(self):
        type(self.place).objects.filter(pk=self.place.pk).update(rating_count=2, rating_avg=3.5)
        with self.assertRaises(ValueError):
            SEOFixEngine().rollback_change(self.change.pk)
        self.place.refresh_from_db()
        self.change.refresh_from_db()
        self.assertEqual((self.place.rating_count, self.place.rating_avg), (2, 3.5))
        self.assertFalse(self.change.is_rolled_back)

    def test_unrestorable_history_is_not_reported_as_rolled_back(self):
        self.change.old_value = "cache refreshed"
        self.change.save(update_fields=["old_value"])
        with self.assertRaises(ValueError):
            SEOFixEngine().rollback_change(self.change.pk)
        self.change.refresh_from_db()
        self.assertFalse(self.change.is_rolled_back)
