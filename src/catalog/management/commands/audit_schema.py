"""Audit Schema.org JSON-LD microdata across KidsMap.az.

Scans public pages and validates structured JSON-LD payloads for correctness,
required fields, and valid schema types.

Usage:
    python manage.py audit_schema
"""

import json
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from django.test import Client
from django.urls import reverse

from catalog.models import Place
from catalog.services.content_quality import public_place_queryset
from catalog.services.public_urls import public_hostname


class Command(BaseCommand):
    help = "Audit Schema.org JSON-LD microdata across KidsMap.az"

    def handle(self, *args, **options):
        client = Client()
        host = public_hostname() or "kidsmap.az"
        if host not in settings.ALLOWED_HOSTS and "testserver" in settings.ALLOWED_HOSTS:
            host = "testserver"

        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write("SCHEMA.ORG MICRODATA AUDIT")
        self.stdout.write(f"{'=' * 60}\n")

        pages = [
            reverse("home"),
            reverse("place_list"),
            reverse("site_reviews"),
        ]

        place = public_place_queryset(Place.objects.all()).first()
        if place:
            pages.append(place.get_absolute_url())

        schema_count = 0
        schema_types: set[str] = set()
        schema_errors: list[tuple[str, str]] = []

        json_ld_pattern = re.compile(r'<script\s+type=["\']application/ld\+json["\']>(.*?)</script>', re.IGNORECASE | re.DOTALL)

        for path in pages:
            res = client.get(path, secure=True, HTTP_HOST=host, follow=False)
            if not res or res.status_code != 200:
                schema_errors.append((path, f"Page returned HTTP {res.status_code if res else 'None'}"))
                continue

            content = res.content.decode("utf-8", errors="replace")
            blocks = json_ld_pattern.findall(content)
            for block in blocks:
                schema_count += 1
                try:
                    data = json.loads(block.strip())
                    if isinstance(data, dict):
                        stype = data.get("@type", "Unknown")
                        schema_types.add(stype)
                        if stype == "BreadcrumbList" and not data.get("itemListElement"):
                            schema_errors.append((path, "BreadcrumbList contains empty itemListElement"))
                        elif stype == "LocalBusiness" and not data.get("name"):
                            schema_errors.append((path, "LocalBusiness schema is missing required 'name' field"))
                except json.JSONDecodeError as exc:
                    schema_errors.append((path, f"Invalid JSON syntax: {exc}"))

        self.stdout.write(f"Scanned {len(pages)} key pages.")
        self.stdout.write(f"Validated {schema_count} JSON-LD schema blocks.")
        self.stdout.write(f"Found schema types: {', '.join(sorted(schema_types))}\n")

        if schema_errors:
            self.stdout.write(self.style.ERROR(f"✗ Found {len(schema_errors)} schema error(s):"))
            for path, err in schema_errors:
                self.stdout.write(f"  {path} → {err}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ All Schema.org JSON-LD microdata blocks are valid!"))

        self.stdout.write(f"\n{'=' * 60}\n")
