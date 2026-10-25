from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.testcases.test_task33_publication import PublicationFixture


class AdminDeletedPlaceNavigationTests(PublicationFixture, TestCase):
    def test_deleted_place_get_does_not_redirect_to_itself(self):
        self.client.force_login(self.staff)
        type(self.place).objects.filter(pk=self.place.pk).update(deleted_at=timezone.now())
        url = reverse('admin:catalog_place_change', args=[self.place.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_active_place_still_opens(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk]))
        self.assertEqual(response.status_code, 200)
