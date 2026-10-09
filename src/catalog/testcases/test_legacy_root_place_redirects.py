from django.test import TestCase, override_settings
from django.utils import timezone

from catalog.models import Place
from catalog.testcases.utils import create_quality_place


@override_settings(LOCALIZED_PLACE_URLS_ENABLED=True, PUBLIC_BASE_URL="https://kidsmap.az")
class LegacyRootPlaceRedirectTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(
            name_az="Oyuncaq Muzeyi", name_ru="Музей игрушек", name_en="Toy Museum",
            description_ru="Музей игрушек для детей", description_en="A toy museum for children",
        )
        Place.objects.filter(pk=self.place.pk).update(
            slug="old-museum", slug_az="oyuncaq-muzeyi",
            slug_ru="muzei-igrushek", slug_en="toy-museum",
        )
        self.place.refresh_from_db()

    def test_old_root_urls_redirect_once_to_localized_public_detail(self):
        for prefix, slug in (("", "oyuncaq-muzeyi"), ("/ru", "muzei-igrushek"), ("/en", "toy-museum")):
            with self.subTest(prefix=prefix):
                old = f"{prefix}/{self.place.pk}-obsolete-slug/"
                expected = f"{prefix}/place/{self.place.pk}-{slug}/"
                response = self.client.get(old, follow=True)
                self.assertEqual(response.redirect_chain, [(expected, 301)])
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.request["PATH_INFO"], expected)

    def test_head_uses_the_same_permanent_redirect(self):
        response = self.client.head(f"/en/{self.place.pk}-old-museum/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"/en/place/{self.place.pk}-toy-museum/")

    @override_settings(LOCALIZED_PLACE_URLS_ENABLED=False)
    def test_disabled_localized_urls_redirect_to_existing_public_url(self):
        for prefix in ("", "/ru", "/en"):
            with self.subTest(prefix=prefix):
                expected = f"{prefix}/place/{self.place.pk}-old-museum/"
                response = self.client.get(f"{prefix}/{self.place.pk}-obsolete/", follow=True)
                self.assertEqual(response.redirect_chain, [(expected, 301)])
                self.assertEqual(response.status_code, 200)

    def test_missing_place_remains_404_without_location(self):
        for prefix in ("", "/ru", "/en"):
            response = self.client.get(f"{prefix}/{self.place.pk + 100000}-obsolete/")
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("Location", response)

    def test_nonpublic_place_remains_404_without_disclosing_slug(self):
        for changes in ({"status": Place.STATUS_DRAFT}, {"is_active": False}, {"deleted_at": timezone.now()}):
            Place.objects.filter(pk=self.place.pk).update(
                status=Place.STATUS_PUBLISHED, is_active=True, deleted_at=None,
            )
            Place.objects.filter(pk=self.place.pk).update(**changes)
            for prefix in ("", "/ru", "/en"):
                with self.subTest(changes=changes, prefix=prefix):
                    response = self.client.get(f"{prefix}/{self.place.pk}-obsolete/")
                    self.assertEqual(response.status_code, 404)
                    self.assertNotIn("Location", response)

    def test_malformed_root_identifier_is_not_redirected(self):
        for path in ("/museum-old/", "/ru/12x-museum/", "/en/12-museum/extra/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("Location", response)
