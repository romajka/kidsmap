from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, SimpleTestCase, override_settings

from catalog.context_processors import _google_analytics_context


@override_settings(
    DEBUG=False,
    TESTING=False,
    PUBLIC_BASE_URL="https://kidsmap.az",
    ALLOWED_HOSTS=["*"],
    GOOGLE_ANALYTICS_MEASUREMENT_ID="G-BOUNDARYTEST",
)
class GoogleAnalyticsCollectionBoundaryTests(SimpleTestCase):
    def request(self, *, host="kidsmap.az", path="/ru/place/example/", user=None):
        request = RequestFactory().get(path, HTTP_HOST=host)
        request.user = user if user is not None else AnonymousUser()
        return request

    def assert_disabled(self, request):
        self.assertEqual(_google_analytics_context(request), {
            "google_analytics_enabled": False,
            "google_analytics_measurement_id": "",
        })

    def test_public_anonymous_and_regular_authenticated_visitors_are_measured(self):
        for user in (
            AnonymousUser(),
            SimpleNamespace(is_authenticated=True, is_staff=False, is_superuser=False),
        ):
            with self.subTest(user=user):
                context = _google_analytics_context(self.request(user=user))
                self.assertTrue(context["google_analytics_enabled"])
                self.assertEqual(context["google_analytics_measurement_id"], "G-BOUNDARYTEST")

    def test_only_production_public_hostname_is_measured(self):
        for host in (
            "localhost", "127.0.0.1", "testserver", "[::1]", "192.168.1.10",
            "admin.kidsmap.az", "preview.kidsmap.az", "kidsmap.az.example.invalid",
        ):
            with self.subTest(host=host):
                self.assert_disabled(self.request(host=host))

    def test_staff_and_superuser_public_visits_are_excluded(self):
        for staff, superuser in ((True, False), (False, True), (True, True)):
            with self.subTest(staff=staff, superuser=superuser):
                self.assert_disabled(self.request(user=SimpleNamespace(
                    is_authenticated=True, is_staff=staff, is_superuser=superuser,
                )))

    def test_testing_debug_preview_and_missing_measurement_are_excluded(self):
        for name, value in (
            ("TESTING", True), ("DEBUG", True), ("GOOGLE_ANALYTICS_MEASUREMENT_ID", ""),
        ):
            with self.subTest(setting=name), override_settings(**{name: value}):
                self.assert_disabled(self.request())
        request = self.request()
        request.site_preview = True
        self.assert_disabled(request)

    def test_service_routes_are_excluded_in_all_languages(self):
        for prefix in ("/", "/az/", "/ru/", "/en/"):
            for path in ("admin/", "admin/editor/places/1/", "i18n/setlang/"):
                with self.subTest(prefix=prefix, path=path):
                    self.assert_disabled(self.request(path=prefix + path))

    def test_normal_account_favorites_are_preserved(self):
        request = self.request(path="/ru/account/favorites/", user=SimpleNamespace(
            is_authenticated=True, is_staff=False, is_superuser=False,
        ))
        self.assertTrue(_google_analytics_context(request)["google_analytics_enabled"])

    def test_real_signup_and_login_paths_are_preserved(self):
        for path in ("/auth/login/", "/ru/auth/register/", "/en/auth/verify-email/"):
            with self.subTest(path=path):
                self.assertTrue(_google_analytics_context(self.request(path=path))["google_analytics_enabled"])

    def test_public_origin_misconfiguration_fails_closed(self):
        with override_settings(PUBLIC_BASE_URL="https://preview.kidsmap.az"):
            self.assert_disabled(self.request())
