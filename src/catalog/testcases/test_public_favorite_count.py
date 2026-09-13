from django.core.exceptions import ValidationError
from django.test import TestCase
from django.template.loader import render_to_string

from django.contrib.auth.models import User

from catalog.models import Place, PlaceLike, SiteSettings
from catalog.services.public_favorite_count import build_public_favorite_count


class PublicFavoriteCountSettingsTests(TestCase):
    def test_disabled_by_default(self):
        settings = SiteSettings()
        self.assertFalse(settings.public_favorites_count_enabled)

    def test_activation_requires_threshold(self):
        settings = SiteSettings(public_favorites_count_enabled=True, public_favorites_minimum=None)
        with self.assertRaises(ValidationError):
            settings.full_clean()

    def test_exact_threshold_uses_authoritative_count(self):
        place = Place.objects.create(name="Public favorites", category="EDU")
        user = User.objects.create_user("public-favorite")
        PlaceLike.objects.create(place=place, user=user)
        config = SiteSettings(public_favorites_count_enabled=True, public_favorites_minimum=1)
        result = build_public_favorite_count(place_id=place.pk, site_settings=config)
        self.assertTrue(result.visible)
        self.assertEqual(result.count, 1)
        html = render_to_string("catalog/includes/favorite_social_proof.html", {"favorite_social_proof": result})
        self.assertIn("favorite-social-proof", html)

    def test_partial_is_not_silently_activated_on_public_place(self):
        place = Place.objects.create(name="Hidden proof", category="EDU", is_active=True)
        response = self.client.get("/ru" + place.get_absolute_url())
        self.assertNotContains(response, "favorite-social-proof")

    def test_enabled_count_is_rendered_on_public_place_detail(self):
        place = Place.objects.create(name="Visible proof", category="EDU", is_active=True)
        user = User.objects.create_user("visible-public-favorite")
        PlaceLike.objects.create(place=place, user=user)
        settings = SiteSettings.get_solo()
        settings.public_favorites_count_enabled = True
        settings.public_favorites_minimum = 1
        settings.save()

        response = self.client.get("/ru" + place.get_absolute_url())

        self.assertContains(response, "favorite-social-proof")
        self.assertContains(response, "Сохранил 1 пользователь")
