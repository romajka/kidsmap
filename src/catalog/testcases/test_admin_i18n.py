from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings


class AdminI18nTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.superadmin = User.objects.create_superuser(
            username="admin_i18n_tester",
            email="admin_i18n@example.com",
            password="testpassword123",
        )
        self.client = Client()
        self.client.force_login(self.superadmin)

    def test_admin_set_language_endpoint_sets_cookie_and_redirects(self):
        """Test that posting to /i18n/setlang/ correctly sets django_language cookie and redirects to admin."""
        url = reverse("set_language")
        for lang_code in ["az", "ru", "en"]:
            response = self.client.post(
                url,
                data={"language": lang_code, "next": "/admin/"},
            )
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/admin/")
            self.assertIn(settings.LANGUAGE_COOKIE_NAME, response.cookies)
            self.assertEqual(response.cookies[settings.LANGUAGE_COOKIE_NAME].value, lang_code)

    def test_admin_navbar_renders_language_chooser_with_current_language(self):
        """Test that the custom language switcher button and dropdown are rendered in admin base template."""
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "az"
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        self.assertIn("km-admin-lang-btn", content)
        self.assertIn("jazzy-languagemenu", content)
        self.assertIn("AZ", content)
        self.assertIn("RU", content)
        self.assertIn("EN", content)

    def test_admin_index_localized_in_az_ru_en(self):
        """Test that the admin dashboard reflects the language set in cookie."""
        # 1. Azerbaijani
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "az"
        res_az = self.client.get(reverse("admin:index"))
        self.assertEqual(res_az.status_code, 200)
        content_az = res_az.content.decode("utf-8")
        self.assertIn("Tədbirlər", content_az)
        self.assertIn("Daimi məkanlar", content_az)

        # 2. English
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        res_en = self.client.get(reverse("admin:index"))
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode("utf-8")
        self.assertIn("Events", content_en)
        self.assertIn("Permanent places", content_en)

        # 3. Russian
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ru"
        res_ru = self.client.get(reverse("admin:index"))
        self.assertEqual(res_ru.status_code, 200)
        content_ru = res_ru.content.decode("utf-8")
        self.assertIn("Мероприятия", content_ru)
        self.assertIn("Постоянные места", content_ru)

    def test_staff_access_changelist_localized(self):
        """Test that staffaccessuser change list is localized."""
        url = reverse("admin:catalog_staffaccessuser_changelist")

        # English
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        res_en = self.client.get(url)
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode("utf-8")
        self.assertIn("Admin staff", content_en)

        # Azerbaijani
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "az"
        res_az = self.client.get(url)
        self.assertEqual(res_az.status_code, 200)
        content_az = res_az.content.decode("utf-8")
        self.assertIn("İdarəetmə əməkdaşları", content_az)

        # Russian
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ru"
        res_ru = self.client.get(url)
        self.assertEqual(res_ru.status_code, 200)
        content_ru = res_ru.content.decode("utf-8")
        self.assertIn("Сотрудники админки", content_ru)

    def test_seo_issue_changelist_localized(self):
        """Test that seoissue change list quick filters and headers are localized."""
        url = reverse("admin:catalog_seoissue_changelist")

        # English
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "en"
        res_en = self.client.get(url)
        self.assertEqual(res_en.status_code, 200)
        content_en = res_en.content.decode("utf-8")
        self.assertIn("Registry of SEO issues and recommendations", content_en)

        # Azerbaijani
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "az"
        res_az = self.client.get(url)
        self.assertEqual(res_az.status_code, 200)
        content_az = res_az.content.decode("utf-8")
        self.assertIn("SEO problemləri və tövsiyələri reyestri", content_az)

        # Russian
        self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = "ru"
        res_ru = self.client.get(url)
        self.assertEqual(res_ru.status_code, 200)
        content_ru = res_ru.content.decode("utf-8")
        self.assertIn("Реестр SEO-проблем и рекомендаций", content_ru)

    def test_explicit_admin_prefix_wins_over_language_cookie(self):
        for prefix in ('ru', 'en'):
            for cookie in ('az', 'ru', 'en'):
                with self.subTest(prefix=prefix, cookie=cookie):
                    self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie
                    response = self.client.get(f'/{prefix}/admin/catalog/place/')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.wsgi_request.LANGUAGE_CODE, prefix)

    def test_unprefixed_admin_keeps_selected_cookie_language(self):
        for cookie in ('az', 'ru', 'en'):
            with self.subTest(cookie=cookie):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie
                response = self.client.get('/admin/catalog/place/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.wsgi_request.LANGUAGE_CODE, cookie)

    def test_legacy_az_admin_prefix_remains_canonical_redirect(self):
        for cookie in ('az', 'ru', 'en'):
            with self.subTest(cookie=cookie):
                self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie
                response = self.client.get('/az/admin/catalog/place/')
                self.assertEqual(response.status_code, 301)
                self.assertEqual(response.url, '/admin/catalog/place/')
                self.assertEqual(response.wsgi_request.LANGUAGE_CODE, 'az')
