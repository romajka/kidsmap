"""The place gallery and the owner's affiliation workflow have separate entry points."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Organization, Place
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place


class OwnerPlaceNavigationTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create_user(username="gallery-owner")
        self.other = get_user_model().objects.create_user(username="gallery-other")
        self.org = Organization.objects.create(owner=self.owner, name_az="Şəbəkə",
            name_ru="Учебная сеть", status="published", approved_at=timezone.now())
        self.public = create_quality_place(owner=self.owner, name_az="Public branch")
        self.draft = create_quality_place(owner=self.owner, name_az="Private draft",
            status=Place.STATUS_DRAFT, is_active=False)
        request_join(actor=self.owner, place_id=self.public.pk, organization_id=self.org.pk)
        self.client.force_login(self.owner)

    def test_gallery_opens_public_card_and_draft_and_keeps_connections_separate(self):
        response = self.client.get(reverse("owner_places_dashboard"))
        self.assertNotContains(response, 'id="organization-links"')
        for url in (self.public.get_absolute_url(), reverse("owner_place_edit", args=[self.draft.pk])):
            self.assertContains(response, f'class="account-owner-card__link" href="{url}"')
        self.assertContains(response, reverse("owner_connections"))

    def test_connections_link_to_localized_public_destinations_and_show_real_count(self):
        with override("ru"):
            response = self.client.get(reverse("owner_connections"))
            self.assertEqual(response.context["connection_count"], 1)
            self.assertContains(response, self.public.get_absolute_url())
            self.assertContains(response, self.org.get_absolute_url())
            self.assertContains(response, "Учебная сеть")
            self.assertContains(response, reverse("organization_detach_preview", args=[self.org.pk, self.public.pk]))

    def test_empty_account_and_anonymous_access(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("owner_connections"))
        self.assertEqual(response.context["connection_count"], 0)
        self.assertNotContains(response, reverse("organization_detach_preview", args=[self.org.pk, self.public.pk]))
        self.assertContains(response, "data-empty-connections")
        self.client.logout()
        self.assertEqual(self.client.get(reverse("owner_connections")).status_code, 302)


    def test_join_form_handles_selected_organization_and_returns_to_connections(self):
        external = Organization.objects.create(owner=self.other, name_az="Another network",
            status="published", approved_at=timezone.now())
        response = self.client.post(reverse("owner_connection_join"), {
            "organization_id": external.pk, "place_id": self.draft.pk,
        })
        self.assertRedirects(response, reverse("owner_connections"))
        page = self.client.get(reverse("owner_connections"))
        self.assertEqual(page.context["connection_count"], 2)
        self.assertEqual([item.organization_id for item in page.context["place_affiliation_requests"]], [external.pk])
        self.assertContains(page, reverse("organization_join_recovery",
            args=[external.pk, page.context["place_affiliation_requests"][0].pk]))

    def test_private_organization_opens_its_workspace_only_for_authorized_user(self):
        Organization.objects.filter(pk=self.org.pk).update(status="draft", approved_at=None)
        response = self.client.get(reverse("owner_connections"))
        self.assertContains(response, reverse("organization_workspace_detail", args=[self.org.pk]))
        self.assertNotContains(response, self.org.get_absolute_url())
