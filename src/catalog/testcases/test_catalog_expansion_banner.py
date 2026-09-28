from django.test import TestCase
from django.urls import reverse

class CatalogExpansionBannerTests(TestCase):
    def test_catalog_expansion_banner_renders_in_place_list_default_az(self):
        url = reverse('place_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('catalog-expansion-banner', content)
        self.assertIn(reverse('add_place'), content)
        # Default language AZ check
        self.assertIn('KidsMap bazası böyüyür', content)
        self.assertIn('Məkan əlavə et', content)

    def test_catalog_expansion_banner_renders_ru_and_en(self):
        # Russian test
        response_ru = self.client.get('/ru/catalog/')
        self.assertEqual(response_ru.status_code, 200)
        content_ru = response_ru.content.decode()
        self.assertIn('catalog-expansion-banner', content_ru)
        self.assertIn('База KidsMap постоянно растёт', content_ru)
        self.assertIn('Добавить место', content_ru)

        # English test
        response_en = self.client.get('/en/catalog/')
        self.assertEqual(response_en.status_code, 200)
        content_en = response_en.content.decode()
        self.assertIn('catalog-expansion-banner', content_en)
        self.assertIn('KidsMap is expanding', content_en)
        self.assertIn('Add a place', content_en)
