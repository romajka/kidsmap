from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from catalog.models import Place, PlaceReview, PlaceLike, WorkflowNotification


class AccountNavigationBadgesTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='nav_badge_user',
            email='nav_badge_user@example.com',
            password='TestPassword123!',
        )
        self.place = Place.objects.create(
            owner=self.user,
            name_az='Nav Place 1',
            category='EDU',
            status='published',
            is_active=True,
        )
        self.place2 = Place.objects.create(
            name_az='Nav Place 2',
            category='EDU',
            status='published',
            is_active=True,
        )
        PlaceReview.objects.create(
            user=self.user,
            place=self.place,
            rating=5,
            text='Great place!',
            status='approved',
        )
        PlaceLike.objects.create(
            user=self.user,
            place=self.place2,
        )
        WorkflowNotification.objects.create(
            recipient_user=self.user,
            recipient_email='',
            recipient_key=f'user:{self.user.pk}',
            event_kind='moderation_decision',
            entity_type='volunteer_revision',
            entity_id=1,
            entity_version=1,
        )

    def test_sidebar_badges_consistent_across_all_account_pages(self):
        self.client.force_login(self.user)
        routes = [
            reverse('account_dashboard'),
            reverse('owner_places_dashboard'),
            reverse('owner_reviews_dashboard'),
            reverse('account_favorites'),
            reverse('account_notifications'),
            reverse('account_settings'),
        ]
        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                html = response.content.decode()
                # 1 badge in sidebar
                self.assertIn('>1</span>', html)
                # verify navigation links exist
                self.assertIn(reverse('owner_places_dashboard'), html)
                self.assertIn(reverse('owner_reviews_dashboard'), html)
                self.assertIn(reverse('account_favorites'), html)
                self.assertIn(reverse('account_notifications'), html)
