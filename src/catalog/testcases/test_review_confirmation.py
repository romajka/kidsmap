from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import PlaceReview, SiteReview, Specialist, SpecialistReview, SiteSettings
from catalog.services.content_quality import approved_review_queryset
from catalog.testcases.utils import create_quality_place


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=0)
class ReviewConfirmationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='confirmation-user')
        self.client.force_login(self.user)
        self.place = create_quality_place()
        site = SiteSettings.get_solo()
        site.specialists_section_enabled = True
        site.save()
        self.specialist = Specialist.objects.create(name="Test specialist", slug="confirmation-specialist",
                                                     owner=self.user, status="published", is_active=True)

    def test_post_confirmation_visible_once_after_redirect_in_all_languages(self):
        for language, heading in {
            'ru': 'Спасибо! Отзыв отправлен на модерацию',
            'az': 'Təşəkkür edirik! Rəyiniz yoxlanışa göndərildi',
            'en': 'Thank you! Your review was submitted for moderation.',
        }.items():
            with self.subTest(language=language), override(language):
                response = self.client.post(reverse('add_place_review', args=[self.place.pk]),
                                            {'rating': '5', 'text': 'Unique unpublished review text'}, follow=True)
                self.assertContains(response, heading)
                self.assertContains(response, 'data-review-notice')
                review = PlaceReview.objects.filter(place=self.place, user=self.user).latest('created_at')
                self.assertEqual(review.status, 'pending')
                self.assertFalse(review.is_approved)
                self.assertFalse(approved_review_queryset(PlaceReview.objects.all()).exists())
                self.assertNotContains(response, 'Unique unpublished review text')
                self.assertNotContains(self.client.get(response.redirect_chain[-1][0]), '<strong data-review-title>'+heading)

    def test_ajax_success_history_or_update_and_validation(self):
        for name, args, model in [('add_place_review', [self.place.pk], PlaceReview),
                                  ('add_site_review', [], SiteReview),
                                  ('add_specialist_review', [self.specialist.pk], SpecialistReview)]:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                for _ in range(2):
                    response = self.client.post(url, {'rating': '5', 'text': 'A useful review for moderation'},
                                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.json()['ok'])
                self.assertEqual(model.objects.filter(user=self.user).count(), 2 if model is PlaceReview else 1)
                self.assertEqual(model.objects.filter(user=self.user).latest('created_at').status, 'pending')
                response = self.client.post(url, {'rating': '9', 'text': 'Invalid rating'},
                                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 400)
                self.assertFalse(response.json()['ok'])
                self.assertTrue(all(rating == 5 for rating in model.objects.filter(user=self.user).values_list('rating', flat=True)))

    def test_place_review_is_pending_from_first_save(self):
        from django.db.models.signals import post_save
        observed = []

        def observe(sender, instance, **kwargs):
            observed.append((instance.status, instance.is_approved))

        post_save.connect(observe, sender=PlaceReview)
        try:
            self.client.post(reverse('add_place_review', args=[self.place.pk]),
                             {'rating': '5', 'text': 'Review must never be published before moderation'})
        finally:
            post_save.disconnect(observe, sender=PlaceReview)
        self.assertTrue(observed)
        self.assertTrue(all(status == 'pending' and not approved for status, approved in observed), observed)

    def test_post_validation_error_and_success_for_each_review_scope(self):
        for name, args, model in [('add_place_review', [self.place.pk], PlaceReview),
                                  ('add_site_review', [], SiteReview),
                                  ('add_specialist_review', [self.specialist.pk], SpecialistReview)]:
            with self.subTest(name=name), override('ru'):
                url = reverse(name, args=args)
                response = self.client.post(url, {'rating': '9'}, follow=True)
                self.assertContains(response, 'Оценка вне диапазона')
                self.assertNotContains(response, 'Спасибо! Отзыв отправлен на модерацию')
                self.assertFalse(model.objects.filter(user=self.user).exists())
                response = self.client.post(url, {'rating': '5', 'text': 'Unpublished fixture review content'}, follow=True)
                self.assertContains(response, 'Спасибо! Отзыв отправлен на модерацию')
                self.assertNotContains(response, 'Unpublished fixture review content')
                self.assertFalse(model.objects.get(user=self.user).is_approved)
                self.client.get(response.redirect_chain[-1][0])
                self.assertEqual(model.objects.filter(user=self.user).count(), 1)

    def test_expired_session_never_returns_success(self):
        self.client.logout()
        for name, args in [('add_place_review', [self.place.pk]), ('add_site_review', []),
                           ('add_specialist_review', [self.specialist.pk])]:
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=args), {'rating': '5', 'text': 'No session'},
                                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 401)
                self.assertTrue(response.json()['auth_required'])
                self.assertFalse(response.json().get('ok', False))

    def review_routes(self):
        return [('add_place_review', [self.place.pk], PlaceReview, self.place.get_absolute_url()),
                ('add_site_review', [], SiteReview, reverse('site_reviews')),
                ('add_specialist_review', [self.specialist.pk], SpecialistReview, self.specialist.get_absolute_url())]

    def test_invalid_rating_and_text_boundaries_in_all_languages(self):
        for language in ('ru', 'az', 'en'):
            with override(language):
                for name, args, model, _ in self.review_routes():
                    for rating in ('', '0', '6', '-1', 'abc', '2.5'):
                        with self.subTest(language=language, scope=name, rating=rating):
                            response = self.client.post(reverse(name, args=args),
                                                        {'rating': rating, 'text': 'A valid review body'},
                                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                            self.assertEqual(response.status_code, 400)
                            self.assertFalse(response.json()['ok'])
                            self.assertTrue(response.json()['message'])
                            self.assertEqual(response.json()['title'], '')
                    response = self.client.post(reverse(name, args=args), {'rating': '5', 'text': 'x' * 5001},
                                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertEqual(response.status_code, 400)
                    self.assertFalse(model.objects.filter(user=self.user).exists())

    def test_empty_text_requirement_matches_existing_scope_rules(self):
        for name, args, model, _ in self.review_routes():
            with self.subTest(scope=name):
                response = self.client.post(reverse(name, args=args), {'rating': '5', 'text': '  '},
                                            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                allowed = name == 'add_site_review'
                self.assertEqual(response.status_code, 200 if allowed else 400)
                self.assertEqual(model.objects.filter(user=self.user).exists(), allowed)

    def test_edit_of_approved_review_returns_to_pending_and_stays_single(self):
        for name, args, model, public_url in self.review_routes():
            if model is PlaceReview:
                continue  # Place history/cooldown is covered in test_place_review_cooldown.
            with self.subTest(scope=name):
                url = reverse(name, args=args)
                self.client.post(url, {'rating': '5', 'text': 'A public review fixture with enough useful detail'})
                review = model.objects.get(user=self.user)
                review.status = 'approved'
                review.save()
                review.refresh_from_db()
                self.assertTrue(review.is_approved)
                self.assertContains(self.client.get(public_url), review.text)
                for rating in range(1, 6):
                    response = self.client.post(url, {'rating': str(rating), 'text': 'Edited review pending moderation'},
                                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                    self.assertTrue(response.json()['ok'])
                    review.refresh_from_db()
                    self.assertEqual(review.rating, rating)
                    self.assertEqual(review.status, 'pending')
                    self.assertFalse(review.is_approved)
                    self.assertEqual(model.objects.filter(user=self.user).count(), 1)
                self.assertNotContains(self.client.get(public_url), 'Edited review pending moderation')
                review.status = 'rejected'
                review.save()
                self.assertNotContains(self.client.get(public_url), review.text)

    def test_missing_csrf_does_not_save_review(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        for name, args, model, _ in self.review_routes():
            with self.subTest(scope=name):
                response = client.post(reverse(name, args=args), {'rating': '5', 'text': 'Missing CSRF'},
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')
                self.assertEqual(response.status_code, 403)
                self.assertFalse(model.objects.filter(user=self.user).exists())
