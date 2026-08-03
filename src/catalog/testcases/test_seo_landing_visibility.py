from django.test import TestCase

from catalog.models import CatalogContentSettings, Place
from catalog.services.seo_landing_visibility import build_seo_landing_visibility
from catalog.testcases.utils import create_quality_place


class SeoLandingIndexabilityTests(TestCase):
    weak_slug = "threshold-page"
    strong_slug = "strong-page"

    def setUp(self):
        content_settings = CatalogContentSettings.get_solo()
        content_settings.seo_pages_json = {
            language: {
                self.weak_slug: self._page(
                    title={
                        "az": "Hədd səhifəsi",
                        "ru": "Страница порога",
                        "en": "Threshold page",
                    }[language],
                    catalog_query="?category=EDU",
                ),
                self.strong_slug: self._page(
                    title={
                        "az": "Güclü seçim",
                        "ru": "Сильная подборка",
                        "en": "Strong collection",
                    }[language],
                    catalog_query="?category=ART",
                ),
            }
            for language in ("az", "ru", "en")
        }
        content_settings.save(update_fields=["seo_pages_json", "updated_at"])
        self.content_settings = content_settings

    @staticmethod
    def _page(*, title, catalog_query):
        return {
            "title": title,
            "meta_description": f"{title}: verified KidsMap listings.",
            "intro": f"{title}: current catalog results.",
            "benefits": ["Current public listings"],
            "catalog_query": catalog_query,
            "faq": [["How are listings selected?", "By the real catalog filter."]],
        }

    @staticmethod
    def _landing_paths(slug):
        return (
            f"/catalog/{slug}/",
            f"/ru/catalog/{slug}/",
            f"/en/catalog/{slug}/",
        )

    def _create_places(self, count, *, category):
        for index in range(count):
            create_quality_place(
                name=f"Quality {category} place {index}",
                name_az=f"Keyfiyyətli {category} məkanı {index}",
                category=category,
            )

    def test_zero_cards_keeps_all_languages_available_but_noindex(self):
        expected_count_labels = (
            "0 məkan tapıldı",
            "Найдено 0 карточек",
            "0 listings found",
        )

        for path, count_label in zip(
            self._landing_paths(self.weak_slug), expected_count_labels
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    '<meta name="robots" content="noindex,follow" />',
                    html=False,
                )
                self.assertContains(
                    response,
                    '<meta name="googlebot" content="noindex,follow" />',
                    html=False,
                )
                self.assertContains(response, count_label)
                self.assertContains(
                    response,
                    f'<link rel="alternate" hreflang="az" href="http://testserver/catalog/{self.weak_slug}/" />',
                    html=False,
                )
                self.assertContains(
                    response,
                    f'<link rel="alternate" hreflang="ru" href="http://testserver/ru/catalog/{self.weak_slug}/" />',
                    html=False,
                )
                self.assertContains(
                    response,
                    f'<link rel="alternate" hreflang="en" href="http://testserver/en/catalog/{self.weak_slug}/" />',
                    html=False,
                )

        sitemap = self.client.get("/sitemap.xml")
        self.assertNotContains(sitemap, f"/catalog/{self.weak_slug}/")

    def test_four_cards_stays_noindex_and_is_hidden_from_useful_collections(self):
        self._create_places(4, category="EDU")
        self._create_places(5, category="ART")

        weak_response = self.client.get(f"/ru/catalog/{self.weak_slug}/")
        strong_response = self.client.get(f"/ru/catalog/{self.strong_slug}/")
        sitemap = self.client.get("/sitemap.xml")

        self.assertContains(weak_response, "Найдено 4 карточки")
        self.assertContains(
            weak_response,
            '<meta name="robots" content="noindex,follow" />',
            html=False,
        )
        self.assertContains(weak_response, "Сильная подборка")
        self.assertNotContains(strong_response, "Страница порога")
        self.assertNotContains(sitemap, f"/catalog/{self.weak_slug}/")
        self.assertContains(sitemap, f"/catalog/{self.strong_slug}/")

    def test_five_cards_automatically_indexes_all_languages_and_returns_to_sitemap(self):
        self._create_places(5, category="EDU")
        create_quality_place(
            name="Excluded draft place",
            name_az="Dərc olunmamış məkan",
            category="EDU",
            status=Place.STATUS_DRAFT,
        )

        for path in self._landing_paths(self.weak_slug):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />',
                    html=False,
                )
                self.assertContains(
                    response,
                    f'<link rel="alternate" hreflang="x-default" href="http://testserver/catalog/{self.weak_slug}/" />',
                    html=False,
                )

        ru_response = self.client.get(f"/ru/catalog/{self.weak_slug}/")
        self.assertContains(ru_response, "Найдено 5 карточек")

        sitemap = self.client.get("/sitemap.xml")
        for path in self._landing_paths(self.weak_slug):
            self.assertContains(sitemap, path)

        filtered_catalog = self.client.get("/ru/catalog/", {"category": "EDU"})
        self.assertContains(filtered_catalog, '<meta name="robots" content="noindex,follow" />', html=False)

    def test_current_landing_filters_are_counted_in_one_database_query(self):
        # One feature-flag lookup from public_place_queryset plus one aggregate
        # for every SEO landing configured in all three languages.
        with self.assertNumQueries(2):
            visibility = build_seo_landing_visibility(self.content_settings)

        self.assertEqual(visibility.pages("az")[self.weak_slug]["matching_count"], 0)
