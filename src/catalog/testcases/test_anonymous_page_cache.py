from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TransactionTestCase, override_settings
from django.urls import reverse

from catalog.models import CatalogContentSettings, PlaceReview, SiteSettings
from catalog.testcases.utils import create_ready_place


@override_settings(PAGE_CACHE_ENABLED=True, PAGE_CACHE_DEPLOY_SHA="a" * 40,
                   LOCAL_ANALYTICS_STORAGE_ENABLED=False)
class AnonymousPageCacheTests(TransactionTestCase):
    def setUp(self):
        SiteSettings.get_solo()
        CatalogContentSettings.get_solo()
        cache.clear()
        self.addCleanup(cache.clear)

    def test_separate_clients_share_only_the_public_html(self):
        with patch.object(cache, "set", wraps=cache.set) as writes:
            cold = Client().get("/ru/")
        warm = Client(enforce_csrf_checks=True)
        hit = warm.get("/ru/")
        self.assertEqual(cold.headers["X-KidsMap-Cache"], "MISS")
        self.assertEqual(hit.headers["X-KidsMap-Cache"], "HIT")
        self.assertNotEqual(cold.cookies["csrftoken"].value, hit.cookies["csrftoken"].value)
        body, = [call.args[1] for call in writes.call_args_list
                 if str(call.args[0]).startswith("km:page:")]
        for private in (b"csrfmiddlewaretoken", b"sessionid", cold.cookies["csrftoken"].value.encode()):
            self.assertNotIn(private, body)
            self.assertNotIn(private, hit.content)
        self.assertContains(hit, "data-km-csrf")
        # Anonymous review controls use the real login/navigation POST first.
        submitted = warm.post(reverse("account_login"), {"auth_navigation": "1", "next": "/ru/#reviews",
                              "csrfmiddlewaretoken": warm.cookies["csrftoken"].value})
        self.assertIn(submitted.status_code, (200, 302))
        self.assertEqual(Client().head("/ru/").headers["X-KidsMap-Cache"], "HIT")

    def test_authentication_private_cookie_and_query_bypass_reads_and_writes(self):
        path = "/ru/catalog/"
        user = get_user_model().objects.create_user("private-navigation")
        private = Client()
        private.force_login(user)
        self.assertEqual(private.get(path).headers["X-KidsMap-Cache"], "MISS")
        self.assertEqual(self.client.get(path).headers["X-KidsMap-Cache"], "MISS")
        self.assertEqual(private.get(path).headers["X-KidsMap-Cache"], "MISS")
        for cookie in ("sessionid", "messages", "unknown"):
            visitor = Client()
            visitor.cookies[cookie] = "opaque"
            self.assertEqual(visitor.get(path).headers["X-KidsMap-Cache"], "MISS")
        self.assertEqual(self.client.get(path, {"district": "baku_yasamal"}).headers["X-KidsMap-Cache"], "MISS")
        for lang in ("ru", "en"):
            path = f"/{lang}/catalog/?page=2"
            self.assertEqual(self.client.get(path).headers["X-KidsMap-Cache"], "MISS")
            response = self.client.get(path)
            self.assertEqual(response.headers["X-KidsMap-Cache"], "HIT")
            self.assertContains(response, f'<html lang="{lang}"')

    def test_analytics_cookies_share_the_anonymous_html(self):
        path = "/ru/catalog/"
        visitor = Client()
        visitor.cookies["_ga"] = "analytics-first-visitor"
        cold = visitor.get(path)
        self.assertEqual(cold.headers["X-KidsMap-Cache"], "MISS")
        self.assertNotContains(cold, "analytics-first-visitor")
        for name in ("_ga", "_ga_STREAM", "_gid", "_gat", "_gat_tracker", "_gcl_aw", "_fbp", "_fbc"):
            with self.subTest(cookie=name):
                other = Client()
                other.cookies[name] = "analytics-second-visitor"
                hit = other.get(path)
                self.assertEqual(hit.headers["X-KidsMap-Cache"], "HIT")
                self.assertEqual(hit.content, cold.content)
        self.assertEqual(Client().get(path).headers["X-KidsMap-Cache"], "HIT")

    def test_analytics_does_not_hide_a_private_or_unrecognized_cookie(self):
        path = "/ru/catalog/"
        self.client.get(path)
        for name in ("sessionid", "django_language", "messages", "_unknown", "_gaExtra", "_fbp_extra"):
            with self.subTest(cookie=name):
                other = Client()
                other.cookies["_ga"] = "analytics-visitor"
                other.cookies[name] = "ru"
                self.assertEqual(other.get(path).headers["X-KidsMap-Cache"], "MISS")

    def test_signed_in_analytics_visitors_always_see_their_own_navigation(self):
        path = "/ru/catalog/"
        guest = Client()
        guest.cookies["_ga"] = "shared-analytics-id"
        guest.get(path)
        clients = []
        names = ("CacheAlice", "CacheBoris")
        for name in names:
            user = get_user_model().objects.create_user(username=name, first_name=name)
            client = Client()
            client.cookies["_ga"] = "shared-analytics-id"
            client.force_login(user)
            clients.append(client)

        for client, own, other in ((clients[0], names[0], names[1]), (clients[1], names[1], names[0])):
            page = client.get(path)
            self.assertEqual(page.headers["X-KidsMap-Cache"], "MISS")
            self.assertContains(page, 'id="account-menu-trigger"')
            self.assertContains(page, own)
            self.assertNotContains(page, other)
        page = guest.get(path)
        self.assertEqual(page.headers["X-KidsMap-Cache"], "HIT")
        self.assertContains(page, "user-entry-logged-out")
        for name in names:
            self.assertNotContains(page, name)

    def test_withdrawal_and_publication_change_the_cached_catalog(self):
        place = create_ready_place()
        path = "/ru/catalog/"
        staff = Client()
        staff.force_login(get_user_model().objects.create_superuser("cache-editor", "", "fictional"))
        for action, visible in ((None, True), ("mark_draft", False), ("mark_published", True)):
            if action:
                result = staff.post(reverse("admin:catalog_place_changelist"), {
                    "action": action, "_selected_action": [place.pk],
                })
                self.assertEqual(result.status_code, 302)
            first = self.client.get(path)
            self.assertEqual(first.headers["X-KidsMap-Cache"], "MISS")
            second = self.client.get(path)
            self.assertEqual(second.headers["X-KidsMap-Cache"], "HIT")
            self.assertEqual(f'data-place-id="{place.pk}"'.encode() in second.content, visible)


    @override_settings(REVIEWS_REQUIRE_AUTH=False)
    def test_review_submission_after_warm_place_get(self):
        from django.utils.translation import override
        place = create_ready_place()
        with override("ru"):
            path = place.get_absolute_url()
            action = reverse("add_place_review", args=[place.pk])
        Client().get(path)
        visitor = Client(enforce_csrf_checks=True)
        self.assertEqual(visitor.get(path).headers["X-KidsMap-Cache"], "HIT")
        result = visitor.post(action, {"rating": "5", "text": "Good local activity",
                              "csrfmiddlewaretoken": visitor.cookies["csrftoken"].value})
        self.assertEqual(result.status_code, 302)
        self.assertTrue(PlaceReview.objects.filter(place=place, text="Good local activity").exists())

    def test_admin_recommendation_bulk_action_invalidates_home(self):
        place = create_ready_place()
        self.client.get("/ru/")
        self.assertEqual(self.client.get("/ru/").headers["X-KidsMap-Cache"], "HIT")
        staff = Client()
        staff.force_login(get_user_model().objects.create_superuser("rail-editor", "", "fictional"))
        for action in ("mark_home_recommended", "unmark_home_recommended"):
            staff.post(reverse("admin:catalog_place_changelist"), {"action": action, "_selected_action": [place.pk]})
            self.assertEqual(self.client.get("/ru/").headers["X-KidsMap-Cache"], "MISS")
            self.assertEqual(self.client.get("/ru/").headers["X-KidsMap-Cache"], "HIT")

    def test_guide_and_seo_pages_and_unsupported_cookie_mode(self):
        for path in ("/ru/parents/baku-with-kids/", "/ru/catalog/dzudo-dlya-detey-v-baku/"):
            with self.subTest(path=path):
                self.assertEqual(Client().get(path).headers["X-KidsMap-Cache"], "MISS")
                self.assertEqual(Client().get(path).headers["X-KidsMap-Cache"], "HIT")
                with override_settings(CSRF_COOKIE_HTTPONLY=True):
                    self.assertContains(Client().get(path), 'name="csrfmiddlewaretoken"')

    @override_settings(PAGE_CACHE_ENABLED=False)
    def test_disabled_returns_normal_forms_and_no_cache_header(self):
        response = self.client.get("/ru/")
        self.assertNotIn("X-KidsMap-Cache", response.headers)
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
