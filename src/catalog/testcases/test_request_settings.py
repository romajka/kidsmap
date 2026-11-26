from django.db import connection
from django.http import JsonResponse
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import path

from catalog.models import CatalogContentSettings, SiteSettings
from catalog.models.site import SiteBrandingSettings
from catalog.testcases.test_site_qa15_settings_concurrency import Site15FixtureMixin


def settings_view(request):
    brand = SiteSettings.get_solo().brand_name
    districts = CatalogContentSettings.get_solo().districts_json
    if request.method == "POST":
        proxy = SiteBrandingSettings.objects.get()
        proxy.brand_name = "New brand"
        proxy.save(update_fields=["brand_name"])
        content = CatalogContentSettings.objects.get()
        content.districts_json = ["changed"]
        content.save(update_fields=["districts_json"])
    return JsonResponse({
        "before": [brand, districts],
        "after": [SiteSettings.get_solo().brand_name, CatalogContentSettings.get_solo().districts_json],
    })


urlpatterns = [path("settings/", settings_view)]


@override_settings(ROOT_URLCONF=__name__)
class RequestSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SiteSettings.get_solo()
        CatalogContentSettings.get_solo()

    def test_each_request_reads_each_singleton_once(self):
        for brand in ("First", "Second"):
            SiteSettings.objects.update(brand_name=brand)
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get("/settings/")
            self.assertEqual(response.json()["after"][0], brand)
            for table in ("catalog_sitesettings", "catalog_catalogcontentsettings"):
                with self.subTest(brand=brand, table=table):
                    self.assertEqual(sum(f'FROM "{table}"' in q["sql"] for q in queries), 1)

    def test_proxy_and_content_save_refresh_current_and_next_request(self):
        response = self.client.post("/settings/").json()
        self.assertNotEqual(response["before"], response["after"])
        expected = ["New brand", ["changed"]]
        self.assertEqual(response["after"], expected)
        self.assertEqual(self.client.get("/settings/").json()["before"], expected)

    def test_outside_request_each_read_observes_database(self):
        for brand in ("Before", "After"):
            SiteSettings.objects.update(brand_name=brand)
            self.assertEqual(SiteSettings.get_solo().brand_name, brand)


class AdminSettingsReadbackTests(Site15FixtureMixin, TestCase):
    def test_anonymous_contacts_page_refreshes_after_admin_save(self):
        visitor = Client()
        self.assertContains(visitor.get("/ru/contacts/"), "site15-before@example.invalid")
        form = self.payload()
        form["footer_email"] = "updated@example.invalid"
        self.assertEqual(self.client.post(self.url, form).status_code, 302)
        page = visitor.get("/ru/contacts/")
        self.assertContains(page, 'href="mailto:updated@example.invalid"')
        self.assertNotContains(page, "site15-before@example.invalid")
