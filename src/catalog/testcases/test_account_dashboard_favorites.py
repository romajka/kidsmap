"""Account overview must render real favorite Place objects with or without ratings."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Category, Place, PlaceLike


class AccountDashboardFavoritesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="dashboard-favorites", email="dashboard-favorites@example.invalid"
        )
        self.client.force_login(self.user)
        self.client.raise_request_exception = False
        category, _ = Category.objects.get_or_create(code="EDU", defaults={"name": "Education"})
        self.place = Place.objects.create(
            name="Favorite learning club",
            name_az="Sevimli dərnək",
            name_ru="Любимый кружок",
            name_en="Favorite learning club",
            category=category,
            status=Place.STATUS_PUBLISHED,
            is_active=True,
        )

    def test_overview_shows_rated_favorite_in_each_language(self):
        # Removing support for a real rated favorite must break this HTTP contract.
        Place.objects.filter(pk=self.place.pk).update(rating_avg=4.5, rating_count=2)
        PlaceLike.objects.create(place=self.place, user=self.user)
        for language, rating in (("az", "4,5"), ("ru", "4,5"), ("en", "4.5")):
            with self.subTest(language=language), override(language):
                response = self.client.get(reverse("account_dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "fav-chip-star")
                self.assertContains(response, rating)

    def test_overview_keeps_unrated_favorite_without_star_badge(self):
        PlaceLike.objects.create(place=self.place, user=self.user)
        with override("ru"):
            response = self.client.get(reverse("account_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Любимый кружок")
        self.assertNotContains(response, "fav-chip-star")

    def test_overview_opens_without_favorites(self):
        response = self.client.get(reverse("account_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["favorites_count"], 0)
