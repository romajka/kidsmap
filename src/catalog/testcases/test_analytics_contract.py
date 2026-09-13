from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class AnalyticsContractTests(SimpleTestCase):
    def test_taxonomy_documents_every_canonical_event(self):
        document = (Path(settings.BASE_DIR) / "docs/product/analytics-event-taxonomy.md").read_text(encoding="utf-8")
        for name in (
            "organization_view", "place_view", "activity_view", "favorite_added", "favorite_removed",
            "phone_click", "whatsapp_click", "website_click", "social_click", "directions_click",
        ):
            self.assertIn(f"`{name}`", document)
        for heading in ("Subject", "Allowed metadata", "Source of truth", "Metric"):
            self.assertIn(heading, document)
