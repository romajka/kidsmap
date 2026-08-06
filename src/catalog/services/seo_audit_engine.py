"""Centralized SEO Audit Engine for KidsMap.

Scans the site's public URLs, place listings, taxonomy, schema JSON-LD, sitemap,
robots, canonical, and hreflang settings to discover technical and content issues.
Classifies each issue into Level A (Safe Auto-Fix), Level B (Draft Proposal),
or Level C (Manual Review Only).
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from catalog.models import CatalogContentSettings, Category, Place, SEOAuditRun, SEOIssue, Specialist
from catalog.services.content_quality import place_quality_check, public_place_queryset
from catalog.services.features import is_events_section_enabled, is_specialists_section_enabled
from catalog.services.public_urls import build_public_absolute_uri, public_hostname, public_origin
from catalog.services.seo_landing_visibility import build_seo_landing_visibility


class SEOAuditEngine:
    def __init__(self, *, environment: str = "production", code_version: str = "1.0.0"):
        self.environment = environment
        self.code_version = code_version
        self.client = Client()
        self.host = public_hostname() or "kidsmap.az"
        if self.host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            self.host = "testserver"

    def run_audit(
        self,
        *,
        audit_type: str = SEOAuditRun.AUDIT_TYPE_FULL,
        only_errors: bool = False,
        target_url: str | None = None,
        target_place_id: int | None = None,
        target_language: str | None = None,
        target_page_type: str | None = None,
        limit: int | None = None,
        skip_performance: bool = True,
    ) -> SEOAuditRun:
        run = SEOAuditRun.objects.create(
            audit_type=audit_type,
            status=SEOAuditRun.STATUS_RUNNING,
            environment=self.environment,
            code_version=self.code_version,
        )

        issues: list[SEOIssue] = []
        tested_urls: set[str] = set()

        try:
            if target_place_id:
                place = Place.objects.filter(pk=target_place_id).first()
                if place:
                    self._audit_place(place, run=run, issues=issues, tested_urls=tested_urls, target_language=target_language)
            elif target_url:
                self._audit_single_url(target_url, run=run, issues=issues, tested_urls=tested_urls)
            else:
                if audit_type in (SEOAuditRun.AUDIT_TYPE_FULL, SEOAuditRun.AUDIT_TYPE_SITEMAP, SEOAuditRun.AUDIT_TYPE_TECHNICAL):
                    self._audit_sitemap_and_robots(run=run, issues=issues, tested_urls=tested_urls)

                if audit_type in (SEOAuditRun.AUDIT_TYPE_FULL, SEOAuditRun.AUDIT_TYPE_TECHNICAL, SEOAuditRun.AUDIT_TYPE_CONTENT):
                    self._audit_static_routes(run=run, issues=issues, tested_urls=tested_urls, target_language=target_language)
                    self._audit_seo_landings(run=run, issues=issues, tested_urls=tested_urls, target_language=target_language)
                    self._audit_places_all(run=run, issues=issues, tested_urls=tested_urls, target_language=target_language, limit=limit)

            if only_errors:
                issues = [i for i in issues if i.severity == SEOIssue.SEVERITY_CRITICAL]

            # Save issues
            SEOIssue.objects.bulk_create(issues, ignore_conflicts=True)

            error_count = sum(1 for i in issues if i.severity == SEOIssue.SEVERITY_CRITICAL)
            warning_count = sum(1 for i in issues if i.severity == SEOIssue.SEVERITY_WARNING)
            auto_fixable_count = sum(1 for i in issues if i.level == SEOIssue.LEVEL_A)

            run.total_urls = len(tested_urls)
            run.error_count = error_count
            run.warning_count = warning_count
            run.auto_fix_count = auto_fixable_count
            run.status = SEOAuditRun.STATUS_COMPLETED
            run.finished_at = timezone.now()
            run.summary_notes = (
                f"Checked {len(tested_urls)} URLs. "
                f"Found {error_count} critical errors, {warning_count} warnings. "
                f"{auto_fixable_count} safe Level A auto-fixable items."
            )
            run.save()

        except Exception as exc:
            run.status = SEOAuditRun.STATUS_FAILED
            run.summary_notes = f"Audit failed with exception: {exc}"
            run.finished_at = timezone.now()
            run.save()
            raise exc

        return run

    def _get_page(self, path: str):
        try:
            return self.client.get(path, secure=True, HTTP_HOST=self.host, follow=False)
        except Exception:
            return None

    def _audit_single_url(self, path: str, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str]):
        tested_urls.add(path)
        response = self._get_page(path)
        if response is None:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type="custom_url",
                    issue_code="http_connection_failed",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_C,
                    description=f"Cannot connect to URL {path}",
                )
            )
            return

        if response.status_code != 200:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type="custom_url",
                    issue_code="non_200_status",
                    severity=SEOIssue.SEVERITY_CRITICAL if response.status_code >= 400 else SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_C,
                    description=f"URL returned HTTP {response.status_code}",
                    current_value=str(response.status_code),
                )
            )
            return

        content = response.content.decode("utf-8", errors="replace") if hasattr(response, "content") else ""
        self._check_html_meta(path=path, html=content, run=run, issues=issues, page_type="custom_url")

    def _audit_sitemap_and_robots(self, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str]):
        # Robots.txt
        robots_res = self._get_page("/robots.txt")
        tested_urls.add("/robots.txt")
        if not robots_res or robots_res.status_code != 200:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url="/robots.txt",
                    page_type="technical",
                    issue_code="robots_txt_missing",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_B,
                    description="/robots.txt is missing or non-200",
                    requires_approval=True,
                )
            )
        else:
            robots_text = robots_res.content.decode("utf-8", errors="replace")
            if "Sitemap:" not in robots_text:
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url="/robots.txt",
                        page_type="technical",
                        issue_code="robots_sitemap_missing",
                        severity=SEOIssue.SEVERITY_WARNING,
                        level=SEOIssue.LEVEL_B,
                        description="/robots.txt is missing 'Sitemap:' directive",
                        requires_approval=True,
                    )
                )

        # Sitemap.xml
        sitemap_res = self._get_page("/sitemap.xml")
        tested_urls.add("/sitemap.xml")
        if not sitemap_res or sitemap_res.status_code != 200:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url="/sitemap.xml",
                    page_type="sitemap",
                    issue_code="sitemap_unavailable",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_A,
                    description="sitemap.xml is unavailable or non-200",
                    is_auto_fixable=True,
                )
            )
            return

        if "X-Robots-Tag" in sitemap_res.headers:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url="/sitemap.xml",
                    page_type="sitemap",
                    issue_code="sitemap_has_x_robots_tag",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_A,
                    description="sitemap.xml contains X-Robots-Tag header which can interfere with GSC",
                    current_value=sitemap_res.headers.get("X-Robots-Tag", ""),
                    is_auto_fixable=True,
                )
            )

        try:
            root = ET.fromstring(sitemap_res.content)
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            loc_elements = [u.find("s:loc", ns) for u in root.findall("s:url", ns)]
            locs = [l.text for l in loc_elements if l is not None and l.text]

            # Check duplicates
            if len(locs) != len(set(locs)):
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url="/sitemap.xml",
                        page_type="sitemap",
                        issue_code="sitemap_duplicate_urls",
                        severity=SEOIssue.SEVERITY_WARNING,
                        level=SEOIssue.LEVEL_A,
                        description=f"sitemap.xml contains {len(locs) - len(set(locs))} duplicate URL(s)",
                        is_auto_fixable=True,
                    )
                )

            # Check unwanted draft or form URLs in sitemap
            unwanted = [l for l in locs if "/catalog/new/" in l or "/admin/" in l or "/auth/" in l or "/account/" in l]
            if unwanted:
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url="/sitemap.xml",
                        page_type="sitemap",
                        issue_code="sitemap_unwanted_urls",
                        severity=SEOIssue.SEVERITY_CRITICAL,
                        level=SEOIssue.LEVEL_A,
                        description=f"sitemap.xml contains {len(unwanted)} unwanted/private URL(s)",
                        current_value=", ".join(unwanted[:5]),
                        is_auto_fixable=True,
                    )
                )

            # Check if all published public places are in sitemap
            public_places = public_place_queryset(Place.objects.all())
            sitemap_paths = {urlparse(l).path for l in locs}
            missing_places = []
            for place in public_places:
                if place.get_absolute_url() not in sitemap_paths:
                    missing_places.append(place)

            if missing_places:
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url="/sitemap.xml",
                        page_type="sitemap",
                        issue_code="sitemap_missing_published_places",
                        severity=SEOIssue.SEVERITY_WARNING,
                        level=SEOIssue.LEVEL_A,
                        description=f"{len(missing_places)} published place(s) are missing from sitemap.xml",
                        is_auto_fixable=True,
                    )
                )

        except ET.ParseError as exc:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url="/sitemap.xml",
                    page_type="sitemap",
                    issue_code="sitemap_invalid_xml",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_A,
                    description=f"sitemap.xml is invalid XML: {exc}",
                    is_auto_fixable=True,
                )
            )

    def _audit_static_routes(self, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str], target_language: str | None = None):
        from django.utils.translation import override
        languages = [target_language] if target_language else ["az", "ru", "en"]
        static_route_names = [
            "home",
            "place_list",
            "site_reviews",
            "about",
            "contacts",
            "for_business",
            "privacy",
            "terms",
            "review_rules",
            "listing_rules",
        ]
        if is_events_section_enabled():
            static_route_names.append("events_landing")
        if is_specialists_section_enabled():
            static_route_names.append("specialist_list")

        for route_name in static_route_names:
            for lang in languages:
                with override(lang):
                    path = reverse(route_name)
                tested_urls.add(path)
                res = self._get_page(path)
                if not res or res.status_code != 200:
                    issues.append(
                        SEOIssue(
                            audit_run=run,
                            url=path,
                            page_type="static",
                            language=lang,
                            issue_code="static_page_non_200",
                            severity=SEOIssue.SEVERITY_CRITICAL,
                            level=SEOIssue.LEVEL_C,
                            description=f"Static route {path} returned HTTP {res.status_code if res else 'None'}",
                        )
                    )
                else:
                    html = res.content.decode("utf-8", errors="replace")
                    self._check_html_meta(path=path, html=html, run=run, issues=issues, page_type="static", lang=lang)

    def _audit_seo_landings(self, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str], target_language: str | None = None):
        from django.utils.translation import override
        content_settings = CatalogContentSettings.get_solo()
        visibility = build_seo_landing_visibility(content_settings)
        languages = [target_language] if target_language else ["az", "ru", "en"]

        for lang in languages:
            pages = visibility.pages(lang)
            for slug, page_info in pages.items():
                with override(lang):
                    path = reverse("seo_landing", kwargs={"seo_slug": slug})
                tested_urls.add(path)
                res = self._get_page(path)
                if not res or res.status_code != 200:
                    issues.append(
                        SEOIssue(
                            audit_run=run,
                            url=path,
                            page_type="seo_landing",
                            language=lang,
                            issue_code="seo_landing_non_200",
                            severity=SEOIssue.SEVERITY_CRITICAL,
                            level=SEOIssue.LEVEL_C,
                            description=f"SEO landing {path} returned HTTP {res.status_code if res else 'None'}",
                        )
                    )
                else:
                    html = res.content.decode("utf-8", errors="replace")
                    self._check_html_meta(path=path, html=html, run=run, issues=issues, page_type="seo_landing", lang=lang)
                    # FAQ schema check
                    if "FAQPage" not in html and page_info.get("faq"):
                        issues.append(
                            SEOIssue(
                                audit_run=run,
                                url=path,
                                page_type="seo_landing",
                                language=lang,
                                issue_code="seo_landing_missing_faq_schema",
                                severity=SEOIssue.SEVERITY_WARNING,
                                level=SEOIssue.LEVEL_A,
                                description=f"SEO landing {path} has FAQ items but missing FAQPage schema",
                                is_auto_fixable=True,
                            )
                        )

    def _audit_places_all(self, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str], target_language: str | None = None, limit: int | None = None):
        from django.utils.translation import override
        queryset = Place.objects.filter(deleted_at__isnull=True).order_by("-updated_at")
        if limit:
            queryset = queryset[:limit]

        for place in queryset:
            self._audit_place(place, run=run, issues=issues, tested_urls=tested_urls, target_language=target_language)

    def _audit_place(self, place: Place, *, run: SEOAuditRun, issues: list[SEOIssue], tested_urls: set[str], target_language: str | None = None):
        from django.utils.translation import override
        languages = [target_language] if target_language else ["az", "ru", "en"]
        quality = place_quality_check(place)

        # Place Data Quality Issues (Level C if factual/unpublish, Level A if quality counter recalculation)
        if place.status == Place.STATUS_PUBLISHED and not quality.is_ready:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=place.get_absolute_url(),
                    page_type="place_detail",
                    issue_code="published_place_fails_quality_check",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_C,
                    description=f"Published place #{place.pk} ('{place.name}') fails quality check score={quality.score}: {', '.join(quality.errors)}",
                    current_value=f"score={quality.score}, errors={quality.errors}",
                    place=place,
                )
            )

        if not (place.name_az or place.name or "").strip():
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=place.get_absolute_url(),
                    page_type="place_detail",
                    issue_code="place_missing_name",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_C,
                    description=f"Place #{place.pk} is missing name in AZ language",
                    place=place,
                )
            )

        if not place.category:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=place.get_absolute_url(),
                    page_type="place_detail",
                    issue_code="place_missing_category",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_C,
                    description=f"Place #{place.pk} ('{place.name}') is missing category",
                    place=place,
                )
            )

        if place.lat is None or place.lng is None:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=place.get_absolute_url(),
                    page_type="place_detail",
                    issue_code="place_missing_coordinates",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_C,
                    description=f"Place #{place.pk} ('{place.name}') is missing lat/lng coordinates",
                    place=place,
                )
            )

        if not (place.photo or place.cover_photo or place.gallery.exists()):
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=place.get_absolute_url(),
                    page_type="place_detail",
                    issue_code="place_missing_photo",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_C,
                    description=f"Place #{place.pk} ('{place.name}') has no primary photo or gallery images",
                    place=place,
                )
            )

        # Check public URL HTTP status and HTML meta
        if place.status == Place.STATUS_PUBLISHED and place.is_active:
            for lang in languages:
                with override(lang):
                    path = place.get_absolute_url()
                tested_urls.add(path)
                res = self._get_page(path)
                if not res or res.status_code != 200:
                    issues.append(
                        SEOIssue(
                            audit_run=run,
                            url=path,
                            page_type="place_detail",
                            language=lang,
                            issue_code="place_detail_non_200",
                            severity=SEOIssue.SEVERITY_CRITICAL,
                            level=SEOIssue.LEVEL_C,
                            description=f"Published place detail {path} returned HTTP {res.status_code if res else 'None'}",
                            place=place,
                        )
                    )
                else:
                    html = res.content.decode("utf-8", errors="replace")
                    self._check_html_meta(path=path, html=html, run=run, issues=issues, page_type="place_detail", lang=lang, place=place)

    def _check_html_meta(
        self,
        *,
        path: str,
        html: str,
        run: SEOAuditRun,
        issues: list[SEOIssue],
        page_type: str,
        lang: str = "az",
        place: Place | None = None,
    ):
        # 1. Title tag
        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if not title_match or not title_match.group(1).strip():
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_title",
                    severity=SEOIssue.SEVERITY_CRITICAL,
                    level=SEOIssue.LEVEL_B,
                    description=f"Page {path} has missing or empty <title> tag",
                    requires_approval=True,
                    place=place,
                )
            )
        else:
            title_text = title_match.group(1).strip()
            if len(title_text) < 10:
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url=path,
                        page_type=page_type,
                        language=lang,
                        issue_code="title_too_short",
                        severity=SEOIssue.SEVERITY_WARNING,
                        level=SEOIssue.LEVEL_B,
                        description=f"Page {path} has short title ({len(title_text)} chars): '{title_text}'",
                        current_value=title_text,
                        requires_approval=True,
                        place=place,
                    )
                )

        # 2. Meta description
        meta_desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE | re.DOTALL)
        if not meta_desc_match or not meta_desc_match.group(1).strip():
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_meta_description",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_B,
                    description=f"Page {path} has missing or empty meta description",
                    requires_approval=True,
                    place=place,
                )
            )

        # 3. Canonical tag
        canonical_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\'](.*?)["\']', html, re.IGNORECASE)
        if not canonical_match:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_canonical",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_A,
                    description=f"Page {path} is missing rel='canonical' tag",
                    is_auto_fixable=True,
                    place=place,
                )
            )
        else:
            canonical_href = canonical_match.group(1).strip()
            if not canonical_href.startswith("https://"):
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url=path,
                        page_type=page_type,
                        language=lang,
                        issue_code="canonical_not_https",
                        severity=SEOIssue.SEVERITY_WARNING,
                        level=SEOIssue.LEVEL_A,
                        description=f"Canonical URL on {path} is not HTTPS: {canonical_href}",
                        current_value=canonical_href,
                        is_auto_fixable=True,
                        place=place,
                    )
                )

        # 4. Hreflang links
        hreflang_matches = re.findall(r'<link\s+rel=["\']alternate["\']\s+hreflang=["\'](.*?)["\']\s+href=["\'](.*?)["\']', html, re.IGNORECASE)
        hreflangs = {lang_code.lower(): href for lang_code, href in hreflang_matches}
        if not hreflangs:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_hreflangs",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_A,
                    description=f"Page {path} is missing alternate hreflang links",
                    is_auto_fixable=True,
                    place=place,
                )
            )
        elif "x-default" not in hreflangs:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_x_default_hreflang",
                    severity=SEOIssue.SEVERITY_INFO,
                    level=SEOIssue.LEVEL_A,
                    description=f"Page {path} has hreflangs but is missing x-default hreflang",
                    is_auto_fixable=True,
                    place=place,
                )
            )

        # 5. Schema JSON-LD validation
        json_ld_matches = re.findall(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', html, re.IGNORECASE | re.DOTALL)
        if not json_ld_matches and page_type in ("place_detail", "home", "seo_landing"):
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="missing_schema_json_ld",
                    severity=SEOIssue.SEVERITY_WARNING,
                    level=SEOIssue.LEVEL_A,
                    description=f"Page {path} has no application/ld+json schema scripts",
                    is_auto_fixable=True,
                    place=place,
                )
            )

        for json_str in json_ld_matches:
            try:
                data = json.loads(json_str.strip())
                # Validate schema structure
                if isinstance(data, dict):
                    schema_type = data.get("@type", "")
                    if schema_type == "BreadcrumbList":
                        elements = data.get("itemListElement", [])
                        if not elements:
                            issues.append(
                                SEOIssue(
                                    audit_run=run,
                                    url=path,
                                    page_type=page_type,
                                    language=lang,
                                    issue_code="empty_breadcrumb_schema",
                                    severity=SEOIssue.SEVERITY_WARNING,
                                    level=SEOIssue.LEVEL_A,
                                    description=f"BreadcrumbList schema on {path} has empty itemListElement",
                                    is_auto_fixable=True,
                                    place=place,
                                )
                            )
            except json.JSONDecodeError as exc:
                issues.append(
                    SEOIssue(
                        audit_run=run,
                        url=path,
                        page_type=page_type,
                        language=lang,
                        issue_code="invalid_json_ld",
                        severity=SEOIssue.SEVERITY_CRITICAL,
                        level=SEOIssue.LEVEL_A,
                        description=f"Page {path} has invalid JSON-LD schema syntax: {exc}",
                        current_value=json_str[:200],
                        is_auto_fixable=True,
                        place=place,
                    )
                )

        # 6. Images missing alt attribute
        img_tags = re.findall(r"<img\s+[^>]*>", html, re.IGNORECASE)
        missing_alt_count = sum(1 for img in img_tags if 'alt="' not in img.lower() and "alt='" not in img.lower())
        if missing_alt_count > 0:
            issues.append(
                SEOIssue(
                    audit_run=run,
                    url=path,
                    page_type=page_type,
                    language=lang,
                    issue_code="images_missing_alt",
                    severity=SEOIssue.SEVERITY_INFO,
                    level=SEOIssue.LEVEL_A,
                    description=f"Page {path} has {missing_alt_count} image(s) missing alt attribute",
                    current_value=f"{missing_alt_count} images without alt",
                    is_auto_fixable=True,
                    place=place,
                )
            )
