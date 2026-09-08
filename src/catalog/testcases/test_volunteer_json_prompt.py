import json
import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from catalog.models import Place


class VolunteerJsonPromptTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("prompt-volunteer", is_staff=True)
        self.user.groups.add(Group.objects.get_or_create(name="KidsMap Volunteers")[0])
        self.client.force_login(self.user)

    def test_instruction_available_on_add_and_own_edit_with_taxonomy(self):
        place = Place.objects.create(name="Own draft", category="EDU", created_by=self.user, status="draft", is_active=False)
        for url in (reverse("admin:volunteer_add"), reverse("admin:volunteer_edit", args=[place.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "data-place-json-prompt-copy")
                self.assertContains(response, "data-place-json-prompt-dialog")
                self.assertContains(response, "admin/js/kidsmap_place_json_import.js")
                config = re.search(r'<script id="km-place-taxonomy-config" type="application/json">(.*?)</script>', response.content.decode(), re.S)
                self.assertIsNotNone(config)
                taxonomy = json.loads(config.group(1))
                self.assertTrue(taxonomy["regions"])
                self.assertTrue(taxonomy["price_modes"])
                self.assertNotContains(response, "data-place-json-import-dialog")
                self.assertNotContains(response, "data-pricing-validate-url")

    def test_instruction_does_not_grant_other_place_access(self):
        place = Place.objects.create(name="Other draft", category="EDU", status="draft", is_active=False)
        self.assertEqual(self.client.get(reverse("admin:volunteer_edit", args=[place.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("admin:catalog_place_add")).status_code, 403)
