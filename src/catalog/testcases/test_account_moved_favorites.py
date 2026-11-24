from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Category, Place, PlaceLike, PlaceSpecialistMove, SiteSettings, Specialist


class MovedPlaceFavoriteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='saved-before-move')
        self.other = get_user_model().objects.create_user(username='other-favorites')
        self.client.force_login(self.user)
        self.settings = SiteSettings.get_solo()
        self.settings.specialists_section_enabled = True
        self.settings.save()
        category, _ = Category.objects.get_or_create(code='EDU', defaults={'name': 'Education'})
        self.place = Place.objects.create(name='Former class', category=category, is_active=True, status='published')
        self.like = PlaceLike.objects.create(place=self.place, user=self.user)
        self.specialist = Specialist.objects.create(name='Actual teacher', slug='actual-teacher',
                                                    is_active=True, status=Specialist.STATUS_PUBLISHED)
        PlaceSpecialistMove.objects.create(place=self.place, specialist=self.specialist)
        Place.objects.filter(pk=self.place.pk).update(status='draft', is_active=False)
        self.ordinary = Place.objects.create(name='Ordinary favorite', name_az='Adi məkan', category=category,
                                             is_active=True, status='published')
        self.ordinary_like = PlaceLike.objects.create(user=self.user, place=self.ordinary)

    def test_prior_favorite_links_to_real_profile_in_both_account_views(self):
        for lang in ('az', 'en', 'ru'):
            with self.subTest(lang=lang), override(lang):
                for route in ('account_dashboard', 'account_favorites'):
                    response = self.client.get(reverse(route))
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.context['favorites_count'], 2)
                    self.assertEqual(
                        [entry['target'] for entry in response.context['favorite_entries']],
                        [self.ordinary, self.specialist],
                    )
                    self.assertContains(response, f'href="{self.specialist.get_absolute_url()}"')
                    self.assertContains(response, self.specialist.name)
                    self.assertNotContains(response, f'href="{self.place.get_absolute_url()}"')
                    self.assertContains(response, f'href="{self.ordinary.get_absolute_url()}"')
                    if route == 'account_favorites':
                        self.assertContains(response, 'name="remove_moved_favorite"')
                self.assertEqual(self.client.get(self.specialist.get_absolute_url()).status_code, 200)

    def test_draft_disabled_and_other_users_never_gain_a_link(self):
        for status, active, section in [('draft', True, True), ('published', False, True),
                                         ('published', True, False)]:
            with self.subTest(status=status, active=active, section=section):
                Specialist.objects.filter(pk=self.specialist.pk).update(status=status, is_active=active)
                self.settings.specialists_section_enabled = section
                self.settings.save()
                response = self.client.get(reverse('account_favorites'))
                self.assertEqual(response.context['favorites_count'], 1)
                self.assertNotContains(response, self.specialist.get_absolute_url())
        self.settings.specialists_section_enabled = True
        self.settings.save()
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(reverse('account_favorites')), self.specialist.get_absolute_url())

    def test_removal_is_private_and_idempotent(self):
        url = reverse('account_favorites')
        payload = {'remove_moved_favorite': str(self.like.pk)}
        self.client.force_login(self.other)
        self.client.post(url, payload)
        self.assertTrue(PlaceLike.objects.filter(pk=self.like.pk).exists())
        self.client.logout()
        self.assertEqual(self.client.post(url, payload).status_code, 302)
        self.assertTrue(PlaceLike.objects.filter(pk=self.like.pk).exists())

        self.client.force_login(self.user)
        self.client.post(url, {'remove_moved_favorite': self.ordinary_like.pk})
        self.assertTrue(PlaceLike.objects.filter(pk=self.ordinary_like.pk).exists())
        for _ in range(2):
            self.assertRedirects(self.client.post(url, payload), url, fetch_redirect_response=False)
        self.assertFalse(PlaceLike.objects.filter(place=self.place).exists())
        self.assertTrue(PlaceLike.objects.filter(place=self.ordinary, user=self.user).exists())
        self.assertEqual(self.client.post(reverse('toggle_place_like', args=[self.place.pk])).status_code, 404)
