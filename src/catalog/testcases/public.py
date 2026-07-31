import json
from pathlib import Path
from io import StringIO
from datetime import timedelta
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils import timezone
from django.utils.translation import gettext as translate, override
from catalog.controllers.place_controller import PlaceController
from catalog.forms import OwnerPlaceCreateForm
from catalog.interfaces.geocoding import GeocodingPoint
from catalog.models import (
    CatalogContentSettings,
    Category,
    Event,
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceLike,
    PlacePhoto,
    PlaceScheduleDay,
    PlaceScheduleInterval,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    PlaceReview,
    PlaceReviewReaction,
    SiteGalleryImage,
    SiteSettings,
    SiteReview,
    SiteReviewReaction,
    SiteVisit,
    Subcategory,
    UserEmailVerification,
    UserProfile,
)
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.content_quality import public_place_queryset, public_review_queryset, review_quality_check
from catalog.services.place_schedule import dump_schedule_payload
from catalog.testcases.auth_access import TestAccountsAndReviewAccess
from catalog.testcases.auth_flow import (
    TestAccountProfileUpdates,
    TestAuthValidationAndNextSecurity,
    TestEmailVerificationFlow,
    TestPasswordResetIdentifierSupport,
)
from catalog.services.tracking import GA4_CONVERSION_EVENT_NAMES, TRACKED_EVENT_NAMES
from catalog.testcases.tracking import TestGoogleAnalyticsEvents, TestSiteVisitMiddleware, TestTrackingController
from config.views import serve_media_file
User = get_user_model()

from catalog.testcases.utils import *

class TestPublicPagesSmoke(TestCase):
    def test_home_page_opens_with_i18n_redirect(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="az">', html=False)
        self.assertNotContains(response, "total_place_reviews_count")
        self.assertNotContains(response, "data-count-target")

    def test_legacy_az_urls_redirect_to_default_language_without_prefix(self):
        response = self.client.get("/az/catalog/", {"category": "EDU"})

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/catalog/?category=EDU")

    def test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query(self):
        response = self.client.get("/az/catalog/?category=EDU&next=/place/33-slug/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/catalog/?category=EDU")

    def test_catalog_page_opens_with_i18n_redirect(self):
        response = self.client.get("/catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="az">', html=False)

    def test_site_reviews_page_opens_with_i18n_redirect(self):
        response = self.client.get("/reviews/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="az">', html=False)

    def test_admin_page_opens_login(self):
        response = self.client.get("/admin/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.redirect_chain)
        self.assertIn("/admin/login/", response.redirect_chain[-1][0])

    def test_contacts_page_shows_public_phone(self):
        response = self.client.get("/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "+994 50 540 66 39")

    def test_contacts_page_shows_public_social_links(self):
        response = self.client.get("/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://t.me/KidsMap_az")
        self.assertContains(response, "https://www.youtube.com/@KidsMap_az")
        self.assertContains(response, "https://www.tiktok.com/@kidsmap.az?lang=ru-RU")
        self.assertContains(response, "https://www.instagram.com/kidsmap.az/")
        self.assertContains(response, "https://www.facebook.com/people/KidsMap/61583913364027/")
        self.assertContains(response, "https://www.linkedin.com/company/kidsmap-az/")
        self.assertContains(response, "icon-telegram")
        self.assertContains(response, "icon-youtube")
        self.assertContains(response, "icon-tiktok")
        self.assertContains(response, "icon-instagram")
        self.assertContains(response, "icon-facebook")
        self.assertContains(response, "icon-linkedin")

    def test_business_and_legal_pages_open_in_languages(self):
        checks = {
            "/for-business/": "Uşaq məkanınızı KidsMap-də yerləşdirin",
            "/ru/for-business/": "Разместите детское место на KidsMap",
            "/en/for-business/": "List your kids place on KidsMap",
            "/privacy/": "Məxfilik siyasəti",
            "/ru/terms/": "Условия использования",
            "/en/review-rules/": "Review Rules",
        }
        for path, text in checks.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)

    def test_business_page_explains_free_listing_moderation_and_actions_in_all_languages(self):
        checks = {
            "/for-business/": (
                "Əsas yerləşdirmə pulsuzdur",
                "Foto, ünvan, əlaqə məlumatları, iş qrafiki və qiyməti olan kart yaradın.",
                "Məkan əlavə et",
                "Mövcud kartı tap",
                "Moderasiya nəyi yoxlayır",
            ),
            "/ru/for-business/": (
                "Базовое размещение бесплатно",
                "Создайте карточку с фото, адресом, контактами, расписанием и ценой.",
                "Добавить место",
                "Найти существующую карточку",
                "Что проверяет модерация",
            ),
            "/en/for-business/": (
                "Basic listing is free",
                "Create a listing with photos, address, contacts, schedule and price.",
                "Add a place",
                "Find an existing listing",
                "What moderation checks",
            ),
        }

        for path, texts in checks.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                for text in texts:
                    self.assertContains(response, text)
                language_prefix = path.removesuffix("/for-business/")
                self.assertContains(
                    response,
                    f'href="{language_prefix}/account/owner/places/create/?fresh=1"',
                    html=False,
                )
                self.assertContains(response, f'href="{language_prefix}/catalog/"', html=False)
                self.assertNotContains(response, "готовую структуру", html=False)
                self.assertNotContains(response, "Coming soon", html=False)

                create_url = f"{language_prefix}/account/owner/places/create/?fresh=1"
                create_response = self.client.get(create_url)
                login_url = urlparse(create_response.headers["Location"])
                self.assertEqual(login_url.path, f"{language_prefix}/auth/login/")
                self.assertEqual(parse_qs(login_url.query).get("next"), [create_url])

                login_response = self.client.get(create_response.headers["Location"])
                self.assertEqual(login_response.context["next_url"], create_url)
                register_response = self.client.get(
                    f"{language_prefix}/auth/register/",
                    {"next": create_url},
                )
                self.assertEqual(register_response.context["next_url"], create_url)

    def test_privacy_policy_is_full_document_in_all_languages(self):
        checks = (
            (
                "/privacy/",
                "Məxfilik siyasəti",
                "22 iyun 2026",
                "Mündəricat",
                "http://testserver/privacy/",
                {
                    "az": "http://testserver/privacy/",
                    "ru": "http://testserver/ru/privacy/",
                    "en": "http://testserver/en/privacy/",
                },
            ),
            (
                "/ru/privacy/",
                "Политика конфиденциальности",
                "22 июня 2026 года",
                "Оглавление",
                "http://testserver/ru/privacy/",
                {
                    "az": "http://testserver/privacy/",
                    "ru": "http://testserver/ru/privacy/",
                    "en": "http://testserver/en/privacy/",
                },
            ),
            (
                "/en/privacy/",
                "Privacy Policy",
                "June 22, 2026",
                "Contents",
                "http://testserver/en/privacy/",
                {
                    "az": "http://testserver/privacy/",
                    "ru": "http://testserver/ru/privacy/",
                    "en": "http://testserver/en/privacy/",
                },
            ),
        )
        for path, title, effective_date, toc_title, canonical, alternates in checks:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "pages/legal.html")
                self.assertContains(response, title)
                self.assertContains(response, effective_date)
                self.assertContains(response, "kidsmap.az@gmail.com")
                self.assertContains(response, 'href="mailto:kidsmap.az@gmail.com"', html=False)
                self.assertContains(response, toc_title)
                self.assertContains(response, f'<link rel="canonical" href="{canonical}" />', html=False)
                for code, url in alternates.items():
                    self.assertContains(response, f'<link rel="alternate" hreflang="{code}" href="{url}" />', html=False)
                self.assertNotContains(response, "[kidsmap.az@gmail.com]")
                self.assertNotContains(response, "[]")
                self.assertNotContains(response, "privacy@kidsmap.az")
                self.assertNotContains(response, "VÖEN")

                page_sections = response.context["sections"]
                anchor_ids = [item["id"] for item in page_sections]
                self.assertEqual(len(anchor_ids), len(set(anchor_ids)))

    def test_terms_of_use_is_full_document_in_all_languages(self):
        checks = (
            (
                "/terms/",
                "İstifadə şərtləri",
                "22 iyun 2026",
                "Mündəricat",
                "http://testserver/terms/",
                {
                    "az": "http://testserver/terms/",
                    "ru": "http://testserver/ru/terms/",
                    "en": "http://testserver/en/terms/",
                },
            ),
            (
                "/ru/terms/",
                "Условия использования",
                "22 июня 2026 года",
                "Оглавление",
                "http://testserver/ru/terms/",
                {
                    "az": "http://testserver/terms/",
                    "ru": "http://testserver/ru/terms/",
                    "en": "http://testserver/en/terms/",
                },
            ),
            (
                "/en/terms/",
                "Terms of Use",
                "June 22, 2026",
                "Contents",
                "http://testserver/en/terms/",
                {
                    "az": "http://testserver/terms/",
                    "ru": "http://testserver/ru/terms/",
                    "en": "http://testserver/en/terms/",
                },
            ),
        )
        for path, title, effective_date, toc_title, canonical, alternates in checks:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "pages/legal.html")
                self.assertContains(response, title)
                self.assertContains(response, effective_date)
                self.assertContains(response, "kidsmap.az@gmail.com")
                self.assertContains(response, 'href="mailto:kidsmap.az@gmail.com"', html=False)
                self.assertContains(response, toc_title)
                self.assertContains(response, f'<link rel="canonical" href="{canonical}" />', html=False)
                for code, url in alternates.items():
                    self.assertContains(response, f'<link rel="alternate" hreflang="{code}" href="{url}" />', html=False)
                self.assertNotContains(response, "[kidsmap.az@gmail.com]")
                self.assertNotContains(response, "[]")
                self.assertNotContains(response, "privacy@kidsmap.az")

                page_sections = response.context["sections"]
                anchor_ids = [item["id"] for item in page_sections]
                self.assertEqual(len(anchor_ids), len(set(anchor_ids)))

    def test_terms_page_mentions_public_sources_disclaimer(self):
        response = self.client.get("/ru/terms/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "может быть получена из открытых источников")
        self.assertContains(response, "не гарантирует полноту, актуальность и безошибочность")

    def test_ru_footer_privacy_link_points_to_ru_privacy(self):
        response = self.client.get("/ru/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/ru/privacy/"', html=False)
        self.assertContains(response, "Часть информации на сайте может быть получена из открытых источников и от третьих лиц.")

    def test_about_page_shows_extended_project_description(self):
        response = self.client.get("/ru/about/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Что такое KidsMap")
        self.assertContains(response, "Как это работает")
        self.assertContains(response, "Что получает родитель")
        self.assertContains(response, "Что получает владелец кружка")

    def test_en_login_page_uses_english_auth_labels(self):
        response = self.client.get("/en/auth/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to your account")
        self.assertContains(response, "Email")
        self.assertContains(response, "Remember me")
        self.assertContains(response, "Forgot password?")
        self.assertNotContains(response, "Логин или email")
        self.assertNotContains(response, "Запомнить меня")
        self.assertNotContains(response, "Забыли пароль?")

    def test_en_password_reset_page_uses_english_text(self):
        response = self.client.get("/en/auth/password-reset/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Password reset")
        self.assertContains(response, "Send reset link")
        self.assertContains(response, "Back to sign in")
        self.assertNotContains(response, "Восстановление пароля")
        self.assertNotContains(response, "Отправить ссылку")
        self.assertNotContains(response, "Вернуться ко входу")

    def test_en_register_page_uses_english_helper_text(self):
        response = self.client.get("/en/auth/register/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create your account")
        self.assertContains(response, "Register")
        self.assertContains(response, "Already have an account?")
        self.assertNotContains(response, "Выберите статус аккаунта")
        self.assertNotContains(response, "Кто вы?")
        self.assertNotContains(response, "* işarəsi olan sahələr mütləq doldurulmalıdır.")

    def test_en_catalog_page_uses_english_map_strings(self):
        response = self.client.get("/en/catalog/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Results on the map")
        self.assertContains(response, "The interactive map will be available after Google Maps is configured.")
        self.assertNotContains(response, "Результаты на карте")
        self.assertNotContains(response, "Интерактивная карта станет доступна после настройки Google Maps.")

    def test_az_catalog_page_localizes_catalog_seo_strings(self):
        response = self.client.get("/catalog/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('<html lang="az">', content)
        self.assertIn("Azərbaycanda uşaqlar üçün dərnəklər və məşğələlər kataloqu", content)
        self.assertNotIn("Каталог кружков и секций для детей в Баку", content)
        self.assertNotIn("Найдено %(total)s карточек", content)

    def test_en_catalog_page_localizes_catalog_seo_strings(self):
        response = self.client.get("/en/catalog/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('<html lang="en">', content)
        self.assertIn("Catalog of clubs and activities for kids in Azerbaijan", content)
        self.assertNotIn("Каталог кружков и секций для детей в Баку", content)
        self.assertNotIn("Найдено %(total)s карточек", content)

    def test_ru_catalog_uses_ru_result_count_and_singular_card_grammar(self):
        create_quality_place(
            name="Unique singular search place",
            name_ru="Уникальный кружок для проверки склонения",
        )

        response = self.client.get(
            "/ru/catalog/",
            {"q": "Уникальный кружок для проверки склонения"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Найден 1 кружок")
        self.assertContains(response, "Найдена 1 карточка")
        self.assertNotContains(response, "kart tapıldı")
        self.assertNotContains(response, "dərnək tapıldı")
        self.assertNotContains(response, "məkan tapıldı")

    def test_en_home_title_is_localized(self):
        response = self.client.get("/en/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Clubs and activities for kids in Azerbaijan | KidsMap</title>", html=True)

    def test_en_reviews_page_sets_html_lang_and_translates_apply_button(self):
        response = self.client.get("/en/reviews/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('<html lang="en">', content)
        self.assertIn("General site reviews", content)
        self.assertIn(">Apply<", content)
        self.assertIn("Leave a site review", content)
        self.assertNotIn(">Применить<", content)
        self.assertNotIn("Оставить отзыв о сайте", content)

    def test_az_home_page_translates_faq_supporting_cards(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KidsMap haqqında tez-tez verilən suallar")
        self.assertContains(response, "Uşaq üçün dərnəyi necə tez tapmaq olar?")
        self.assertContains(response, "Kataloqa bax")
        self.assertNotContains(response, "Частые вопросы о KidsMap")

    def test_az_reviews_page_translates_reaction_helper(self):
        response = self.client.get("/reviews/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rəylər məhz KidsMap haqqındadır")
        self.assertContains(response, "Bir kliklə like və dislike")
        self.assertNotContains(response, "Лайк и дизлайк в один клик")

    def test_az_contacts_page_uses_azerbaijani_contact_helpers(self):
        response = self.client.get("/contacts/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sizin üçün uyğun əlaqə üsulunu seçin: zəng, email və ya WhatsApp.")
        self.assertContains(response, "KidsMap yeniliklərini öyrəşdiyiniz kanallardan izləyin.")
        self.assertContains(response, "Saytın əsas bölmələrinə sürətli keçidlər.")
        self.assertNotContains(response, "Выберите удобный способ связи: звонок, email или WhatsApp.")

    def test_register_page_hides_role_selector(self):
        response = self.client.get("/ru/auth/register/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Кто вы?")

    def test_en_home_page_translates_current_faq_interface(self):
        response = self.client.get("/en/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frequently asked questions about KidsMap")
        self.assertContains(response, "How can I quickly find a club for my child?")
        self.assertNotContains(response, "Частые вопросы о KidsMap")

    def test_en_header_uses_translated_language_names(self):
        response = self.client.get("/en/auth/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Azerbaijani")
        self.assertNotContains(response, "Азербайджанский")

    @override_settings(ADMIN_HOST="admin.kidsmap.az")
    def test_admin_page_redirects_to_admin_host_when_configured(self):
        response = self.client.get(
            "/ru/admin/login/?next=/ru/admin/",
            secure=True,
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            "https://admin.kidsmap.az/ru/admin/login/?next=/ru/admin/",
        )

    def test_home_page_renders_interactive_map_without_google_maps_key(self):
        create_quality_place(
            name="Home Map Place",
            name_ru="Кружок для карты на главной",
            category="EDU",
            is_active=True,
            lat=40.4093,
            lng=49.8671,
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="home-map"', html=False)
        self.assertContains(response, "leaflet@1.9.4/dist/leaflet.css")
        self.assertContains(response, "leaflet@1.9.4/dist/leaflet.js")
        self.assertContains(response, "home-map-data")

    def test_home_page_limits_recommended_places_to_four_cards(self):
        for idx in range(4):
            create_quality_place(
                name=f"Popular Place {idx + 1}",
                name_ru=f"Популярный кружок {idx + 1}",
                category="EDU",
                is_active=True,
                likes_count=10 - idx,
            )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["popular_places"]), 4)

    def test_home_page_uses_admin_selected_recommendations_in_configured_order(self):
        create_quality_place(
            name="Automatic Popular Place",
            name_ru="Автоматически популярный кружок",
            category="EDU",
            likes_count=100,
        )
        second = create_quality_place(
            name="Second Recommended Place",
            name_ru="Вторая рекомендация",
            category="EDU",
            is_home_recommended=True,
            home_recommended_order=20,
        )
        first = create_quality_place(
            name="First Recommended Place",
            name_ru="Первая рекомендация",
            category="EDU",
            is_home_recommended=True,
            home_recommended_order=10,
        )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [place.pk for place in response.context["popular_places"]],
            [first.pk, second.pk],
        )

    def test_home_page_uses_compact_conversion_flow_without_dropping_seo_links(self):
        create_quality_place(
            name="Compact Home Place",
            name_ru="Место для компактной главной",
            category="EDU",
            is_active=True,
            lat=40.4093,
            lng=49.8671,
            likes_count=20,
        )

        response = self.client.get("/ru/", follow=True)

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        ordered_markers = (
            'class="home-hero panel"',
            'class="panel home-map-panel"',
            'class="panel home-recommended"',
            'class="home-steps panel home-steps-lite',
            'id="for-owners"',
            'class="panel home-faq-panel"',
        )
        positions = [content.index(marker) for marker in ordered_markers]
        self.assertEqual(positions, sorted(positions))

        self.assertContains(response, 'class="home-search home-search-compact"', html=False)
        self.assertContains(response, "Открыть весь каталог")
        self.assertContains(response, "Рекомендуемые места и занятия")
        self.assertContains(response, "Как это работает")
        self.assertContains(response, "Разместить место")
        self.assertContains(response, "Частые вопросы о KidsMap")
        self.assertContains(response, 'class="home-faq-popular"', html=False)
        self.assertContains(response, 'href="/ru/catalog/?category=EDU"', html=False)
        self.assertContains(response, "Курсы для детей в Азербайджане")
        self.assertContains(response, "Проверенные и активные места")
        self.assertNotContains(response, 'class="panel home-events"', html=False)
        self.assertNotContains(response, 'class="home-owner-showcase"', html=False)

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    def test_home_page_prefers_google_maps_when_key_is_configured(self):
        create_quality_place(
            name="Home Map Place",
            name_ru="Кружок для карты на главной",
            category="EDU",
            is_active=True,
            lat=40.4093,
            lng=49.8671,
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "static/js/home_map.js")
        self.assertContains(response, 'data-home-map-google-key="test-key"', html=False)
        self.assertNotContains(response, "maps.googleapis.com/maps/api/js?key=test-key")
        self.assertNotContains(response, "kidsMapInitHomeMap")

    def test_home_page_does_not_render_manual_static_version_query_params(self):
        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "?v=")

    @override_settings(
        DEBUG=False,
        ALLOWED_HOSTS=["kidsmap.az"],
        GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123",
    )
    def test_home_page_includes_google_analytics_tag_when_configured(self):
        response = self.client.get("/", HTTP_HOST="kidsmap.az", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "https://www.googletagmanager.com/gtag/js?id=G-TEST123")
        self.assertContains(response, 'gtag("config", "G\\u002DTEST123")')

    def test_home_page_renders_static_hero_grid_for_single_slide(self):
        SiteGalleryImage.objects.all().delete()
        for index in range(3):
            SiteGalleryImage.objects.create(
                placement=SiteGalleryImage.PLACEMENT_HOME_HERO,
                image=SimpleUploadedFile(
                    f"hero-{index + 1}.jpg",
                    b"hero-image",
                    content_type="image/jpeg",
                ),
                title_ru=f"Фото {index + 1}",
                order=index + 1,
                is_active=True,
            )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "home-hero-slider-single")
        self.assertContains(response, "home-hero-photo-side-top")
        self.assertContains(response, "home-hero-photo-side-bottom")
        self.assertNotContains(response, "data-home-hero-slider-track")
        self.assertNotContains(response, "data-home-hero-slider-prev")

    def test_home_page_includes_website_schema_with_search_action(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"@type": "WebSite"', html=False)
        self.assertContains(response, '"SearchAction"', html=False)
        self.assertContains(response, "/catalog/?q={search_term_string}", html=False)

    def test_home_page_does_not_show_site_reviews_teaser(self):
        SiteReview.objects.create(author_name="No Text", rating=4, text="")
        SiteReview.objects.create(author_name="With Text", rating=5, text="Очень полезный сервис для родителей.")

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("site_reviews_teaser", response.context)
        self.assertNotContains(response, 'id="site-reviews"', html=False)
        self.assertNotContains(response, "Очень полезный сервис для родителей.")

    def test_login_page_is_marked_noindex(self):
        response = self.client.get("/ru/auth/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex,follow" />', html=False)
        self.assertContains(response, '<meta name="googlebot" content="noindex,follow" />', html=False)

    def test_filtered_catalog_page_uses_noindex_and_itemlist_schema(self):
        create_quality_place(
            name="Seo Place",
            name_ru="SEO кружок",
            category="EDU",
            is_active=True,
            district="Ясамал",
        )

        response = self.client.get("/ru/catalog/", {"category": "EDU"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex,follow" />', html=False)
        self.assertContains(response, "<title>Образование для детей в Азербайджане | KidsMap</title>", html=False)
        self.assertContains(response, '"@type": "ItemList"', html=False)
        self.assertContains(response, '"@type": "BreadcrumbList"', html=False)

    def test_place_detail_page_includes_breadcrumb_and_aggregate_rating_schema(self):
        place = create_quality_place(
            name="Seo Place",
            name_ru="SEO кружок",
            category="EDU",
            is_active=True,
            district="Ясамал",
            rating_avg=4.7,
            rating_count=12,
        )

        response = self.client.get(place.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"@type": "BreadcrumbList"', html=False)
        self.assertContains(response, '"AggregateRating"', html=False)
        self.assertContains(response, "<title>SEO кружок — Образование для детей в регионе Баку, Ясамальский район | KidsMap</title>", html=False)

    def test_robots_txt_disallows_private_sections(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /auth/")
        self.assertContains(response, "Disallow: /account/")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Disallow: /ru/auth/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_sitemap_includes_all_languages_and_hreflang_alternates(self):
        place = create_quality_place(
            name="Sitemap place",
            name_ru="Место для sitemap",
            category="EDU",
            is_active=True,
            district="Баку",
        )

        response = self.client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'xmlns:xhtml="http://www.w3.org/1999/xhtml"', html=False)
        self.assertContains(response, "<loc>http://testserver/</loc>", html=False)
        self.assertContains(response, "<loc>http://testserver/ru/</loc>", html=False)
        self.assertContains(response, "<loc>http://testserver/en/</loc>", html=False)
        self.assertContains(response, f"<loc>http://testserver{place.get_absolute_url()}</loc>", html=False)
        self.assertContains(response, f'<xhtml:link rel="alternate" hreflang="ru" href="http://testserver/ru{place.get_absolute_url()}"', html=False)
        self.assertContains(response, f'<xhtml:link rel="alternate" hreflang="en" href="http://testserver/en{place.get_absolute_url()}"', html=False)
        self.assertContains(response, f'<xhtml:link rel="alternate" hreflang="x-default" href="http://testserver{place.get_absolute_url()}"', html=False)

    def test_seo_landing_uses_matching_language_content_and_hreflang(self):
        checks = (
            (
                "/catalog/kruzhki-v-baku/",
                "Bakıda uşaqlar üçün dərnəklər",
                "http://testserver/catalog/kruzhki-v-baku/",
            ),
            (
                "/ru/catalog/kruzhki-v-baku/",
                "Кружки в Баку для детей",
                "http://testserver/ru/catalog/kruzhki-v-baku/",
            ),
            (
                "/en/catalog/kruzhki-v-baku/",
                "Kids' clubs in Baku",
                "http://testserver/en/catalog/kruzhki-v-baku/",
            ),
        )

        for path, heading, canonical in checks:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)
                self.assertContains(response, " | KidsMap</title>", html=False)
                self.assertContains(response, f'<link rel="canonical" href="{canonical}" />', html=False)
                self.assertContains(response, '<meta property="og:description"', html=False)
                self.assertContains(response, '<meta name="twitter:description"', html=False)
                self.assertContains(response, '<link rel="alternate" hreflang="az" href="http://testserver/catalog/kruzhki-v-baku/" />', html=False)
                self.assertContains(response, '<link rel="alternate" hreflang="ru" href="http://testserver/ru/catalog/kruzhki-v-baku/" />', html=False)
                self.assertContains(response, '<link rel="alternate" hreflang="en" href="http://testserver/en/catalog/kruzhki-v-baku/" />', html=False)

    def test_home_map_popup_uses_main_photo_preview(self):
        place = Place.objects.create(
            name="Home Map Place",
            name_ru="Кружок для карты на главной",
            category="EDU",
            is_active=True,
            status=Place.STATUS_PUBLISHED,
            lat=40.4093,
            lng=49.8671,
            age_from=6,
            age_to=12,
            address="Баку, ул. Низами, 10",
            price_from=50,
            price_to=80,
            description_ru=(
                "Достаточно подробное описание карточки, чтобы место прошло фильтры "
                "публичной выдачи и отобразилось на главной карте. "
                "Текст специально сделан длиннее минимального порога для public-выдачи. "
                "Здесь есть формат занятий, возрастная группа, полезные детали для родителей "
                "и ещё одна фраза, чтобы описание уверенно прошло проверку длины."
            ),
            phone1="+994501112233",
            schedule="Пн-Пт 10:00-18:00",
            website="https://example.com/home-map-place",
            photo=SimpleUploadedFile("popup-main.png", b"main-image", content_type="image/png"),
            cover_photo=SimpleUploadedFile("popup-cover.png", b"cover-image", content_type="image/png"),
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["map_places"][0]["image_url"], place.photo.url)
        self.assertTrue(response.context["map_places"][0]["price"])
        self.assertContains(response, "home-map-data")
        self.assertContains(response, place.photo.url)

    def test_home_map_search_text_includes_subcategory_name(self):
        category = Category.objects.create(code="SPORT", name="Sport", name_ru="Спорт")
        subcategory = Subcategory.objects.create(
            category=category,
            code="judo-test",
            name="Judo",
            name_ru="Дзюдо",
        )
        Place.objects.create(
            name="Judo Place",
            name_ru="Секция дзюдо",
            category=category.code,
            subcategory=subcategory,
            is_active=True,
            status=Place.STATUS_PUBLISHED,
            lat=40.4093,
            lng=49.8671,
            age_from=6,
            age_to=12,
            district="Ясамал",
            address="Баку, ул. Низами, 10",
            price_from=60,
            price_to=90,
            description_ru=(
                "Достаточно подробное описание карточки, чтобы место прошло фильтры "
                "публичной выдачи и отобразилось на главной карте. "
                "Текст специально сделан длиннее минимального порога для public-выдачи. "
                "Здесь есть формат занятий, возрастная группа, полезные детали для родителей "
                "и ещё одна фраза, чтобы описание уверенно прошло проверку длины."
            ),
            phone1="+994501112233",
            schedule="Пн-Пт 10:00-18:00",
            website="https://example.com/judo-place",
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("дзюдо", response.context["map_places"][0]["search_text"])

    def test_public_site_css_uses_subset_font_without_heavy_ttf(self):
        css_path = Path(settings.BASE_DIR) / "static" / "css" / "site.css"
        self.assertTrue(css_path.exists())
        css = css_path.read_text(encoding="utf-8")
        self.assertIn("ChironGoRoundTC-PublicSubset.woff2", css)
        self.assertIn("Chiron GoRound TC Public", css)
        self.assertNotIn("ChironGoRoundTC-VariableFont_wght.ttf", css)

    def test_collectstatic_builds_manifest_for_public_assets_in_production_mode(self):
        with TemporaryDirectory() as tmp_dir:
            manifest_root = Path(tmp_dir)
            production_storages = {
                "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
                "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
            }

            with override_settings(DEBUG=False, STATIC_ROOT=manifest_root, STORAGES=production_storages):
                call_command("collectstatic", interactive=False, verbosity=0, clear=True)

            manifest_path = manifest_root / "staticfiles.json"
            self.assertTrue(manifest_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paths = manifest.get("paths", {})

            self.assertIn("css/site.css", paths)
            self.assertIn("img/logo.svg", paths)
            self.assertIn("fonts/chiron/ChironGoRoundTC-PublicSubset.woff2", paths)
            self.assertIn("js/bg_scene.js", paths)
            self.assertIn("admin/css/pages/kidsmap_changelist.css", paths)
            self.assertIn("admin/css/kidsmap_taxonomy.css", paths)
            self.assertIn("admin/js/kidsmap_place_changelist.js", paths)
            self.assertIn("admin/js/kidsmap_place_form.js", paths)

    @override_settings(MEDIA_CACHE_MAX_AGE=3600)
    def test_media_serve_view_sets_cache_headers(self):
        request = RequestFactory().get("/media/example.jpg")
        response = HttpResponse(b"content", content_type="image/jpeg")

        with patch("config.views.serve_static_file", return_value=response) as serve_mock:
            served = serve_media_file(request, "example.jpg")

        serve_mock.assert_called_once_with(request, "example.jpg", document_root=settings.MEDIA_ROOT)
        self.assertEqual(served["Cache-Control"], "public, max-age=3600")
        self.assertEqual(served["X-Content-Type-Options"], "nosniff")

    def test_header_uses_icon_only_account_language_and_search_controls(self):
        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "user-entry-link")
        self.assertContains(response, "img/ui/login.svg")
        self.assertContains(response, "lang-flag-icon")
        self.assertContains(response, "img/flags/ru.png")
        self.assertContains(response, "img/flags/az.png")
        self.assertContains(response, "img/flags/en.png")
        self.assertContains(response, "lang-trigger-icononly")

class TestCatalogContentSettingsWiring(TestCase):
    def test_default_metro_station_list_contains_all_open_baku_metro_stations(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.metro_stations_json = []
        settings_obj.save(update_fields=["metro_stations_json", "updated_at"])

        form = OwnerPlaceCreateForm()
        metro_values = [value for value, _label in form.fields["metro"].choices if value]

        self.assertEqual(len(metro_values), 27)
        self.assertIn("Memar Əcəmi-2", metro_values)

    def test_home_page_uses_catalog_settings_districts(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Тестовый район"]
        settings_obj.save(update_fields=["districts_json", "updated_at"])
        create_quality_place(
            name="District Visible",
            name_ru="Район в фильтре",
            district="Тестовый район",
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["value"] for item in response.context["home_districts"]], ["тестовый район"])

    def test_owner_place_form_uses_catalog_settings_metro_options(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.metro_stations_json = ["Тестовое метро"]
        settings_obj.save(update_fields=["metro_stations_json", "updated_at"])

        form = OwnerPlaceCreateForm()
        metro_values = [value for value, _label in form.fields["metro"].choices]

        self.assertIn("Тестовое метро", metro_values)
        self.assertNotIn("Иншаатчылар", metro_values)

    def test_owner_place_form_uses_only_main_photo_field(self):
        form = OwnerPlaceCreateForm()

        self.assertIn("photo", form.fields)
        self.assertNotIn("cover_photo", form.fields)

    def test_place_gallery_files_prefers_main_photo_before_cover(self):
        place = Place.objects.create(
            name="Media Place",
            name_ru="Медиа-кружок",
            category="EDU",
            photo=SimpleUploadedFile("main-photo.png", b"main-image", content_type="image/png"),
            cover_photo=SimpleUploadedFile("cover-photo.png", b"cover-image", content_type="image/png"),
        )

        files = place.gallery_files()

        self.assertEqual(len(files), 1)
        self.assertIn("main-photo", files[0].name)

    def test_place_gallery_files_uses_cover_photo_only_as_fallback(self):
        place = Place.objects.create(
            name="Fallback Media Place",
            name_ru="Медиа без главного фото",
            category="EDU",
            photo=None,
            cover_photo=SimpleUploadedFile("cover-photo.png", b"cover-image", content_type="image/png"),
        )

        files = place.gallery_files()

        self.assertEqual(len(files), 1)
        self.assertIn("cover-photo", files[0].name)

    def test_catalog_filter_values_are_sorted_alphabetically(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Забрат", "Ахмедлы", "Бинагади"]
        settings_obj.metro_stations_json = ["Нариман Нариманов", "20 Января", "Азадлыг проспекти"]
        settings_obj.save(update_fields=["districts_json", "metro_stations_json", "updated_at"])
        create_quality_place(name="District 1", name_ru="District 1", district="Забрат", metro="Нариман Нариманов")
        create_quality_place(name="District 2", name_ru="District 2", district="Ахмедлы", metro="20 Января")
        create_quality_place(name="District 3", name_ru="District 3", district="Бинагади", metro="Азадлыг проспекти")

        response = self.client.get(reverse("place_list"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["value"] for item in response.context["district_options"]], ["baku", "baku_binagadi", "ахмедлы", "забрат"])
        self.assertEqual(
            [item["value"] for item in response.context["metro_options"]],
            ["20 Января", "Азадлыг проспекти", "Нариман Нариманов"],
        )

class TestLocalizedFilterOptions(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Баку", "Нариманов"]
        settings_obj.metro_stations_json = ["Ичеришехер"]
        settings_obj.save(update_fields=["districts_json", "metro_stations_json", "updated_at"])
        cls.category = Category.objects.create(
            code="L10N",
            name="Тестовая категория",
            name_az="Kateqoriya test",
            name_ru="Тестовая категория",
            name_en="Category test",
            is_active=True,
            order=999,
        )
        cls.subcategory = Subcategory.objects.create(
            category=cls.category,
            code="localized-filter-test",
            name="Подготовка к школе",
            name_az="Məktəbə hazırlıq",
            name_ru="Подготовка к школе",
            name_en="School prep",
            is_active=True,
            order=999,
        )
        cls.public_place = create_quality_place(
            name="Localized Public Place",
            name_ru="Локализованное место",
            name_az="Lokallaşdırılmış məkan",
            name_en="Localized place",
            category="L10N",
            subcategory=cls.subcategory,
            district="Баку",
            metro="Ичеришехер",
        )
        cls.public_place_two = create_quality_place(
            name="Localized Public Place Two",
            name_ru="Локализованное место 2",
            name_az="Lokallaşdırılmış məkan 2",
            name_en="Localized place 2",
            category="L10N",
            district="Нариманов",
            metro="Ичеришехер",
        )

    def test_az_catalog_and_home_render_localized_labels_with_stable_values(self):
        catalog_response = self.client.get("/az/catalog/", follow=True)
        home_response = self.client.get("/az/", follow=True)

        self.assertEqual(catalog_response.status_code, 200)
        self.assertContains(catalog_response, 'value="baku"', html=False)
        self.assertContains(catalog_response, 'data-label-current="Bakı"', html=False)
        self.assertContains(catalog_response, "Bakı — 2")
        self.assertContains(catalog_response, "Nərimanov", html=False)
        self.assertTrue(any(item["value"] == "L10N" and item["label"] == "Kateqoriya test" and item["count"] == 2 for item in catalog_response.context["categories"]))
        self.assertContains(home_response, 'value="baku"', html=False)
        self.assertContains(home_response, 'data-label-current="Bakı"', html=False)
        self.assertContains(home_response, 'Bakı — 2', html=False)
        self.assertNotContains(home_response, 'value="Bakı"', html=False)
        self.assertContains(home_response, '<option value="">Bütün kateqoriyalar</option>', html=False)

    def test_ru_catalog_renders_russian_labels(self):
        response = self.client.get("/ru/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-label-current="Баку"', html=False)
        self.assertContains(response, "Баку — 2")
        self.assertContains(response, "Нариманов", html=False)
        self.assertTrue(any(item["value"] == "L10N" and item["label"] == "Тестовая категория" and item["count"] == 2 for item in response.context["categories"]))

    def test_en_catalog_renders_english_labels(self):
        response = self.client.get("/en/catalog/", follow=True)
        home_response = self.client.get("/en/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-label-current="Baku"', html=False)
        self.assertContains(response, "Baku — 2")
        self.assertContains(response, "Narimanov", html=False)
        self.assertTrue(any(item["value"] == "L10N" and item["label"] == "Category test" and item["count"] == 2 for item in response.context["categories"]))
        self.assertContains(home_response, '<option value="">All categories</option>', html=False)

    def test_ru_home_uses_single_all_categories_option(self):
        response = self.client.get("/ru/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<option value="">Все категории</option>', html=False)
        self.assertNotContains(response, '<option value="">Категория</option>', html=False)

    def test_catalog_autocomplete_options_include_fallback_labels_for_search(self):
        response = self.client.get("/az/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-label-current="Bakı"', html=False)
        self.assertContains(response, 'data-label-ru="Баку"', html=False)
        self.assertContains(response, 'data-label-en="Baku"', html=False)
        self.assertContains(response, 'data-label-current="İçərişəhər"', html=False)
        self.assertContains(response, 'data-label-ru="Ичеришехер"', html=False)
        self.assertContains(response, 'data-label-en="Icherisheher"', html=False)

    def test_owner_place_form_uses_current_language_labels_and_stable_codes(self):
        with override("en"):
            form = OwnerPlaceCreateForm()
            category_html = form["category"].as_widget()
            subcategory_html = form["subcategory"].as_widget()
            district_choices = dict(form.fields["district"].choices)
            region_choices = dict(form.fields["region"].choices)

            self.assertIn('value="L10N"', category_html)
            self.assertIn(">Category test<", category_html)
            self.assertIn(f'value="{self.subcategory.pk}"', subcategory_html)
            self.assertIn(">School prep<", subcategory_html)
            self.assertIn(f'data-category="{self.category.code}"', subcategory_html)
            self.assertEqual(region_choices["baku"], "Baku")
            self.assertEqual(district_choices["baku_yasamal"], "Yasamal")

    def test_catalog_keeps_category_filter_by_stable_code_on_localized_pages(self):
        response = self.client.get("/az/catalog/?category=L10N", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["selected"]["category"], "L10N")
        self.assertContains(response, 'option value="L10N" selected', html=False)

class TestPublicFilterCounts(TestCase):
    @classmethod
    def setUpTestData(cls):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Баку", "Нариманов", "Пустой район"]
        settings_obj.metro_stations_json = ["Ичеришехер", "28 Май", "Пустое метро"]
        settings_obj.save(update_fields=["districts_json", "metro_stations_json", "updated_at"])

        cls.visible_category = Category.objects.create(
            code="COUNTED",
            name="Счетная категория",
            name_az="Sayılan kateqoriya",
            name_ru="Счетная категория",
            name_en="Counted category",
            is_active=True,
            order=1000,
        )
        cls.empty_category = Category.objects.create(
            code="EMPTYCAT",
            name="Пустая категория",
            name_az="Boş kateqoriya",
            name_ru="Пустая категория",
            name_en="Empty category",
            is_active=True,
            order=1001,
        )
        cls.visible_subcategory = Subcategory.objects.create(
            category=cls.visible_category,
            code="counted-subcategory",
            name="Счетная подкатегория",
            name_az="Sayılan alt kateqoriya",
            name_ru="Счетная подкатегория",
            name_en="Counted subcategory",
            is_active=True,
            order=1000,
        )
        cls.empty_subcategory = Subcategory.objects.create(
            category=cls.empty_category,
            code="empty-subcategory",
            name="Пустая подкатегория",
            name_az="Boş alt kateqoriya",
            name_ru="Пустая подкатегория",
            name_en="Empty subcategory",
            is_active=True,
            order=1001,
        )

        cls.visible_place_one = create_quality_place(
            name="Counted One",
            name_ru="Счетное место 1",
            category="COUNTED",
            subcategory=cls.visible_subcategory,
            district="Баку",
            metro="Ичеришехер",
        )
        cls.visible_place_two = create_quality_place(
            name="Counted Two",
            name_ru="Счетное место 2",
            category="COUNTED",
            district="Нариманов",
            metro="Ичеришехер",
        )
        cls.visible_place_three = create_quality_place(
            name="Education One",
            name_ru="Образовательное место",
            category="EDU",
            district="Баку",
            metro="28 Май",
        )
        for order, weekday in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun")):
            PlaceScheduleDay.objects.create(
                place=cls.visible_place_three,
                weekday=weekday,
                is_closed=False,
                order=order,
            )

        create_quality_place(
            name="Draft Counted",
            name_ru="Черновик счетной категории",
            category="COUNTED",
            subcategory=cls.visible_subcategory,
            district="Пустой район",
            metro="Пустое метро",
            status=Place.STATUS_DRAFT,
        )
        create_quality_place(
            name="Inactive Counted",
            name_ru="Неактивное счетное место",
            category="COUNTED",
            district="Пустой район",
            metro="Пустое метро",
            is_active=False,
        )
        create_quality_place(
            name="Deleted Counted",
            name_ru="Удаленное счетное место",
            category="COUNTED",
            district="Пустой район",
            metro="Пустое метро",
            deleted_at=timezone.now(),
        )
        create_quality_place(
            name="Low Quality Counted",
            name_ru="Некачественное счетное место",
            category="COUNTED",
            district="Пустой район",
            metro="Пустое метро",
            description_az="Qisa tesvir",
        )

    def test_catalog_filters_hide_zero_options_and_show_public_counts(self):
        response = self.client.get("/ru/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["value"] for item in response.context["categories"][:2]],
            ["COUNTED", "EDU"],
        )
        self.assertEqual(
            {item["value"]: item["count"] for item in response.context["categories"] if item.get("count") is not None},
            {"COUNTED": 2, "EDU": 1},
        )
        self.assertEqual(
            {item["value"]: item["count"] for item in response.context["district_options"] if item.get("count") is not None},
            {"baku": 3, "baku_narimanov": 1},
        )
        self.assertEqual(
            {item["value"]: item["count"] for item in response.context["metro_options"] if item.get("count") is not None},
            {"28 Май": 1, "Ичеришехер": 2},
        )
        self.assertEqual(
            {item["value"]: item["count"] for item in response.context["subcategory_options"] if item.get("count") is not None},
            {str(self.visible_subcategory.pk): 1},
        )
        self.assertNotContains(response, "Пустая категория")
        self.assertNotContains(response, "Пустой район")
        self.assertNotContains(response, "Пустое метро")

    def test_catalog_collapses_categories_after_first_ten(self):
        for index in range(9):
            category = Category.objects.create(
                code=f"OVERFLOW{index}",
                name=f"Категория {index}",
                name_az=f"Kateqoriya {index}",
                name_ru=f"Категория {index}",
                name_en=f"Category {index}",
                is_active=True,
                order=1100 + index,
            )
            create_quality_place(
                name=f"Overflow place {index}",
                name_ru=f"Место категории {index}",
                category=category,
            )

        response = self.client.get("/ru/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["categories"][0]["value"], "COUNTED")
        self.assertContains(response, " is-category-extra", count=2, html=False)
        self.assertContains(response, "Показать ещё", count=4)
        self.assertContains(response, 'class="category-overflow-toggle"', count=2, html=False)

    def test_home_filters_use_same_public_counts(self):
        response = self.client.get("/ru/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Счетная категория — 2")
        self.assertContains(response, "Баку — 3")
        self.assertNotContains(response, "Пустая категория")
        self.assertNotContains(response, "Пустой район")

    def test_selected_zero_value_is_preserved_in_catalog_form(self):
        response = self.client.get("/ru/catalog/?category=EMPTYCAT&district=Пустой район&metro=Пустое метро", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["value"] == "EMPTYCAT" and item.get("count") is None for item in response.context["categories"]))
        self.assertTrue(any(item["value"] == "пустой район" and item.get("count") is None for item in response.context["district_options"]))
        self.assertTrue(any(item["value"] == "Пустое метро" and item.get("count") is None for item in response.context["metro_options"]))
        self.assertContains(response, 'option value="EMPTYCAT" selected', html=False)
        self.assertContains(response, 'name="district" value="пустой район"', html=False)
        self.assertContains(response, 'name="metro" value="Пустое метро"', html=False)

    def test_public_filter_counts_are_localized_in_all_languages(self):
        az_response = self.client.get("/az/catalog/", follow=True)
        en_response = self.client.get("/en/catalog/", follow=True)

        self.assertTrue(any(item["value"] == "COUNTED" and item["label_with_count"] == "Sayılan kateqoriya — 2" for item in az_response.context["categories"]))
        self.assertTrue(any(item["value"] == "COUNTED" and item["label_with_count"] == "Counted category — 2" for item in en_response.context["categories"]))
        self.assertTrue(any(item["value"] == "baku" and item["label_with_count"] == "Bakı — 3" for item in az_response.context["district_options"]))
        self.assertTrue(any(item["value"] == "baku" and item["label_with_count"] == "Baku — 3" for item in en_response.context["district_options"]))

    def test_home_page_uses_consistent_localized_ui_for_az_ru_en(self):
        Category.objects.create(
            code="L10N",
            name="Локализованная категория",
            name_az="Lokalizasiya kateqoriyası",
            name_ru="Локализованная категория",
            name_en="Localized category",
            is_active=True,
            order=1002,
        )
        structured_place = create_quality_place(
            name="Structured Place",
            name_ru="Структурированное место",
            name_az="Strukturlaşdırılmış məkan",
            name_en="Structured place",
            category="L10N",
            district="baku_narimanov",
            metro="28 Май",
            schedule="",
            lat=40.4093,
            lng=49.8671,
        )
        for order, weekday in enumerate(("mon", "tue", "wed", "thu", "fri", "sat", "sun")):
            day = PlaceScheduleDay.objects.create(
                place=structured_place,
                weekday=weekday,
                is_closed=(weekday == "sun"),
                is_24_hours=False,
                order=order,
            )
            if weekday != "sun":
                PlaceScheduleInterval.objects.create(
                    schedule_day=day,
                    start_time="09:00",
                    end_time="18:00",
                    order=0,
                )

        second_place = create_quality_place(
            name="Sabail Place",
            name_ru="Место в Сабаиле",
            name_az="Səbaildə məkan",
            name_en="Sabail place",
            category="L10N",
            district="baku_sabail",
            lat=40.3700,
            lng=49.8400,
        )
        third_place = create_quality_place(
            name="Khatai Place",
            name_ru="Место в Хатаи",
            name_az="Xətaidə məkan",
            name_en="Khatai place",
            category="L10N",
            district="baku_khatai",
            lat=40.3850,
            lng=49.8900,
        )

        az_response = self.client.get("/", follow=True)
        ru_response = self.client.get("/ru/", follow=True)
        en_response = self.client.get("/en/", follow=True)

        for response in (az_response, ru_response, en_response):
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, ">baku_narimanov<", html=False)
            self.assertNotContains(response, ">baku_sabail<", html=False)
            self.assertNotContains(response, ">baku_khatai<", html=False)

        self.assertContains(az_response, "Bakı, Nərimanov rayonu")
        self.assertContains(az_response, "Bakı, Səbail rayonu")
        self.assertContains(az_response, "Bakı, Xətai rayonu")
        self.assertTrue(any("Bazar ertəsi" in item["schedule"] for item in az_response.context["map_places"]))
        self.assertContains(az_response, "Hələ rəy yoxdur")
        self.assertNotContains(az_response, "Пока нет отзывов")
        self.assertNotContains(az_response, "No reviews yet")
        self.assertNotContains(az_response, "Monday")

        self.assertContains(ru_response, "Баку, Наримановский район")
        self.assertContains(ru_response, "Баку, Сабаильский район")
        self.assertContains(ru_response, "Баку, Хатаинский район")
        self.assertTrue(any("Понедельник" in item["schedule"] for item in ru_response.context["map_places"]))
        self.assertContains(ru_response, "Пока нет отзывов")
        self.assertNotContains(ru_response, "Hələ rəy yoxdur")
        self.assertNotContains(ru_response, "No reviews yet")
        self.assertNotContains(ru_response, "Monday")

        self.assertContains(en_response, "Narimanov District, Baku")
        self.assertContains(en_response, "Sabail District, Baku")
        self.assertContains(en_response, "Khatai District, Baku")
        self.assertTrue(any("Monday" in item["schedule"] for item in en_response.context["map_places"]))
        self.assertContains(en_response, "No reviews yet")
        self.assertNotContains(en_response, "Hələ rəy yoxdur")
        self.assertNotContains(en_response, "Пока нет отзывов")
        self.assertNotContains(en_response, "Понедельник")

        self.assertEqual(len(az_response.context["map_places"]), 3)
        self.assertEqual(len(ru_response.context["map_places"]), 3)
        self.assertEqual(len(en_response.context["map_places"]), 3)
        self.assertEqual(
            {item["value"]: item.get("count") for item in az_response.context["home_categories"]},
            {item["value"]: item.get("count") for item in ru_response.context["home_categories"]},
        )
        self.assertEqual(
            {item["value"]: item.get("count") for item in az_response.context["home_categories"]},
            {item["value"]: item.get("count") for item in en_response.context["home_categories"]},
        )

    def test_catalog_category_colors_fall_back_to_preset_palette(self):
        category = Category.objects.get(code="EDU")
        category.color_bg = "#FFFFFF"
        category.color_text = "#111827"
        category.save(update_fields=["color_bg", "color_text"])

        response = self.client.get("/ru/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        edu_option = next(item for item in response.context["categories"] if item["value"] == "EDU")
        self.assertEqual(edu_option["color_bg"], "#E6ECFF")
        self.assertEqual(edu_option["color_text"], "#4F46E5")

class TestCatalogEnhancements(TestCase):
    def test_home_map_and_favorite_buttons_have_localized_names(self):
        create_quality_place(
            name="Home Accessible Place",
            name_az="Əlçatan Ev Məkanı",
            name_ru="Доступное место на главной",
            name_en="Accessible Home Place",
            lat=40.4093,
            lng=49.8671,
            likes_count=50,
        )
        expectations = {
            "az": ("Xəritədə məkanı aç: {name}", "Seçilmişlərə əlavə et"),
            "ru": ("Открыть место на карте: {name}", "Добавить в избранное"),
            "en": ("Open place on map: {name}", "Add to favorites"),
        }

        for language_code, (marker_label, favorite_label) in expectations.items():
            url = "/" if language_code == "az" else f"/{language_code}/"
            response = self.client.get(url, follow=True)

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'data-marker-label="{marker_label}"', html=False)
            self.assertContains(response, f'aria-label="{favorite_label}"', html=False)
            self.assertContains(response, 'aria-pressed="false"', html=False)

    def test_public_catalog_accessibility_labels_are_localized(self):
        create_quality_place(
            name="Accessible Place",
            name_az="Əlçatan Məkan",
            name_ru="Доступное место",
            name_en="Accessible Place",
            lat=40.4093,
            lng=49.8671,
            rating_avg=4.8,
            rating_count=12,
        )
        expectations = {
            "az": ("Seçilmişlərə əlavə et", "Filtrləri aç", "Nəticələri xəritədə göstər", "Reytinq 4,8 / 5"),
            "ru": ("Добавить в избранное", "Открыть фильтры", "Показать результаты на карте", "Рейтинг 4,8 из 5"),
            "en": ("Add to favorites", "Open filters", "Show results on map", "Rating 4.8 out of 5"),
        }

        for language_code, labels in expectations.items():
            url = "/catalog/" if language_code == "az" else f"/{language_code}/catalog/"
            response = self.client.get(url, follow=True)

            self.assertEqual(response.status_code, 200)
            for label in labels:
                self.assertContains(response, f'aria-label="{label}"', html=False)
            self.assertContains(response, 'class="like-btn"', html=False)
            self.assertContains(response, 'aria-pressed="false"', html=False)
            self.assertContains(response, 'data-marker-label=', html=False)
            self.assertContains(response, 'aria-expanded="false"', html=False)

    def test_authenticated_favorite_exposes_pressed_state_and_both_labels(self):
        user = User.objects.create_user(username="accessible_user", password="StrongPass123!!")
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER)
        place = create_quality_place(name="Favorite Accessible Place")
        PlaceLike.objects.create(place=place, user=user)
        self.client.force_login(user)

        response = self.client.get("/en/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'aria-pressed="true"', html=False)
        self.assertContains(response, 'aria-label="Remove from favorites"', html=False)
        self.assertContains(response, 'data-favorite-add-label="Add to favorites"', html=False)
        self.assertContains(response, 'data-favorite-remove-label="Remove from favorites"', html=False)

    def test_place_detail_star_picker_has_localized_names_and_hidden_glyphs(self):
        user = User.objects.create_user(username="rating_access_user", password="StrongPass123!!")
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER)
        place = create_quality_place(name="Rating Accessible Place")
        self.client.force_login(user)
        expectations = {
            "az": "5 baldan 1 bal",
            "ru": "1 из 5 звёзд",
            "en": "1 out of 5 stars",
        }

        for language_code, label in expectations.items():
            with override(language_code):
                detail_url = place.get_absolute_url()
            response = self.client.get(detail_url, follow=True)

            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'aria-label="{label}"', html=False)
            self.assertContains(response, '<span aria-hidden="true">★</span>', count=5, html=False)

    def test_review_count_filter_localizes_zero_one_two_and_five(self):
        from django.template import Context, Template

        template = Template("{% load catalog_i18n %}{{ count|review_count }}")
        expected_by_language = {
            "az": {0: "0 rəy", 1: "1 rəy", 2: "2 rəy", 5: "5 rəy"},
            "ru": {0: "0 отзывов", 1: "1 отзыв", 2: "2 отзыва", 5: "5 отзывов"},
            "en": {0: "0 reviews", 1: "1 review", 2: "2 reviews", 5: "5 reviews"},
        }

        for language_code, cases in expected_by_language.items():
            with override(language_code):
                for count, expected in cases.items():
                    with self.subTest(language_code=language_code, count=count):
                        self.assertEqual(template.render(Context({"count": count})), expected)

    def test_place_detail_drops_foreign_next_query_parameter(self):
        place = create_quality_place(
            name="Context Place",
            name_ru="Карточка с контекстом",
        )

        next_url = "/ru/catalog/?district=%D0%AF%D1%81%D0%B0%D0%BC%D0%B0%D0%BB"
        response = self.client.get(f"{place.get_absolute_url()}?next={next_url}")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], place.get_absolute_url())

    def test_catalog_keeps_its_own_filter_query_and_detail_links_are_clean(self):
        place = create_quality_place(name="Clean catalog link", name_ru="Чистая ссылка")

        response = self.client.get(f"{reverse('place_list')}?q=%D0%A7%D0%B8%D1%81%D1%82%D0%B0%D1%8F")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{place.get_absolute_url()}"', html=False)
        self.assertNotContains(response, f'{place.get_absolute_url()}?next=', html=False)

    def test_language_switch_preserves_catalog_filters_only(self):
        response = self.client.get(f"{reverse('place_list')}?category=EDU&next=/catalog/")

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], f"{reverse('place_list')}?category=EDU")

    def test_catalog_can_sort_places_by_review_count(self):
        low_reviews = create_quality_place(
            name="Few Reviews",
            name_ru="Мало отзывов",
            rating_count=1,
            rating_avg=4.2,
        )
        high_reviews = create_quality_place(
            name="Many Reviews",
            name_ru="Много отзывов",
            rating_count=9,
            rating_avg=4.8,
        )

        response = self.client.get(reverse("place_list"), {"sort": "reviews_desc"}, follow=True)

        self.assertEqual(response.status_code, 200)
        ordered_names = [item.name_ru for item in response.context["places"]]
        self.assertLess(ordered_names.index(high_reviews.name_ru), ordered_names.index(low_reviews.name_ru))

    def test_catalog_district_filter_matches_exact_value_only(self):
        exact_place = create_quality_place(
            name="Exact District",
            name_ru="Точный район",
            district="Ясамал",
        )
        partial_place = create_quality_place(
            name="Partial District",
            name_ru="Похожий район",
            district="Новый Ясамал",
        )

        with override("ru"):
            response = self.client.get(reverse("place_list"), {"district": "Ясамал"}, follow=True)

        self.assertEqual(response.status_code, 200)
        names = [item.name_ru for item in response.context["places"]]
        self.assertIn(exact_place.name_ru, names)
        self.assertNotIn(partial_place.name_ru, names)

    def test_catalog_metro_filter_matches_exact_value_only(self):
        exact_place = create_quality_place(
            name="Exact Metro",
            name_ru="Точное метро",
            metro="28 Май",
        )
        partial_place = create_quality_place(
            name="Partial Metro",
            name_ru="Похожее метро",
            metro="Около 28 Май",
        )

        response = self.client.get(reverse("place_list"), {"metro": "28 Май"}, follow=True)

        self.assertEqual(response.status_code, 200)
        names = [item.name_ru for item in response.context["places"]]
        self.assertIn(exact_place.name_ru, names)
        self.assertNotIn(partial_place.name_ru, names)

    def test_catalog_price_filter_uses_range_overlap(self):
        overlapping_place = create_quality_place(
            name="Overlap Price",
            name_ru="Подходящий диапазон цены",
            price_from=80,
            price_to=120,
        )
        out_of_range_place = create_quality_place(
            name="Out Price",
            name_ru="Неподходящий диапазон цены",
            price_from=200,
            price_to=260,
        )

        response = self.client.get(
            reverse("place_list"),
            {"price_from": "100", "price_to": "150"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        names = [item.name_ru for item in response.context["places"]]
        self.assertIn(overlapping_place.name_ru, names)
        self.assertNotIn(out_of_range_place.name_ru, names)

    def test_new_page_with_photo_filter_ignores_null_photo_fields(self):
        with_photo_place = create_quality_place(
            name="Recent With Photo",
            name_ru="Новое с фото",
            photo=SimpleUploadedFile("new-photo.png", b"main-image", content_type="image/png"),
        )
        without_photo_place = create_quality_place(
            name="Recent Without Photo",
            name_ru="Новое без фото",
            photo=None,
            cover_photo=None,
        )

        response = self.client.get(reverse("place_new"), {"with_photo": "1"}, follow=True)

        self.assertEqual(response.status_code, 200)
        timeline_names = [item.name_ru for item in response.context["timeline_places"]]
        page_names = [item.name_ru for item in response.context["places"]]
        all_names = timeline_names + page_names
        self.assertIn(with_photo_place.name_ru, all_names)
        self.assertNotIn(without_photo_place.name_ru, all_names)

    def test_place_detail_renders_extended_schedule_and_pricing_information(self):
        place = create_quality_place(
            name="Detailed Place",
            name_ru="Кружок с подробной ценой",
            schedule="Пн/Ср/Пт 18:00-19:00",
            lesson_duration_minutes=60,
            lesson_format="group",
            price_from=80,
            price_to=120,
            price_per_lesson=20,
            price_per_month=160,
            price_per_8_lessons=140,
            extra_conditions="Пробный урок бесплатно",
            additional_info="Нужна спортивная форма",
        )

        with override("ru"):
            response = self.client.get(place.get_absolute_url(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Цена и занятия")
        self.assertContains(response, "detail-unified-pricing--no-plans")
        self.assertContains(response, "detail-unified-pricing--with-schedule")
        self.assertContains(response, "20 AZN")
        self.assertNotContains(response, 'class="detail-unified-pricing__price-sub"', html=False)
        self.assertContains(response, "Формат занятий")
        self.assertContains(response, "Групповые")
        self.assertContains(response, "60 мин")
        self.assertContains(response, "detail-highlight-card--lesson")
        self.assertNotContains(response, "detail-highlight-card--schedule")
        self.assertContains(response, "Пн/Ср/Пт 18:00-19:00")
        self.assertContains(response, "Пробный урок бесплатно")
        self.assertContains(response, "Нужна спортивная форма")

    def test_place_detail_renders_structured_schedule_rows(self):
        place = create_quality_place(
            name="Structured Detail Place",
            name_ru="Кружок со структурированным расписанием",
            schedule="",
            lesson_duration_minutes=60,
        )
        payload = json.loads(build_structured_schedule_payload())
        from catalog.services.place_schedule import sync_place_schedule

        sync_place_schedule(place, payload)

        with override("ru"):
            response = self.client.get(place.get_absolute_url(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пн–Пт")
        self.assertContains(response, "09:00–18:00")
        self.assertContains(response, "Сб")
        self.assertContains(response, "10:00–16:00")

    def test_place_detail_does_not_show_owner_request_block(self):
        place = create_quality_place(
            name="Owner Claim Place",
            name_ru="Кружок без блока владельца",
            address="Баку, Низами 10",
            schedule="Пн-Пт 10:00-18:00",
            phone1="+994501112233",
            age_from=5,
            price_from=30,
            description_ru=(
                "Полезное место для детей и родителей с понятным расписанием, контактами, "
                "возрастными ограничениями и описанием услуг для семейного каталога KidsMap."
            ),
        )

        with override("ru"):
            response = self.client.get(
                reverse("place_detail", kwargs={"pk": place.pk, "slug": place.slug}),
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Вы представитель этого кружка?")
        self.assertNotContains(response, "intent=owner_place")

    def test_place_detail_shows_information_disclaimer(self):
        place = create_quality_place(
            name="Place With Disclaimer",
            name_ru="Кружок с дисклеймером",
        )

        with override("az"):
            response = self.client.get(
                reverse("place_detail", kwargs={"pk": place.pk, "slug": place.slug}),
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bu səhifədəki məlumatların bir hissəsi açıq mənbələrdən və üçüncü şəxslərdən əldə oluna bilər.")
        self.assertContains(response, "Cədvəli, qiyməti, ünvanı və şərtləri ziyarətdən əvvəl birbaşa təşkilatla dəqiqləşdirin.")
        self.assertNotContains(response, reverse("request_place_ownership", args=[place.id]))

    def test_card_price_badge_label_keeps_from_prefix_for_lower_bound_price(self):
        with override("ru"):
            place = Place(price_from=80, category="EDU")

            self.assertEqual(place.card_price_badge_label, "от")
            self.assertEqual(place.card_price_badge_value, "80")
            self.assertEqual(place.card_price_badge_currency, "AZN")

    def test_free_place_prices_are_localized_in_model_helpers(self):
        with override("ru"):
            ru_place = Place(category="EDU", price_from=0, price_to=0)
            self.assertEqual(ru_place.price_range_display, "Бесплатно")
            self.assertEqual(ru_place.card_price_badge_value, "Бесплатно")
            self.assertEqual(ru_place.card_price_badge_currency, "")

        with override("az"):
            az_place = Place(category="EDU", price_from=0, price_to=0, price_per_month=0)
            self.assertEqual(az_place.price_range_display, "Pulsuz")
            self.assertEqual(az_place.card_price_badge_value, "Pulsuz")
            self.assertIn(("1 ay", "Pulsuz"), az_place.pricing_options)

        with override("en"):
            en_place = Place(category="EDU", price_per_lesson=0)
            self.assertEqual(en_place.card_price_badge, "Free")
            self.assertEqual(en_place.card_price_badge_value, "Free")
            self.assertEqual(en_place.card_price_badge_currency, "")

    def test_place_detail_and_catalog_show_free_instead_of_zero_price(self):
        place = create_quality_place(
            name="Free Place",
            name_ru="Бесплатный кружок",
            price_from=0,
            price_to=0,
            price_per_month=0,
        )

        with override("ru"):
            detail_response = self.client.get(place.get_absolute_url(), follow=True)
            catalog_response = self.client.get(reverse("place_list"), follow=True)

        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Бесплатно")
        self.assertNotContains(detail_response, "0 AZN")
        self.assertContains(catalog_response, "Бесплатно")

    def test_owner_place_form_explains_how_to_mark_free_price(self):
        with override("ru"):
            form = OwnerPlaceCreateForm()

        self.assertIn("0 в обоих полях", form.fields["price_from"].help_text)
        self.assertIn("Если бесплатно, укажите 0.", form.fields["price_per_lesson"].help_text)

    def test_place_detail_renders_swipe_ready_gallery(self):
        place = create_quality_place(
            name="Gallery Place",
            name_ru="Кружок с галереей",
            photo=SimpleUploadedFile("detail-main.png", b"main-image", content_type="image/png"),
        )
        PlacePhoto.objects.create(
            place=place,
            image=SimpleUploadedFile("detail-gallery.png", b"gallery-image", content_type="image/png"),
            order=1,
        )

        response = self.client.get(place.get_absolute_url(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-place-gallery")
        self.assertContains(response, "data-place-gallery-main")
        self.assertContains(response, "swiper-wrapper")
        self.assertContains(response, "place-gallery__backdrop")
        self.assertContains(response, "place-gallery__image")
        self.assertContains(response, "data-place-gallery-thumb")
        self.assertContains(response, "static/js/place_gallery.js")

    def test_catalog_card_does_not_render_redundant_more_details_block(self):
        create_quality_place(
            name="More Details Kids Club",
            name_ru="Карточка с блоком другое",
            address="Баку, улица Низами, 5",
            schedule="Вторник и четверг 15:00-17:00",
            additional_info="Есть пробное занятие",
        )

        with override("ru"):
            response = self.client.get(reverse("place_list"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "place-more-details")
        self.assertNotContains(response, "Есть пробное занятие")

    def test_catalog_map_uses_only_filtered_map_ready_places(self):
        matching_place = create_quality_place(
            name="Map Match",
            name_ru="Точка на карте",
            district="Ясамал",
            metro="Низами",
            lat=40.3771,
            lng=49.8412,
        )
        Place.objects.create(
            name="Map Other District",
            name_ru="Чужой район",
            category="EDU",
            is_active=True,
            district="Нариманов",
            lat=40.4001,
            lng=49.8532,
        )
        create_quality_place(
            name="Map Missing Coordinates",
            name_ru="Без координат",
            district="Ясамал",
            lat=None,
            lng=None,
        )

        response = self.client.get(reverse("place_list"), {"district": "Ясамал"}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-catalog-map-open")
        self.assertContains(response, "catalog-map-data")
        self.assertEqual(response.context["catalog_map_places_count"], 1)
        self.assertEqual(response.context["catalog_map_missing_count"], 1)
        language_code = response.context["language"]
        from catalog.services.locations import get_location_translation
        with override(language_code):
            expected_location = " / ".join(
                part for part in (get_location_translation(matching_place.district, language_code), translate(matching_place.metro)) if part
            )
            expected_category = matching_place.get_category_display()
        self.assertEqual(
            response.context["catalog_map_places"],
            [
                {
                    "id": matching_place.id,
                    "name": matching_place.name_i18n(language_code),
                    "lat": matching_place.lat,
                    "lng": matching_place.lng,
                    "url": matching_place.get_absolute_url(),
                    "category": expected_category,
                    "category_code": matching_place.category_code,
                    "category_color_bg": matching_place.category.resolved_color_bg,
                    "category_color_text": matching_place.category.resolved_color_text,
                    "category_icon_url": matching_place.category.icon_file_url,
                    "category_icon_is_svg": matching_place.category.icon_is_svg,
                    "category_icon_is_font": matching_place.category.icon_is_font_class,
                    "category_icon_name": matching_place.category.icon or "",
                    "image_url": "",
                    "location": expected_location,
                    "address": "Bakı şəhəri, Nizami küçəsi 10, " + get_location_translation(matching_place.district, language_code),
                    "district": get_location_translation(matching_place.district, language_code),
                    "metro": translate(matching_place.metro),
                    "rating": 0.0,
                    "reviews_count": 0,
                    "phone": "+994501112233",
                    "schedule": "Bazar ertəsi, çərşənbə və cümə 15:00-17:00",
                }
            ],
        )

    def test_catalog_map_serialization_includes_card_fields(self):
        place = create_quality_place(
            name="Map Card Place",
            name_ru="Карточка на карте",
            district="Ясамал",
            metro="Низами",
            lat=40.3771,
            lng=49.8412,
            address="Bakı, Yasamal, Mərkəzi küçə 12",
            phone1="+994501234567",
            rating_avg=4.6,
            rating_count=128,
        )

        with override("ru"):
            serialized = PlaceController.build_default()._serialize_map_places(
                Place.objects.filter(pk=place.pk),
                language_code="ru",
            )
            expected_category = place.get_category_display()
            expected_url = place.get_absolute_url()

        self.assertEqual(
            serialized,
            [
                {
                    "id": place.id,
                    "name": place.name_i18n("ru"),
                    "lat": place.lat,
                    "lng": place.lng,
                    "url": expected_url,
                    "category": expected_category,
                    "category_code": place.category_code,
                    "category_color_bg": place.category.resolved_color_bg,
                    "category_color_text": place.category.resolved_color_text,
                    "category_icon_url": place.category.icon_file_url,
                    "category_icon_is_svg": place.category.icon_is_svg,
                    "category_icon_is_font": place.category.icon_is_font_class,
                    "category_icon_name": place.category.icon or "",
                    "image_url": "",
                    "location": "Баку, Ясамальский район / Низами",
                    "address": "Bakı, Yasamal, Mərkəzi küçə 12, Баку, Ясамальский район",
                    "district": "Баку, Ясамальский район",
                    "metro": "Низами",
                    "rating": 4.6,
                    "reviews_count": 128,
                    "phone": "+994501234567",
                    "schedule": "Bazar ertəsi, çərşənbə və cümə 15:00-17:00",
                }
            ],
        )

    def test_az_place_detail_uses_translated_labels_and_duration(self):
        place = create_quality_place(
            name="AZ Place",
            name_az="AZ Məkan",
            lesson_duration_minutes=90,
        )

        with override("az"):
            response = self.client.get(
                reverse("place_detail", kwargs={"pk": place.pk, "slug": place.slug}),
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Əsas xüsusiyyətlər")
        self.assertContains(response, "Qısa məlumat")
        self.assertContains(response, "90 dəqiqə")
        self.assertNotContains(response, "Основные характеристики")
        self.assertNotContains(response, "Краткая информация")
        self.assertNotContains(response, "90 мин")

    def test_catalog_card_uses_localized_district_instead_of_code(self):
        baku_place = create_quality_place(
            name="District Code Place",
            name_az="Rayon Kodlu Məkan",
            district="baku_narimanov",
        )
        region_place = create_quality_place(
            name="Region Code Place",
            name_az="Region Kodlu Məkan",
            district="agdash",
        )

        response = self.client.get("/az/catalog/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bakı, Nərimanov rayonu")
        self.assertContains(response, "Ağdaş")
        self.assertNotContains(response, ">baku_narimanov<", html=False)
        self.assertNotContains(response, ">agdash<", html=False)
        self.assertContains(response, baku_place.name_az)
        self.assertContains(response, region_place.name_az)

    def test_localized_address_removes_duplicate_city_and_district_segments(self):
        from catalog.services.locations import localize_address_text

        cases = (
            (
                "az",
                "Bakı şəhəri, Bakı, Bakı, Nərimanov rayonu rayonu",
                "Bakı şəhəri, Nərimanov rayonu",
            ),
            (
                "az",
                "Баку город, Баку, Наримановский район район",
                "Bakı şəhəri, Nərimanov rayonu",
            ),
            (
                "en",
                "Baku city, Baku, Baku, Narimanov District district",
                "Baku city, Narimanov District",
            ),
            (
                "ru",
                "Баку город, Баку, Баку, Наримановский район район",
                "Баку город, Наримановский район",
            ),
            (
                "ru",
                "Bakı şəhəri, Bakı, Nərimanov rayonu rayonu",
                "Баку город, Наримановский район",
            ),
        )

        for language_code, value, expected in cases:
            with self.subTest(language_code=language_code, value=value):
                self.assertEqual(localize_address_text(value, language_code), expected)

class TestReviewEnhancements(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="review_user",
            email="review_user@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(user=self.user, role=UserProfile.ROLE_USER)
        self.place = Place.objects.create(
            name="Review Place",
            name_ru="Кружок для отзывов",
            category="EDU",
            is_active=True,
        )

    def test_place_review_profanity_is_masked_before_publish(self):
        self.client.login(username="review_user", password="StrongPass123!!")

        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={
                "rating": "5",
                "text": "This place is fucking great",
                "author_name": "Tester",
                "next": f"{self.place.get_absolute_url()}#reviews",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        review = PlaceReview.objects.get(place=self.place)
        self.assertTrue(review.contains_profanity)
        self.assertNotIn("fucking", review.text.lower())
        self.assertIn("*", review.text)
        self.assertContains(response, "автоматически скрыты")

    def test_place_review_reactions_update_counters(self):
        review = PlaceReview.objects.create(place=self.place, rating=5, text="Хорошо", author_name="User")
        self.client.login(username="review_user", password="StrongPass123!!")

        response = self.client.post(
            reverse("vote_place_review", args=[review.id]),
            data={"value": "1", "next": f"{self.place.get_absolute_url()}#reviews"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.likes_count, 1)
        self.assertEqual(review.dislikes_count, 0)
        self.assertTrue(PlaceReviewReaction.objects.filter(review=review, value=1).exists())

        self.client.post(
            reverse("vote_place_review", args=[review.id]),
            data={"value": "-1", "next": f"{self.place.get_absolute_url()}#reviews"},
            follow=True,
        )
        review.refresh_from_db()
        self.assertEqual(review.likes_count, 0)
        self.assertEqual(review.dislikes_count, 1)

    def test_place_review_reaction_ajax_updates_without_reload(self):
        review = PlaceReview.objects.create(place=self.place, rating=5, text="Отлично", author_name="User")
        self.client.login(username="review_user", password="StrongPass123!!")

        response = self.client.post(
            reverse("vote_place_review", args=[review.id]),
            data={"value": "1", "next": f"{self.place.get_absolute_url()}#reviews"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["current_reaction"], 1)
        self.assertEqual(payload["likes_count"], 1)
        self.assertEqual(payload["dislikes_count"], 0)
        self.assertEqual(PlaceReviewReaction.objects.filter(review=review, user=self.user).count(), 1)

    def test_place_review_reaction_requires_login_for_guest_ajax(self):
        review = PlaceReview.objects.create(place=self.place, rating=5, text="Отлично", author_name="User")

        response = self.client.post(
            reverse("vote_place_review", args=[review.id]),
            data={"value": "1", "next": f"{self.place.get_absolute_url()}#reviews"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 401)
        payload = json.loads(response.content)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["auth_required"])
        self.assertIn(reverse("account_login"), payload["redirect_url"])
        self.assertIn("message", payload)
        self.assertEqual(PlaceReviewReaction.objects.filter(review=review).count(), 0)

    def test_place_reviews_feed_shows_a_clear_link_to_the_reviewed_place(self):
        self.place.district = "Nərimanov"
        self.place.save(update_fields=["district"])
        PlaceReview.objects.create(
            place=self.place,
            rating=5,
            text="Очень удобная страница с отзывами.",
            author_name="Alina",
        )

        response = self.client.get(reverse("place_reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="review-place-card"', html=False)
        self.assertContains(response, self.place.get_absolute_url(), html=False)
        self.assertContains(response, self.place.name_i18n)
        self.assertContains(response, "Alina")

    def test_review_models_disable_anonymous_flag_and_keep_author_name(self):
        place_review = PlaceReview.objects.create(
            place=self.place,
            author_name="Мария",
            rating=5,
            text="Текст отзыва",
            is_anonymous=True,
        )
        site_review = SiteReview.objects.create(
            author_name="Ирина",
            rating=4,
            text="Текст отзыва о сайте",
            is_anonymous=True,
        )

        place_review.refresh_from_db()
        site_review.refresh_from_db()

        self.assertFalse(place_review.is_anonymous)
        self.assertFalse(site_review.is_anonymous)
        self.assertEqual(place_review.author_name_i18n, "Мария")
        self.assertEqual(site_review.author_name_i18n, "Ирина")

    def test_site_reviews_page_can_sort_reviews_by_likes(self):
        SiteReview.objects.create(author_name="Low", rating=4, text="Нормально", likes_count=1, dislikes_count=0)
        SiteReview.objects.create(author_name="High", rating=5, text="Отлично", likes_count=7, dislikes_count=0)

        response = self.client.get(reverse("site_reviews"), {"sort": "likes"}, follow=True)

        self.assertEqual(response.status_code, 200)
        ordered_authors = [item.author_name for item in response.context["site_reviews"]]
        self.assertEqual(ordered_authors[:2], ["High", "Low"])

    def test_site_reviews_page_skips_blank_text_reviews(self):
        SiteReview.objects.create(author_name="Blank", rating=4, text="   ", likes_count=1, dislikes_count=0)
        SiteReview.objects.create(author_name="Empty", rating=5, text="", likes_count=0, dislikes_count=0)
        SiteReview.objects.create(author_name="Visible", rating=5, text="Отличный сервис", likes_count=3, dislikes_count=0)

        response = self.client.get(reverse("site_reviews"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["site_reviews_count"], 1)
        self.assertEqual(len(response.context["site_reviews"]), 1)
        self.assertEqual(response.context["site_reviews"][0].author_name, "Visible")
        self.assertContains(response, 'class="review-item"', count=1)
        self.assertNotContains(response, "Пока нет отзывов с текстом.")

    def test_site_reviews_page_shows_empty_state_without_text_reviews(self):
        SiteReview.objects.create(author_name="Blank", rating=4, text="  ", likes_count=1, dislikes_count=0)
        SiteReview.objects.create(author_name="Empty", rating=5, text="", likes_count=0, dislikes_count=0)

        response = self.client.get(reverse("site_reviews"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["site_reviews_count"], 0)
        self.assertContains(response, "Пока нет отзывов с текстом.")
        self.assertNotContains(response, 'class="review-item"')

    def test_site_review_demo_content_is_localized_in_az_and_en(self):
        review = SiteReview.objects.create(
            author_name="Наталья М.",
            rating=4,
            text="Хороший каталог, особенно полезны карта и быстрые фильтры по категориям.",
        )

        with override("az"):
            self.assertEqual(review.author_name_i18n, "Nataliya M.")
            self.assertEqual(review.text_i18n, "Yaxşı kataloqdur, xüsusilə xəritə və kateqoriyalar üzrə sürətli filtrlər faydalıdır.")

        with override("en"):
            self.assertEqual(review.author_name_i18n, "Natalia M.")
            self.assertEqual(review.text_i18n, "A good catalog, especially useful for the map and quick category filters.")

    def test_home_and_catalog_use_localized_strings_in_az_and_en(self):
        Place.objects.create(name="Test", name_ru="Тест", category="EDU", is_active=True)
        SiteReview.objects.create(
            author_name="Рамин А.",
            rating=5,
            text="Сайт помогает быстро находить новые кружки в Баку, интерфейс понятный.",
        )

        az_home = self.client.get("/az/", follow=True)
        self.assertEqual(az_home.status_code, 200)
        self.assertContains(az_home, "Valideynlərə sizi yaxınlıqda tapmağa kömək edin")
        self.assertContains(az_home, "Tam lent və reaksiyalar")
        self.assertContains(az_home, "Ramin A.")
        self.assertContains(az_home, "Sayt Bakıda yeni dərnəkləri tez tapmağa kömək edir, interfeys aydındır.")
        self.assertNotContains(az_home, "Приведите новых родителей через KidsMap")
        self.assertNotContains(az_home, "Полная лента и реакции")

        az_catalog = self.client.get("/az/catalog/", follow=True)
        self.assertEqual(az_catalog.status_code, 200)
        self.assertContains(az_catalog, "Dərnək seçin")
        self.assertContains(az_catalog, "Kateqoriya, rayon, metro, yaş və büdcə bir yerdə.")
        self.assertNotContains(az_catalog, "Подобрать кружок")
        self.assertNotContains(az_catalog, "Категория, район, метро, возраст и бюджет в одном месте.")

        en_home = self.client.get("/en/", follow=True)
        self.assertEqual(en_home.status_code, 200)
        self.assertContains(en_home, "Help parents find you nearby")
        self.assertContains(en_home, "Full feed and reactions")
        self.assertContains(en_home, "Ramin A.")
        self.assertContains(en_home, "The site helps you quickly find new clubs in Baku, and the interface is easy to understand.")
        self.assertNotContains(en_home, "Приведите новых родителей через KidsMap")
        self.assertNotContains(en_home, "Полная лента и реакции")

        ru_home = self.client.get("/ru/", follow=True)
        self.assertEqual(ru_home.status_code, 200)
        self.assertContains(ru_home, "Для владельцев детских мест")
        self.assertContains(ru_home, "Помогите родителям найти вас рядом")
        self.assertContains(ru_home, "Разместить место")
        self.assertNotContains(ru_home, "Valideynlərə sizi yaxınlıqda tapmağa kömək edin")
        self.assertNotContains(ru_home, "Məkan yerləşdir")

        az_catalog = self.client.get("/az/catalog/", follow=True)
        self.assertEqual(az_catalog.status_code, 200)
        self.assertContains(az_catalog, "kart tapıldı")
        self.assertNotContains(az_catalog, "Найдено")

        en_catalog = self.client.get("/en/catalog/", follow=True)
        self.assertEqual(en_catalog.status_code, 200)
        self.assertContains(en_catalog, "clubs found")
        self.assertNotContains(en_catalog, "Найдено")

    def test_site_review_reactions_update_counters(self):
        review = SiteReview.objects.create(author_name="Site User", rating=5, text="Люблю этот сайт")
        self.client.login(username="review_user", password="StrongPass123!!")

        response = self.client.post(
            reverse("vote_site_review", args=[review.id]),
            data={"value": "1", "next": reverse("site_reviews")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.likes_count, 1)
        self.assertEqual(review.dislikes_count, 0)
        self.assertTrue(SiteReviewReaction.objects.filter(review=review, value=1).exists())

    def test_site_review_reaction_requires_login_for_guest_ajax(self):
        review = SiteReview.objects.create(author_name="Site User", rating=5, text="Люблю этот сайт")

        response = self.client.post(
            reverse("vote_site_review", args=[review.id]),
            data={"value": "1", "next": reverse("site_reviews")},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 401)
        payload = json.loads(response.content)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["auth_required"])
        self.assertIn(reverse("account_login"), payload["redirect_url"])
        self.assertIn("message", payload)
        self.assertEqual(SiteReviewReaction.objects.filter(review=review).count(), 0)

    def test_place_like_requires_login_and_redirects_guest(self):
        response = self.client.post(
            reverse("toggle_place_like", args=[self.place.id]),
            data={"next": self.place.get_absolute_url()},
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        location = response["Location"]
        self.assertIn(reverse("account_login"), location)
        self.assertEqual(parse_qs(urlparse(location).query).get("next"), [self.place.get_absolute_url()])
        self.assertEqual(PlaceLike.objects.filter(place=self.place).count(), 0)

    def test_place_like_requires_login_for_guest_ajax(self):
        response = self.client.post(
            reverse("toggle_place_like", args=[self.place.id]),
            data={"next": self.place.get_absolute_url()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 401)
        payload = json.loads(response.content)
        self.assertFalse(payload["ok"])
        self.assertTrue(payload["auth_required"])
        self.assertIn(reverse("account_login"), payload["redirect_url"])
        self.assertEqual(PlaceLike.objects.filter(place=self.place).count(), 0)

    def test_place_like_ajax_updates_without_reload_for_authenticated_user(self):
        self.client.login(username="review_user", password="StrongPass123!!")

        response = self.client.post(
            reverse("toggle_place_like", args=[self.place.id]),
            data={"next": self.place.get_absolute_url()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["liked"])
        self.assertEqual(payload["likes_count"], 1)
        self.assertEqual(payload["analytics_event"]["name"], FunnelEvent.EVENT_FAVORITE_TOGGLE)
        self.assertEqual(payload["analytics_event"]["params"]["action"], "saved")
        self.assertEqual(PlaceLike.objects.filter(place=self.place, user=self.user).count(), 1)

        response = self.client.post(
            reverse("toggle_place_like", args=[self.place.id]),
            data={"next": self.place.get_absolute_url()},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = json.loads(response.content)
        self.assertFalse(payload["liked"])
        self.assertEqual(payload["likes_count"], 0)
        self.assertEqual(payload["analytics_event"]["params"]["action"], "removed")

    def test_add_place_review_requires_login_and_redirects_guest(self):
        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={
                "rating": "5",
                "text": "Хороший кружок",
                "author_name": "Guest",
                "next": f"{self.place.get_absolute_url()}#reviews",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        location = response["Location"]
        self.assertIn(reverse("account_login"), location)
        self.assertEqual(parse_qs(urlparse(location).query).get("next"), [f"{self.place.get_absolute_url()}#reviews"])
        self.assertEqual(PlaceReview.objects.filter(place=self.place).count(), 0)

    def test_az_guest_review_block_uses_azerbaijani_text(self):
        response = self.client.get(f"/az{self.place.get_absolute_url()}", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rəy yazmaq üçün daxil olun və ya qeydiyyatdan keçin.")
        self.assertNotContains(response, "Чтобы оставить отзыв, войдите или зарегистрируйтесь.")

class EventsLandingTests(TestCase):
    def setUp(self):
        self.place = create_quality_place(
            name="Event Place",
            name_ru="Площадка для событий",
            district="Ясамал",
        )
        now = timezone.now()
        self.upcoming_event = Event.objects.create(
            related_place=self.place,
            name="Weekend Workshop",
            name_ru="Мастер-класс выходного дня",
            description_ru="Подробное описание открытого семейного мастер-класса для детей и родителей.",
            category="ART",
            start_datetime=now + timedelta(days=2),
            end_datetime=now + timedelta(days=2, hours=2),
            status=Event.STATUS_PUBLISHED,
            address="Ясамал, Баку",
            price_text="25 AZN",
        )
        Event.objects.create(
            name="Past Event",
            name_ru="Прошедшее событие",
            description_ru="Это событие уже завершилось и не должно быть на афише.",
            category="ART",
            start_datetime=now - timedelta(days=3),
            end_datetime=now - timedelta(days=2),
            status=Event.STATUS_PUBLISHED,
            address="Баку",
        )

    def test_events_landing_shows_only_active_events(self):
        with override("ru"):
            response = self.client.get(reverse("events_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["results_total"], 1)
        self.assertContains(response, "Мастер-класс выходного дня")
        self.assertNotContains(response, "Прошедшее событие")

    def test_events_landing_does_not_render_filter_controls(self):
        response = self.client.get(reverse("events_landing"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="q"')
        self.assertNotContains(response, 'name="category"')
        self.assertNotContains(response, 'name="district"')
        self.assertNotContains(response, 'name="age_from"')
        self.assertNotContains(response, 'name="age_to"')

    def test_home_upcoming_events_link_points_to_events_landing(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, f'href="{reverse("events_landing")}"')

    def test_home_shows_only_four_upcoming_events(self):
        now = timezone.now()
        for idx in range(5):
            Event.objects.create(
                name=f"Extra Event {idx}",
                name_ru=f"Дополнительное событие {idx}",
                description_ru="Дополнительное событие для проверки лимита на главной.",
                category="ART",
                start_datetime=now + timedelta(days=3 + idx),
                end_datetime=now + timedelta(days=3 + idx, hours=2),
                status=Event.STATUS_PUBLISHED,
                address="Баку",
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["upcoming_events"]), 4)

    def test_event_address_is_localized_for_az_public_pages(self):
        self.upcoming_event.address = "ул. Школьная 9, Баку"
        self.upcoming_event.save(update_fields=["address", "updated_at"])

        with override("az"):
            events_response = self.client.get(reverse("events_landing"))
            detail_response = self.client.get(self.upcoming_event.get_absolute_url())

        self.assertContains(events_response, "küç. Məktəb 9, Bakı")
        self.assertContains(detail_response, "küç. Məktəb 9, Bakı")

    def test_event_address_is_localized_for_en_public_pages(self):
        self.upcoming_event.address = "пр. Гусейна Джавида 18, Баку"
        self.upcoming_event.save(update_fields=["address", "updated_at"])

        with override("en"):
            response = self.client.get(reverse("events_landing"))

        self.assertContains(response, "Ave. Huseyn Javid 18, Baku")
