from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from catalog.models import CatalogContentSettings, Place, PlaceScheduleDay, Subcategory
from catalog.services.seo_landing_aggregates import build_judo_landing_aggregates
from catalog.testcases.utils import create_quality_place


class JudoSeoLandingAggregateTests(TestCase):
    slug = "dzudo-dlya-detey-v-baku"

    def setUp(self):
        self.subcategory, _created = Subcategory.objects.get_or_create(
            code="judo",
            defaults={
                "category_id": "SPRT",
                "name": "Дзюдо",
                "name_ru": "Дзюдо",
                "name_az": "Cüdo",
                "name_en": "Judo",
                "is_active": True,
            },
        )
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.seo_pages_json = {
            language: {
                self.slug: {
                    "title": {"az": "Bakıda uşaqlar üçün cüdo", "ru": "Дзюдо для детей в Баку", "en": "Judo for children in Baku"}[language],
                    "meta_description": "Current published judo listings in Baku.",
                    "intro": "Current data from real listings.",
                    "benefits": ["Real listings"],
                    "catalog_query": "?q=judo&district=baku",
                    "comparison_key": "judo",
                    "faq": [["How is the data selected?", "From public listings."]],
                }
            }
            for language in ("az", "ru", "en")
        }
        settings_obj.save(update_fields=["seo_pages_json", "updated_at"])

        self.first = create_quality_place(
            name="Yasamal Judo",
            name_ru="Дзюдо Ясамал",
            name_az="Yasamal Cüdo",
            name_en="Yasamal Judo",
            category="SPRT",
            subcategory=self.subcategory,
            district="baku_yasamal",
            metro="Низами",
            age_from=5,
            age_to=12,
            price_from=80,
            price_to=120,
            schedule="Понедельник и среда, 18:00",
        )
        self.second = create_quality_place(
            name="Narimanov Judo",
            name_ru="Дзюдо Нариманов",
            name_az="Nərimanov Cüdo",
            name_en="Narimanov Judo",
            category="SPRT",
            subcategory=self.subcategory,
            district="baku_narimanov",
            metro="",
            age_from=7,
            age_to=None,
            age_open_ended=True,
            price_from=None,
            price_to=None,
            price_per_month=150,
            schedule="",
            lesson_format=Place.LESSON_FORMAT_GROUP,
            lessons_per_week=2,
        )
        PlaceScheduleDay.objects.create(
            place=self.second,
            weekday="tue",
            is_closed=False,
            is_24_hours=True,
        )
        create_quality_place(
            name="Hidden Judo",
            name_ru="Скрытое дзюдо",
            category="SPRT",
            subcategory=self.subcategory,
            district="baku_khatai",
            status=Place.STATUS_DRAFT,
        )

    def test_ru_page_aggregates_missing_price_open_age_and_multiple_districts(self):
        response = self.client.get(f"/ru/catalog/{self.slug}/")

        self.assertEqual(response.status_code, 200)
        aggregate = response.context["seo_aggregate"]
        self.assertEqual(aggregate["count"], 2)
        self.assertEqual((aggregate["price_min"], aggregate["price_max"]), (80, 120))
        self.assertEqual(aggregate["known_price_count"], 1)
        self.assertFalse(aggregate["price_coverage_complete"])
        self.assertEqual(aggregate["age_min"], 5)
        self.assertIsNone(aggregate["age_max"])
        self.assertTrue(aggregate["age_open_ended"])
        self.assertEqual(len(aggregate["districts"]), 2)
        self.assertIn("Баку, Ясамальский район", aggregate["districts"])
        self.assertIn("Баку, Наримановский район", aggregate["districts"])
        self.assertNotIn("Скрытое дзюдо", response.content.decode())
        self.assertContains(response, "указан не у всех секций: 1 из 2")
        self.assertContains(response, "От 5 лет, верхняя граница не указана")
        self.assertContains(response, "1 месяц: 150 AZN")
        self.assertContains(response, "Групповые · Занятий в неделю: 2")
        self.assertNotContains(response, "24 часа")
        self.assertContains(response, "Последнее обновление данных")

    def test_az_and_en_pages_localize_interface_and_empty_values(self):
        az_response = self.client.get(f"/catalog/{self.slug}/")
        en_response = self.client.get(f"/en/catalog/{self.slug}/")

        self.assertContains(az_response, "Real cüdo bölmələri üzrə məlumatlar")
        self.assertContains(az_response, "Göstərilməyib")
        self.assertContains(en_response, "Data from real judo listings")
        self.assertContains(en_response, "Not provided")
        self.assertContains(en_response, "From age 5; no upper limit provided")

    def test_aggregate_query_count_does_not_grow_per_place(self):
        page = CatalogContentSettings.get_solo().seo_pages("ru")[self.slug]

        # Feature settings, listings and one tariff prefetch, regardless of rows.
        with CaptureQueriesContext(connection) as queries:
            aggregate = build_judo_landing_aggregates(
                seo_slug=self.slug,
                page=page,
                language_code="ru",
            )

        self.assertLessEqual(len(queries), 3)
        self.assertEqual(len(aggregate["rows"]), 2)
