from datetime import timedelta
from urllib.parse import parse_qs

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import Category, Event, SiteSettings
from catalog.testcases.test_module11_seo import Module11Fixture,Head
from catalog.testcases.test_parent_guide_images import ImageMarkup

# Localized afisha paths (2026-11): /tedbirler/, /ru/afisha/, /en/events/.
AFISHA_PATHS = {"": "/tedbirler/", "/ru": "/ru/afisha/", "/en": "/en/events/"}

class FilteredDirectoryIndexabilityTests(Module11Fixture):
    def page(self,route,lang,query=None):
        self.client.cookies['django_language']=lang
        with translation.override(lang):url=reverse(route)
        response=self.client.get(url,query or {});self.assertEqual(response.status_code,200);return response,Head(response.content.decode())
    def test_filtered_specialist_and_event_search_pages_are_noindex(self):
        for lang in ('az','ru','en'):
            for route in ('specialist_list','events_landing'):
                with self.subTest(lang=lang,route=route):
                    response,head=self.page(route,lang,{'q':'M11-no-public-result','format':'online'});self.assertIn('noindex',head.one('robots'));self.assertIn('noindex',head.one('googlebot'))
    def test_unfiltered_directories_remain_indexable(self):
        for route in ('specialist_list','events_landing'):
            response,head=self.page(route,'az');self.assertTrue(head.one('robots').startswith('index,'))
    def test_language_switch_retains_valid_filter_inputs(self):
        for route in ('specialist_list','events_landing'):
            response,head=self.page(route,'ru',{'q':'M11-no-public-result','format':'online'});self.assertEqual(parse_qs(response.context['language_switch_query']),{'q':['M11-no-public-result'],'format':['online']})


@override_settings(PUBLIC_BASE_URL="https://kidsmap.az")
class AfishaSearchIndexabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        site = SiteSettings.get_solo()
        site.events_section_enabled = True
        site.save(update_fields=["events_section_enabled"])
        category = Category.objects.create(code="afisha-search", name_az="Afişa")
        for day in range(1, 14):
            start = timezone.now() + timedelta(days=day)
            Event.objects.create(
                name_az=f"Afişa {day}", status=Event.STATUS_PUBLISHED, category=category,
                start_datetime=start, end_datetime=start + timedelta(hours=1),
            )

    def test_baku_headings_snippets_and_breadcrumbs_are_localized(self):
        for prefix, heading, city in (
            ("", "Bakıda uşaqlar üçün tədbirlər", "Bakıda"),
            ("/ru", "Детская афиша Баку", "Баку"),
            ("/en", "Kids’ events in Baku", "Baku"),
        ):
            path = AFISHA_PATHS[prefix]
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertContains(response, f"<h1>{heading}</h1>", count=1)
                markup = ImageMarkup(response.content.decode())
                self.assertIn(city, markup.meta["og:title"])
                self.assertIn(city, markup.meta["description"])
                breadcrumbs = next(item for item in markup.schemas if item["@type"] == "BreadcrumbList")
                self.assertEqual(breadcrumbs["itemListElement"][-1]["item"], "https://kidsmap.az" + path)
                self.assertNotIn("Event", [item["@type"] for item in markup.schemas])

    def test_real_later_pages_can_be_indexed_with_locale_specific_canonicals(self):
        expected = {
            "az": "https://kidsmap.az/tedbirler/?page=2",
            "ru": "https://kidsmap.az/ru/afisha/?page=2",
            "en": "https://kidsmap.az/en/events/?page=2",
            "x-default": "https://kidsmap.az/tedbirler/?page=2",
        }
        for language, prefix in (("az", ""), ("ru", "/ru"), ("en", "/en")):
            path = AFISHA_PATHS[prefix]
            with self.subTest(path=path):
                response = self.client.get(path, {"page": 2})
                self.assertEqual(response.status_code, 200)
                head = Head(response.content.decode())
                self.assertEqual(head.links["canonical"], [expected[language]])
                self.assertTrue(head.one("robots").startswith("index,"))
                self.assertTrue(head.one("googlebot").startswith("index,"))
                for locale, url in expected.items():
                    self.assertContains(response, f'hreflang="{locale}" href="{url}"', count=1)
                self.assertContains(response, f'href="{path}#events-feed"')
                self.assertRedirects(self.client.head(path + "?page=1"), path, status_code=301)

    def test_calendar_filtered_and_nonexistent_page_variants_stay_out_of_the_index(self):
        for query in ({"view": "calendar"}, {"q": "Afişa", "page": 2}, {"page": 999}):
            with self.subTest(query=query):
                response = self.client.get("/ru/afisha/", query)
                self.assertContains(response, 'name="robots" content="noindex,follow"')

    def test_family_guide_links_to_the_localized_afisha_in_its_content(self):
        for prefix in ("", "/ru", "/en"):
            response = self.client.get(f"{prefix}/parents/baku-with-kids/")
            self.assertContains(response, f'class="pg-text-link" href="{AFISHA_PATHS[prefix]}"', count=1)
        site = SiteSettings.get_solo()
        site.events_section_enabled = False
        site.save(update_fields=["events_section_enabled"])
        response = self.client.get("/ru/parents/baku-with-kids/")
        self.assertNotContains(response, 'class="pg-text-link" href="/ru/afisha/"')
