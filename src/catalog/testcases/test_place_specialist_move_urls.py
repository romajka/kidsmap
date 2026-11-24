from django.db.models.deletion import ProtectedError
from django.test import RequestFactory, TestCase
from django.utils.translation import override

from catalog.models import Place, PlaceSpecialistMove, SiteSettings, Specialist
from catalog.testcases.utils import create_quality_place


class PlaceSpecialistMoveUrlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.place = create_quality_place(
            name_az='Köhnə dərnək', name_ru='Старый клуб', name_en='Old club',
        )
        cls.specialist = Specialist.objects.create(
            name='New specialist', slug='new-specialist',
            status=Specialist.STATUS_PUBLISHED, is_active=True,
        )
        cls.move = PlaceSpecialistMove.objects.create(place=cls.place, specialist=cls.specialist)
        Place.objects.filter(pk=cls.place.pk).update(is_active=False)
        settings = SiteSettings.get_solo()
        settings.specialists_section_enabled = True
        settings.save()

    def test_all_previous_public_addresses_redirect_straight_to_localized_profile(self):
        for language, prefix in [('az', ''), ('ru', '/ru'), ('en', '/en'), ('az', '/az')]:
            with override(language):
                expected = self.specialist.get_absolute_url()
                old_slug = getattr(self.place, f'public_slug_{language}')
            for path in (
                f'/place/{old_slug}/', f'/place/{self.place.pk}/',
                f'/place/{self.place.pk}-obsolete/', f'/{self.place.pk}-obsolete/',
            ):
                with self.subTest(prefix=prefix, path=path):
                    response = self.client.get(f'{prefix}{path}?utm_source=old')
                    self.assertRedirects(response, expected, status_code=301)
        self.assertRedirects(
            self.client.head(f'/en/place/{self.place.pk}/'),
            '/en/specialists/new-specialist/', status_code=301, fetch_redirect_response=False,
        )

    def test_views_accept_existing_positional_arguments(self):
        from catalog.views.public import place_detail, place_detail_legacy

        request = RequestFactory().get(f'/en/place/{self.place.pk}-old/')
        request.LANGUAGE_CODE = 'en'
        for view in (place_detail, place_detail_legacy):
            response = view(request, self.place.pk, 'old')
            self.assertEqual(response.status_code, 301)
            self.assertEqual(response['Location'], '/en/specialists/new-specialist/')

    def test_unpublished_inactive_or_disabled_target_is_never_disclosed(self):
        for changes in ({'status': Specialist.STATUS_PENDING}, {'is_active': False}):
            Specialist.objects.filter(pk=self.specialist.pk).update(**changes)
            response = self.client.get(f'/ru/place/{self.place.pk}-old/')
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('Location', response)
            Specialist.objects.filter(pk=self.specialist.pk).update(
                status=Specialist.STATUS_PUBLISHED, is_active=True,
            )
        settings = SiteSettings.get_solo()
        settings.specialists_section_enabled = False
        settings.save()
        self.assertEqual(self.client.get(f'/en/{self.place.pk}-old/').status_code, 404)

    def test_wrong_ids_languages_and_unmapped_hidden_places_stay_private(self):
        hidden = create_quality_place(is_active=False, status=Place.STATUS_DRAFT)
        for path in (
            f'/place/{hidden.pk}-{self.place.public_slug_az}/',
            f'/en/place/{self.place.pk + 1000}-{self.place.public_slug_en}/',
            f'/ru/place/{self.place.public_slug_en}/',
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn('Location', response)

    def test_existing_public_place_and_submission_routes_keep_their_behaviour(self):
        for suffix in ('like/', 'review/', 'ownership-request/'):
            for prefix in ('', '/az', '/en'):
                response = self.client.post(f'{prefix}/place/{self.place.pk}/{suffix}')
                self.assertNotIn('/specialists/', response.get('Location', ''))
        self.assertEqual(self.client.post(f'/place/{self.place.pk}/').status_code, 404)
        Place.objects.filter(pk=self.place.pk).update(is_active=True)
        with override('az'):
            expected = self.place.get_absolute_url()
        self.assertRedirects(self.client.get(f'/place/{self.place.pk}/'), expected, status_code=301)
        self.assertRedirects(
            self.client.get('/az' + expected), expected, status_code=301,
        )

    def test_mapping_protects_both_records(self):
        self.assertEqual(self.move.localized_seo, {})
        self.assertEqual(self.specialist.place_move.pk, self.place.specialist_move.pk)
        for obj in (self.place, self.specialist):
            with self.assertRaises(ProtectedError):
                obj.delete()
