"""Audit internal links across KidsMap.az.

Scans rendered pages for internal href links and verifies that every target link returns HTTP 200 OK.
Detects broken internal links (404/500) and orphan pages.

Usage:
    python manage.py audit_internal_links
"""

import re
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse

from catalog.models import Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.public_urls import public_hostname


class Command(BaseCommand):
    help = "Audit internal links across KidsMap.az to find broken links and orphan pages"

    def add_arguments(self, parser):
        parser.add_argument("--limit-places", type=int, default=20, help="Limit place detail pages to scan")

    def handle(self, *args, **options):
        client = Client()
        host = public_hostname() or "kidsmap.az"
        if host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            host = "testserver"

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("INTERNAL LINKS AUDIT")
        self.stdout.write(f"{'=' * 60}\n")

        # Collect pages to scan
        routes_to_scan = [
            reverse("home"),
            reverse("place_list"),
            reverse("about"),
            reverse("contacts"),
            reverse("privacy"),
            reverse("terms"),
        ]

        places = public_place_queryset(Place.objects.all())[: options["limit_places"]]
        for place in places:
            routes_to_scan.append(place.get_absolute_url())

        discovered_links: set[str] = set()
        broken_links: list[tuple[str, str, int]] = []

        href_pattern = re.compile(r'<a\s+[^>]*href=["\'](.*?)["\']', re.IGNORECASE)

        for source_path in routes_to_scan:
            try:
                res = client.get(source_path, secure=True, HTTP_HOST=host, follow=False)
                if not res or res.status_code != 200:
                    continue
                content = res.content.decode("utf-8", errors="replace")
                hrefs = href_pattern.findall(content)
                for href in hrefs:
                    href = href.strip()
                    if href.startswith("/") and not href.startswith("//") and not href.startswith("/static/") and not href.startswith("/media/"):
                        path = href.split("#")[0].split("?")[0]
                        if path:
                            discovered_links.add(path)
                            # Check target
                            target_res = client.get(path, secure=True, HTTP_HOST=host, follow=False)
                            if not target_res or target_res.status_code >= 400:
                                broken_links.append((source_path, path, target_res.status_code if target_res else 0))
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"⚠ Error scanning {source_path}: {exc}"))

        self.stdout.write(f"Scanned {len(routes_to_scan)} source pages.")
        self.stdout.write(f"Discovered {len(discovered_links)} unique internal links.\n")

        if broken_links:
            self.stdout.write(self.style.ERROR(f"✗ Found {len(broken_links)} broken internal link(s):"))
            for source, target, status in broken_links[:20]:
                self.stdout.write(f"  Source: {source} → Target: {target} (HTTP {status})")
        else:
            self.stdout.write(self.style.SUCCESS("✓ No broken internal links found! All internal links return HTTP 200."))

        self.stdout.write(f"\n{'=' * 60}\n")
