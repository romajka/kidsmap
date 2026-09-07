from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from catalog.models import PlaceReview
from catalog.testcases.utils import create_quality_place


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=120)
class PlaceReviewCooldownTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='cooldown-user')
        self.client.force_login(self.user)
        self.place = create_quality_place()
        self.url = reverse('add_place_review', args=[self.place.pk])
        self.start = timezone.now()

    def submit(self, text='Первый отзыв', at=None, url=None):
        with patch('django.utils.timezone.now', return_value=at or self.start):
            return self.client.post(url or self.url, {'rating': '5', 'text': text},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def test_early_repeat_is_429_and_never_overwrites_review(self):
        self.assertEqual(self.submit().status_code, 200)
        response = self.submit('Повторное нажатие', self.start + timedelta(seconds=119))
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response['Retry-After'], '1')
        self.assertFalse(response.json()['ok'])
        self.assertEqual(PlaceReview.objects.get(user=self.user).text, 'Первый отзыв')

    def test_boundary_creates_separate_pending_review_and_preserves_approved_history(self):
        self.submit()
        first = PlaceReview.objects.get(user=self.user)
        first.status = 'approved'
        first.save()
        response = self.submit('Второй отзыв', self.start + timedelta(seconds=120))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceReview.objects.filter(user=self.user).count(), 2)
        first.refresh_from_db()
        self.assertEqual(first.status, 'approved')
        self.assertEqual(first.text, 'Первый отзыв')
        second = PlaceReview.objects.exclude(pk=first.pk).get(user=self.user)
        self.assertEqual(second.status, 'pending')
        self.assertFalse(second.is_approved)

    def test_other_place_and_other_user_are_independent(self):
        self.submit()
        other_place = create_quality_place(name='Other cooldown place')
        self.assertEqual(self.submit(url=reverse('add_place_review', args=[other_place.pk])).status_code, 200)
        other_user = get_user_model().objects.create_user(username='cooldown-other')
        self.client.force_login(other_user)
        self.assertEqual(self.submit().status_code, 200)

    def test_deletion_does_not_bypass_timer(self):
        self.submit()
        PlaceReview.objects.filter(user=self.user).delete()
        self.assertEqual(self.submit().status_code, 429)
        self.assertFalse(PlaceReview.objects.filter(user=self.user).exists())

    def test_invalid_submission_does_not_start_timer(self):
        response = self.client.post(self.url, {'rating': '0', 'text': 'Неверная оценка'},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.submit().status_code, 200)

    def test_get_restores_timer_for_the_same_user_only(self):
        self.submit()
        response = self.client.get(self.place.get_absolute_url())
        self.assertContains(response, 'data-review-cooldown')
        self.assertTrue(response.context['review_cooldown']['active'])
        self.client.logout()
        response = self.client.get(self.place.get_absolute_url())
        self.assertFalse(response.context['review_cooldown']['active'])

    def test_failed_save_rolls_back_timer_reservation(self):
        with patch('catalog.services.place_review_submission.PlaceReview.objects.create', side_effect=RuntimeError('synthetic save failure')):
            with self.assertRaises(RuntimeError):
                self.submit()
        self.assertEqual(self.submit().status_code, 200)


class ReviewAdminDeleteAndPermissionsTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(username='review-admin', email='review-admin@example.test', password='test-password')
        self.client.force_login(self.admin)
        self.place = create_quality_place()
        self.first = PlaceReview.objects.create(place=self.place, user=self.admin, rating=5, text='Published review one', status='approved')
        self.second = PlaceReview.objects.create(place=self.place, user=self.admin, rating=1, text='Published review two', status='approved')

    def test_delete_requires_confirmation_and_recalculates_rating(self):
        url = reverse('admin:catalog_placereview_delete', args=[self.second.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(PlaceReview.objects.filter(place=self.place).count(), 2)
        response = self.client.post(url, {'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlaceReview.objects.filter(pk=self.second.pk).exists())
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 1)
        self.assertEqual(self.place.rating_avg, 5)

    def test_bulk_delete_recalculates_rating(self):
        url = reverse('admin:catalog_placereview_changelist')
        data = {'action': 'delete_selected', '_selected_action': [self.first.pk, self.second.pk]}
        self.assertEqual(self.client.post(url, data).status_code, 200)
        self.assertEqual(PlaceReview.objects.filter(place=self.place).count(), 2)
        response = self.client.post(url, {**data, 'post': 'yes'})
        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 0)
        self.assertEqual(self.place.rating_avg, 0)

    def test_staff_without_permissions_cannot_moderate_or_delete(self):
        staff = get_user_model().objects.create_user(username='review-no-permissions', is_staff=True)
        self.client.force_login(staff)
        for action in ('approve', 'hide', 'reject', 'delete'):
            with self.subTest(action=action):
                url = reverse('admin:catalog_placereview_' + action, args=[self.first.pk])
                self.assertEqual(self.client.post(url, {'post': 'yes'}).status_code, 403)
        self.first.refresh_from_db()
        self.assertEqual(self.first.status, 'approved')
