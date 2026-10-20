from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from catalog import context_processors


@override_settings(
    DEBUG=False, TESTING=False, PUBLIC_BASE_URL="https://kidsmap.az",
    ALLOWED_HOSTS=["*"], YANDEX_METRICA_COUNTER_ID="12345678",
    YANDEX_METRICA_WEBVISOR_ENABLED=True,
)
class YandexMetricaGateTests(SimpleTestCase):
    def request(self, *, host="kidsmap.az", route="place_detail", user=None):
        request = RequestFactory().get("/ru/place/example/", HTTP_HOST=host)
        request.user = user if user is not None else AnonymousUser()
        request.resolver_match = SimpleNamespace(url_name=route)
        return request

    def context(self, request=None):
        return context_processors._yandex_metrica_context(request or self.request())

    def test_only_anonymous_public_pages_are_enabled(self):
        for route in ("home", "place_list", "place_new", "seo_landing", "place_detail"):
            with self.subTest(route=route):
                self.assertTrue(self.context(self.request(route=route))["yandex_metrica_enabled"])
        self.assertEqual(self.context()["yandex_metrica_counter_id"], "12345678")
        self.assertTrue(self.context()["yandex_metrica_webvisor_enabled"])

    def test_fail_closed_for_configuration_host_identity_route_and_preview(self):
        for setting, values in {
            "YANDEX_METRICA_COUNTER_ID": ("", "0", "-1", "12x", "１２３", "1e5"),
            "DEBUG": (True,), "TESTING": (True,),
        }.items():
            for value in values:
                with self.subTest(setting=setting, value=value), override_settings(**{setting: value}):
                    self.assertEqual(self.context(), {
                        "yandex_metrica_enabled": False, "yandex_metrica_counter_id": "",
                        "yandex_metrica_webvisor_enabled": False,
                    })
        for host in ("localhost", "127.0.0.1", "testserver", "admin.kidsmap.az", "kidsmap.az.evil.test"):
            with self.subTest(host=host):
                self.assertFalse(self.context(self.request(host=host))["yandex_metrica_enabled"])
        for route in (None, "privacy", "account", "login", "place_edit"):
            self.assertFalse(self.context(self.request(route=route))["yandex_metrica_enabled"])
        request = self.request()
        request.site_preview = True
        self.assertFalse(self.context(request)["yandex_metrica_enabled"])
        request = self.request(user=SimpleNamespace(is_authenticated=True))
        self.assertFalse(self.context(request)["yandex_metrica_enabled"])
        request = self.request()
        del request.user
        self.assertFalse(self.context(request)["yandex_metrica_enabled"])

    def test_webvisor_can_be_disabled_independently(self):
        with override_settings(YANDEX_METRICA_WEBVISOR_ENABLED=False):
            self.assertTrue(self.context()["yandex_metrica_enabled"])
            self.assertFalse(self.context()["yandex_metrica_webvisor_enabled"])

    def test_site_settings_keeps_metrica_when_database_is_unavailable(self):
        from django.db.utils import OperationalError
        request = self.request()
        request.LANGUAGE_CODE = "ru"
        request.session = {}
        with patch.object(context_processors.SiteSettings, "get_solo", side_effect=OperationalError):
            self.assertTrue(context_processors.site_settings(request)["yandex_metrica_enabled"])

    def test_conditional_include_has_one_deferred_loader_and_no_pixel(self):
        for enabled in (True, False):
            context = self.context()
            context["yandex_metrica_enabled"] = enabled
            html = render_to_string("includes/yandex_metrica.html", context)
            self.assertEqual(html.count('id="kidsmap-yandex-metrica"'), int(enabled))
            self.assertNotIn("<noscript", html)
            if enabled:
                self.assertIn('data-counter-id="12345678"', html)
                self.assertIn('data-webvisor="true"', html)
                self.assertIn("defer", html)

    def test_base_template_uses_independent_event_bridge(self):
        from pathlib import Path
        from django.conf import settings
        source = (settings.BASE_DIR / "src/catalog/templates/base.html").read_text()
        self.assertEqual(source.count('{% include "includes/yandex_metrica.html" %}'), 1)
        self.assertIn("window.kidsMapTrackYandexMetricaEvent(eventItem.name)", source)


@override_settings(
    DEBUG=False, TESTING=False, PUBLIC_BASE_URL="https://kidsmap.az",
    ALLOWED_HOSTS=["*"], YANDEX_METRICA_COUNTER_ID="12345678",
    YANDEX_METRICA_WEBVISOR_ENABLED=False, GOOGLE_ANALYTICS_MEASUREMENT_ID="",
)
class YandexMetricaPageTests(TestCase):
    def test_rendered_public_pages_and_signed_in_exclusion(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        from django.utils.translation import override
        from catalog.models import Place

        place = Place.objects.create(
            name="Metrica fixture", name_az="Metrica fixture", name_ru="Metrica fixture",
            name_en="Metrica fixture", description_az="A public family activity fixture.",
            category="EDU", address="Baku, fixture", is_active=True,
            status=Place.STATUS_PUBLISHED, age_from=3, age_to=12,
            schedule="09:00-18:00", price_mode="free", lat=40.4, lng=49.8,
        )
        for language in ("az", "ru", "en"):
            with override(language):
                for url in (reverse("home"), reverse("place_list"), place.get_absolute_url()):
                    response = self.client.get(url, HTTP_HOST="kidsmap.az", secure=True)
                    with self.subTest(language=language, url=url):
                        self.assertEqual(response.status_code, 200)
                        self.assertContains(response, 'id="kidsmap-yandex-metrica"', count=1)
                        self.assertContains(response, 'data-webvisor="false"')
        self.client.force_login(get_user_model().objects.create_user(username="metrica-fixture"))
        response = self.client.get("/ru/catalog/", HTTP_HOST="kidsmap.az", secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="kidsmap-yandex-metrica"')
