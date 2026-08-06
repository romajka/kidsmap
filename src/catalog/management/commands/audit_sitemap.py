"""Audit the sitemap for consistency, duplicates, and quality issues.

Usage:
    python manage.py audit_sitemap
    python manage.py audit_sitemap --check-live   # also check HTTP status of each URL
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog.models import CatalogContentSettings, Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.seo_landing_visibility import build_seo_landing_visibility


class Command(BaseCommand):
    help = "Audit the sitemap for consistency, duplicates, and quality issues."

    def add_arguments(self, parser):
        parser.add_argument(
            "--check-live",
            action="store_true",
            help="Fetch each URL via Django test client and report non-200 responses.",
        )

    def handle(self, *args, **options):
        from django.test import Client
        from catalog.services.public_urls import public_hostname

        host = public_hostname() or "kidsmap.az"
        if host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            host = "testserver"

        client = Client()
        response = client.get("/sitemap.xml", secure=True, HTTP_HOST=host)
        if response.status_code == 301 and response.headers.get("Location"):
            response = client.get(response.headers["Location"], secure=True, HTTP_HOST=host)

        content = response.content
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("SITEMAP AUDIT REPORT")
        self.stdout.write(f"{'=' * 60}\n")

        # Parse XML
        try:
            root = ET.fromstring(content)
            self.stdout.write(self.style.SUCCESS("✓ XML is valid"))
        except ET.ParseError as exc:
            self.stdout.write(self.style.ERROR(f"✗ XML parse error: {exc}"))
            return

        # Content-Type
        content_type = response.get("Content-Type", "")
        if "xml" in content_type:
            self.stdout.write(self.style.SUCCESS(f"✓ Content-Type: {content_type}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ Content-Type: {content_type} (expected application/xml)"))

        # URL counts
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        url_elements = root.findall("s:url", ns)
        locs = []
        lastmod_issues = []
        for url_el in url_elements:
            loc_el = url_el.find("s:loc", ns)
            if loc_el is not None:
                locs.append(loc_el.text)
            lastmod_el = url_el.find("s:lastmod", ns)
            if lastmod_el is not None and lastmod_el.text:
                # Basic date format check
                text = lastmod_el.text.strip()
                if not (len(text) >= 10 and text[4] == "-" and text[7] == "-"):
                    lastmod_issues.append((loc_el.text if loc_el is not None else "?", text))

        total = len(locs)
        unique = len(set(locs))
        self.stdout.write(f"\nTotal <url> entries: {total}")
        self.stdout.write(f"Unique <loc> entries: {unique}")

        # Duplicates
        if total != unique:
            self.stdout.write(self.style.ERROR(f"✗ {total - unique} duplicate URL(s) found:"))
            for loc, count in Counter(locs).most_common():
                if count > 1:
                    self.stdout.write(f"  {count}x {loc}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ No duplicate URLs"))

        # Categorize
        place_urls = [l for l in locs if "/place/" in l]
        seo_urls = [l for l in locs if "/catalog/" in l and "/place/" not in l and "/new/" not in l]
        specialist_urls = [l for l in locs if "/specialist/" in l]
        static_urls = [l for l in locs if l not in place_urls and l not in seo_urls and l not in specialist_urls]

        self.stdout.write(f"\nURL breakdown by type:")
        self.stdout.write(f"  Static pages:    {len(static_urls)}")
        self.stdout.write(f"  Places:          {len(place_urls)}")
        self.stdout.write(f"  SEO landings:    {len(seo_urls)}")
        self.stdout.write(f"  Specialists:     {len(specialist_urls)}")

        # Language breakdown
        default_lang = (settings.LANGUAGE_CODE or "az").split("-")[0]
        lang_codes = [code for code, _label in settings.LANGUAGES]
        lang_counts = {}
        for code in lang_codes:
            if code == default_lang:
                lang_counts[code] = len([l for l in locs if f"/{code}/" not in l and all(f"/{c}/" not in l for c in lang_codes if c != default_lang)])
            else:
                lang_counts[code] = len([l for l in locs if f"/{code}/" in l])
        self.stdout.write(f"\nURL breakdown by language:")
        for code, count in lang_counts.items():
            self.stdout.write(f"  {code}: {count}")

        # Lastmod issues
        urls_with_lastmod = sum(1 for url_el in url_elements if url_el.find("s:lastmod", ns) is not None)
        self.stdout.write(f"\nURLs with lastmod: {urls_with_lastmod}/{total}")
        if lastmod_issues:
            self.stdout.write(self.style.WARNING(f"⚠ {len(lastmod_issues)} lastmod format issue(s):"))
            for loc, text in lastmod_issues[:10]:
                self.stdout.write(f"  {loc} → {text}")

        # Check for unwanted URLs
        unwanted_patterns = ["/catalog/new/", "/admin/", "/auth/", "/account/"]
        unwanted_found = []
        for loc in locs:
            for pattern in unwanted_patterns:
                if pattern in loc:
                    unwanted_found.append((loc, pattern))
        if unwanted_found:
            self.stdout.write(self.style.ERROR(f"\n✗ {len(unwanted_found)} unwanted URL(s) found:"))
            for loc, pattern in unwanted_found:
                self.stdout.write(f"  {loc} (matched {pattern})")
        else:
            self.stdout.write(self.style.SUCCESS("\n✓ No unwanted URLs (admin, auth, place_new, etc.)"))

        # Check for non-HTTPS URLs (if PUBLIC_BASE_URL is set)
        public_base = (getattr(settings, "PUBLIC_BASE_URL", "") or "").strip()
        if public_base and public_base.startswith("https://"):
            non_https = [l for l in locs if not l.startswith("https://")]
            if non_https:
                self.stdout.write(self.style.ERROR(f"✗ {len(non_https)} non-HTTPS URL(s) found"))
            else:
                self.stdout.write(self.style.SUCCESS("✓ All URLs use HTTPS"))

        # Check missing from sitemap: published places not in sitemap
        public_places = public_place_queryset(Place.objects.all())
        place_slugs_in_sitemap = set()
        for loc in place_urls:
            parts = loc.rstrip("/").split("/")
            if parts:
                place_slugs_in_sitemap.add(parts[-1])

        missing_places = []
        for place in public_places:
            slug = place.get_absolute_url().rstrip("/").split("/")[-1]
            if slug not in place_slugs_in_sitemap:
                missing_places.append(place)

        if missing_places:
            self.stdout.write(self.style.WARNING(f"\n⚠ {len(missing_places)} published place(s) missing from sitemap:"))
            for place in missing_places[:10]:
                self.stdout.write(f"  {place.get_absolute_url()} ({place.name})")
        else:
            self.stdout.write(self.style.SUCCESS("✓ All public places are in sitemap"))

        # Check indexable SEO landings
        try:
            content_settings = CatalogContentSettings.get_solo()
            visibility = build_seo_landing_visibility(content_settings)
            default_language = (settings.LANGUAGE_CODE or "az").split("-", 1)[0]
            indexable = list(visibility.pages(default_language, indexable_only=True).keys())
            self.stdout.write(f"\nIndexable SEO landings: {len(indexable)}")
            for slug in indexable:
                self.stdout.write(f"  /catalog/{slug}/")
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"⚠ Could not check SEO landings: {exc}"))

        # File size
        size_bytes = len(content)
        size_kb = size_bytes / 1024
        self.stdout.write(f"\nSitemap file size: {size_kb:.1f} KB")
        if size_bytes > 50 * 1024 * 1024:
            self.stdout.write(self.style.ERROR("✗ Exceeds 50 MB limit!"))
        elif total > 50000:
            self.stdout.write(self.style.ERROR("✗ Exceeds 50,000 URL limit!"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Within limits ({total}/50,000 URLs, {size_kb:.0f} KB/50,000 KB)"))

        # Optional live check
        if options["check_live"]:
            self._check_live(locs)

        self.stdout.write(f"\n{'=' * 60}\n")

    def _check_live(self, locs):
        from django.test import Client
        from catalog.services.public_urls import public_hostname

        host = public_hostname() or "kidsmap.az"
        if host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            host = "testserver"

        self.stdout.write(f"\nLive URL check ({len(locs)} URLs)...")
        client = Client()
        issues = []
        for loc in locs:
            # Extract path from full URL
            from urllib.parse import urlparse
            parsed = urlparse(loc)
            path = parsed.path
            try:
                response = client.get(path, secure=True, HTTP_HOST=host, follow=False)
                status = response.status_code
                if status != 200:
                    issues.append((loc, f"HTTP {status}"))
                # Check noindex
                content = response.content.decode("utf-8", errors="replace") if hasattr(response, "content") else ""
                if 'name="robots" content="noindex' in content:
                    issues.append((loc, "has noindex meta"))
            except Exception as exc:
                issues.append((loc, str(exc)))

        if issues:
            self.stdout.write(self.style.WARNING(f"⚠ {len(issues)} issue(s) found:"))
            for loc, issue in issues[:50]:
                self.stdout.write(f"  {loc} → {issue}")
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ All {len(locs)} URLs return 200 without noindex"))
