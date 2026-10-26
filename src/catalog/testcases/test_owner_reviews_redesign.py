from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import Place, PlaceReview


class OwnerReviewsRedesignTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(
            username='rev_owner_test',
            email='rev_owner@example.com',
            password='TestPassword123!',
        )
        self.reviewer = User.objects.create_user(
            username='reviewer_parent',
            email='reviewer@example.com',
            password='TestPassword123!',
            first_name='Айсель',
            last_name='Мамедова',
        )
        self.place = Place.objects.create(
            owner=self.owner,
            name_az='Test Uşaq Mərkəzi',
            name_ru='Тестовый Детский Центр',
            category='EDU',
            status='published',
            is_active=True,
        )
        self.review = PlaceReview.objects.create(
            user=self.reviewer,
            place=self.place,
            author_name='Айсель Мамедова',
            rating=4,
            text='Отличный центр, преподаватели внимательные и чуткие!',
            status='approved',
            is_approved=True,
        )

    def test_owner_reviews_renders_cards_avatar_stars_and_reply_button(self):
        self.client.force_login(self.owner)
        response = self.client.get('/ru/account/places/reviews/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        # Check card structure
        self.assertIn('account-review-card', html)
        self.assertIn('account-review-avatar', html)
        self.assertIn('account-review-stars', html)
        self.assertIn('star-filled', html)

        # Check author initials / name
        self.assertIn('Айсель Мамедова', html)

        # Check action buttons
        self.assertIn('Ответить на отзыв', html)
        self.assertIn('Страница места', html)
        self.assertIn(reverse('typed_reviews', args=['place', self.place.pk]), html)
        self.assertIn(self.place.get_absolute_url(), html)

        # Check review text and moderation badge
        self.assertIn('Отличный центр', html)
        self.assertIn('Одобрен', html)
