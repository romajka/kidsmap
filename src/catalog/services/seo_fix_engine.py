"""Bounded cache refreshes with invariant checks and truthful legacy rollback."""

from __future__ import annotations

import math
import re

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.test import Client
from django.utils import timezone

from catalog.models import Place, SEOChange, SEOIssue
from catalog.services.public_urls import public_hostname
from catalog.services.seo_audit_engine import SEOAuditEngine


class SEOFixEngine:
    SITEMAP_CODES = frozenset((
        "sitemap_unavailable", "sitemap_invalid_xml", "sitemap_duplicate_urls",
        "sitemap_unwanted_urls", "sitemap_missing_published_places", "sitemap_has_x_robots_tag",
    ))
    HTML_CODES = frozenset((
        "missing_canonical", "canonical_not_https", "missing_hreflangs",
        "missing_x_default_hreflang", "missing_schema_json_ld", "empty_breadcrumb_schema",
        "seo_landing_missing_faq_schema", "invalid_json_ld", "images_missing_alt",
    ))

    def __init__(self):
        self.client = Client()
        self.host = public_hostname() or "kidsmap.az"
        if self.host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            self.host = "testserver"

    def apply_safe_fixes(self, *, dry_run: bool = True, issue_id: int | None = None) -> list[SEOChange]:
        query = SEOIssue.objects.filter(
            level=SEOIssue.LEVEL_A, status=SEOIssue.STATUS_OPEN,
            is_auto_fixable=True, requires_approval=False,
        )
        if issue_id:
            query = query.filter(pk=issue_id)
        changes = []
        for issue in query:
            change = self._fix_single_issue(issue, dry_run=dry_run)
            if change:
                changes.append(change)
        return changes

    def _fix_single_issue(self, issue: SEOIssue, *, dry_run: bool) -> SEOChange | None:
        if issue.level != SEOIssue.LEVEL_A or issue.issue_code not in self.SITEMAP_CODES | self.HTML_CODES | {"place_detail_non_200"}:
            return None
        fields = dict(
            issue=issue,
            change_summary=f"Invalidated cache and rechecked {issue.issue_code}",
            old_value=issue.current_value,
            new_value="Cache invalidated; original SEO invariant rechecked",
            reason=f"Cache refresh attempt for {issue.issue_code}; source data unchanged",
            source="safe_auto_fix",
            # Clearing a cache does not have a captured state that can be restored.
            is_reversible=False,
        )
        if dry_run:
            fields.update(change_summary=f"[DRY-RUN] {fields['change_summary']}", source="safe_auto_fix_dry_run")
            return SEOChange(**fields)

        with transaction.atomic():
            issue = SEOIssue.objects.select_for_update().get(pk=issue.pk)
            if issue.status != SEOIssue.STATUS_OPEN:
                return None
            cache.clear()
            verified, result = self._check_original_invariant(issue)
            fields["issue"] = issue
            change = SEOChange.objects.create(**fields, recheck_result=result[:200])
            if verified:
                issue.status = SEOIssue.STATUS_FIXED
            issue.last_checked_at = timezone.now()
            issue.save(update_fields=["status", "last_checked_at"])
            return change

    def _check_original_invariant(self, issue: SEOIssue) -> tuple[bool, str]:
        try:
            engine = SEOAuditEngine(environment="recheck")
            engine.client, engine.host = self.client, self.host
            findings = []
            if issue.issue_code in self.SITEMAP_CODES:
                engine._audit_sitemap_and_robots(run=None, issues=findings, tested_urls=set())
                key = (issue.url, "all", issue.issue_code)
            else:
                response = self.client.get(issue.url, secure=True, HTTP_HOST=self.host, follow=False)
                if response.status_code != 200:
                    return False, f"Re-check FAILED: HTTP {response.status_code}; {issue.issue_code} not verified"
                if issue.issue_code == "place_detail_non_200":
                    return True, "Re-check SUCCESS: place detail HTTP 200"
                html = response.content.decode("utf-8", errors="replace")
                engine._check_html_meta(
                    path=issue.url, html=html, run=None, issues=findings,
                    page_type=issue.page_type, lang=issue.language, place=issue.place,
                )
                if issue.issue_code == "seo_landing_missing_faq_schema":
                    if issue.page_type != "seo_landing":
                        return False, "Re-check FAILED: FAQ page context is unknown"
                    if '"FAQPage"' not in html:
                        return False, f"Re-check FAILED: {issue.issue_code} remains"
                    return True, f"Re-check SUCCESS: {issue.issue_code} verified"
                key = (issue.url, issue.language, issue.issue_code)
            if key not in engine.checked_issue_keys:
                return False, f"Re-check FAILED: {issue.issue_code} could not be evaluated"
            if any(item.issue_code == issue.issue_code for item in findings):
                return False, f"Re-check FAILED: {issue.issue_code} remains"
            return True, f"Re-check SUCCESS: {issue.issue_code} verified"
        except Exception as exc:
            return False, f"Re-check FAILED: {type(exc).__name__}; {issue.issue_code} not verified"

    def _recheck_issue_url(self, issue: SEOIssue) -> str:
        return self._check_original_invariant(issue)[1]

    @staticmethod
    def _captured_rating(value):
        match = re.fullmatch(r"rating_count=(\d+), rating_avg=([0-9]+(?:\.[0-9]+)?)", value)
        if not match:
            raise ValueError("Historical change has no restorable rating snapshot.")
        count, average = int(match[1]), float(match[2])
        if not math.isfinite(average) or not 0 <= average <= 5:
            raise ValueError("Historical rating snapshot is invalid.")
        return count, average

    @transaction.atomic
    def rollback_change(self, change_id: int) -> SEOChange:
        change = SEOChange.objects.select_for_update().filter(pk=change_id).first()
        if not change:
            raise ValueError(f"SEOChange #{change_id} not found.")
        if change.is_rolled_back:
            raise ValueError(f"SEOChange #{change_id} has already been rolled back.")
        if not change.is_reversible:
            raise ValueError(f"SEOChange #{change_id} is marked non-reversible.")
        old_count, old_average = self._captured_rating(change.old_value)
        new_count, new_average = self._captured_rating(change.new_value)
        issue = SEOIssue.objects.select_for_update().filter(pk=change.issue_id).first()
        if not issue or not issue.place_id:
            raise ValueError("Historical rating change no longer has its original place.")
        place = Place.objects.select_for_update().get(pk=issue.place_id)
        if place.rating_count != new_count or not math.isclose(place.rating_avg, new_average, abs_tol=1e-9):
            raise ValueError("Ratings changed after this SEO repair; manual review is required.")
        place.rating_count, place.rating_avg = old_count, old_average
        place.save(update_fields=["rating_count", "rating_avg"])
        change.is_rolled_back, change.rolled_back_at = True, timezone.now()
        change.save(update_fields=["is_rolled_back", "rolled_back_at"])
        issue.status = SEOIssue.STATUS_OPEN
        issue.save(update_fields=["status", "last_checked_at"])
        transaction.on_commit(cache.clear)
        return change
