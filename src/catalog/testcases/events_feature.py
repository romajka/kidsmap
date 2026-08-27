from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Event, SiteSettings


User = get_user_model()


class TestEventsFeatureFlag(TestCase):
    def setUp(self):
        self.settings = SiteSettings.get_solo()
        self.owner = User.objects.create_user(username="events_owner", password="password")
        now = timezone.now()
        self.event = Event.objects.create(
            owner=self.owner,
            name="Hidden event",
            name_ru="Скрытое мероприятие",
            category="ART",
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=2),
            status=Event.STATUS_PUBLISHED,
            address="Баку",
        )

    def test_disabled_section_hides_public_and_owner_event_interfaces(self):
        self.settings.events_section_enabled = False
        self.settings.save()

        for url in (
            reverse("events_landing"),
            self.event.get_absolute_url(),
        ):
            self.assertEqual(self.client.get(url).status_code, 410)

        home = self.client.get(reverse("home"))
        self.assertEqual(home.status_code, 200)
        self.assertNotContains(home, f'href="{reverse("events_landing")}"')
        self.assertEqual(home.context["upcoming_events"], [])

        catalog = self.client.get(reverse("place_list"), {"event_type": "temporary"})
        self.assertEqual(catalog.status_code, 200)
        self.assertNotContains(catalog, 'name="event_type"')
        self.assertNotContains(catalog, "Временные")

        self.client.login(username="events_owner", password="password")
        for url in (
            reverse("owner_event_create"),
            reverse("owner_event_edit", kwargs={"pk": self.event.pk}),
        ):
            self.assertEqual(self.client.get(url).status_code, 404)

        dashboard = self.client.get(reverse("owner_places_dashboard"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertNotContains(dashboard, "owner-events-list")
        self.assertNotContains(dashboard, reverse("owner_event_create"))

    def test_proxy_admin_save_invalidates_cached_event_feature_flag(self):
        from catalog.models.site import SiteVisibilitySettings
        from catalog.services.features import is_events_section_enabled

        self.settings.events_section_enabled = True
        self.settings.save()
        self.assertTrue(is_events_section_enabled())

        visibility_settings = SiteVisibilitySettings.objects.get(pk=self.settings.pk)
        visibility_settings.events_section_enabled = False
        visibility_settings.save()

        self.assertFalse(is_events_section_enabled())
