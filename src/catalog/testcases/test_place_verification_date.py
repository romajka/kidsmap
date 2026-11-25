from datetime import datetime, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import override

from catalog.models import Place
from catalog.services.staff_roles import VOLUNTEER_GROUP


class PlaceVerificationDateTests(TestCase):
    """The public card must not present the creation date as a check of the facts."""

    def make_place(self, **kwargs):
        return Place.objects.create(
            name='Verification Museum', name_az='Yoxlama Muzeyi', name_ru='Музей проверки',
            name_en='Verification Museum', category='EDU', status='published', is_active=True, **kwargs,
        )

    def detail(self, place, lang):
        with override(lang):
            return self.client.get(place.get_absolute_url())

    def test_unverified_place_says_so_instead_of_showing_creation_date(self):
        place = self.make_place()
        for lang, text in [('ru', 'Сведения ещё не проверены редакцией'),
                           ('en', 'Information not yet checked by the editors'),
                           ('az', 'Məlumat hələ redaksiya tərəfindən yoxlanılmayıb')]:
            with self.subTest(lang=lang):
                response = self.detail(place, lang)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)
                self.assertContains(response, 'data-verification="unverified"')
                self.assertNotContains(response, 'Карточка добавлена')
                self.assertNotContains(response, 'Card added')

    def test_verified_place_shows_verification_date(self):
        place = self.make_place(last_verified_at=datetime(2026, 11, 20, 9, 0, tzinfo=dt_timezone.utc))
        response = self.detail(place, 'ru')
        self.assertContains(response, 'Сведения проверены редакцией: 20.11.2026')
        self.assertContains(response, 'data-verification="verified"')
        response = self.detail(place, 'en')
        self.assertContains(response, 'Information checked by the editors: 20.11.2026')


class PlaceMarkInfoVerifiedActionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_superuser(username='verifier', email='verifier@example.com', password='x')
        self.place = Place.objects.create(name='Pool', name_az='Hovuz', name_ru='Бассейн', name_en='Pool',
                                          category='EDU', status='published', is_active=True)

    def run_action(self):
        return self.client.post(reverse('admin:catalog_place_changelist'),
                                {'action': 'mark_info_verified', '_selected_action': [self.place.pk]}, follow=True)

    def test_staff_marks_place_as_checked_today(self):
        self.client.force_login(self.admin)
        version = self.place.content_version
        response = self.run_action()
        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_verified)  # retired badge flag stays untouched
        self.assertIsNotNone(self.place.last_verified_at)
        self.assertEqual(self.place.content_version, version + 1)

    def test_volunteer_cannot_mark_place_as_checked(self):
        User = get_user_model()
        volunteer = User.objects.create_user(username='vol', email='vol@example.com', password='x', is_staff=True)
        volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        self.client.force_login(volunteer)
        self.run_action()
        self.place.refresh_from_db()
        self.assertIsNone(self.place.last_verified_at)
