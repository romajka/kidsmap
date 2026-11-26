"""SQL ceilings for complete anonymous page requests on the Stage 1 fixture."""
from datetime import datetime, time, timedelta

from django.core.cache import cache
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.utils import timezone, translation

from catalog.models import CatalogContentSettings, Category, Event, SiteSettings, Specialist, Subcategory
from catalog.testcases.utils import create_ready_place


SEO_SLUG = "dzudo-dlya-detey-v-baku"


def create_page_fixture():
    settings = SiteSettings.get_solo()
    settings.events_section_enabled = settings.specialists_section_enabled = True
    settings.save(update_fields=["events_section_enabled", "specialists_section_enabled"])
    category, _ = Category.objects.get_or_create(code="SPRT", defaults={"name_az": "İdman"})
    judo, _ = Subcategory.objects.get_or_create(
        code="judo", defaults={"category": category, "name_az": "Cüdo", "name_ru": "Дзюдо"},
    )
    content = CatalogContentSettings.get_solo()
    content.seo_pages_json = {
        "ru": {SEO_SLUG: {
            "title": "Stage1 Judo в Баку", "intro": "Детские занятия дзюдо",
            "meta_description": "Stage1 Judo", "benefits": ["Тестовые секции"],
            "faq": [["Какие секции вошли?", "Опубликованные секции дзюдо."]],
            "catalog_query": "?q=judo&district=baku", "comparison_key": "judo",
        }},
    }
    content.save(update_fields=["seo_pages_json", "updated_at"])
    return judo


def add_places(judo, first, last):
    """Each group of five places also adds one visible event and one specialist."""
    tomorrow = timezone.localdate() + timedelta(days=1)
    starts_at = timezone.make_aware(datetime.combine(tomorrow, time(12)))
    for number in range(first, last + 1):
        name = f"Stage1 Judo {number:02d}"
        place = create_ready_place(
            name=name, name_az=name, name_ru=name, name_en=name, category="SPRT",
            subcategory=judo, district="baku_yasamal", lat=40.39 + number / 10000,
            lng=49.81 + number / 10000,
        )
        if number % 5 == 0:
            event_name = f"Stage1 Festival {number}"
            Event.objects.create(
                name=event_name, name_az=event_name, name_ru=event_name,
                status=Event.STATUS_PUBLISHED, category_id="SPRT",
                start_datetime=starts_at, end_datetime=starts_at + timedelta(hours=2),
            )
            Specialist.objects.create(
                name=f"Stage1 Tutor {number}", is_active=True, status="published", lesson_price=35,
            )
    return place


def fixture_pages(place):
    with translation.override("ru"):
        detail_path = place.get_absolute_url()
    return {
        "home_az": ("/", "home", "Stage1 Judo"),
        "home_ru": ("/ru/", "home", "Stage1 Judo"),
        "catalog": ("/ru/catalog/", "place_list", "Stage1 Judo"),
        "events": ("/ru/afisha/", "events_landing", "Stage1 Festival"),
        "specialists": ("/ru/specialists/", "specialist_list", "Stage1 Tutor"),
        "place": (detail_path, "place_detail", place.name_ru),
        "seo": (f"/ru/catalog/{SEO_SLUG}/", "seo_landing", "Stage1 Judo"),
    }


def count_page_queries(pages, size):
    counts = {}
    for key, (path, view_name, marker) in pages.items():
        count = 0

        def count_query(execute, sql, params, many, context):
            nonlocal count
            count += 1
            return execute(sql, params, many, context)

        cache.clear()
        client = Client()
        with translation.override("az"), connection.execute_wrapper(count_query):
            response = client.get(path)
        if response.status_code != 200 or response.wsgi_request.resolver_match.url_name != view_name:
            raise AssertionError(f"{path}: expected 200 from {view_name}, got {response.status_code}")
        if marker.encode() not in response.content:
            raise AssertionError(f"{path}: missing fixture content {marker!r}")
        if key == "seo" and response.context["seo_aggregate"]["count"] != size:
            raise AssertionError(f"{path}: aggregate does not contain {size} places")
        counts[key] = count
    return counts


@override_settings(DEBUG=False, LOCAL_ANALYTICS_STORAGE_ENABLED=False, OWNER_ANALYTICS_ENABLED=False)
class PageQueryBudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        judo = create_page_fixture()
        detail = add_places(judo, 1, 20)
        pages = fixture_pages(detail)
        cls.small = count_page_queries(pages, 20)
        add_places(judo, 21, 60)
        cls.large = count_page_queries(pages, 60)

    def test_twenty_place_ceilings(self):
        ceilings = {"home_az": 35, "home_ru": 35, "catalog": 26, "events": 22,
                    "specialists": 13, "place": 34, "seo": 10}
        for page, ceiling in ceilings.items():
            with self.subTest(page=page):
                self.assertLessEqual(self.small[page], ceiling)

    def test_growth_on_catalog_specialists_place_and_seo(self):
        for page in ("catalog", "specialists", "place", "seo"):
            with self.subTest(page=page):
                self.assertLessEqual(self.large[page], self.small[page])

    def test_known_growth_stays_within_measured_sixty_place_ceilings(self):
        for page, ceiling in (("home_az", 35), ("home_ru", 35), ("events", 22)):
            with self.subTest(page=page):
                self.assertLessEqual(self.large[page], ceiling)

    def test_az_home_query_count_does_not_grow(self):
        self.assertLessEqual(self.large["home_az"], self.small["home_az"])

    def test_ru_home_query_count_does_not_grow(self):
        self.assertLessEqual(self.large["home_ru"], self.small["home_ru"])

    def test_events_query_count_does_not_grow(self):
        self.assertLessEqual(self.large["events"], self.small["events"])

    def test_two_hundred_places_keep_home_and_events_constant(self):
        judo = Subcategory.objects.get(code="judo")
        detail = add_places(judo, 61, 200)
        pages = {key: page for key, page in fixture_pages(detail).items()
                 if key in ("home_az", "home_ru", "events")}
        counts = count_page_queries(pages, 200)
        for page in pages:
            with self.subTest(page=page):
                self.assertLessEqual(counts[page], self.small[page])
