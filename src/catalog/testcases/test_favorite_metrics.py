from django.contrib.auth.models import User
from django.test import TestCase

from catalog.models import AnalyticsActorExclusion, Place, PlaceLike
from catalog.services.favorite_metrics import eligible_favorites_count, reconcile_place_favorite_counts


class FavoriteMetricTests(TestCase):
    def setUp(self):
        self.place = Place.objects.create(name="Favorite place", category="EDU", is_active=True)

    def test_only_active_nonexcluded_registered_users_count(self):
        active = User.objects.create_user("active")
        inactive = User.objects.create_user("inactive", is_active=False)
        excluded = User.objects.create_user("excluded")
        PlaceLike.objects.create(place=self.place, user=active)
        PlaceLike.objects.create(place=self.place, user=inactive)
        PlaceLike.objects.create(place=self.place, user=excluded)
        AnalyticsActorExclusion.objects.create(user=excluded, reason_code="staff_test")
        self.assertEqual(eligible_favorites_count(place_id=self.place.pk), 1)

    def test_reconcile_repairs_cached_count(self):
        user = User.objects.create_user("saved")
        PlaceLike.objects.create(place=self.place, user=user)
        Place.objects.filter(pk=self.place.pk).update(likes_count=99)
        result = reconcile_place_favorite_counts(place_ids=[self.place.pk])
        self.place.refresh_from_db()
        self.assertEqual(result.changed, 1)
        self.assertEqual(self.place.likes_count, 1)

    def test_user_deactivation_reconciles_cached_count(self):
        user = User.objects.create_user("later-inactive")
        PlaceLike.objects.create(place=self.place, user=user)
        self.place.refresh_from_db()
        self.assertEqual(self.place.likes_count, 1)
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.place.refresh_from_db()
        self.assertEqual(self.place.likes_count, 0)
