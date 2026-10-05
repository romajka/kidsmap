"""R1 maintenance/cohort must stop writes while keeping compatible readers."""
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import PlaceLike, PlaceReview
from catalog.testcases.utils import create_quality_place


class R1WriteCohortTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_user(username='r1-cohort-parent')
        self.other = get_user_model().objects.create_user(username='r1-cohort-outside')
        self.staff = get_user_model().objects.create_superuser(username='r1-cohort-staff', email='staff@example.test', password='synthetic')
        self.place = create_quality_place()
        self.client.force_login(self.actor)
        self.like_url = reverse('toggle_place_like', args=[self.place.pk])

    @override_settings(TASK33_R1_WRITE_MODE='off')
    def test_disabled_cohort_blocks_http_write_without_deleting_post_switch_rows(self):
        old = PlaceLike.objects.create(place=self.place, user=self.other)
        review = PlaceReview.objects.create(place=self.place, user=self.other, text='Post-switch preserved', rating=5, status='approved')
        response = self.client.post(self.like_url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['code'], 'r1_writes_paused')
        self.assertTrue(PlaceLike.objects.filter(pk=old.pk).exists())
        self.assertFalse(PlaceLike.objects.filter(place=self.place, user=self.actor).exists())
        self.assertEqual(PlaceReview.objects.get(pk=review.pk).text, 'Post-switch preserved')
        self.assertEqual(self.client.get(reverse('typed_reviews', args=['place', self.place.pk])).status_code, 200)

    @override_settings(TASK33_R1_WRITE_MODE='selected')
    def test_selected_cohort_allows_only_explicit_actor_ids(self):
        with override_settings(TASK33_R1_WRITE_USER_IDS=(self.actor.pk,)):
            self.assertEqual(self.client.post(self.like_url).status_code, 302)
            self.assertTrue(PlaceLike.objects.filter(place=self.place, user=self.actor).exists())
            self.client.force_login(self.other)
            self.assertEqual(self.client.post(self.like_url, HTTP_X_R1_COHORT='enabled').status_code, 503)
            self.assertFalse(PlaceLike.objects.filter(place=self.place, user=self.other).exists())
            self.client.force_login(self.staff)
            self.assertEqual(self.client.post(self.like_url).status_code, 503)

    @override_settings(TASK33_R1_WRITE_MODE='off')
    def test_admin_content_post_is_disabled_without_disabling_login_or_public_reads(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('admin:catalog_place_change', args=[self.place.pk]), {'name': 'Should not apply'})
        self.assertEqual(response.status_code, 503)
        self.place.refresh_from_db()
        self.assertNotEqual(self.place.name, 'Should not apply')
        self.assertEqual(self.client.get(reverse('admin:catalog_place_change', args=[self.place.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('place_detail_legacy', args=[self.place.pk]), follow=True).status_code, 200)
        self.assertNotEqual(Client().post(reverse('account_login'), {}).status_code, 503)

    def test_invalid_configuration_fails_closed_and_all_mode_preserves_existing_write(self):
        for mode in ('invalid', '', None):
            with self.subTest(mode=mode), override_settings(TASK33_R1_WRITE_MODE=mode):
                self.assertEqual(self.client.post(self.like_url).status_code, 503)
        with override_settings(TASK33_R1_WRITE_MODE='all'):
            self.assertEqual(self.client.post(self.like_url).status_code, 302)
            self.assertTrue(PlaceLike.objects.filter(place=self.place, user=self.actor).exists())

    def test_localized_admin_cannot_bypass_off_or_selected_cohort(self):
        self.client.force_login(self.staff)
        for language in ('ru', 'en'):
            for mode in ('off', 'selected'):
                with self.subTest(language=language, mode=mode), override(language), override_settings(
                    TASK33_R1_WRITE_MODE=mode, TASK33_R1_WRITE_USER_IDS=(self.actor.pk,)
                ):
                    url = reverse('localized_admin:catalog_place_change', args=[self.place.pk])
                    self.assertEqual(self.client.post(url, {'name': 'Paused edit'}).status_code, 503)
                    self.assertEqual(self.client.get(url).status_code, 200)
                    self.assertNotEqual(Client().post(reverse('localized_admin:login'), {}).status_code, 503)
        self.place.refresh_from_db()
        self.assertNotEqual(self.place.name, 'Paused edit')

    @override_settings(TASK33_R1_WRITE_MODE='selected', TASK33_R1_WRITE_USER_IDS=('malformed',))
    def test_malformed_cohort_does_not_open_writes(self):
        self.assertEqual(self.client.post(self.like_url).status_code, 503)

    @override_settings(TASK33_R1_WRITE_MODE='all')
    def test_cohort_membership_does_not_bypass_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.actor)
        self.assertEqual(csrf_client.post(self.like_url).status_code, 403)
        self.assertFalse(PlaceLike.objects.filter(place=self.place, user=self.actor).exists())
