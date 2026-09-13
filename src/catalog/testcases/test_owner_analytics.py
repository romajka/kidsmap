from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import OwnerTeamMembership, Place


@override_settings(
    OWNER_ANALYTICS_ENABLED=True,
    LOCAL_ANALYTICS_STORAGE_ENABLED=True,
    ANALYTICS_COLLECTION_STARTED_AT="2026-09-01T00:00:00Z",
)
class OwnerAnalyticsTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user("place-owner", password="test-password")
        self.other = User.objects.create_user("other-owner", password="test-password")
        self.place = Place.objects.create(
            name="Owner analytics", category="EDU", owner=self.owner,
            status=Place.STATUS_DRAFT, is_active=False,
        )
        self.url = reverse("owner_place_analytics", args=[self.place.pk])

    def test_direct_owner_can_view_aggregate_page_for_draft(self):
        self.client.force_login(self.owner)
        response = self.client.get("/ru" + self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KidsMap Analytics")
        self.assertNotContains(response, "visitor_key_hash")
        self.assertNotContains(response, "session_key_hash")
        self.assertNotContains(response, "referrer_domain")
        self.assertContains(
            response,
            'class="owner-analytics__metric-icon material-symbols-rounded"',
            count=5,
            html=False,
        )
        dashboard = self.client.get(reverse("owner_places_dashboard"))
        self.assertContains(dashboard, self.url)
        self.assertContains(response, "Пользователи, сохранившие место")

    def test_unrelated_user_and_deleted_place_are_not_disclosed(self):
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.force_login(self.owner)
        from django.utils import timezone
        self.place.deleted_at = timezone.now()
        self.place.save(update_fields=["deleted_at"])
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_team_stats_permission_is_scoped_by_role(self):
        OwnerTeamMembership.objects.create(
            place=self.place, owner=self.owner, member=self.other, role="MODERATOR"
        )
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        OwnerTeamMembership.objects.filter(place=self.place, member=self.other).update(role="EDITOR")
        self.assertEqual(self.client.get(self.url).status_code, 404)

    @override_settings(OWNER_ANALYTICS_ENABLED=False)
    def test_feature_gate_hides_route(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.url).status_code, 404)
