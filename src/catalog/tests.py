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
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from django.utils import timezone
from django.utils.translation import override

from catalog.forms import OwnerPlaceCreateForm
from catalog.interfaces.geocoding import GeocodingPoint
from catalog.models import (
    CatalogContentSettings,
    FunnelEvent,
    OwnerTeamInvitation,
    OwnerTeamMembership,
    Place,
    PlaceChangeAudit,
    PlaceLike,
    PlacePhoto,
    PlaceOwnershipRequest,
    PlaceOwnershipRequestAudit,
    PlaceReview,
    PlaceReviewReaction,
    SiteGalleryImage,
    SiteReview,
    SiteReviewReaction,
    SiteVisit,
    UserEmailVerification,
    UserProfile,
)
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.content_quality import public_place_queryset, public_review_queryset, review_quality_check
from catalog.services.tracking import GA4_CONVERSION_EVENT_NAMES, TRACKED_EVENT_NAMES
from config.views import serve_media_file


User = get_user_model()


class StubGeocodingRepository:
    def __init__(self, *, point: GeocodingPoint | None = None, configured: bool = True):
        self.point = point
        self.configured = configured
        self.queries: list[str] = []

    def is_configured(self) -> bool:
        return self.configured

    def geocode(self, *, query: str, language: str = "ru", region: str = "az") -> GeocodingPoint | None:
        self.queries.append(query)
        return self.point


def create_quality_place(**overrides):
    long_description = (
        "Uşaqlar üçün diqqətlə hazırlanmış dərslər, yaşa uyğun qruplar, "
        "müntəzəm cədvəl və valideynlərlə açıq əlaqə təqdim edən mərkəz."
    )
    defaults = {
        "name": "Quality Kids Club",
        "name_az": "Keyfiyyətli Uşaq Dərnəyi",
        "description_az": long_description,
        "category": "EDU",
        "age_from": 6,
        "age_to": 12,
        "district": "Bakı",
        "address": "Bakı şəhəri, Nizami küçəsi 10",
        "phone1": "+994501112233",
        "schedule": "Bazar ertəsi, çərşənbə və cümə 15:00-17:00",
        "price_from": 80,
        "price_to": 80,
        "is_active": True,
        "status": Place.STATUS_PUBLISHED,
    }
    defaults.update(overrides)
    return Place.objects.create(**defaults)


class ContentModerationPublicVisibilityTests(TestCase):
    def test_only_published_quality_places_are_public(self):
        public_place = create_quality_place()
        create_quality_place(name="Draft Club", status=Place.STATUS_DRAFT)
        create_quality_place(name="Pending Club", status=Place.STATUS_PENDING)
        create_quality_place(name="Rejected Club", status=Place.STATUS_REJECTED)

        self.assertEqual(list(public_place_queryset(Place.objects.all())), [public_place])

    def test_place_with_test_content_is_not_public(self):
        create_quality_place(name="test club")

        self.assertEqual(public_place_queryset(Place.objects.all()).count(), 0)

    def test_review_public_queryset_requires_approved_status_and_quality_text(self):
        place = create_quality_place()
        approved = PlaceReview.objects.create(
            place=place,
            rating=5,
            text="Bu dərnək barədə real və faydalı təcrübə paylaşılır.",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )
        PlaceReview.objects.create(
            place=place,
            rating=5,
            text="Bu rəy moderasiyadan keçməyib və görünməməlidir.",
            status=PlaceReview.STATUS_PENDING,
            is_approved=False,
        )
        PlaceReview.objects.create(
            place=place,
            rating=5,
            text="test aaa lorem",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )

        self.assertEqual(list(public_review_queryset(PlaceReview.objects.all())), [approved])

    def test_short_or_test_review_cannot_pass_quality_check(self):
        place = create_quality_place()
        review = PlaceReview.objects.create(
            place=place,
            rating=5,
            text="test",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )

        self.assertIn("text_too_short", review_quality_check(review).errors)
        self.assertIn("test_content", review_quality_check(review).errors)


class TestPublicPagesSmoke(TestCase):
    def test_home_page_opens_with_i18n_redirect(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="az">', html=False)

    def test_legacy_az_urls_redirect_to_default_language_without_prefix(self):
        response = self.client.get("/az/catalog/", {"category": "EDU"})

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
            "/for-business/": "Uşaq dərnəyinizi KidsMap-də yerləşdirin",
            "/ru/for-business/": "Разместите ваш детский кружок на KidsMap",
            "/en/for-business/": "List your kids club on KidsMap",
            "/privacy/": "Məxfilik siyasəti",
            "/ru/terms/": "Условия использования",
            "/en/review-rules/": "Review Rules",
        }
        for path, text in checks.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)

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
        self.assertContains(response, "Username or email")
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
        self.assertContains(response, "Create your KidsMap account.")
        self.assertContains(response, "Register")
        self.assertContains(response, "Fields marked with an asterisk are required.")
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
        self.assertIn("Bakıda uşaqlar üçün dərnəklər və məşğələlər kataloqu", content)
        self.assertNotIn("Каталог кружков и секций для детей в Баку", content)
        self.assertNotIn("Найдено %(total)s карточек", content)

    def test_en_catalog_page_localizes_catalog_seo_strings(self):
        response = self.client.get("/en/catalog/")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn('<html lang="en">', content)
        self.assertIn("Catalog of clubs and activities for kids in Baku", content)
        self.assertNotIn("Каталог кружков и секций для детей в Баку", content)
        self.assertNotIn("Найдено %(total)s карточек", content)

    def test_en_home_title_is_localized(self):
        response = self.client.get("/en/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Clubs and activities for kids in Baku | KidsMap</title>", html=True)

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
        self.assertContains(response, "Bu bölmə nə haqqındadır")
        self.assertContains(response, "Sürətli axtarış")
        self.assertContains(response, "Rəylər və like-lar")
        self.assertNotContains(response, "О чём этот раздел")

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

    def test_en_home_page_translates_leisure_category(self):
        response = self.client.get("/en/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leisure")
        self.assertNotContains(response, "Досуг")

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
        Place.objects.create(
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

    def test_home_page_limits_recommended_places_to_three_cards(self):
        for idx in range(4):
            Place.objects.create(
                name=f"Popular Place {idx + 1}",
                name_ru=f"Популярный кружок {idx + 1}",
                category="EDU",
                is_active=True,
                likes_count=10 - idx,
            )

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["popular_places"]), 3)

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    def test_home_page_prefers_google_maps_when_key_is_configured(self):
        Place.objects.create(
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

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_home_page_includes_google_analytics_tag_when_configured(self):
        response = self.client.get("/", follow=True)

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

    def test_home_page_shows_only_text_site_reviews_in_teaser(self):
        SiteReview.objects.create(author_name="No Text", rating=4, text="")
        SiteReview.objects.create(author_name="With Text", rating=5, text="Очень полезный сервис для родителей.")

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["site_reviews_teaser"]), 1)
        self.assertContains(response, "Очень полезный сервис для родителей.")
        self.assertNotContains(response, "Пользователь оставил оценку без текстового комментария.")

    def test_login_page_is_marked_noindex(self):
        response = self.client.get("/ru/auth/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex,follow" />', html=False)
        self.assertContains(response, '<meta name="googlebot" content="noindex,follow" />', html=False)

    def test_filtered_catalog_page_uses_noindex_and_itemlist_schema(self):
        Place.objects.create(
            name="Seo Place",
            name_ru="SEO кружок",
            category="EDU",
            is_active=True,
            district="Ясамал",
        )

        response = self.client.get("/ru/catalog/", {"category": "EDU"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<meta name="robots" content="noindex,follow" />', html=False)
        self.assertContains(response, "<title>Образование для детей в Баку | KidsMap</title>", html=False)
        self.assertContains(response, '"@type": "ItemList"', html=False)
        self.assertContains(response, '"@type": "BreadcrumbList"', html=False)

    def test_place_detail_page_includes_breadcrumb_and_aggregate_rating_schema(self):
        place = Place.objects.create(
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
        self.assertContains(response, "<title>SEO кружок — Образование для детей в Ясамал, Баку | KidsMap</title>", html=False)

    def test_robots_txt_disallows_private_sections(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /auth/")
        self.assertContains(response, "Disallow: /account/")
        self.assertContains(response, "Disallow: /admin/")
        self.assertContains(response, "Disallow: /ru/auth/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_home_map_popup_uses_main_photo_preview(self):
        place = Place.objects.create(
            name="Home Map Place",
            name_ru="Кружок для карты на главной",
            category="EDU",
            is_active=True,
            lat=40.4093,
            lng=49.8671,
            photo=SimpleUploadedFile("popup-main.png", b"main-image", content_type="image/png"),
            cover_photo=SimpleUploadedFile("popup-cover.png", b"cover-image", content_type="image/png"),
        )

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["map_places"][0]["image_url"], place.photo.url)
        self.assertContains(response, "home-map-data")
        self.assertContains(response, place.photo.url)

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
        self.assertContains(response, "img/ui/user.png")
        self.assertContains(response, "lang-flag-icon")
        self.assertContains(response, "img/flags/ru.png")
        self.assertContains(response, "img/flags/az.png")
        self.assertContains(response, "img/flags/en.png")
        self.assertContains(response, "lang-trigger-icononly")


class TestCatalogContentSettingsWiring(TestCase):
    def test_home_page_uses_catalog_settings_districts(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Тестовый район"]
        settings_obj.save(update_fields=["districts_json", "updated_at"])

        response = self.client.get("/", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'option value="Тестовый район"', html=False)
        self.assertEqual(response.context["home_districts"], ["Тестовый район"])

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

        self.assertGreaterEqual(len(files), 2)
        self.assertIn("main-photo", files[0].name)
        self.assertIn("cover-photo", files[1].name)

    def test_catalog_filter_values_are_sorted_alphabetically(self):
        settings_obj = CatalogContentSettings.get_solo()
        settings_obj.districts_json = ["Забрат", "Ахмедлы", "Бинагади"]
        settings_obj.metro_stations_json = ["Нариман Нариманов", "20 Января", "Азадлыг проспекти"]
        settings_obj.save(update_fields=["districts_json", "metro_stations_json", "updated_at"])

        response = self.client.get(reverse("place_list"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["district_options"], ["Ахмедлы", "Бинагади", "Забрат"])
        self.assertEqual(
            response.context["metro_options"],
            ["20 Января", "Азадлыг проспекти", "Нариман Нариманов"],
        )


class TestPlaceGeocodingService(TestCase):
    def test_service_updates_coordinates_from_repository_result(self):
        place = Place.objects.create(
            name="Geo Service Place",
            name_ru="Геосервис кружок",
            category="EDU",
            address="ул. Низами, 15",
            district="Ясамал",
            metro="Ичеришехер",
        )
        repository = StubGeocodingRepository(
            point=GeocodingPoint(lat=40.4093, lng=49.8671, formatted_address="Baku"),
        )
        service = PlaceGeocodingService(geocoding_repository=repository)

        result = service.geocode_place(place=place, overwrite=True)

        self.assertTrue(result.updated)
        place.refresh_from_db()
        self.assertEqual(place.lat, 40.4093)
        self.assertEqual(place.lng, 49.8671)
        self.assertEqual(len(repository.queries), 1)
        self.assertIn("ул. Низами, 15", repository.queries[0])
        self.assertIn("Ясамал", repository.queries[0])
        self.assertIn("метро Ичеришехер", repository.queries[0])
        self.assertIn("Баку", repository.queries[0])


class TestAdminOwnershipModerationUX(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="superadmin_adminux",
            email="superadmin-adminux@example.com",
            password="StrongPass123!!",
        )
        self.owner_user = User.objects.create_user(
            username="owner_adminux",
            email="owner-adminux@example.com",
            password="StrongPass123!!",
        )
        self.second_owner_user = User.objects.create_user(
            username="owner_adminux_second",
            email="owner-adminux-second@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(user=self.owner_user, role=UserProfile.ROLE_OWNER)
        UserProfile.objects.create(user=self.second_owner_user, role=UserProfile.ROLE_OWNER)
        self.place = Place.objects.create(
            name="Admin UX Place",
            name_ru="Кружок для модерации",
            category="EDU",
            is_active=True,
        )
        self.request_item = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            note="Прошу одобрить владение",
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )
        self.client.login(username="superadmin_adminux", password="StrongPass123!!")

    def _admin_place_change_payload(self, **overrides):
        data = {
            "name": self.place.name,
            "name_ru": self.place.name_ru,
            "name_az": self.place.name_az,
            "name_en": self.place.name_en,
            "description_ru": self.place.description_ru,
            "description_az": self.place.description_az,
            "description_en": self.place.description_en,
            "category": self.place.category,
            "subcategory": self.place.subcategory,
            "is_temporary": "on" if self.place.is_temporary else "",
            "temporary_start": "",
            "temporary_end": "",
            "is_active": "on" if self.place.is_active else "",
            "is_verified": "on" if self.place.is_verified else "",
            "owner": str(self.place.owner_id or ""),
            "likes_count": str(self.place.likes_count or 0),
            "age_from": "" if self.place.age_from is None else str(self.place.age_from),
            "age_to": "" if self.place.age_to is None else str(self.place.age_to),
            "price_from": "" if self.place.price_from is None else str(self.place.price_from),
            "price_to": "" if self.place.price_to is None else str(self.place.price_to),
            "price_per_lesson": "" if self.place.price_per_lesson is None else str(self.place.price_per_lesson),
            "price_per_month": "" if self.place.price_per_month is None else str(self.place.price_per_month),
            "price_per_8_lessons": "" if self.place.price_per_8_lessons is None else str(self.place.price_per_8_lessons),
            "lesson_duration_minutes": (
                "" if self.place.lesson_duration_minutes is None else str(self.place.lesson_duration_minutes)
            ),
            "district": self.place.district,
            "metro": self.place.metro,
            "address": self.place.address,
            "lat": "" if self.place.lat is None else str(self.place.lat),
            "lng": "" if self.place.lng is None else str(self.place.lng),
            "phone1": self.place.phone1,
            "instagram": self.place.instagram,
            "website": self.place.website,
            "schedule": self.place.schedule,
            "extra_conditions": self.place.extra_conditions,
            "additional_info": self.place.additional_info,
            "gallery-TOTAL_FORMS": "0",
            "gallery-INITIAL_FORMS": "0",
            "gallery-MIN_NUM_FORMS": "0",
            "gallery-MAX_NUM_FORMS": "1000",
            "reviews-TOTAL_FORMS": "0",
            "reviews-INITIAL_FORMS": "0",
            "reviews-MIN_NUM_FORMS": "0",
            "reviews-MAX_NUM_FORMS": "1000",
            "change_audits-TOTAL_FORMS": "0",
            "change_audits-INITIAL_FORMS": "0",
            "change_audits-MIN_NUM_FORMS": "0",
            "change_audits-MAX_NUM_FORMS": "1000",
        }
        data.update(overrides)
        return data

    def test_admin_index_shows_pending_badge_and_hides_internal_models(self):
        response = self.client.get("/ru/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "На рассмотрении: 1")
        self.assertContains(response, "Заявки на владение кружком")
        self.assertContains(response, "Пользователи сайта")
        self.assertContains(response, "Сотрудники админки")
        self.assertContains(response, "Отзывы о сайте")
        self.assertNotContains(response, "Профили пользователей")
        self.assertNotContains(response, "Группы")
        self.assertNotContains(response, "Аудит заявок на владение")

    def test_admin_language_switcher_uses_language_specific_next_urls(self):
        response = self.client.get("/ru/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="language" value="ru"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/ru/admin/"', html=False)
        self.assertContains(response, 'name="language" value="az"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/admin/"', html=False)
        self.assertContains(response, 'name="language" value="en"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/en/admin/"', html=False)

    @override_settings(
        GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123",
        GOOGLE_ANALYTICS_PROPERTY_ID="123456789",
    )
    @patch("catalog.services.admin_analytics.build_google_analytics_context")
    def test_admin_site_analytics_page_shows_ga4_block(self, ga4_context_mock):
        ga4_context_mock.return_value = {
            "enabled": True,
            "connected": True,
            "measurement_id": "G-TEST123",
            "property_id": "123456789",
            "credentials_path": "/app/.secrets/ga4.json",
            "error": "",
            "period_stats": {
                "day": {"active_users": 4, "sessions": 5, "page_views": 9},
                "week": {"active_users": 14, "sessions": 18, "page_views": 42},
                "month": {"active_users": 40, "sessions": 57, "page_views": 130},
                "year": {"active_users": 180, "sessions": 260, "page_views": 920},
            },
            "daily_chart": {
                "labels": ["01.04", "02.04"],
                "active_users": [3, 4],
                "page_views": [7, 9],
            },
            "top_pages": [{"page_path": "/ru/catalog/", "page_views": 55}],
            "top_events": [{"event_name": "place_open", "event_count": 17}],
        }

        response = self.client.get(reverse("admin:catalog_siteanalytics_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Google Analytics 4")
        self.assertContains(response, "G-TEST123")
        self.assertContains(response, "123456789")
        self.assertContains(response, "/ru/catalog/")
        self.assertContains(response, "place_open")

    def test_admin_can_approve_request_with_direct_button_url(self):
        self.place.is_active = False
        self.place.save(update_fields=["is_active"])

        approve_url = reverse("admin:catalog_placeownershiprequest_approve", args=[self.request_item.id])
        confirm_response = self.client.get(approve_url)
        self.assertEqual(confirm_response.status_code, 200)

        response = self.client.post(
            approve_url,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.request_item.refresh_from_db()
        self.place.refresh_from_db()
        self.assertEqual(self.request_item.status, PlaceOwnershipRequest.STATUS_APPROVED)
        self.assertEqual(self.place.owner, self.owner_user)
        self.assertTrue(self.place.is_active)

    def test_admin_can_reject_request_with_direct_button_url(self):
        second_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.second_owner_user,
            note="Повторная заявка",
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )

        reject_url = reverse("admin:catalog_placeownershiprequest_reject", args=[second_request.id])
        confirm_response = self.client.get(reject_url)
        self.assertEqual(confirm_response.status_code, 200)

        response = self.client.post(
            reject_url,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        second_request.refresh_from_db()
        self.assertEqual(second_request.status, PlaceOwnershipRequest.STATUS_REJECTED)

    def test_place_admin_shows_coordinates_and_map_readiness_statuses(self):
        self.place.lat = 40.4093
        self.place.lng = 49.8671
        self.place.save(update_fields=["lat", "lng", "updated_at"])
        Place.objects.create(
            name="Place Without Coordinates",
            name_ru="Карточка без координат",
            category="EDU",
            is_active=True,
        )

        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertTrue("Есть координаты" in content or "Koordinatlar var" in content)
        self.assertTrue("Нужны координаты" in content or "Koordinatlar tələb olunur" in content)
        self.assertTrue("Готово для карты" in content or "Xəritə üçün hazırdır" in content)
        self.assertTrue("Не готово для карты" in content or "Xəritə üçün hazır deyil" in content)
        self.assertContains(response, "Локация")
        self.assertContains(response, "Публикация")
        self.assertContains(response, "Вовлеченность")
        self.assertContains(response, "admin/css/kidsmap_admin.css")

    def test_place_admin_changelist_shows_bulk_bar_quick_filters_and_row_actions(self):
        deleted_place = Place.objects.create(
            name="Deleted place",
            name_ru="Удалённая карточка",
            category="EDU",
            slug="deleted-place",
            is_active=True,
        )
        deleted_place.soft_delete(deleted_by=self.superuser)

        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-bulk-bar")
        self.assertContains(response, "Выберите карточки, чтобы массовые действия стали доступны.")
        self.assertContains(response, 'data-action="move_selected_to_deleted"', html=False)
        self.assertContains(response, 'data-action="restore_selected"', html=False)
        self.assertContains(response, "Выбрать все на странице")
        self.assertContains(response, "Снять выделение")
        self.assertContains(response, "Опубликованы")
        self.assertContains(response, "В удалённых")
        self.assertContains(response, "Без координат")
        self.assertContains(response, reverse("admin:catalog_place_delete", args=[self.place.id]))
        self.assertContains(response, reverse("admin:catalog_place_restore", args=[deleted_place.id]))
        self.assertContains(response, "km-place-row-actions")
        self.assertContains(response, "В удалённые")
        self.assertContains(response, "Восстановить")

    def test_place_admin_changelist_uses_compact_search_panel(self):
        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-search-panel")
        self.assertContains(response, "Поиск по карточкам")
        self.assertContains(response, "Найти")
        self.assertContains(response, "карточка")
        self.assertNotContains(response, 'id="toolbar"', html=False)

    def test_place_admin_change_form_shows_coordinate_refresh_button(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сохранить и рассчитать координаты")
        self.assertContains(response, "_refresh_coordinates_from_address")

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_place_admin_can_refresh_coordinates_from_address(self, geocode_mock):
        self.place.address = "ул. Низами, 15"
        self.place.district = "Ясамал"
        self.place.metro = "Ичеришехер"
        self.place.save(update_fields=["address", "district", "metro", "updated_at"])
        geocode_mock.return_value = GeocodingPoint(lat=40.401234, lng=49.812345, formatted_address="Baku")
        payload = self._admin_place_change_payload(
            address="ул. Низами, 15",
            district="Ясамал",
            metro="Ичеришехер",
        )
        payload["_refresh_coordinates_from_address"] = "1"

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data=payload,
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.lat, 40.401234)
        self.assertEqual(self.place.lng, 49.812345)
        self.assertContains(response, "Изменения сохранены. Координаты обновлены: 40.401234, 49.812345.")
        geocode_mock.assert_called_once()
        self.assertIn("ул. Низами, 15", geocode_mock.call_args.kwargs["query"])
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.place,
                changed_by=self.superuser,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lat",
            ).exists()
        )

    def test_place_admin_delete_view_confirms_move_to_deleted(self):
        delete_url = reverse("admin:catalog_place_delete", args=[self.place.id])

        response = self.client.get(delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "будет перемещен в раздел удаленных")
        self.assertContains(response, "Переместить в удаленные")

    def test_place_admin_single_delete_moves_place_to_deleted(self):
        delete_url = reverse("admin:catalog_place_delete", args=[self.place.id])

        response = self.client.post(delete_url, data={"post": "yes"}, follow=True)

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertTrue(Place.objects.filter(pk=self.place.pk).exists())
        self.assertIsNotNone(self.place.deleted_at)
        self.assertFalse(self.place.is_active)
        self.assertEqual(self.place.deleted_by, self.superuser)
        self.assertContains(response, "перемещена в удалённые")
        public_response = self.client.get(self.place.get_absolute_url(), follow=True)
        self.assertEqual(public_response.status_code, 404)

    def test_place_admin_restore_view_confirms_and_restores_place(self):
        self.place.soft_delete(deleted_by=self.superuser)
        restore_url = reverse("admin:catalog_place_restore", args=[self.place.id])

        response = self.client.get(restore_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "будет восстановлена из раздела удалённых")
        self.assertContains(response, "Восстановить карточку")

        post_response = self.client.post(restore_url, follow=True)

        self.assertEqual(post_response.status_code, 200)
        self.place.refresh_from_db()
        self.assertIsNone(self.place.deleted_at)
        self.assertFalse(self.place.is_active)
        self.assertContains(post_response, "восстановлена из удалённых и оставлена неактивной")

    def test_place_admin_bulk_move_to_deleted_and_restore(self):
        confirm_response = self.client.post(
            reverse("admin:catalog_place_changelist"),
            data={
                "action": "move_selected_to_deleted",
                "_selected_action": [str(self.place.id)],
                "index": 0,
            },
        )

        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, "будут перемещены в раздел удаленных")

        response = self.client.post(
            reverse("admin:catalog_place_changelist"),
            data={
                "action": "move_selected_to_deleted",
                "_selected_action": [str(self.place.id)],
                "post": "yes",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertIsNotNone(self.place.deleted_at)
        self.assertContains(response, "В удалённые перемещена 1 карточка")

        deleted_list_response = self.client.get(
            reverse("admin:catalog_place_changelist"),
            data={"deleted_state": "deleted"},
        )
        self.assertContains(deleted_list_response, "Кружок для модерации")
        self.assertContains(deleted_list_response, "В удаленных")

        restore_response = self.client.post(
            reverse("admin:catalog_place_changelist"),
            data={
                "action": "restore_selected",
                "_selected_action": [str(self.place.id)],
                "index": 0,
            },
            follow=True,
        )

        self.assertEqual(restore_response.status_code, 200)
        self.place.refresh_from_db()
        self.assertIsNone(self.place.deleted_at)
        self.assertFalse(self.place.is_active)
        self.assertContains(restore_response, "Из удалённых восстановлена 1 карточка")

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_place_admin_bulk_action_regeocodes_selected_places(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.5001, lng=49.9001, formatted_address="Baku")
        self.place.address = "Проспект 10"
        self.place.district = "Ясамал"
        self.place.lat = 40.1001
        self.place.lng = 49.1001
        self.place.save(update_fields=["address", "district", "lat", "lng", "updated_at"])

        response = self.client.post(
            reverse("admin:catalog_place_changelist"),
            data={
                "action": "refresh_coordinates",
                "_selected_action": [str(self.place.id)],
                "index": 0,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.lat, 40.5001)
        self.assertEqual(self.place.lng, 49.9001)
        response_content = response.content.decode("utf-8")
        self.assertTrue(
            "Повторное геокодирование завершено: обновлено 1" in response_content
            or "Təkrar geokodlaşdırma tamamlandi: yeniləndi 1" in response_content
        )
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.place,
                changed_by=self.superuser,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lat",
            ).exists()
        )

    def test_place_change_audit_changelist_uses_human_readable_labels_and_filters(self):
        PlaceChangeAudit.objects.create(
            place=self.place,
            changed_by=self.superuser,
            source=PlaceChangeAudit.SOURCE_ADMIN,
            field_name="deleted_at",
            old_value="",
            new_value="2026-04-15 09:00:00",
        )
        PlaceChangeAudit.objects.create(
            place=self.place,
            changed_by=self.owner_user,
            source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
            field_name="phone1",
            old_value="+994 55 111 11 11",
            new_value="+994 55 222 22 22",
        )

        response = self.client.get(reverse("admin:catalog_placechangeaudit_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "История изменений карточек")
        self.assertContains(response, "Карточка перемещена в удалённые")
        self.assertContains(response, "Контакты карточки обновлены")
        self.assertContains(response, "Удаление")
        self.assertContains(response, "Telefon")
        self.assertContains(response, "km-audit-actions")
        self.assertContains(response, "km-audit-action")
        self.assertContains(response, "km-audit-place-link")
        self.assertContains(response, reverse("admin:catalog_place_change", args=[self.place.id]))
        self.assertContains(response, self.place.get_absolute_url())

        filtered_response = self.client.get(
            reverse("admin:catalog_placechangeaudit_changelist"),
            data={"change_kind": "delete"},
        )
        self.assertEqual(filtered_response.status_code, 200)
        self.assertContains(filtered_response, "Карточка перемещена в удалённые")
        self.assertNotContains(filtered_response, "Телефон")

    def test_place_review_admin_changelist_shows_preview_status_filters_and_row_actions(self):
        published_review = PlaceReview.objects.create(
            place=self.place,
            author_name="Мария",
            rating=5,
            text="Очень подробный и полезный отзыв о кружке для проверки админского списка.",
            is_approved=True,
        )
        suspicious_review = PlaceReview.objects.create(
            place=self.place,
            author_name="",
            is_anonymous=True,
            rating=1,
            text="",
            contains_profanity=True,
            is_approved=False,
            dislikes_count=3,
        )

        response = self.client.get(reverse("admin:catalog_placereview_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-bulk-bar")
        self.assertContains(response, "Модерация отзывов по кружкам")
        self.assertContains(response, "Только оценка без комментария")
        self.assertContains(response, "Есть скрытая лексика")
        self.assertContains(response, "Требуют проверки")
        self.assertContains(response, "Опубликованы")
        self.assertContains(response, "Скрытые")
        self.assertContains(response, 'data-action="approve_selected"', html=False)
        self.assertContains(response, 'data-action="hide_selected"', html=False)
        self.assertContains(response, 'data-action="reject_selected"', html=False)
        self.assertContains(response, 'data-action="delete_selected"', html=False)
        self.assertContains(response, reverse("admin:catalog_placereview_change", args=[published_review.id]))
        self.assertContains(response, reverse("admin:catalog_placereview_approve", args=[suspicious_review.id]))
        self.assertContains(response, reverse("admin:catalog_placereview_hide", args=[published_review.id]))
        self.assertContains(response, reverse("admin:catalog_place_change", args=[self.place.id]))

    def test_place_review_admin_bulk_hide_and_approve_actions(self):
        review = PlaceReview.objects.create(
            place=self.place,
            author_name="Ольга",
            rating=4,
            text="Полезный отзыв",
            is_approved=True,
        )

        hide_response = self.client.post(
            reverse("admin:catalog_placereview_changelist"),
            data={"action": "hide_selected", "_selected_action": [str(review.id)], "index": 0},
            follow=True,
        )
        self.assertEqual(hide_response.status_code, 200)
        review.refresh_from_db()
        self.assertFalse(review.is_approved)

        approve_response = self.client.post(
            reverse("admin:catalog_placereview_changelist"),
            data={"action": "approve_selected", "_selected_action": [str(review.id)], "index": 0},
            follow=True,
        )
        self.assertEqual(approve_response.status_code, 200)
        review.refresh_from_db()
        self.assertTrue(review.is_approved)

    def test_place_review_admin_moderation_views_update_visibility(self):
        review = PlaceReview.objects.create(
            place=self.place,
            author_name="Ирина",
            rating=2,
            text="Нужно проверить",
            is_approved=False,
        )

        approve_get = self.client.get(reverse("admin:catalog_placereview_approve", args=[review.id]))
        self.assertEqual(approve_get.status_code, 200)
        self.assertContains(approve_get, "Опубликовать отзыв")

        approve_post = self.client.post(
            reverse("admin:catalog_placereview_approve", args=[review.id]),
            follow=True,
        )
        self.assertEqual(approve_post.status_code, 200)
        review.refresh_from_db()
        self.assertTrue(review.is_approved)

        reject_post = self.client.post(
            reverse("admin:catalog_placereview_reject", args=[review.id]),
            follow=True,
        )
        self.assertEqual(reject_post.status_code, 200)
        review.refresh_from_db()
        self.assertFalse(review.is_approved)

    def test_place_review_admin_change_form_shows_full_text_panel(self):
        review = PlaceReview.objects.create(
            place=self.place,
            author_name="Карина",
            rating=5,
            text="Полный текст отзыва для детального просмотра в админке.",
            is_approved=True,
        )

        response = self.client.get(reverse("admin:catalog_placereview_change", args=[review.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Полный текст отзыва")
        self.assertContains(response, "К карточке кружка")
        self.assertContains(response, review.text)

    def test_userprofile_changelist_works_without_500(self):
        response = self.client.get("/ru/admin/catalog/userprofile/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Профили пользователей")

    def test_user_change_form_has_no_groups_block(self):
        response = self.client.get(reverse("admin:auth_user_change", args=[self.owner_user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="groups"')
        self.assertNotContains(response, "id_groups")

    def test_site_users_section_shows_only_non_staff_users(self):
        staff_user = User.objects.create_user(
            username="staff_adminux",
            email="staff-adminux@example.com",
            password="StrongPass123!!",
            is_staff=True,
        )

        response = self.client.get(reverse("admin:catalog_siteregistereduser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[self.owner_user.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[self.superuser.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_siteregistereduser_change", args=[staff_user.id]),
        )

    def test_site_users_changelist_shows_profile_details(self):
        self.owner_user.first_name = "Али"
        self.owner_user.last_name = "Керимов"
        self.owner_user.email = "ali.kerimov@example.com"
        self.owner_user.save(update_fields=["first_name", "last_name", "email"])
        profile = self.owner_user.profile
        profile.phone = "+994 50 123 45 67"
        profile.save(update_fields=["phone"])

        response = self.client.get(reverse("admin:catalog_siteregistereduser_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner_adminux")
        self.assertContains(response, "ali.kerimov@example.com")
        self.assertContains(response, "Али Керимов")
        self.assertEqual(response.content.decode("utf-8").count("+994 50 123 45 67"), 1)

    def test_staff_section_shows_only_staff_and_superusers(self):
        staff_user = User.objects.create_user(
            username="staff_adminux_2",
            email="staff-adminux-2@example.com",
            password="StrongPass123!!",
            is_staff=True,
        )

        response = self.client.get(reverse("admin:catalog_staffaccessuser_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[self.superuser.id]),
        )
        self.assertContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[staff_user.id]),
        )
        self.assertNotContains(
            response,
            reverse("admin:catalog_staffaccessuser_change", args=[self.owner_user.id]),
        )


class TestTrackingController(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Test Place",
            name_ru="Тестовая площадка",
            category="EDU",
            is_active=True,
        )

    def test_track_event_rejects_invalid_json(self):
        response = self.client.post(
            reverse("track_event"),
            data="{invalid",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"ok": False, "error": "invalid_payload"})

    def test_track_event_saves_supported_cta_event(self):
        payload = {
            "event_type": FunnelEvent.EVENT_CTA_CALL,
            "place_id": self.place.id,
            "source": "catalog-list",
            "path": "/ru/catalog/",
        }
        response = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(FunnelEvent.objects.count(), 1)

        event = FunnelEvent.objects.first()
        self.assertEqual(event.event_type, FunnelEvent.EVENT_CTA_CALL)
        self.assertEqual(event.place_id, self.place.id)
        self.assertEqual(event.path, "/ru/catalog/")
        self.assertEqual(event.event_meta.get("source"), "catalog-list")

    def test_track_event_saves_claim_place_start_event(self):
        payload = {
            "event_type": FunnelEvent.EVENT_CLAIM_PLACE_START,
            "place_id": self.place.id,
            "source": "place-claim-auth",
            "path": "/ru/place/test/",
        }

        response = self.client.post(
            reverse("track_event"),
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        event = FunnelEvent.objects.get()
        self.assertEqual(event.event_type, FunnelEvent.EVENT_CLAIM_PLACE_START)
        self.assertEqual(event.place_id, self.place.id)
        self.assertEqual(event.event_meta.get("source"), "place-claim-auth")


class TestGoogleAnalyticsEvents(TestCase):
    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_catalog_page_renders_google_analytics_search_and_filter_events(self):
        response = self.client.get("/ru/catalog/?q=robot&min_rating=4")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kidsmap-analytics-events")
        self.assertContains(response, '"name": "catalog_search"')
        self.assertContains(response, '"name": "catalog_filter"')

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_place_detail_renders_google_analytics_place_open_event(self):
        place = Place.objects.create(
            name="Analytics Place",
            name_ru="Карточка для аналитики",
            category="EDU",
            is_active=True,
            phone1="+994501112233",
            lat=40.4093,
            lng=49.8671,
        )

        response = self.client.get(place.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "kidsmap-analytics-events")
        self.assertContains(response, '"name": "place_open"')
        self.assertContains(response, '"place_id": %s' % place.id)

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_register_page_with_owner_intent_renders_owner_signup_start_event(self):
        response = self.client.get(f"{reverse('account_register')}?intent=owner_place")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"name": "owner_signup_start"')
        self.assertContains(response, '"intent": "owner_place"')

    def test_tracking_registry_includes_named_events_and_conversions(self):
        self.assertEqual(
            TRACKED_EVENT_NAMES,
            (
                FunnelEvent.EVENT_CATALOG_SEARCH,
                FunnelEvent.EVENT_CATALOG_FILTER,
                FunnelEvent.EVENT_PLACE_OPEN,
                FunnelEvent.EVENT_CTA_CALL,
                FunnelEvent.EVENT_CTA_WHATSAPP,
                FunnelEvent.EVENT_CTA_INSTAGRAM,
                FunnelEvent.EVENT_FAVORITE_TOGGLE,
                FunnelEvent.EVENT_REVIEW_SUBMIT,
                FunnelEvent.EVENT_CLAIM_PLACE_START,
                FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
                FunnelEvent.EVENT_OWNER_SIGNUP_START,
                FunnelEvent.EVENT_OWNER_SIGNUP_COMPLETE,
            ),
        )
        self.assertEqual(
            GA4_CONVERSION_EVENT_NAMES,
            (
                FunnelEvent.EVENT_CTA_CALL,
                FunnelEvent.EVENT_CTA_WHATSAPP,
                FunnelEvent.EVENT_REVIEW_SUBMIT,
                FunnelEvent.EVENT_CLAIM_PLACE_SUBMIT,
                FunnelEvent.EVENT_OWNER_SIGNUP_COMPLETE,
            ),
        )


class TestSiteVisitMiddleware(TestCase):
    def test_site_visit_increments_for_same_session(self):
        self.client.get("/ru/")
        self.client.get("/ru/catalog/")

        self.assertEqual(SiteVisit.objects.count(), 1)
        visit = SiteVisit.objects.first()
        self.assertEqual(visit.hits, 2)

    def test_site_visit_skips_excluded_path(self):
        self.client.get("/favicon.ico")
        self.assertEqual(SiteVisit.objects.count(), 0)

    def test_site_visit_skips_localized_admin_path(self):
        self.client.get("/ru/admin/login/")
        self.assertEqual(SiteVisit.objects.count(), 0)


class TestAccountsAndReviewAccess(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Auth Place",
            name_ru="Площадка для авторизации",
            category="EDU",
            is_active=True,
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_register_creates_inactive_profile_and_verification_challenge(self):
        with patch("catalog.services.email_verification._generate_code", return_value="123456"):
            response = self.client.post(
                reverse("account_register"),
                data={
                    "username": "owner_user",
                    "first_name": "Рамин",
                    "last_name": "Алиев",
                    "email": "owner@example.com",
                    "phone": "+994 50 123 45 67",
                    "gender": UserProfile.GENDER_MALE,
                    "password1": "StrongPass123!!",
                    "password2": "StrongPass123!!",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_verify_email"), response.headers["Location"])
        user = User.objects.get(username="owner_user")
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(user.profile.role, UserProfile.ROLE_USER)
        self.assertEqual(user.profile.phone, "+994 50 123 45 67")
        self.assertEqual(user.profile.gender, UserProfile.GENDER_MALE)
        self.assertEqual(user.first_name, "Рамин")
        self.assertEqual(user.last_name, "Алиев")

        challenge = UserEmailVerification.objects.get(user=user)
        self.assertEqual(challenge.email, "owner@example.com")
        self.assertFalse(challenge.is_verified)
        self.assertGreater(challenge.attempts_left, 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_anonymous_cannot_submit_place_review(self):
        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={"rating": "5", "text": "Отлично", "author_name": "Гость"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceReview.objects.count(), 0)

    def test_anonymous_cannot_submit_site_review(self):
        response = self.client.post(
            reverse("add_site_review"),
            data={"rating": "5", "text": "Супер", "author_name": "Гость"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SiteReview.objects.count(), 0)

    def test_authenticated_user_can_submit_place_review(self):
        user = User.objects.create_user(username="member", email="member@example.com", password="StrongPass123!!")
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER)
        self.client.login(username="member", password="StrongPass123!!")

        response = self.client.post(
            reverse("add_place_review", args=[self.place.id]),
            data={"rating": "4", "text": "Нормально", "author_name": "Пользователь"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceReview.objects.count(), 1)
        review = PlaceReview.objects.first()
        self.assertEqual(review.user, user)
        self.assertContains(response, '"name": "review_submit"')
        self.assertContains(response, '"review_scope": "place"')

    def test_registration_page_shows_required_fields_note_in_current_language(self):
        response = self.client.get(reverse("account_register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Поля, отмеченные звездочкой, обязательны для заполнения.")


class TestCatalogEnhancements(TestCase):
    def test_place_detail_uses_safe_next_url_for_back_link(self):
        place = Place.objects.create(
            name="Context Place",
            name_ru="Карточка с контекстом",
            category="EDU",
            is_active=True,
        )

        next_url = "/ru/catalog/?district=%D0%AF%D1%81%D0%B0%D0%BC%D0%B0%D0%BB"
        response = self.client.get(f"{place.get_absolute_url()}?next={next_url}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('href="/ru/catalog/?district=Ясамал"', response.content.decode("utf-8"))

    def test_catalog_can_sort_places_by_review_count(self):
        low_reviews = Place.objects.create(
            name="Few Reviews",
            name_ru="Мало отзывов",
            category="EDU",
            is_active=True,
            rating_count=1,
            rating_avg=4.2,
        )
        high_reviews = Place.objects.create(
            name="Many Reviews",
            name_ru="Много отзывов",
            category="EDU",
            is_active=True,
            rating_count=9,
            rating_avg=4.8,
        )

        response = self.client.get(reverse("place_list"), {"sort": "reviews_desc"}, follow=True)

        self.assertEqual(response.status_code, 200)
        ordered_names = [item.name_ru for item in response.context["places"]]
        self.assertLess(ordered_names.index(high_reviews.name_ru), ordered_names.index(low_reviews.name_ru))

    def test_catalog_district_filter_matches_exact_value_only(self):
        exact_place = Place.objects.create(
            name="Exact District",
            name_ru="Точный район",
            category="EDU",
            is_active=True,
            district="Ясамал",
        )
        partial_place = Place.objects.create(
            name="Partial District",
            name_ru="Похожий район",
            category="EDU",
            is_active=True,
            district="Новый Ясамал",
        )

        response = self.client.get(reverse("place_list"), {"district": "Ясамал"}, follow=True)

        self.assertEqual(response.status_code, 200)
        names = [item.name_ru for item in response.context["places"]]
        self.assertIn(exact_place.name_ru, names)
        self.assertNotIn(partial_place.name_ru, names)

    def test_catalog_metro_filter_matches_exact_value_only(self):
        exact_place = Place.objects.create(
            name="Exact Metro",
            name_ru="Точное метро",
            category="EDU",
            is_active=True,
            metro="28 Май",
        )
        partial_place = Place.objects.create(
            name="Partial Metro",
            name_ru="Похожее метро",
            category="EDU",
            is_active=True,
            metro="Около 28 Май",
        )

        response = self.client.get(reverse("place_list"), {"metro": "28 Май"}, follow=True)

        self.assertEqual(response.status_code, 200)
        names = [item.name_ru for item in response.context["places"]]
        self.assertIn(exact_place.name_ru, names)
        self.assertNotIn(partial_place.name_ru, names)

    def test_catalog_price_filter_uses_range_overlap(self):
        overlapping_place = Place.objects.create(
            name="Overlap Price",
            name_ru="Подходящий диапазон цены",
            category="EDU",
            is_active=True,
            price_from=80,
            price_to=120,
        )
        out_of_range_place = Place.objects.create(
            name="Out Price",
            name_ru="Неподходящий диапазон цены",
            category="EDU",
            is_active=True,
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
        with_photo_place = Place.objects.create(
            name="Recent With Photo",
            name_ru="Новое с фото",
            category="EDU",
            is_active=True,
            photo=SimpleUploadedFile("new-photo.png", b"main-image", content_type="image/png"),
        )
        without_photo_place = Place.objects.create(
            name="Recent Without Photo",
            name_ru="Новое без фото",
            category="EDU",
            is_active=True,
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
        place = Place.objects.create(
            name="Detailed Place",
            name_ru="Кружок с подробной ценой",
            category="EDU",
            is_active=True,
            schedule="Пн/Ср/Пт 18:00-19:00",
            lesson_duration_minutes=60,
            price_from=80,
            price_to=120,
            price_per_lesson=20,
            price_per_month=160,
            price_per_8_lessons=140,
            extra_conditions="Пробный урок бесплатно",
            additional_info="Нужна спортивная форма",
        )

        response = self.client.get(place.get_absolute_url(), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Расписание и цена")
        self.assertContains(response, "1 урок")
        self.assertContains(response, "160 AZN")
        self.assertContains(response, "Пробный урок бесплатно")
        self.assertContains(response, "Нужна спортивная форма")

    def test_place_detail_shows_owner_request_block_for_anonymous_users(self):
        place = Place.objects.create(
            name="Owner Request Place",
            name_ru="Кружок с заявкой владельца",
            category="EDU",
            is_active=True,
        )

        response = self.client.get(f"/ru{place.get_absolute_url()}", follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Вы представитель этого кружка?")
        self.assertContains(response, "intent=owner_place")
        self.assertContains(response, reverse("account_login"))

    def test_card_price_badge_label_keeps_from_prefix_for_lower_bound_price(self):
        with override("ru"):
            place = Place(price_from=80, category="EDU")

            self.assertEqual(place.card_price_badge_label, "от")
            self.assertEqual(place.card_price_badge_value, "80")
            self.assertEqual(place.card_price_badge_currency, "AZN")

    def test_place_detail_renders_swipe_ready_gallery(self):
        place = Place.objects.create(
            name="Gallery Place",
            name_ru="Кружок с галереей",
            category="EDU",
            is_active=True,
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
        self.assertContains(response, "data-place-gallery-thumb")
        self.assertContains(response, "static/js/place_gallery.js")

    def test_catalog_card_renders_more_details_block(self):
        Place.objects.create(
            name="More Details Place",
            name_ru="Карточка с блоком другое",
            category="EDU",
            is_active=True,
            address="ул. Тестовая, 5",
            phone1="+994501112233",
            schedule="Вт/Чт",
            additional_info="Есть пробное занятие",
        )

        response = self.client.get(reverse("place_list"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "place-more-details")
        self.assertContains(response, "Подробнее")
        self.assertContains(response, "Подробности")
        self.assertContains(response, "Есть пробное занятие")

    def test_catalog_map_uses_only_filtered_map_ready_places(self):
        matching_place = Place.objects.create(
            name="Map Match",
            name_ru="Точка на карте",
            category="EDU",
            is_active=True,
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
        Place.objects.create(
            name="Map Missing Coordinates",
            name_ru="Без координат",
            category="EDU",
            is_active=True,
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
        self.assertEqual(
            response.context["catalog_map_places"],
            [
                {
                    "name": matching_place.name_i18n("ru"),
                    "lat": matching_place.lat,
                    "lng": matching_place.lng,
                    "url": matching_place.get_absolute_url(),
                    "category": matching_place.get_category_display(),
                    "image_url": "",
                    "location": "Ясамал / Низами",
                }
            ],
        )


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
        self.assertContains(az_home, "KidsMap vasitəsilə yeni valideynlər cəlb edin")
        self.assertContains(az_home, "Tam lent və reaksiyalar")
        self.assertContains(az_home, "Ramin A.")
        self.assertContains(az_home, "Sayt Bakıda yeni dərnəkləri tez tapmağa kömək edir, interfeys aydındır.")
        self.assertNotContains(az_home, "Приведите новых родителей через KidsMap")
        self.assertNotContains(az_home, "Полная лента и реакции")

        en_home = self.client.get("/en/", follow=True)
        self.assertEqual(en_home.status_code, 200)
        self.assertContains(en_home, "Bring new parents through KidsMap")
        self.assertContains(en_home, "Full feed and reactions")
        self.assertContains(en_home, "Ramin A.")
        self.assertContains(en_home, "The site helps you quickly find new clubs in Baku, and the interface is easy to understand.")
        self.assertNotContains(en_home, "Приведите новых родителей через KidsMap")
        self.assertNotContains(en_home, "Полная лента и реакции")

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


class TestAuthValidationAndNextSecurity(TestCase):
    def _registration_payload(self, **overrides):
        payload = {
            "username": "new_user",
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": "new@example.com",
            "phone": "+994 50 111 22 33",
            "gender": UserProfile.GENDER_MALE,
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
        }
        payload.update(overrides)
        return payload

    def test_register_requires_email(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_email_user", email=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_email_user").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_requires_phone(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_phone_user", email="no-phone@example.com", phone=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_phone_user").exists())
        self.assertIn("phone", response.context["form"].errors)

    def test_register_requires_gender(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="no_gender_user", email="no-gender@example.com", gender=""),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="no_gender_user").exists())
        self.assertIn("gender", response.context["form"].errors)

    def test_register_rejects_invalid_first_name(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                username="bad_first_name",
                email="bad-first-name@example.com",
                first_name="123",
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bad_first_name").exists())
        self.assertIn("first_name", response.context["form"].errors)

    def test_register_rejects_duplicate_email_case_insensitive(self):
        User.objects.create_user(
            username="first_user",
            email="Dup@Example.com",
            password="StrongPass123!!",
        )

        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="second_user", email="dup@example.com"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="second_user").exists())
        self.assertIn("email", response.context["form"].errors)

    def test_register_rejects_duplicate_username_case_insensitive(self):
        User.objects.create_user(
            username="ExistingUser",
            email="existing@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(username="existinguser", email="new-existing@example.com"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="new-existing@example.com").exists())
        self.assertIn("username", response.context["form"].errors)

    def test_register_defaults_to_regular_user_role(self):
        response = self.client.post(
            reverse("account_register"),
            data=self._registration_payload(
                username="default_role_user",
                email="default-role@example.com",
            ),
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="default_role_user")
        self.assertEqual(user.profile.role, UserProfile.ROLE_USER)

    def test_register_rejects_external_next_redirect(self):
        response = self.client.post(
            f"{reverse('account_register')}?next=https://evil.example",
            data=self._registration_payload(username="safe_next_user", email="safe-next@example.com"),
        )
        self.assertEqual(response.status_code, 302)
        parsed = urlparse(response.headers["Location"])
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.path, reverse("account_verify_email"))
        self.assertEqual(params.get("next"), [reverse("account_profile")])

    def test_login_rejects_external_next_redirect(self):
        User.objects.create_user(
            username="login_safe_user",
            email="login-safe@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            f"{reverse('account_login')}?next=https://evil.example",
            data={"username": "login_safe_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ru/account/profile/")

    def test_login_without_next_redirects_to_account_profile(self):
        User.objects.create_user(
            username="login_profile_user",
            email="login-profile@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "login_profile_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ru/account/profile/")

    def test_login_accepts_email_instead_of_username(self):
        User.objects.create_user(
            username="login_email_user",
            email="login-email@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "login-email@example.com", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/ru/account/profile/")

    def test_login_without_remember_me_expires_session_on_browser_close(self):
        User.objects.create_user(
            username="session_short_user",
            email="session-short@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "session_short_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_with_remember_me_persists_session(self):
        User.objects.create_user(
            username="session_long_user",
            email="session-long@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_login"),
            data={"username": "session_long_user", "password": "StrongPass123!!", "remember_me": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.client.session.get_expire_at_browser_close())


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TestPasswordResetIdentifierSupport(TestCase):
    def test_password_reset_accepts_username_and_sends_email(self):
        User.objects.create_user(
            username="reset_user",
            email="reset-user@example.com",
            password="StrongPass123!!",
            is_active=True,
        )

        response = self.client.post(
            reverse("password_reset"),
            data={"email": "reset_user"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["reset-user@example.com"])
        self.assertIn("Логин аккаунта: reset_user.", mail.outbox[0].body)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_OTP_TTL_MINUTES=10,
    EMAIL_OTP_RESEND_COOLDOWN_SECONDS=60,
    EMAIL_OTP_MAX_ATTEMPTS=5,
)
class TestEmailVerificationFlow(TestCase):
    def _registration_payload(self, *, username: str, email: str):
        return {
            "username": username,
            "first_name": "Иван",
            "last_name": "Иванов",
            "email": email,
            "phone": "+994 50 111 22 33",
            "gender": UserProfile.GENDER_MALE,
            "role": UserProfile.ROLE_USER,
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
        }

    def _register(self, *, username: str, email: str, code: str = "123456"):
        with patch("catalog.services.email_verification._generate_code", return_value=code):
            response = self.client.post(
                reverse("account_register"),
                data=self._registration_payload(username=username, email=email),
            )
        return response, User.objects.get(username=username)

    def test_login_requires_email_confirmation_for_inactive_user(self):
        self._register(username="inactive_login_user", email="inactive-login@example.com")
        response = self.client.post(
            reverse("account_login"),
            data={"username": "inactive_login_user", "password": "StrongPass123!!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email не подтвержден")

    def test_verify_email_activates_user_and_logs_in(self):
        register_response, user = self._register(username="verify_user", email="verify@example.com", code="123456")
        self.assertEqual(register_response.status_code, 302)
        self.assertIn(reverse("account_verify_email"), register_response.headers["Location"])

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "verify@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
            },
        )
        self.assertEqual(verify_response.status_code, 302)
        self.assertEqual(verify_response.headers["Location"], reverse("account_profile"))

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        challenge = UserEmailVerification.objects.get(user=user)
        self.assertTrue(challenge.is_verified)
        self.assertIsNone(challenge.expires_at)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    @override_settings(GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST123")
    def test_verify_email_with_owner_intent_queues_owner_signup_complete_event(self):
        register_response, user = self._register(username="owner_verify_user", email="owner-verify@example.com", code="123456")
        self.assertEqual(register_response.status_code, 302)

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "owner-verify@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
                "intent": "owner_place",
            },
            follow=True,
        )

        self.assertEqual(verify_response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertContains(verify_response, '"name": "owner_signup_complete"')
        self.assertContains(verify_response, '"intent": "owner_place"')

    def test_verify_email_rejects_expired_code(self):
        _, user = self._register(username="expired_user", email="expired@example.com", code="123456")
        challenge = UserEmailVerification.objects.get(user=user)
        challenge.expires_at = timezone.now() - timedelta(minutes=1)
        challenge.save(update_fields=["expires_at", "updated_at"])

        verify_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "verify",
                "email": "expired@example.com",
                "code": "123456",
                "next": reverse("account_profile"),
            },
            follow=True,
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertContains(verify_response, "Срок действия кода истек")
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_resend_respects_cooldown_and_then_sends_new_code(self):
        _, user = self._register(username="resend_user", email="resend@example.com", code="111111")
        self.assertEqual(len(mail.outbox), 1)

        cooldown_response = self.client.post(
            reverse("account_verify_email"),
            data={
                "form_action": "resend",
                "email": "resend@example.com",
                "next": reverse("account_profile"),
            },
            follow=True,
        )
        self.assertEqual(cooldown_response.status_code, 200)
        self.assertContains(cooldown_response, "Повторная отправка будет доступна")
        self.assertEqual(len(mail.outbox), 1)

        challenge = UserEmailVerification.objects.get(user=user)
        challenge.resend_available_at = timezone.now() - timedelta(seconds=1)
        challenge.save(update_fields=["resend_available_at", "updated_at"])

        with patch("catalog.services.email_verification._generate_code", return_value="222222"):
            resend_response = self.client.post(
                reverse("account_verify_email"),
                data={
                    "form_action": "resend",
                    "email": "resend@example.com",
                    "next": reverse("account_profile"),
                },
                follow=True,
            )

        self.assertEqual(resend_response.status_code, 200)
        self.assertContains(resend_response, "Код подтверждения отправлен")
        challenge.refresh_from_db()
        self.assertFalse(challenge.is_verified)
        self.assertEqual(challenge.attempts_left, 5)
        self.assertEqual(len(mail.outbox), 2)

    def test_resend_works_when_user_exists_but_challenge_not_created_yet(self):
        user = User.objects.create_user(
            username="pending_without_challenge",
            email="pending@example.com",
            password="StrongPass123!!",
            is_active=False,
        )
        UserProfile.objects.create(user=user, role=UserProfile.ROLE_USER, phone="+994 50 111 22 33")
        self.assertFalse(UserEmailVerification.objects.filter(user=user).exists())

        with patch("catalog.services.email_verification._generate_code", return_value="333333"):
            response = self.client.post(
                reverse("account_verify_email"),
                data={
                    "form_action": "resend",
                    "email": "pending@example.com",
                    "next": reverse("account_profile"),
                },
                follow=True,
            )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Код подтверждения отправлен")
        self.assertTrue(UserEmailVerification.objects.filter(user=user).exists())
        self.assertEqual(len(mail.outbox), 1)


class TestAccountProfileUpdates(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile_user",
            email="profile@example.com",
            password="StrongPass123!!",
            first_name="Старое",
            last_name="Имя",
        )
        UserProfile.objects.create(user=self.user, role=UserProfile.ROLE_USER, phone="+994 50 000 00 00")
        self.client.login(username="profile_user", password="StrongPass123!!")

    def test_account_profile_opens_for_authenticated_user(self):
        response = self.client.get(reverse("account_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "profile_user")

    def test_account_profile_updates_names_and_phone(self):
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "profile",
                "email": "profile-new@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "phone": "+994 55 111 22 33",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile-new@example.com")
        self.assertEqual(self.user.first_name, "Новый")
        self.assertEqual(self.user.last_name, "Пользователь")
        self.assertEqual(self.user.profile.phone, "+994 55 111 22 33")

    def test_account_profile_rejects_email_which_is_already_used(self):
        User.objects.create_user(
            username="existing_mail_user",
            email="used@example.com",
            password="StrongPass123!!",
        )
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "profile",
                "email": "used@example.com",
                "first_name": "Новый",
                "last_name": "Пользователь",
                "phone": "+994 55 111 22 33",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["profile_form"].errors)

    def test_account_dashboard_favorites_and_settings_pages_open(self):
        dashboard_response = self.client.get(reverse("account_dashboard"))
        favorites_response = self.client.get(reverse("account_favorites"))
        settings_response = self.client.get(reverse("account_settings"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertEqual(favorites_response.status_code, 200)
        self.assertEqual(settings_response.status_code, 200)

    def test_account_favorites_lists_liked_places(self):
        place = Place.objects.create(
            name="Fav Place",
            name_ru="Избранный кружок",
            category="EDU",
            is_active=True,
        )
        PlaceLike.objects.create(place=place, user=self.user)
        response = self.client.get(reverse("account_favorites"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Избранный кружок")

    def test_account_profile_can_change_password(self):
        response = self.client.post(
            reverse("account_profile"),
            data={
                "form_action": "password",
                "old_password": "StrongPass123!!",
                "new_password1": "NewStrongPass123!!",
                "new_password2": "NewStrongPass123!!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.client.login(username="profile_user", password="NewStrongPass123!!"))


class TestOwnershipWorkflow(TestCase):
    def setUp(self):
        self.place = Place.objects.create(
            name="Ownership Place",
            name_ru="Кружок для привязки",
            category="EDU",
            is_active=True,
        )
        self.owner_user = User.objects.create_user(
            username="owner_role_user",
            email="owner-role@example.com",
            password="StrongPass123!!",
        )
        self.regular_user = User.objects.create_user(
            username="regular_role_user",
            email="regular-role@example.com",
            password="StrongPass123!!",
        )
        self.moderator = User.objects.create_superuser(
            username="moderator_admin",
            email="moderator@example.com",
            password="StrongPass123!!",
        )

        UserProfile.objects.create(user=self.owner_user, role=UserProfile.ROLE_OWNER)
        UserProfile.objects.create(user=self.regular_user, role=UserProfile.ROLE_USER)

    def test_owner_can_submit_place_ownership_request(self):
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("request_place_ownership", args=[self.place.id]),
            data={"note": "Я представитель кружка"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceOwnershipRequest.objects.count(), 1)
        ownership_request = PlaceOwnershipRequest.objects.first()
        self.assertEqual(ownership_request.applicant, self.owner_user)
        self.assertEqual(ownership_request.place, self.place)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 1)
        self.assertContains(response, '"name": "claim_place_submit"')
        self.assertContains(response, f'"place_id": {self.place.id}')

    def test_owner_cabinet_shows_claim_candidates(self):
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("claimable_places", response.context)
        self.assertIn(self.place, response.context["claimable_places"])

    def test_owner_cabinet_claim_search_filters_candidates(self):
        Place.objects.create(
            name="Another Place",
            name_ru="Другой кружок",
            category="TECH",
            is_active=True,
        )
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"), data={"claim_q": "Другой"})

        self.assertEqual(response.status_code, 200)
        claimable_places = list(response.context["claimable_places"])
        self.assertEqual(len(claimable_places), 1)
        self.assertEqual(claimable_places[0].name_ru, "Другой кружок")

    def test_owner_cabinet_shows_grouped_request_sections_without_management_blocks(self):
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает",
        )
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Принято",
        )
        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            status=PlaceOwnershipRequest.STATUS_REJECTED,
            note="Отклонено",
        )

        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Заявки на рассмотрении")
        self.assertContains(response, "Принятые заявки")
        self.assertContains(response, "Отклоненные заявки")
        self.assertNotContains(response, "Создать заявку на управление карточкой")
        self.assertNotContains(response, "Мои кружки")

    def test_regular_user_can_submit_place_ownership_request(self):
        self.client.login(username="regular_role_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("request_place_ownership", args=[self.place.id]),
            data={"note": "Хочу управлять карточкой"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaceOwnershipRequest.objects.count(), 1)
        ownership_request = PlaceOwnershipRequest.objects.first()
        self.assertEqual(ownership_request.applicant, self.regular_user)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)
        self.assertContains(response, '"name": "claim_place_submit"')

    def test_approve_request_assigns_place_owner_and_writes_audit(self):
        ownership_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.regular_user,
            note="Подтверждаю права на кружок",
        )

        ownership_request.apply_moderation(
            moderator=self.moderator,
            new_status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Проверено",
        )
        ownership_request.refresh_from_db()
        self.place.refresh_from_db()

        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_APPROVED)
        self.assertEqual(ownership_request.moderated_by, self.moderator)
        self.assertEqual(self.place.owner, self.regular_user)
        self.regular_user.profile.refresh_from_db()
        self.assertEqual(self.regular_user.profile.role, UserProfile.ROLE_OWNER)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 2)
        latest_audit = PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).first()
        self.assertEqual(latest_audit.action, PlaceOwnershipRequestAudit.ACTION_APPROVED)

    def test_reject_request_keeps_place_unassigned_and_writes_audit(self):
        ownership_request = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.owner_user,
            note="Подтверждаю права на кружок",
        )

        ownership_request.apply_moderation(
            moderator=self.moderator,
            new_status=PlaceOwnershipRequest.STATUS_REJECTED,
            note="Недостаточно подтверждений",
        )
        ownership_request.refresh_from_db()
        self.place.refresh_from_db()

        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_REJECTED)
        self.assertIsNone(self.place.owner)
        self.assertEqual(PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).count(), 2)
        latest_audit = PlaceOwnershipRequestAudit.objects.filter(ownership_request=ownership_request).first()
        self.assertEqual(latest_audit.action, PlaceOwnershipRequestAudit.ACTION_REJECTED)


class TestOwnerPlaceManagementAndPermissions(TestCase):
    def setUp(self):
        self.manager_user = User.objects.create_user(
            username="owner_manager",
            email="manager@example.com",
            password="StrongPass123!!",
        )
        self.editor_user = User.objects.create_user(
            username="owner_editor",
            email="editor@example.com",
            password="StrongPass123!!",
        )
        self.moderator_user = User.objects.create_user(
            username="owner_moderator",
            email="moderator-role@example.com",
            password="StrongPass123!!",
        )
        self.regular_user = User.objects.create_user(
            username="regular_for_owner_pages",
            email="regular-owner-pages@example.com",
            password="StrongPass123!!",
        )

        UserProfile.objects.create(
            user=self.manager_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MANAGER,
        )
        UserProfile.objects.create(
            user=self.editor_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_EDITOR,
        )
        UserProfile.objects.create(
            user=self.moderator_user,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MODERATOR,
        )
        UserProfile.objects.create(user=self.regular_user, role=UserProfile.ROLE_USER)

        self.manager_place = Place.objects.create(
            name="Manager Place",
            name_ru="Кружок менеджера",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
            rating_avg=4.7,
            rating_count=10,
            likes_count=25,
        )
        self.editor_place = Place.objects.create(
            name="Editor Place",
            name_ru="Кружок редактора",
            category="TECH",
            owner=self.editor_user,
            is_active=False,
        )
        self.moderator_place = Place.objects.create(
            name="Moderator Place",
            name_ru="Кружок модератора",
            category="MUS",
            owner=self.moderator_user,
            is_active=True,
        )

    def _image_upload(self, name: str) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, b"fake-image-content", content_type="image/png")

    def _oversized_image_upload(self, name: str) -> SimpleUploadedFile:
        return SimpleUploadedFile(name, b"x" * (2 * 1024 * 1024 + 1), content_type="image/png")

    def test_owner_manager_can_open_places_dashboard(self):
        self.manager_place.status = Place.STATUS_DRAFT
        self.manager_place.save(update_fields=["status", "updated_at"])
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кружок менеджера")
        self.assertContains(response, "Redaktəni davam et")
        self.assertContains(response, reverse("owner_place_edit", args=[self.manager_place.id]))

    def test_owner_edit_page_shows_current_photo_preview(self):
        self.editor_place.photo = self._image_upload("preview-main.png")
        self.editor_place.save(update_fields=["photo"])

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_edit", args=[self.editor_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner-file-uploader-current-preview")
        self.assertContains(response, "owner-file-uploader-clear")
        self.assertContains(response, "data-owner-wizard")
        self.assertContains(response, "data-owner-completion")
        self.assertContains(response, "data-owner-wizard-shell")
        self.assertContains(response, 'data-owner-step="4"', html=False)
        self.assertContains(response, "owner-wizard-progressbar")
        self.assertContains(response, "owner_place_wizard.js")
        self.assertNotContains(response, '<footer class="site-footer panel">', html=False)
        self.assertNotContains(response, "Фото для шапки")

    def test_owner_editor_can_save_incomplete_edit_as_draft(self):
        self.editor_place.name_az = "Redakte qaralama"
        self.editor_place.description_az = "Ilkin tesvir"
        self.editor_place.category = "EDU"
        self.editor_place.status = Place.STATUS_DRAFT
        self.editor_place.is_active = False
        self.editor_place.photo = self._image_upload("draft-edit.png")
        self.editor_place.save()

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "form_action": "save_draft",
                "name_ru": "",
                "name_az": "Redakte qaralama",
                "name_en": "",
                "description_ru": "",
                "description_az": "Yenilenmis qaralama tesviri",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "lat": "",
                "lng": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "lesson_duration_minutes": "",
                "price_per_lesson": "",
                "price_per_month": "",
                "price_per_8_lessons": "",
                "extra_conditions": "",
                "additional_info": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.editor_place.refresh_from_db()
        self.assertEqual(self.editor_place.name_az, "Redakte qaralama")
        self.assertEqual(self.editor_place.description_az, "Yenilenmis qaralama tesviri")
        self.assertEqual(self.editor_place.status, Place.STATUS_DRAFT)

    def test_owner_edit_page_hides_public_link_for_inactive_place(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_edit", args=[self.editor_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Открыть страницу кружка")
        self.assertContains(response, "owner-place-actions-note")

    def test_owner_dashboard_draft_card_name_is_not_public_link(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f'href="{self.editor_place.get_absolute_url()}"', html=False)
        self.assertContains(response, self.editor_place.name_i18n())

    def test_owner_create_page_renders_map_picker(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-owner-map-picker")
        self.assertContains(response, "owner-form-intro-title")
        self.assertContains(response, "AZ")
        self.assertContains(response, 'name="lat"', html=False)
        self.assertContains(response, 'name="lng"', html=False)
        self.assertContains(response, "data-owner-wizard-shell")
        self.assertContains(response, "data-map-search-input")
        self.assertContains(response, "data-map-search")
        self.assertContains(response, "owner_place_map_picker.js")
        self.assertContains(response, "owner_place_wizard.js")
        self.assertContains(response, "leaflet@1.9.4/dist/leaflet.css")
        self.assertNotContains(response, '<footer class="site-footer panel">', html=False)
        self.assertNotContains(response, "Фото для шапки")
        self.assertContains(response, "data-owner-completion")
        self.assertContains(response, "owner-form-step-lead")
        self.assertContains(response, "owner-form-details-secondary")
        self.assertContains(response, 'data-owner-step="4"', html=False)
        self.assertContains(response, "owner-language-tablist")
        self.assertContains(response, 'data-owner-step="2"', html=False)
        html = response.content.decode("utf-8")
        self.assertLess(html.index('name="name_az"'), html.index('name="name_ru"'))
        self.assertLess(html.index('name="description_az"'), html.index('name="description_ru"'))
        self.assertLess(html.index('data-owner-step="2"'), html.index('name="is_temporary"'))

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    def test_owner_create_page_uses_google_maps_when_key_is_configured(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "maps.googleapis.com/maps/api/js?key=test-key&libraries=places")
        self.assertContains(response, "kidsMapInitOwnerMapPickers")
        self.assertContains(response, 'data-map-provider="google"', html=False)
        self.assertContains(response, "data-map-search-input")
        self.assertNotContains(response, "leaflet@1.9.4/dist/leaflet.css")

    def test_owner_editor_can_edit_but_cannot_publish(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")

        edit_response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "name_ru": "Кружок редактора обновлен",
                "name_az": "",
                "name_en": "",
                "description_ru": "Новое описание",
                "description_az": "",
                "description_en": "",
                "category": "TECH",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        self.editor_place.refresh_from_db()
        self.assertEqual(self.editor_place.name_ru, "Кружок редактора обновлен")

        publish_response = self.client.post(
            reverse("owner_place_publish", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(publish_response.status_code, 200)
        self.editor_place.refresh_from_db()
        self.assertFalse(self.editor_place.is_active)

    def test_owner_manager_can_publish_draft(self):
        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Одобрено модератором",
        )
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_publish", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertTrue(self.manager_place.is_active)

    def test_owner_manager_cannot_publish_draft_without_approval(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_publish", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertFalse(self.manager_place.is_active)

    def test_owner_dashboard_shows_publish_hint_for_unapproved_draft(self):
        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает проверки",
        )
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-publish-unavailable="1"')
        self.assertNotContains(response, 'owner-place-btn-primary')

    def test_owner_dashboard_shows_clear_moderation_statuses_on_cards(self):
        rejected_place = Place.objects.create(
            name="Rejected Place",
            name_ru="Отклоненный кружок",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
        )
        approved_place = Place.objects.create(
            name="Approved Place",
            name_ru="Одобренный кружок",
            category="TECH",
            owner=self.manager_user,
            is_active=False,
        )

        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
            note="Ожидает проверки",
        )
        PlaceOwnershipRequest.objects.create(
            place=rejected_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_REJECTED,
            moderation_note="Нужно добавить нормальное фото",
        )
        PlaceOwnershipRequest.objects.create(
            place=approved_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
            note="Одобрено",
        )

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "owner-place-fact-label")
        self.assertContains(response, "owner-status-badge-pending")
        self.assertContains(response, "owner-status-badge-approved")
        self.assertContains(response, "owner-status-badge-rejected")
        self.assertContains(response, "Нужно добавить нормальное фото")

    def test_owner_dashboard_shows_coordinates_and_map_readiness_statuses(self):
        self.manager_place.lat = 40.4093
        self.manager_place.lng = 49.8671
        self.manager_place.is_active = True
        self.manager_place.save(update_fields=["lat", "lng", "is_active", "updated_at"])
        Place.objects.create(
            name="Manager Draft Without Coordinates",
            name_ru="Черновик без координат",
            category="EDU",
            owner=self.manager_user,
            is_active=False,
            address="Улица без координат",
        )

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Koordinatlar var")
        self.assertContains(response, "Koordinatlar tələb olunur")
        self.assertContains(response, "Xəritə üçün hazırdır")

    def test_owner_manager_can_soft_delete_own_place(self):
        self.manager_place.is_active = True
        self.manager_place.save(update_fields=["is_active", "updated_at"])

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_delete", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertIsNotNone(self.manager_place.deleted_at)
        self.assertEqual(self.manager_place.deleted_by, self.manager_user)
        self.assertFalse(self.manager_place.is_active)
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.manager_place,
                changed_by=self.manager_user,
                source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
                field_name="deleted_at",
            ).exists()
        )

        dashboard_response = self.client.get(reverse("owner_places_dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertNotContains(dashboard_response, "Кружок менеджера")

        public_response = self.client.get(reverse("place_detail_legacy", args=[self.manager_place.id]))
        self.assertEqual(public_response.status_code, 404)

    def test_owner_cannot_delete_place_of_another_owner(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_delete", args=[self.editor_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kart tapılmadı")
        self.editor_place.refresh_from_db()
        self.assertIsNone(self.editor_place.deleted_at)
        self.assertIsNone(self.editor_place.deleted_by)

    def test_owner_moderator_cannot_edit_place(self):
        self.client.login(username="owner_moderator", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.moderator_place.id]),
            data={
                "name_ru": "Изменение от модератора",
                "name_az": "",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "MUS",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.moderator_place.refresh_from_db()
        self.assertNotEqual(self.moderator_place.name_ru, "Изменение от модератора")

    def test_owner_manager_can_create_place_and_send_for_moderation(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Новая карточка владельца",
                "name_az": "Yeni owner karti",
                "name_en": "",
                "description_ru": "Описание новой карточки",
                "description_az": "Yeni owner kartinin tesviri",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Новая карточка на проверку",
                "photo": self._image_upload("main.png"),
                "gallery_images": [self._image_upload("g1.png"), self._image_upload("g2.png")],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("owner_places_dashboard"))

        place = Place.objects.get(owner=self.manager_user, name_ru="Новая карточка владельца")
        self.assertFalse(place.is_active)
        self.assertFalse(place.is_verified)
        self.assertEqual(place.name, "Yeni owner karti")
        self.assertEqual(PlacePhoto.objects.filter(place=place).count(), 2)
        ownership_request = PlaceOwnershipRequest.objects.get(place=place, applicant=self.manager_user)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)

    def test_owner_manager_can_save_incomplete_place_as_draft(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "form_action": "save_draft",
                "name_az": "Yarımçıq qaralama",
                "category": "EDU",
                "description_az": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        place = Place.objects.get(owner=self.manager_user, name_az="Yarımçıq qaralama")
        self.assertEqual(place.status, Place.STATUS_DRAFT)
        self.assertFalse(place.is_active)
        self.assertFalse(place.is_verified)
        self.assertFalse(PlaceOwnershipRequest.objects.filter(place=place, applicant=self.manager_user).exists())

    def test_owner_cannot_create_more_than_ten_places(self):
        for index in range(2, 11):
            Place.objects.create(
                name=f"Manager Place {index}",
                name_ru=f"Кружок менеджера {index}",
                category="EDU",
                owner=self.manager_user,
                is_active=False,
                status=Place.STATUS_DRAFT,
            )

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Limit dolub")

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_manager_create_place_populates_coordinates_automatically(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.401, lng=49.801, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка с геокодированием",
                "name_az": "Geokodlasdirma karti",
                "name_en": "",
                "description_ru": "Описание новой карточки",
                "description_az": "Geokodlasdirma kartinin tesviri",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица 5",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка координат",
                "photo": self._image_upload("main-geocoded.png"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        place = Place.objects.get(owner=self.manager_user, name_ru="Карточка с геокодированием")
        self.assertEqual(place.lat, 40.401)
        self.assertEqual(place.lng, 49.801)
        geocode_mock.assert_called_once()
        self.assertIn("Улица 5", geocode_mock.call_args.kwargs["query"])
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=place,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lat",
            ).exists()
        )

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_manager_create_place_keeps_manual_map_coordinates(self, geocode_mock):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка с ручной точкой",
                "name_az": "Xeritede el ile secilen kart",
                "name_en": "",
                "description_ru": "Описание новой карточки",
                "description_az": "Xeritede el ile secilen kartin tesviri",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Рисование",
                "age_from": "6",
                "age_to": "10",
                "price_from": "80",
                "price_to": "140",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица с ручной точкой 8",
                "lat": "40.377700",
                "lng": "49.892200",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Вт/Чт",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка ручной точки",
                "photo": self._image_upload("main-manual-point.png"),
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        place = Place.objects.get(owner=self.manager_user, name_ru="Карточка с ручной точкой")
        self.assertEqual(place.lat, 40.3777)
        self.assertEqual(place.lng, 49.8922)
        geocode_mock.assert_not_called()
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=place,
                source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
                field_name="lat",
            ).exists()
        )

    def test_owner_place_create_rejects_more_than_ten_gallery_files(self):
        form = OwnerPlaceCreateForm(
            data={
                "name_ru": "Слишком много фото",
                "name_az": "Cox sekil",
                "name_en": "",
                "description_ru": "",
                "description_az": "Sekiller ucun tesvir",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "",
            },
            files=MultiValueDict(
                {
                    "gallery_images": [
                        self._image_upload("g1.png"),
                        self._image_upload("g2.png"),
                        self._image_upload("g3.png"),
                        self._image_upload("g4.png"),
                        self._image_upload("g5.png"),
                        self._image_upload("g6.png"),
                        self._image_upload("g7.png"),
                        self._image_upload("g8.png"),
                        self._image_upload("g9.png"),
                        self._image_upload("g10.png"),
                        self._image_upload("g11.png"),
                    ]
                }
            ),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("gallery_images", form.errors)

    def test_owner_place_create_rejects_main_photo_larger_than_two_mb(self):
        form = OwnerPlaceCreateForm(
            data={
                "name_ru": "Большое фото",
                "name_az": "Boyuk sekil",
                "name_en": "",
                "description_ru": "",
                "description_az": "Boyuk sekil ucun tesvir",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "7",
                "age_to": "12",
                "price_from": "10",
                "price_to": "20",
                "district": "Yasamal",
                "metro": "",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "",
            },
            files=MultiValueDict({"photo": [self._oversized_image_upload("too-large.png")]}),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)
        self.assertIn("2 МБ", form.errors["photo"][0])

    def test_owner_place_create_requires_description_in_azerbaijani(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без описания",
                "name_az": "Tesvirsiz kart",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательного описания",
                "photo": self._image_upload("main-description-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("description_az", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без описания").exists())

    def test_owner_place_create_requires_district_or_metro(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без локации",
                "name_az": "Lokasiyasiz kart",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "Tesvir var",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "",
                "metro": "",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательной локации",
                "photo": self._image_upload("main-location-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("district", response.context["form"].errors)
        self.assertIn("metro", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без локации").exists())

    def test_owner_place_create_temporary_event_requires_start_and_end(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Временное мероприятие без дат",
                "name_az": "Tarixsiz tedbir",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "Tedbir tesviri var",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "on",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательных дат",
                "photo": self._image_upload("main-temporary-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("temporary_start", response.context["form"].errors)
        self.assertIn("temporary_end", response.context["form"].errors)
        self.assertContains(response, 'data-owner-listing-type="temporary"', html=False)
        self.assertContains(response, 'data-owner-mode-panel="temporary"', html=False)
        self.assertContains(response, 'name="is_temporary" class="field-check" id="id_is_temporary" checked', html=False)
        self.assertFalse(Place.objects.filter(name_ru="Временное мероприятие без дат").exists())

    def test_owner_place_create_rejects_custom_metro_value(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка с невалидным метро",
                "name_az": "Metro xetasi olan kart",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "Tesvir var",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "Произвольное значение",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка списка метро",
                "photo": self._image_upload("main-metro-list-only.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("metro", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка с невалидным метро").exists())

    def test_owner_place_create_requires_main_photo(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без фото",
                "name_az": "Fotosuz kart",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "Tesvir var",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательного фото",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("photo", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без фото").exists())

    def test_owner_place_create_requires_name_in_azerbaijani(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "name_ru": "Карточка без AZ названия",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание есть",
                "description_az": "Tesvir var",
                "description_en": "",
                "category": "EDU",
                "subcategory": "Робототехника",
                "age_from": "7",
                "age_to": "12",
                "price_from": "100",
                "price_to": "200",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Улица 1",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "Пн-Сб",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "moderation_note": "Проверка обязательного AZ названия",
                "photo": self._image_upload("main-az-name-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("name_az", response.context["form"].errors)
        self.assertFalse(Place.objects.filter(name_ru="Карточка без AZ названия").exists())

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_create_form_can_check_coordinates_before_saving(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.411111, lng=49.822222, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "address": "Улица 77",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "form_action": "check_coordinates",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "40.411111")
        self.assertContains(response, "49.822222")
        self.assertFalse(Place.objects.filter(owner=self.manager_user, address="Улица 77").exists())
        geocode_mock.assert_called_once()

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_create_form_prefers_manual_point_when_previewing_coordinates(self, geocode_mock):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "address": "Улица 77",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "lat": "40.500000",
                "lng": "49.900000",
                "form_action": "check_coordinates",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "40.500000")
        self.assertContains(response, "49.900000")
        geocode_mock.assert_not_called()

    def test_owner_editor_can_submit_draft_for_moderation(self):
        self.client.login(username="owner_editor", password="StrongPass123!!")

        first_response = self.client.post(
            reverse("owner_place_submit_review", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(
            PlaceOwnershipRequest.objects.filter(place=self.editor_place, applicant=self.editor_user).count(),
            1,
        )

        second_response = self.client.post(
            reverse("owner_place_submit_review", args=[self.editor_place.id]),
            follow=True,
        )
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(second_response, "уже отправлена")
        self.assertEqual(
            PlaceOwnershipRequest.objects.filter(place=self.editor_place, applicant=self.editor_user).count(),
            1,
        )

    def test_regular_user_is_redirected_from_owner_places_dashboard(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_cabinet"))

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_edit_refreshes_coordinates_when_location_changes(self, geocode_mock):
        self.manager_place.address = "Старый адрес"
        self.manager_place.district = "Ясамал"
        self.manager_place.metro = "Иншаатчылар"
        self.manager_place.lat = 40.11
        self.manager_place.lng = 49.11
        self.manager_place.save(update_fields=["address", "district", "metro", "lat", "lng", "updated_at"])
        geocode_mock.return_value = GeocodingPoint(lat=40.55, lng=49.55, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.manager_place.id]),
            data={
                "name_ru": "Кружок менеджера",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание обновлено",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "Yasamal",
                "metro": "28 May",
                "address": "Новый адрес 10",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.lat, 40.55)
        self.assertEqual(self.manager_place.lng, 49.55)
        geocode_mock.assert_called_once()
        self.assertIn("Новый адрес 10", geocode_mock.call_args.kwargs["query"])
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.manager_place,
                source=PlaceChangeAudit.SOURCE_SYSTEM,
                field_name="lng",
            ).exists()
        )

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_edit_form_can_force_refresh_coordinates(self, geocode_mock):
        self.manager_place.address = "Тот же адрес"
        self.manager_place.district = "Ясамал"
        self.manager_place.metro = "Иншаатчылар"
        self.manager_place.lat = 40.111111
        self.manager_place.lng = 49.111111
        self.manager_place.save(update_fields=["address", "district", "metro", "lat", "lng", "updated_at"])
        geocode_mock.return_value = GeocodingPoint(lat=40.666666, lng=49.777777, formatted_address="Baku")

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.manager_place.id]),
            data={
                "name_ru": "Кружок менеджера",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание без смены адреса",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "Yasamal",
                "metro": "İnşaatçılar",
                "address": "Тот же адрес",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
                "form_action": "refresh_coordinates",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.lat, 40.666666)
        self.assertEqual(self.manager_place.lng, 49.777777)
        self.assertContains(response, "40.666666, 49.777777")
        geocode_mock.assert_called_once()

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_owner_edit_keeps_manual_map_coordinates_when_address_changes(self, geocode_mock):
        self.manager_place.address = "Старый адрес"
        self.manager_place.district = "Ясамал"
        self.manager_place.metro = "Иншаатчылар"
        self.manager_place.lat = 40.111111
        self.manager_place.lng = 49.111111
        self.manager_place.save(update_fields=["address", "district", "metro", "lat", "lng", "updated_at"])

        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.manager_place.id]),
            data={
                "name_ru": "Кружок менеджера",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание с ручной точкой",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "Nərimanov",
                "metro": "Gənclik",
                "address": "Новый адрес вручную 15",
                "lat": "40.455500",
                "lng": "49.833300",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.lat, 40.4555)
        self.assertEqual(self.manager_place.lng, 49.8333)
        geocode_mock.assert_not_called()


class TestOwnerTeamAndReviewModeration(TestCase):
    def setUp(self):
        self.owner_manager = User.objects.create_user(
            username="team_owner_manager",
            email="team-owner@example.com",
            password="StrongPass123!!",
        )
        self.team_member = User.objects.create_user(
            username="team_member_user",
            email="team-member@example.com",
            password="StrongPass123!!",
        )
        self.other_user = User.objects.create_user(
            username="team_other_user",
            email="team-other@example.com",
            password="StrongPass123!!",
        )
        UserProfile.objects.create(
            user=self.owner_manager,
            role=UserProfile.ROLE_OWNER,
            owner_role=UserProfile.OWNER_ROLE_MANAGER,
        )
        UserProfile.objects.create(user=self.team_member, role=UserProfile.ROLE_USER)
        UserProfile.objects.create(user=self.other_user, role=UserProfile.ROLE_USER)

        self.place = Place.objects.create(
            name="Team Place",
            name_ru="Кружок команды",
            category="EDU",
            owner=self.owner_manager,
            is_active=True,
        )
        self.place_review = PlaceReview.objects.create(
            place=self.place,
            user=self.other_user,
            author_name="Тест",
            rating=4,
            text="Нормальный кружок",
            is_approved=True,
        )

    def test_owner_manager_can_create_team_invitation(self):
        self.client.login(username="team_owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_team_invite"),
            data={"email": "team-member@example.com", "role": UserProfile.OWNER_ROLE_MODERATOR},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        invitation = OwnerTeamInvitation.objects.get(owner=self.owner_manager, email="team-member@example.com")
        self.assertEqual(invitation.status, OwnerTeamInvitation.STATUS_PENDING)
        self.assertEqual(invitation.role, UserProfile.OWNER_ROLE_MODERATOR)

    def test_user_can_accept_team_invitation(self):
        invitation = OwnerTeamInvitation.objects.create(
            owner=self.owner_manager,
            invited_by=self.owner_manager,
            email="team-member@example.com",
            role=UserProfile.OWNER_ROLE_MODERATOR,
        )

        self.client.login(username="team_member_user", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_team_accept_invitation", args=[invitation.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, OwnerTeamInvitation.STATUS_ACCEPTED)
        membership = OwnerTeamMembership.objects.get(owner=self.owner_manager, member=self.team_member)
        self.assertTrue(membership.is_active)
        self.assertEqual(membership.role, UserProfile.OWNER_ROLE_MODERATOR)

    def test_team_moderator_can_moderate_reviews_but_cannot_edit_content(self):
        OwnerTeamMembership.objects.create(
            owner=self.owner_manager,
            member=self.team_member,
            role=UserProfile.OWNER_ROLE_MODERATOR,
            is_active=True,
            invited_by=self.owner_manager,
        )
        profile = UserProfile.get_or_create_for_user(self.team_member)
        profile.role = UserProfile.ROLE_OWNER
        profile.owner_role = UserProfile.OWNER_ROLE_MODERATOR
        profile.save(update_fields=["role", "owner_role", "updated_at"])

        self.client.login(username="team_member_user", password="StrongPass123!!")
        reviews_response = self.client.get(reverse("owner_reviews_dashboard"))
        self.assertEqual(reviews_response.status_code, 200)
        self.assertContains(reviews_response, "Кружок команды")

        reject_response = self.client.post(
            reverse("owner_review_reject", args=[self.place_review.id]),
            follow=True,
        )
        self.assertEqual(reject_response.status_code, 200)
        self.place_review.refresh_from_db()
        self.assertFalse(self.place_review.is_approved)

        edit_response = self.client.post(
            reverse("owner_place_edit", args=[self.place.id]),
            data={
                "name_ru": "Нельзя менять",
                "name_az": "",
                "name_en": "",
                "description_ru": "",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )
        self.assertEqual(edit_response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, "Кружок команды")

    def test_owner_edit_creates_place_change_audit(self):
        self.client.login(username="team_owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.place.id]),
            data={
                "name_ru": "Кружок команды обновлен",
                "name_az": "",
                "name_en": "",
                "description_ru": "Описание обновлено",
                "description_az": "",
                "description_en": "",
                "category": "EDU",
                "subcategory": "",
                "age_from": "",
                "age_to": "",
                "price_from": "",
                "price_to": "",
                "district": "",
                "metro": "",
                "address": "",
                "phone1": "",
                "instagram": "",
                "website": "",
                "schedule": "",
                "is_temporary": "",
                "temporary_start": "",
                "temporary_end": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        audits = PlaceChangeAudit.objects.filter(place=self.place, changed_by=self.owner_manager)
        self.assertGreaterEqual(audits.count(), 1)
        self.assertTrue(audits.filter(field_name="name_ru").exists())


class TestGeocodePlacesCommand(TestCase):
    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    @patch("catalog.repositories.geocoding_repositories.GoogleMapsGeocodingRepository.geocode")
    def test_command_backfills_coordinates_for_existing_place(self, geocode_mock):
        geocode_mock.return_value = GeocodingPoint(lat=40.777, lng=49.777, formatted_address="Baku")
        place = Place.objects.create(
            name="Backfill Place",
            name_ru="Карточка для бэкфилла",
            category="EDU",
            address="Проспект 1",
            district="Ясамал",
        )
        stdout = StringIO()

        call_command("geocode_places", place_id=place.id, stdout=stdout)

        place.refresh_from_db()
        self.assertEqual(place.lat, 40.777)
        self.assertEqual(place.lng, 49.777)
        self.assertIn("Updated: 1", stdout.getvalue())
