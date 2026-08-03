import json
from pathlib import Path
from io import BytesIO, StringIO
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
from catalog.domain_admin.place import EventAdminForm, PlaceAdminForm
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
    Specialist,
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


class TestAdminTemporaryEventInputs(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_temp_fields",
            email="admin-temp-fields@example.com",
            password="StrongPass123!!",
        )
        self.place = Place.objects.create(
            name="Temporary Admin Place",
            name_az="Temporary Admin Place",
            category="EDU",
            is_temporary=True,
            temporary_start=timezone.now() + timedelta(days=2),
            temporary_end=timezone.now() + timedelta(days=2, hours=2),
        )
        self.client.login(username="admin_temp_fields", password="StrongPass123!!")

    def test_place_admin_form_uses_compact_datetime_local_inputs(self):
        form = PlaceAdminForm(instance=self.place)

        self.assertEqual(form.fields["temporary_start"].widget.input_type, "datetime-local")
        self.assertEqual(form.fields["temporary_end"].widget.input_type, "datetime-local")
        self.assertEqual(
            form.initial["temporary_start"],
            timezone.localtime(self.place.temporary_start).strftime(PlaceAdminForm.DATETIME_LOCAL_FORMAT),
        )
        self.assertEqual(
            form.initial["temporary_end"],
            timezone.localtime(self.place.temporary_end).strftime(PlaceAdminForm.DATETIME_LOCAL_FORMAT),
        )

    def test_place_admin_form_supports_open_ended_age(self):
        self.place.age_to = 12
        self.place.save(update_fields=["age_to"])
        form = PlaceAdminForm(
            data={
                "name_az": "Yaş limiti olmayan yer",
                "category": "EDU",
                "age_from": "3",
                "age_open_ended": "on",
                "status": Place.STATUS_DRAFT,
                "is_active": "",
                "likes_count": "0",
                "rating_avg": "0",
                "rating_count": "0",
                "region": "baku",
                "district": "baku_yasamal",
                "pricing_plans": "[]",
            },
            instance=self.place,
        )

        self.assertTrue(form.is_valid(), form.errors)
        place = form.save()
        self.assertEqual(place.age_from, 3)
        self.assertIsNone(place.age_to)
        self.assertTrue(place.age_open_ended)

    def test_duplicate_candidates_warn_about_matching_contact_and_address(self):
        duplicate = Place.objects.create(
            name="Existing place",
            name_az="Mövcud yer",
            category="EDU",
            phone3="+994501234567",
            website="https://example.com/club",
            instagram="example_club",
            address="Bakı, Yasamal, Nizami küçəsi 10",
        )

        response = self.client.get(
            reverse("admin:catalog_place_duplicate_candidates"),
            {
                "phone": "+994 50 123 45 67",
                "website": "https://www.example.com/club/",
                "instagram": "@example_club",
                "address": "Bakı, Yasamal, Nizami küçəsi 10",
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()["results"]
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], duplicate.pk)
        self.assertEqual(set(result[0]["matched"]), {"телефон", "сайт", "Instagram", "адрес"})

    def test_place_form_exposes_age_and_duplicate_controls(self):
        response = self.client.get(f"{reverse('admin:catalog_place_add')}?type=place")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="age_open_ended"', html=False)
        self.assertContains(response, "data-duplicate-candidates-url", html=False)
        self.assertContains(response, "kidsmap_place_duplicates.js", html=False)

    def test_place_changelist_filters_by_staff_member_who_added_card(self):
        other_staff = User.objects.create_user(
            username="content_manager_filter",
            email="content-manager-filter@example.com",
            password="StrongPass123!!",
            is_staff=True,
        )
        Place.objects.create(
            name="Added by admin",
            name_az="Admin əlavə edib",
            category="EDU",
            created_by=self.superuser,
        )
        Place.objects.create(
            name="Added by content manager",
            name_az="Menecer əlavə edib",
            category="EDU",
            created_by=other_staff,
        )
        Place.objects.bulk_create(
            [
                Place(
                    name=f"Admin pagination place {index}",
                    name_az=f"Admin səhifələmə {index}",
                    slug=f"admin-pagination-place-{index}",
                    category="EDU",
                    created_by=self.superuser,
                )
                for index in range(15)
            ]
        )

        response = self.client.get(
            reverse("admin:catalog_place_changelist"),
            {"created_by": self.superuser.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Added by content manager")
        self.assertContains(response, 'data-field="created_by"', html=False)
        self.assertContains(response, 'km-changelist-pagination__page-status', html=False)
        self.assertContains(response, f"?created_by={self.superuser.pk}&amp;p=2", html=False)

        unknown_response = self.client.get(
            reverse("admin:catalog_place_changelist"),
            {"created_by": "__unknown__"},
        )
        self.assertEqual(unknown_response.status_code, 200)
        self.assertContains(unknown_response, self.place.name)
        self.assertNotContains(unknown_response, "Added by content manager")

    def test_place_change_page_renders_single_compact_datetime_inputs(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="temporary_start"', html=False)
        self.assertContains(response, 'name="temporary_end"', html=False)
        self.assertContains(response, 'type="datetime-local"', count=2, html=False)
        self.assertNotContains(response, 'name="temporary_start_0"', html=False)
        self.assertNotContains(response, 'name="temporary_end_0"', html=False)

    def test_place_change_page_exposes_home_recommendation_controls(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="is_home_recommended"', html=False)
        self.assertContains(response, 'name="home_recommended_order"', html=False)

    def test_localized_admin_add_choice_route_is_reachable(self):
        response = self.client.get("/ru/admin/add-choice/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Добавить публикацию")
        self.assertContains(response, "data-km-sidebar-group", html=False)
        self.assertContains(response, "kidsmap_add_choice.css", html=False)

    def test_place_form_breadcrumb_returns_to_safe_previous_admin_page(self):
        previous_url = "/ru/admin/add-choice/"
        response = self.client.get(
            f"{reverse('admin:catalog_place_add')}?type=permanent",
            HTTP_REFERER=f"http://testserver{previous_url}",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="http://testserver{previous_url}"', html=False)
        self.assertContains(response, "Вернуться на предыдущий шаг", html=False)

    def test_place_form_breadcrumb_falls_back_to_place_list_without_referer(self):
        response = self.client.get(f"{reverse('admin:catalog_place_add')}?type=permanent")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admin:catalog_place_changelist"), html=False)


class TestAdminHomeRecommendations(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_home_recommendations",
            email="admin-home-recommendations@example.com",
            password="StrongPass123!!",
        )
        self.client.login(username="admin_home_recommendations", password="StrongPass123!!")
        self.places = [
            create_quality_place(
                name=f"Recommendation Place {index}",
                name_az=f"Tövsiyə məkanı {index}",
                name_ru=f"Рекомендуемое место {index}",
            )
            for index in range(1, 6)
        ]

    def test_place_list_renders_visual_home_recommendation_editor(self):
        self.places[0].is_home_recommended = True
        self.places[0].home_recommended_order = 10
        self.places[0].save(update_fields=["is_home_recommended", "home_recommended_order"])

        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-home-recommendations", html=False)
        self.assertContains(response, "kidsmap_home_recommendations.css", html=False)
        self.assertContains(response, "kidsmap_home_recommendations.js", html=False)
        self.assertContains(response, "Рекомендуемые места")
        self.assertContains(response, "Рекомендуемое место 1")
        self.assertContains(
            response,
            f'data-save-url="{reverse("admin:catalog_place_home_recommendations_save")}"',
            html=False,
        )
        self.assertNotContains(response, "catalog_moderation/moderationplace/home-recommendations", html=False)

    def test_admin_can_save_home_recommendations_and_order(self):
        save_url = reverse("admin:catalog_place_home_recommendations_save")

        response = self.client.post(
            save_url,
            data=json.dumps({"place_ids": [self.places[2].pk, self.places[0].pk]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.places[0].refresh_from_db()
        self.places[2].refresh_from_db()
        self.assertTrue(self.places[2].is_home_recommended)
        self.assertEqual(self.places[2].home_recommended_order, 10)
        self.assertTrue(self.places[0].is_home_recommended)
        self.assertEqual(self.places[0].home_recommended_order, 20)

    def test_admin_rejects_more_than_four_home_recommendations(self):
        response = self.client.post(
            reverse("admin:catalog_place_home_recommendations_save"),
            data=json.dumps({"place_ids": [place.pk for place in self.places]}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])
        self.assertFalse(Place.objects.filter(is_home_recommended=True).exists())

    def test_candidate_search_returns_only_public_places(self):
        hidden_place = create_quality_place(
            name="Hidden Recommendation Place",
            name_ru="Скрытое место",
            is_active=False,
            status=Place.STATUS_DRAFT,
        )

        response = self.client.get(
            reverse("admin:catalog_place_home_recommendation_candidates"),
            {"q": "Recommendation Place"},
        )

        self.assertEqual(response.status_code, 200)
        result_ids = {item["id"] for item in response.json()["results"]}
        self.assertEqual(result_ids, {place.pk for place in self.places})
        self.assertNotIn(hidden_place.pk, result_ids)


class TestAzerbaijanPhoneFormatting(TestCase):
    def test_place_admin_form_formats_existing_phone_for_input(self):
        place = Place(
            name="Phone Formatting Club",
            name_az="Phone Formatting Club",
            category="EDU",
            phone1="+994501234567",
        )

        form = PlaceAdminForm(instance=place)

        self.assertEqual(form.initial["phone1"], "+994 50 123 45 67")

    def test_place_admin_form_normalizes_local_azerbaijan_phone(self):
        form = PlaceAdminForm()
        form.cleaned_data = {"phone1": "050 123 45 67"}

        self.assertEqual(form.clean_phone1(), "+994501234567")


class TestAdminEventInputs(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="admin_event_fields",
            email="admin-event-fields@example.com",
            password="StrongPass123!!",
        )
        now = timezone.now() + timedelta(days=3)
        self.event = Event.objects.create(
            name="Admin Event Compact",
            name_az="Admin Event Compact",
            category="EDU",
            start_datetime=now,
            end_datetime=now + timedelta(hours=2),
            published_at=now - timedelta(hours=1),
            status=Event.STATUS_DRAFT,
        )
        self.client.login(username="admin_event_fields", password="StrongPass123!!")

    def test_event_admin_form_uses_datetime_picker_inputs(self):
        form = EventAdminForm(instance=self.event)

        self.assertEqual(form.fields["start_datetime"].widget.input_type, "text")
        self.assertEqual(form.fields["end_datetime"].widget.input_type, "text")
        self.assertEqual(form.fields["published_at"].widget.input_type, "datetime-local")
        self.assertEqual(
            form.initial["start_datetime"],
            timezone.localtime(self.event.start_datetime).strftime(EventAdminForm.PICKER_DATETIME_FORMAT),
        )
        self.assertEqual(
            form.initial["end_datetime"],
            timezone.localtime(self.event.end_datetime).strftime(EventAdminForm.PICKER_DATETIME_FORMAT),
        )

    def test_event_change_page_renders_flatpickr_datetime_inputs(self):
        response = self.client.get(reverse("admin:catalog_event_change", args=[self.event.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="start_datetime"', html=False)
        self.assertContains(response, 'name="end_datetime"', html=False)
        self.assertContains(response, 'name="published_at"', html=False)
        self.assertContains(response, 'data-kidsmap-datetime-picker="1"', count=2, html=False)
        self.assertContains(response, 'type="datetime-local"', count=1, html=False)
        self.assertNotContains(response, 'name="start_datetime_0"', html=False)
        self.assertNotContains(response, 'name="end_datetime_0"', html=False)
        self.assertNotContains(response, 'name="published_at_0"', html=False)

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

    def _ga4_disabled_context(self):
        return {
            "enabled": False,
            "connected": False,
            "measurement_id": "",
            "property_id": "",
            "credentials_path": "",
            "error": "",
            "period_stats": {
                "day": {"active_users": 0, "sessions": 0, "page_views": 0},
                "week": {"active_users": 0, "sessions": 0, "page_views": 0},
                "month": {"active_users": 0, "sessions": 0, "page_views": 0},
                "year": {"active_users": 0, "sessions": 0, "page_views": 0},
            },
            "daily_chart": {"labels": [], "active_users": [], "page_views": []},
            "top_pages": [],
            "top_events": [],
        }

    def _admin_place_change_payload(self, **overrides):
        overridden_district = overrides.pop("district", None)
        overridden_region = overrides.pop("region", None)

        from catalog.services.locations import normalize_to_key
        db_district = normalize_to_key(overridden_district or self.place.district or "")

        if not db_district:
            region_val = "baku"
            district_val = "baku_yasamal"
        elif db_district.startswith("baku_"):
            region_val = "baku"
            district_val = db_district
        elif db_district == "baku":
            region_val = "baku"
            district_val = "baku_yasamal"
        else:
            region_val = db_district
            district_val = ""

        if overridden_region:
            region_val = overridden_region
        if overridden_district and overridden_district != "baku":
            # If overridden_district is a key like baku_yasamal or a normalized key, use it
            norm_overridden = normalize_to_key(overridden_district)
            if norm_overridden.startswith("baku_"):
                region_val = "baku"
                district_val = norm_overridden
            elif norm_overridden != "baku":
                region_val = norm_overridden
                district_val = ""

        data = {
            "name": self.place.name,
            "name_ru": self.place.name_ru,
            "name_az": self.place.name_az,
            "name_en": self.place.name_en,
            "description_ru": self.place.description_ru,
            "description_az": self.place.description_az,
            "description_en": self.place.description_en,
            "category": self.place.category_id or "",
            "subcategory": self.place.subcategory_id or "",
            "is_temporary": "on" if self.place.is_temporary else "",
            "temporary_start": "",
            "temporary_end": "",
            "is_active": "on" if self.place.is_active else "",
            "is_verified": "on" if self.place.is_verified else "",
            "status": self.place.status,
            "rejection_reason": self.place.rejection_reason,
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
            "region": region_val,
            "district": district_val,
            "metro": self.place.metro,
            "address": self.place.address,
            "lat": "" if self.place.lat is None else str(self.place.lat),
            "lng": "" if self.place.lng is None else str(self.place.lng),
            "phone1": self.place.phone1,
            "phone2": self.place.phone2,
            "phone3": self.place.phone3,
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

    def _admin_event_change_payload(self, event=None, **overrides):
        event = event or Event.objects.create(
            name="Admin Event",
            name_az="Admin Event",
            category="EDU",
            start_datetime=timezone.now() + timedelta(days=2),
            end_datetime=timezone.now() + timedelta(days=2, hours=2),
            status=Event.STATUS_DRAFT,
        )
        data = {
            "owner": str(event.owner_id or ""),
            "related_place": str(event.related_place_id or ""),
            "name": event.name,
            "slug": event.slug,
            "category": event.category_id or "",
            "name_az": event.name_az,
            "name_ru": event.name_ru,
            "name_en": event.name_en,
            "description_az": event.description_az,
            "description_ru": event.description_ru,
            "description_en": event.description_en,
            "start_datetime": "" if event.start_datetime is None else timezone.localtime(event.start_datetime).strftime(EventAdminForm.PICKER_DATETIME_FORMAT),
            "end_datetime": "" if event.end_datetime is None else timezone.localtime(event.end_datetime).strftime(EventAdminForm.PICKER_DATETIME_FORMAT),
            "age_from": "" if event.age_from is None else str(event.age_from),
            "age_to": "" if event.age_to is None else str(event.age_to),
            "price_text": event.price_text,
            "address": event.address,
            "phone": event.phone,
            "instagram": event.instagram,
            "moderation_note": event.moderation_note,
            "status": event.status,
            "published_at_0": "" if event.published_at is None else timezone.localtime(event.published_at).strftime("%Y-%m-%d"),
            "published_at_1": "" if event.published_at is None else timezone.localtime(event.published_at).strftime("%H:%M:%S"),
            "rejection_reason": event.rejection_reason,
            "gallery-TOTAL_FORMS": "0",
            "gallery-INITIAL_FORMS": "0",
            "gallery-MIN_NUM_FORMS": "0",
            "gallery-MAX_NUM_FORMS": "10",
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

    def test_admin_navigation_pending_count_uses_only_ownership_requests(self):
        Place.objects.create(
            name="Pending Nav Place",
            name_ru="Pending Nav Place",
            category="EDU",
            is_active=False,
            status=Place.STATUS_PENDING,
        )
        Event.objects.create(
            name="Pending Nav Event",
            name_ru="Pending Nav Event",
            description_ru="Тестовое pending-мероприятие для проверки счётчика в меню админки.",
            category="EDU",
            start_datetime=timezone.now() + timedelta(days=3),
            end_datetime=timezone.now() + timedelta(days=3, hours=2),
            status=Event.STATUS_PENDING,
        )

        response = self.client.get("/ru/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "На рассмотрении: 1")
        self.assertContains(response, "Заявки на владение кружком (на рассмотрении: 1)")
        self.assertNotContains(response, "На рассмотрении: 3")
        self.assertNotContains(response, "Заявки на владение кружком (на рассмотрении: 3)")

    def test_admin_index_dashboard_summary_uses_real_database_counts(self):
        Place.objects.create(
            name="Pending Summary Club",
            name_ru="Pending Summary Club",
            description_ru=(
                "Достаточно длинное описание для проверки дашборда админки и связи карточек сайта с базой данных."
            ),
            category="EDU",
            age_from=7,
            age_to=12,
            district="Baku",
            address="Summary street 10",
            phone1="+994501234567",
            schedule="Mon-Fri 15:00-18:00",
            price_from=90,
            price_to=120,
            is_active=False,
            status=Place.STATUS_PENDING,
        )
        Event.objects.create(
            name="Pending Summary Event",
            name_ru="Pending Summary Event",
            description_ru="Описание тестового мероприятия для проверки pending-счётчика в админке.",
            category="EDU",
            start_datetime=timezone.now() + timedelta(days=2),
            end_datetime=timezone.now() + timedelta(days=2, hours=2),
            status=Event.STATUS_PENDING,
        )
        PlaceReview.objects.create(
            place=self.place,
            user=self.owner_user,
            rating=4,
            text="Этот отзыв создан для проверки блока модерации на главной странице админки.",
            status=PlaceReview.STATUS_PENDING,
            is_approved=False,
        )

        response = self.client.get("/ru/admin/")
        content = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)
        self.assertIn('>2</span>\n                    <p class="km-stat-label">Постоянных мест</p>', content)
        self.assertIn('>0</span>\n                    <p class="km-stat-label">Опубликовано мест</p>', content)
        self.assertIn('>1</span>\n                        <p class="km-stat-label">Места на проверке</p>', content)
        self.assertIn('>1</span>\n                        <p class="km-stat-label">Мероприятия на проверке</p>', content)
        self.assertIn('>1</span>\n                        <p class="km-stat-label">Отзывы на проверке</p>', content)
        self.assertIn('>1</span>\n                        <p class="km-stat-label">Заявки владельцев</p>', content)
        self.assertIn('>2</span>\n                    <p class="km-stat-label">Всего пользователей</p>', content)
        self.assertContains(response, '/admin/catalog_moderation/moderationplace/', html=False)
        self.assertContains(response, '/admin/catalog/place/?is_temporary__exact=0" class="km-stat-card km-stat-card--neutral"', html=False)
        self.assertContains(response, '/admin/catalog/place/?is_temporary__exact=0&amp;status__exact=published" class="km-stat-card km-stat-card--good"', html=False)
        self.assertContains(response, '/admin/catalog_moderation/moderationevent/', html=False)
        self.assertContains(response, '/admin/catalog/event/?status__exact=published" class="km-stat-card km-stat-card--info"', html=False)
        self.assertContains(response, '/admin/catalog_moderation/moderationreview/', html=False)
        self.assertContains(response, '/admin/catalog/placeownershiprequest/?status__exact=PENDING', html=False)
        self.assertContains(response, '/admin/catalog/siteregistereduser/" class="km-stat-card km-stat-card--neutral"', html=False)

    def test_admin_language_switcher_uses_language_specific_next_urls(self):
        response = self.client.get("/ru/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="language" value="ru"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/ru/admin/"', html=False)
        self.assertContains(response, 'name="language" value="az"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/admin/"', html=False)
        self.assertContains(response, 'name="language" value="en"', html=False)
        self.assertContains(response, 'name="next" value="http://testserver/en/admin/"', html=False)

    def test_admin_place_changelist_renders_search_suggestions_hook(self):
        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-search-suggest-root', html=False)
        self.assertContains(
            response,
            f'data-suggestions-url="{reverse("admin:catalog_place_search_suggestions")}"',
            html=False,
        )
        self.assertContains(response, 'id="place-search-suggestions"', html=False)

    def test_admin_place_search_suggestions_returns_matching_places(self):
        Place.objects.create(
            name="Robot Academy",
            name_ru="Robot Academy",
            category="TECH",
            address="Baku, Tech street 1",
            phone1="+994551112233",
            owner=self.owner_user,
            is_active=True,
        )

        response = self.client.get(
            reverse("admin:catalog_place_search_suggestions"),
            {"q": "Robot"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["results"])
        self.assertEqual(payload["results"][0]["label"], "Robot Academy")
        self.assertIn("Baku, Tech street 1", payload["results"][0]["meta"])

    def test_admin_place_changelist_renders_filter_select_options(self):
        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-field="category"', html=False)
        self.assertContains(response, 'data-field="status"', html=False)
        self.assertContains(response, "Образование")
        self.assertContains(response, "На рассмотрении")

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
        self.assertContains(response, "Статистика")
        self.assertContains(response, "/ru/catalog/")
        self.assertContains(response, "place_open")

    @patch("catalog.services.admin_analytics.build_google_analytics_context")
    def test_admin_site_analytics_page_uses_new_dashboard_layout_and_period_fallback(self, ga4_context_mock):
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

        PlaceReview.objects.create(
            place=self.place,
            user=self.owner_user,
            rating=5,
            text="Отзывы нужны для карточки состояния каталога.",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )

        response_week = self.client.get(reverse("admin:catalog_siteanalytics_changelist"), {"period": 7})
        response_fallback = self.client.get(reverse("admin:catalog_siteanalytics_changelist"), {"period": 999})
        week_content = response_week.content.decode("utf-8")
        fallback_content = response_fallback.content.decode("utf-8")

        self.assertEqual(response_week.status_code, 200)
        self.assertContains(response_week, 'class="km-statistics-page"', html=False)
        self.assertContains(response_week, 'data-period="7"', html=False)
        self.assertContains(response_week, 'data-kpi="unique_sessions"', html=False)
        self.assertRegex(week_content, r'data-kpi-value="unique_sessions">\s*14\s*<')
        self.assertRegex(week_content, r'data-kpi-value="sessions">\s*18\s*<')
        self.assertRegex(week_content, r'data-kpi-value="page_views">\s*42\s*<')
        self.assertContains(response_week, "Популярные страницы GA4")
        self.assertContains(response_week, "/ru/catalog/")
        self.assertContains(response_week, "place_open")

        self.assertEqual(response_fallback.status_code, 200)
        self.assertContains(response_fallback, 'data-period="30"', html=False)
        self.assertRegex(fallback_content, r'data-kpi-value="unique_sessions">\s*40\s*<')

    @patch("catalog.services.admin_analytics.build_google_analytics_context")
    def test_admin_site_analytics_page_shows_empty_ga_blocks_without_local_fallback(self, ga4_context_mock):
        ga4_context_mock.return_value = self._ga4_disabled_context()

        response = self.client.get(reverse("admin:catalog_siteanalytics_changelist"), {"period": 30})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GA4 пока не вернул событийные данные.")
        self.assertContains(response, "GA4 пока не вернул данные по страницам.")

    @patch("catalog.services.admin_analytics.build_google_analytics_context")
    def test_admin_site_analytics_page_does_not_create_demo_places(self, ga4_context_mock):
        ga4_context_mock.return_value = self._ga4_disabled_context()
        before_count = Place.objects.count()

        response = self.client.get(reverse("admin:catalog_siteanalytics_changelist"), {"period": 30})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Place.objects.count(), before_count)
        self.assertFalse(Place.objects.filter(slug__startswith="club-in-").exists())

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
        self.assertContains(response, "Статистика")
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
        self.assertContains(response, "Выберите карточки, чтобы действия стали доступны.")
        self.assertContains(response, 'data-action="move_selected_to_deleted"', html=False)
        self.assertContains(response, 'data-action="restore_selected"', html=False)
        self.assertContains(response, "Все на странице")
        self.assertContains(response, "Снять выбор")
        self.assertContains(response, "Опубликованы")
        self.assertContains(response, "Черновики")
        self.assertContains(response, 'href="?status__exact=draft"', html=False)
        self.assertContains(response, "В удалённых")
        self.assertContains(response, "Без координат")
        self.assertContains(response, reverse("admin:catalog_place_delete", args=[self.place.id]))
        self.assertContains(response, reverse("admin:catalog_place_toggle_publication", args=[self.place.id]))

        deleted_response = self.client.get(
            reverse("admin:catalog_place_changelist"),
            data={"deleted_state": "deleted"},
        )
        self.assertContains(deleted_response, reverse("admin:catalog_place_restore", args=[deleted_place.id]))
        self.assertContains(response, "km-place-row-actions")
        self.assertContains(response, "В удалённые")
        self.assertContains(response, "Восстановить")
        self.assertContains(response, "place-admin-dashboard")
        self.assertContains(response, "admin/css/pages/kidsmap_changelist.css")

    def test_event_admin_changelist_shows_bulk_bar_and_visibility_actions(self):
        response = self.client.get(reverse("admin:catalog_event_changelist"))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertTrue("Мероприятия" in content or "Tədbirlər" in content)
        self.assertContains(response, "km-place-bulk-bar")
        self.assertContains(response, 'data-action="mark_published"', html=False)
        self.assertContains(response, 'data-action="mark_draft"', html=False)
        self.assertContains(response, 'data-action="mark_pending"', html=False)

    def test_event_admin_bulk_publish_action_updates_status(self):
        event = Event.objects.create(
            name="Draft Event",
            name_az="Draft Event",
            category="EDU",
            status=Event.STATUS_DRAFT,
        )

        response = self.client.post(
            reverse("admin:catalog_event_changelist"),
            data={
                "action": "mark_published",
                "_selected_action": [str(event.pk)],
                "index": "0",
                "select_across": "0",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.STATUS_PUBLISHED)
        self.assertIsNotNone(event.published_at)

    def test_place_admin_changelist_uses_compact_search_panel(self):
        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "place-admin-dashboard__search-form")
        self.assertContains(response, "Название места...")
        self.assertContains(response, "Ищет по названию места")
        self.assertContains(response, "Искать")
        self.assertContains(response, "Категория")
        self.assertContains(response, "Регион / район")
        self.assertContains(response, "Статус")
        self.assertContains(response, "карточка")
        self.assertNotContains(response, 'id="toolbar"', html=False)

    def test_place_admin_changelist_searches_by_azerbaijani_name(self):
        Place.objects.create(
            name="English fallback",
            name_az="Balaca Rəssamlar Studiyası",
            name_ru="Студия маленьких художников",
            category="ART",
            is_active=True,
        )

        response = self.client.get(reverse("admin:catalog_place_changelist"), data={"q": "Rəssamlar"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Balaca Rəssamlar Studiyası")
        self.assertNotContains(response, "Кружок для модерации")

    def test_place_admin_changelist_shows_stats_and_quick_filter_counts(self):
        Place.objects.create(
            name="Pending place",
            name_ru="На модерации",
            category="EDU",
            status=Place.STATUS_PENDING,
            is_active=False,
        )
        Place.objects.create(
            name="No coordinates place",
            name_ru="Без координат",
            category="ART",
            is_active=True,
        )

        response = self.client.get(reverse("admin:catalog_place_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Статистика мест")
        self.assertContains(response, "place-admin-dashboard__stat-card")
        self.assertContains(response, "Фильтры")
        self.assertContains(response, "place-admin-dashboard__quick-filter")
        self.assertContains(response, "Ещё ▾")

    def test_place_admin_change_form_shows_coordinate_refresh_button(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сохранить и рассчитать координаты")
        self.assertContains(response, "_refresh_coordinates_from_address")

    def test_place_admin_change_form_shows_all_saved_phone_numbers(self):
        self.place.phone1 = "+994501112233"
        self.place.phone2 = "+994551112233"
        self.place.phone3 = "+994701112233"
        self.place.save(update_fields=["phone1", "phone2", "phone3"])

        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="phone1"', html=False)
        self.assertContains(response, 'name="phone2"', html=False)
        self.assertContains(response, 'name="phone3"', html=False)
        self.assertContains(response, 'value="+994 50 111 22 33"', html=False)
        self.assertContains(response, 'value="+994 55 111 22 33"', html=False)
        self.assertContains(response, 'value="+994 70 111 22 33"', html=False)
        self.assertContains(response, "Добавить номер")
        self.assertContains(response, 'data-km-phone-remove', count=2, html=False)

    def test_place_admin_can_add_change_and_delete_phone_numbers(self):
        self.place.phone1 = "+994501112233"
        self.place.phone2 = "+994551112233"
        self.place.phone3 = ""
        self.place.save(update_fields=["phone1", "phone2", "phone3"])

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data=self._admin_place_change_payload(
                phone1="+994 50 999 88 77",
                phone2="",
                phone3="070 333 22 11",
                _save_draft="1",
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        if response.context and response.context.get("adminform"):
            self.assertFalse(response.context["adminform"].form.errors, response.context["adminform"].form.errors)
        self.place.refresh_from_db()
        self.assertEqual(self.place.phone1, "+994509998877")
        self.assertEqual(self.place.phone2, "")
        self.assertEqual(self.place.phone3, "+994703332211")

    def test_place_admin_change_form_shows_public_site_link_for_published_place(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Публичная страница")
        self.assertContains(response, "Открыть карточку на сайте")
        self.assertContains(response, f'href="http://testserver/ru/place/{self.place.id}-', html=False)

    def test_place_admin_change_form_uses_readonly_service_dates_instead_of_raw_datetime_widgets(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Проверено модератором")
        self.assertContains(response, "Дата публикации")
        self.assertNotContains(response, "Информация проверена")
        self.assertNotContains(response, 'name="last_verified_at_0"', html=False)
        self.assertNotContains(response, 'name="last_verified_at_1"', html=False)
        self.assertNotContains(response, 'name="published_at_0"', html=False)
        self.assertNotContains(response, 'name="published_at_1"', html=False)

    def test_place_publish_timestamp_is_preserved_after_unpublish_and_draft_save(self):
        initial_published_at = timezone.now() - timedelta(days=2)
        self.place.published_at = initial_published_at
        self.place.status = Place.STATUS_PUBLISHED
        self.place.is_active = True
        self.place.save(update_fields=["published_at", "status", "is_active", "updated_at"])

        unpublish_response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data={**self._admin_place_change_payload(), "_unpublish_place": "1"},
            follow=True,
        )
        self.assertEqual(unpublish_response.status_code, 200)

        self.place.refresh_from_db()
        self.assertEqual(self.place.published_at, initial_published_at)

        draft_response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data={**self._admin_place_change_payload(), "_save_draft": "1"},
            follow=True,
        )
        self.assertEqual(draft_response.status_code, 200)

        self.place.refresh_from_db()
        self.assertEqual(self.place.published_at, initial_published_at)

    def test_place_first_verification_timestamp_is_preserved(self):
        first_verified_at = timezone.now() - timedelta(days=1)
        self.place.is_verified = True
        self.place.last_verified_at = first_verified_at
        self.place.save(update_fields=["is_verified", "last_verified_at", "updated_at"])

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data={**self._admin_place_change_payload(), "is_verified": "on", "_save": "1"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.last_verified_at, first_verified_at)

    def test_place_admin_change_form_hides_public_site_button_for_unpublished_place(self):
        draft_place = Place.objects.create(
            name="Draft admin preview",
            name_ru="Черновик для админки",
            category="ART",
            is_active=False,
            status=Place.STATUS_DRAFT,
        )

        response = self.client.get(reverse("admin:catalog_place_change", args=[draft_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Публичная страница")
        self.assertContains(response, "Сначала опубликуйте карточку")
        self.assertNotContains(response, "Открыть карточку на сайте")

    def test_published_place_with_test_content_is_clearly_hidden_from_public_catalog(self):
        hidden_place = create_quality_place(
            name="Hidden demo place",
            name_ru="Скрытая демо-карточка",
            phone1="+994501234567",
            lat=40.3754,
            lng=49.8327,
        )

        response = self.client.get(reverse("admin:catalog_place_change", args=[hidden_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Скрыто с сайта")
        self.assertNotContains(response, "Открыть карточку на сайте")

    def test_place_admin_change_form_uses_step_layout(self):
        response = self.client.get(f"{reverse('admin:catalog_place_add')}?type=permanent")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-form-page")
        self.assertContains(response, "km-place-form-steps")
        self.assertContains(response, "km-place-form-sidebar")
        self.assertContains(response, "data-place-accordion-collapse-all")
        self.assertContains(response, "data-place-accordion-expand-all")
        self.assertContains(response, "data-place-section-toggle")
        self.assertContains(response, "data-place-accordion-key")
        self.assertContains(response, "Фото")
        self.assertContains(response, "Главное фото")
        self.assertContains(response, "Дополнительные фотографии")
        self.assertContains(response, "data-gallery-root")
        self.assertContains(response, "Сводка карточки")
        self.assertContains(response, "Черновик")
        self.assertContains(response, "Сначала название и описание карточки, затем категория и подкатегория.")
        self.assertContains(response, "Цена и возраст")
        self.assertContains(response, 'data-tariff-input=""', html=False)
        self.assertNotContains(response, "URL-слаг")
        self.assertNotContains(response, "Временное мероприятие")
        self.assertContains(response, "km-place-progress-config")
        self.assertContains(response, "data-progress-pct")
        self.assertContains(response, "data-rejected-status")
        self.assertContains(response, "Импорт из JSON")
        self.assertContains(response, "data-place-json-import-open")
        self.assertContains(response, "Инструкция для ChatGPT")
        self.assertContains(response, "data-place-json-prompt-copy")
        self.assertContains(response, "Инструкция для создания JSON")
        self.assertContains(response, "data-place-json-prompt-input")
        self.assertContains(response, "JSON и примечание")
        self.assertContains(response, "admin/js/kidsmap_place_json_import.js")

    def test_place_admin_schedule_error_identifies_day_and_reason(self):
        invalid_schedule = json.dumps(
            [
                {
                    "weekday": "mon",
                    "is_closed": False,
                    "is_24_hours": False,
                    "intervals": [{"start": "18:00", "end": "09:00"}],
                },
                *[
                    {"weekday": weekday, "is_closed": True, "is_24_hours": False, "intervals": []}
                    for weekday in ("tue", "wed", "thu", "fri", "sat", "sun")
                ],
            ]
        )
        payload = self._admin_place_change_payload(structured_schedule=invalid_schedule)
        payload["_save_draft"] = "1"

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            payload,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Изменения не сохранены")
        self.assertContains(response, "Расписание: Понедельник")
        self.assertContains(response, "Интервал не может переходить через полночь")
        self.assertContains(response, "Исправить")
        self.assertContains(response, 'href="#admin-place-schedule-row-mon"', html=False)
        self.assertContains(response, 'id="admin-place-schedule-row-mon"', html=False)
        self.assertContains(response, "km-schedule-editor__row has-errors", html=False)

    def test_place_admin_saves_valid_structured_schedule(self):
        valid_schedule = json.dumps(
            [
                {
                    "weekday": "mon",
                    "is_closed": False,
                    "is_24_hours": False,
                    "intervals": [{"start": "09:00", "end": "18:00"}],
                },
                *[
                    {"weekday": weekday, "is_closed": True, "is_24_hours": False, "intervals": []}
                    for weekday in ("tue", "wed", "thu", "fri", "sat", "sun")
                ],
            ]
        )
        payload = self._admin_place_change_payload(structured_schedule=valid_schedule)
        payload["_save_draft"] = "1"

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            payload,
        )

        self.assertEqual(response.status_code, 302)
        monday = PlaceScheduleDay.objects.get(place=self.place, weekday="mon")
        self.assertFalse(monday.is_closed)
        interval = monday.intervals.get()
        self.assertEqual(interval.start_time.strftime("%H:%M"), "09:00")
        self.assertEqual(interval.end_time.strftime("%H:%M"), "18:00")

    def test_place_admin_add_form_hides_change_only_inlines_and_collapses_system_fields(self):
        response = self.client.get(reverse("admin:catalog_place_add"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="reviews"', html=False)
        self.assertNotContains(response, 'id="audit"', html=False)
        self.assertNotContains(response, 'name="reviews-TOTAL_FORMS"', html=False)
        self.assertNotContains(response, 'name="change_audits-TOTAL_FORMS"', html=False)
        self.assertContains(response, "Главное фото")
        self.assertContains(response, "Дополнительные фотографии")
        self.assertContains(response, "data-gallery-root")
        self.assertContains(response, 'name="gallery-TOTAL_FORMS"', html=False)
        self.assertContains(response, "Системные поля")
        self.assertContains(response, "Создание новой карточки")

    def test_place_admin_can_save_place_as_draft_and_continue_later(self):
        payload = self._admin_place_change_payload()
        payload["_save_draft"] = "1"

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data=payload,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("admin:catalog_place_change", args=[self.place.id]))
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, Place.STATUS_DRAFT)
        self.assertFalse(self.place.is_active)
        self.assertIsNone(self.place.published_at)

    def test_place_admin_saves_pricing_plans_from_change_form(self):
        pricing_plans = [
            {
                "lesson_format": "group",
                "payment_type": "per_month",
                "sessions_per_month": 12,
                "price": "120",
                "currency": "AZN",
                "title_az": "Aylıq abonement",
                "is_active": True,
            },
            {
                "lesson_format": "individual",
                "payment_type": "per_lesson",
                "price": "40",
                "currency": "AZN",
                "is_active": True,
            },
        ]
        payload = self._admin_place_change_payload(
            pricing_plans=json.dumps(pricing_plans),
            _save_draft="1",
        )

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data=payload,
        )

        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertEqual(len(self.place.pricing_plans), 2)
        self.assertEqual(self.place.pricing_plans[0]["price"], "120.00")
        self.assertEqual(self.place.pricing_plans[1]["price"], "40.00")

    def test_place_admin_saves_gallery_photo_with_draft(self):
        payload = self._admin_place_change_payload(
            **{
                "gallery-TOTAL_FORMS": "1",
                "gallery-0-order": "1",
                "_save_draft": "1",
            }
        )
        photo = SimpleUploadedFile(
            "gallery.gif",
            (
                b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00"
                b"\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00"
                b"\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
            ),
            content_type="image/gif",
        )

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data={**payload, "gallery-0-image": photo},
        )

        self.assertEqual(response.status_code, 302)
        saved_photo = PlacePhoto.objects.get(place=self.place)
        self.assertEqual(saved_photo.order, 1)
        self.assertTrue(saved_photo.image.name.startswith("places/gallery/gallery"))
        self.assertTrue(saved_photo.image.name.endswith(".gif"))

    def test_place_admin_can_save_an_empty_new_place_as_draft(self):
        response = self.client.post(
            f"{reverse('admin:catalog_place_add')}?type=permanent",
            data={
                "_save_draft": "1",
                "pricing_plans": "[]",
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
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            list(Place.objects.filter(status=Place.STATUS_DRAFT).values_list("name", flat=True)),
            ["Черновик без названия"],
        )
        draft = Place.objects.get(name="Черновик без названия")
        self.assertEqual(draft.name, "Черновик без названия")
        self.assertEqual(draft.status, Place.STATUS_DRAFT)
        self.assertFalse(draft.is_active)
        self.assertIsNotNone(draft.category_id)

    def test_place_admin_change_form_shows_visibility_controls(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Видимость на сайте")
        self.assertContains(response, "Снять с публикации")

    def test_place_admin_can_unpublish_place_from_change_form(self):
        payload = self._admin_place_change_payload()
        payload["_unpublish_place"] = "1"

        response = self.client.post(
            reverse("admin:catalog_place_change", args=[self.place.id]),
            data=payload,
        )

        self.assertEqual(response.status_code, 302)
        self.place.refresh_from_db()
        self.assertFalse(self.place.is_active)
        self.assertEqual(self.place.status, Place.STATUS_DRAFT)

    def test_place_admin_can_toggle_publication_from_changelist(self):
        published_place = create_quality_place(
            name="Toggle publication place",
            name_ru="Место для переключения публикации",
            status=Place.STATUS_PUBLISHED,
            is_active=True,
        )
        response = self.client.post(
            reverse("admin:catalog_place_toggle_publication", args=[published_place.id]),
            HTTP_REFERER=reverse("admin:catalog_place_changelist"),
        )

        self.assertEqual(response.status_code, 302)
        published_place.refresh_from_db()
        self.assertFalse(published_place.is_active)
        self.assertEqual(published_place.status, Place.STATUS_DRAFT)

    def test_place_admin_can_publish_ready_place_from_change_form(self):
        ready_place = create_quality_place(
            name="Ready Admin Place",
            name_ru="Готовое место",
            status=Place.STATUS_DRAFT,
            is_active=False,
            published_at=None,
        )
        payload = self._admin_place_change_payload(
            name=ready_place.name,
            name_ru=ready_place.name_ru,
            name_az=ready_place.name_az,
            name_en=ready_place.name_en,
            description_ru=ready_place.description_ru,
            description_az=ready_place.description_az,
            description_en=ready_place.description_en,
            category=ready_place.category_id or "",
            subcategory=ready_place.subcategory_id or "",
            is_temporary="on" if ready_place.is_temporary else "",
            is_active="on" if ready_place.is_active else "",
            is_verified="on" if ready_place.is_verified else "",
            status=ready_place.status,
            rejection_reason=ready_place.rejection_reason,
            owner=str(ready_place.owner_id or ""),
            likes_count=str(ready_place.likes_count or 0),
            age_from="" if ready_place.age_from is None else str(ready_place.age_from),
            age_to="" if ready_place.age_to is None else str(ready_place.age_to),
            price_from="" if ready_place.price_from is None else str(ready_place.price_from),
            price_to="" if ready_place.price_to is None else str(ready_place.price_to),
            price_per_lesson="" if ready_place.price_per_lesson is None else str(ready_place.price_per_lesson),
            price_per_month="" if ready_place.price_per_month is None else str(ready_place.price_per_month),
            price_per_8_lessons="" if ready_place.price_per_8_lessons is None else str(ready_place.price_per_8_lessons),
            lesson_duration_minutes="" if ready_place.lesson_duration_minutes is None else str(ready_place.lesson_duration_minutes),
            district=ready_place.district,
            metro=ready_place.metro,
            address=ready_place.address,
            lat="" if ready_place.lat is None else str(ready_place.lat),
            lng="" if ready_place.lng is None else str(ready_place.lng),
            phone1=ready_place.phone1,
            instagram=ready_place.instagram,
            website=ready_place.website,
            schedule=ready_place.schedule,
            extra_conditions=ready_place.extra_conditions,
            additional_info=ready_place.additional_info,
        )
        payload["_publish_place"] = "1"

        with patch("catalog.domain_admin.place.place_quality_check") as quality_check_mock:
            quality_check_mock.return_value.is_ready = True
            response = self.client.post(
                reverse("admin:catalog_place_change", args=[ready_place.id]),
                data=payload,
            )

        self.assertEqual(response.status_code, 302)
        ready_place.refresh_from_db()
        self.assertTrue(ready_place.is_active)
        self.assertEqual(ready_place.status, Place.STATUS_PUBLISHED)
        self.assertIsNotNone(ready_place.published_at)

    def test_place_admin_change_form_keeps_gallery_reviews_and_audit_sections(self):
        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дополнительные фотографии")
        self.assertContains(response, "Отзывы по кружкам")
        self.assertContains(response, "История изменений карточек")

    def test_place_admin_review_inline_hides_anonymous_and_shows_readable_author(self):
        PlaceReview.objects.create(
            place=self.place,
            user=self.owner_user,
            author_name="Leyla",
            rating=5,
            text="Подробный отзыв для проверки компактного inline-блока в админке.",
            is_anonymous=True,
        )

        response = self.client.get(reverse("admin:catalog_place_change", args=[self.place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Leyla")
        self.assertContains(response, "@owner_adminux")
        self.assertContains(response, "owner-adminux@example.com")
        self.assertContains(response, "column-review_author_display")
        self.assertNotContains(response, "Анонимно")

    def test_event_admin_change_form_uses_step_layout(self):
        response = self.client.get(reverse("admin:catalog_event_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-place-form-page")
        self.assertContains(response, "km-place-form-steps")
        self.assertContains(response, "km-place-form-sidebar")
        self.assertContains(response, "Новое мероприятие")
        self.assertContains(response, "Сохранить и продолжить")
        self.assertContains(response, "Сохранить черновик")
        self.assertNotContains(response, "Сохранить и выйти")
        self.assertContains(response, "Черновик")
        self.assertContains(response, "km-admin-progress-config")
        self.assertContains(response, "data-km-admin-form")

    def test_event_admin_can_save_draft_and_continue_later(self):
        event = Event.objects.create(
            name="Draft Admin Event",
            name_az="Draft Admin Event",
            category="EDU",
            description_az="Описание",
            start_datetime=timezone.now() + timedelta(days=3),
            end_datetime=timezone.now() + timedelta(days=3, hours=1),
            status=Event.STATUS_PENDING,
            published_at=timezone.now(),
        )
        payload = self._admin_event_change_payload(event)
        payload["_save_draft"] = "1"

        response = self.client.post(
            reverse("admin:catalog_event_change", args=[event.id]),
            data=payload,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("admin:catalog_event_change", args=[event.id]))
        event.refresh_from_db()
        self.assertEqual(event.status, Event.STATUS_DRAFT)
        self.assertIsNone(event.published_at)

    def test_event_admin_can_publish_from_change_form(self):
        event = Event.objects.create(
            name="Publish Admin Event",
            name_az="Publish Admin Event",
            category="EDU",
            description_az="Описание для публикации",
            start_datetime=timezone.now() + timedelta(days=5),
            end_datetime=timezone.now() + timedelta(days=5, hours=2),
            status=Event.STATUS_DRAFT,
            published_at=None,
        )
        payload = self._admin_event_change_payload(event)
        payload["_publish_event"] = "1"

        response = self.client.post(
            reverse("admin:catalog_event_change", args=[event.id]),
            data=payload,
        )

        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.STATUS_PUBLISHED)
        self.assertIsNotNone(event.published_at)

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
        self.assertContains(response, "Телефон")
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
            status=PlaceReview.STATUS_PENDING,
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
            status=PlaceReview.STATUS_PENDING,
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
        self.assertNotContains(response, 'name="_addanother"')
        self.assertNotContains(response, 'name="_continue"')
        self.assertContains(response, "km-admin-user-submit")
        self.assertContains(response, "km-admin-user-submit__btn--secondary")

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

class TestSiteGalleryImageAdminMedia(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("media_admin", "media@example.com", "password")
        self.client.force_login(self.admin_user)

    def test_ajax_delete_main_image_clears_uploaded_site_settings_file(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            site = SiteSettings.get_solo()
            site.site_background_image = SimpleUploadedFile(
                "background.jpg",
                b"image-content",
                content_type="image/jpeg",
            )
            site.save()
            self.assertTrue(site.site_background_image)

            response = self.client.post(
                reverse("admin:catalog_sitegalleryimage_ajax_delete_main_image"),
                {"field": "site_background_image"},
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {"success": True, "field": "site_background_image", "deleted": True},
            )
            site.refresh_from_db()
            self.assertFalse(site.site_background_image)

class TestCategoryAdminFormLayout(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(
            username="category_admin_ui",
            email="category-admin-ui@example.com",
            password="StrongPass123!!",
        )

    def setUp(self):
        self.client.force_login(self.superuser)

    def test_category_add_form_uses_two_column_layout(self):
        response = self.client.get(reverse("admin:catalog_category_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-category-form-page")
        self.assertContains(response, "km-category-card__step")
        self.assertContains(response, "km-category-grid")
        self.assertContains(response, 'placeholder="Например: education"', html=False)
        self.assertContains(response, 'name="_save"', html=False)
        self.assertContains(response, 'name="_addanother"', html=False)
        self.assertContains(response, 'name="_continue"', html=False)
        self.assertContains(response, "data-km-category-icon-preview")
        self.assertContains(response, 'name="icon_upload"', html=False)
        self.assertContains(response, 'type="file"', html=False)
        self.assertContains(response, 'enctype="multipart/form-data"', html=False)
        self.assertContains(response, "km-category-actions-card")
        self.assertContains(response, 'name="is_active"', html=False)

    def test_category_change_form_keeps_inline_section_and_actions(self):
        category = Category.objects.create(
            code="UIEDU",
            name="Education",
            name_az="Təhsil",
            name_ru="Образование",
            name_en="Education",
            icon="fas fa-graduation-cap",
        )

        response = self.client.get(reverse("admin:catalog_category_change", args=[category.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-category-form-page")
        self.assertContains(response, "km-category-inline-card")
        self.assertContains(response, "Подкатегории")
        self.assertContains(response, 'name="_save"', html=False)
        self.assertContains(response, 'name="_addanother"', html=False)
        self.assertContains(response, 'name="_continue"', html=False)

    def test_category_add_form_saves_uploaded_icon_into_media_and_sets_icon_url(self):
        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse("admin:catalog_category_add"),
                    data={
                        "code": "UPLOADCAT",
                        "name": "",
                        "name_az": "Kateqoriya",
                        "name_ru": "Категория",
                        "name_en": "Category",
                        "order": "0",
                        "icon": "",
                        "icon_upload": SimpleUploadedFile(
                            "category-icon.svg",
                            b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'></svg>",
                            content_type="image/svg+xml",
                        ),
                        "_save": "Save",
                    },
                )

        self.assertEqual(response.status_code, 302)
        category = Category.objects.get(pk="UPLOADCAT")
        self.assertTrue(category.icon.startswith("/media/cat_icons/"))
        self.assertTrue(category.icon.endswith(".svg"))

    def test_category_icon_rejects_raster_with_wrong_dimensions(self):
        from PIL import Image

        image_bytes = BytesIO()
        Image.new("RGBA", (256, 256), "#ffffff").save(image_bytes, format="PNG")
        response = self.client.post(
            reverse("admin:catalog_category_add"),
            data={
                "code": "BADICON",
                "name_az": "Kateqoriya",
                "name_ru": "Категория",
                "name_en": "Category",
                "order": "0",
                "icon_upload": SimpleUploadedFile("too-small.png", image_bytes.getvalue(), content_type="image/png"),
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PNG и WebP должны быть ровно 512×512 px.")
        self.assertFalse(Category.objects.filter(pk="BADICON").exists())

    def test_subcategory_form_saves_its_own_uploaded_icon(self):
        category = Category.objects.create(code="SUBICON", name="Категория", name_az="Kateqoriya", name_ru="Категория")
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse("admin:catalog_subcategory_add"),
                data={
                    "category": category.pk,
                    "name": "Подкатегория",
                    "name_az": "Alt kateqoriya",
                    "name_ru": "Подкатегория",
                    "name_en": "Subcategory",
                    "icon_upload": SimpleUploadedFile(
                        "subcategory.svg",
                        b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'></svg>",
                        content_type="image/svg+xml",
                    ),
                    "_save": "Save",
                },
            )

        self.assertEqual(response.status_code, 302)
        subcategory = Subcategory.objects.get(name_ru="Подкатегория")
        self.assertTrue(subcategory.icon.startswith("/media/subcategory_icons/"))

    def test_category_admin_rejects_duplicate_translated_name(self):
        Category.objects.create(
            code="EXISTING-CATEGORY",
            name="Təhsil",
            name_az="Təhsil",
            name_ru="Образование",
            name_en="Education",
        )

        response = self.client.post(
            reverse("admin:catalog_category_add"),
            {
                "code": "DUPLICATE-CATEGORY",
                "name_az": "  TƏHSİL  ",
                "name_ru": "Другое название",
                "name_en": "Another name",
                "order": "1",
                "is_active": "on",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Категория с таким названием уже существует")
        self.assertFalse(Category.objects.filter(pk="DUPLICATE-CATEGORY").exists())

    def test_subcategory_admin_rejects_duplicate_name_inside_category(self):
        category = Category.objects.create(code="DUP-SUB-CAT", name="Категория")
        Subcategory.objects.create(
            category=category,
            code="existing-subcategory",
            name="Робототехника",
            name_ru="Робототехника",
        )

        response = self.client.post(
            reverse("admin:catalog_subcategory_add"),
            {
                "category": category.pk,
                "code": "duplicate-subcategory",
                "name_az": "Robototexnika",
                "name_ru": "  РОБОТОТЕХНИКА ",
                "name_en": "Robotics duplicate",
                "order": "1",
                "is_active": "on",
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Подкатегория с таким названием уже существует")
        self.assertFalse(Subcategory.objects.filter(code="duplicate-subcategory").exists())

    def test_taxonomy_toggle_restores_archived_category(self):
        category = Category.objects.create(code="RESTORE-CAT", name="Архивная категория")
        category.archive(self.superuser)

        response = self.client.post(
            reverse("admin:catalog_taxonomy_toggle_active"),
            {"obj_type": "category", "obj_id": category.pk},
        )

        self.assertEqual(response.status_code, 200)
        category.refresh_from_db()
        self.assertTrue(category.is_active)
        self.assertIsNone(category.deleted_at)

class ReviewAdminModerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")
        self.place = create_quality_place()
        self.review = PlaceReview.objects.create(
            place=self.place,
            rating=5,
            text="Test review for admin",
            status=PlaceReview.STATUS_PENDING,
            is_approved=False,
        )

    def test_approve_single_review_action(self):
        url = reverse("admin:catalog_placereview_approve", args=[self.review.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertTrue(self.review.is_approved)
        self.assertEqual(self.review.status, PlaceReview.STATUS_APPROVED)

    def test_reject_single_review_action(self):
        url = reverse("admin:catalog_placereview_reject", args=[self.review.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.review.refresh_from_db()
        self.assertFalse(self.review.is_approved)
        self.assertEqual(self.review.status, PlaceReview.STATUS_REJECTED)

    def test_change_form_injects_km_review_form_summary(self):
        url = reverse("admin:catalog_placereview_change", args=[self.review.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("km_review_form_summary", response.context)
        summary = response.context["km_review_form_summary"]
        self.assertEqual(summary["rating"], 5)
        self.assertEqual(summary["has_text"], True)

class OwnershipRequestAdminModerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@example.com", "password")
        self.client.login(username="admin", password="password")
        self.place = create_quality_place()
        self.applicant = User.objects.create_user("applicant", "app@example.com", "password")
        self.request_obj = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.applicant,
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )

    def test_approve_single_ownership_request(self):
        url = reverse("admin:catalog_placeownershiprequest_approve", args=[self.request_obj.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, PlaceOwnershipRequest.STATUS_APPROVED)

    def test_reject_single_ownership_request(self):
        url = reverse("admin:catalog_placeownershiprequest_reject", args=[self.request_obj.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, PlaceOwnershipRequest.STATUS_REJECTED)

    def test_change_form_injects_km_request_form_summary(self):
        url = reverse("admin:catalog_placeownershiprequest_change", args=[self.request_obj.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("km_request_form_summary", response.context)
        summary = response.context["km_request_form_summary"]
        self.assertTrue(summary["is_pending"])
        self.assertEqual(summary["applicant"], "app@example.com")

class UserAdminUXTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.superadmin = User.objects.create_superuser(
            username="superadmin", email="superadmin@example.com", password="password"
        )
        self.client.login(username="superadmin", password="password")

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password", first_name="Test", last_name="User"
        )
        from catalog.models.user import UserProfile, UserEmailVerification
        self.profile = UserProfile.get_or_create_for_user(self.user)
        self.profile.phone = "+994501234567"
        self.profile.save()

        UserEmailVerification.objects.create(
            user=self.user,
            email=self.user.email,
            is_verified=True,
        )

    def test_siteregistereduser_change_form_injects_km_user_form_summary(self):
        url = reverse("admin:catalog_siteregistereduser_change", args=[self.user.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("km_user_form_summary", response.context)
        
        summary = response.context["km_user_form_summary"]
        self.assertEqual(summary["full_name"], "Test User")
        self.assertEqual(summary["email"], "test@example.com")
        self.assertTrue(summary["email_verified"])
        self.assertEqual(summary["phone"], "+994501234567")
        self.assertFalse(summary["owner_workflow"]["has_requests"])
        
        content = response.content.decode("utf-8")
        self.assertIn("Email подтвержден", content)
        self.assertIn("Test User", content)
        self.assertIn("+994501234567", content)

    def test_staffaccessuser_changelist_is_compact_and_supports_role_filter(self):
        staff_user = User.objects.create_user(
            username="staff-list-user",
            email="staff-list@example.com",
            password="password",
            is_staff=True,
        )
        url = reverse("admin:catalog_staffaccessuser_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("km-staff-access-list__table", content)
        self.assertIn('name="role"', content)
        self.assertIn("Добавленные места", content)
        self.assertIn(staff_user.email, content)
        self.assertNotIn("Дата регистрации", content)

        response = self.client.get(url, {"role": "superadmin"})
        self.assertContains(response, self.superadmin.username)
        self.assertNotContains(response, staff_user.username)

    def test_superadmin_can_delete_staff_member_after_confirmation(self):
        staff_user = User.objects.create_user(
            username="staff-to-delete",
            email="staff-delete@example.com",
            password="password",
            is_staff=True,
        )
        delete_url = reverse("admin:catalog_staffaccessuser_delete", args=[staff_user.pk])

        self.assertEqual(self.client.get(delete_url).status_code, 200)
        response = self.client.post(delete_url, {"post": "yes"})

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=staff_user.pk).exists())

    def test_superadmin_cannot_delete_self_or_last_superadmin(self):
        delete_url = reverse("admin:catalog_staffaccessuser_delete", args=[self.superadmin.pk])

        response = self.client.get(delete_url)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=self.superadmin.pk).exists())

    def test_superadmin_can_create_staff_user_with_profile_fields(self):
        response = self.client.get(reverse("admin:catalog_staffaccessuser_add"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "km-user-access-page")
        self.assertContains(response, "Новый сотрудник")
        self.assertContains(response, 'name="email"', html=False)
        self.assertContains(response, 'name="admin_role"', html=False)
        self.assertContains(response, "Модератор")
        self.assertContains(response, "Контент-менеджер")
        self.assertContains(response, "Суперадмин")
        self.assertContains(response, 'name="profile-0-role"', html=False)
        self.assertNotContains(response, "Профили пользователей")

        response = self.client.post(
            reverse("admin:catalog_staffaccessuser_add"),
            data={
                "username": "new_staff_admin",
                "email": "new-staff@example.com",
                "first_name": "New",
                "last_name": "Staff",
                "password1": "StrongPass123!!",
                "password2": "StrongPass123!!",
                "admin_role": "moderator",
                "is_active": "on",
                "is_staff": "on",
                "profile-TOTAL_FORMS": "1",
                "profile-INITIAL_FORMS": "0",
                "profile-MIN_NUM_FORMS": "0",
                "profile-MAX_NUM_FORMS": "1",
                "profile-0-role": UserProfile.ROLE_USER,
                "profile-0-owner_role": UserProfile.OWNER_ROLE_MANAGER,
                "profile-0-owner_permissions_override": "[]",
                "profile-0-phone": "",
                "profile-0-gender": UserProfile.GENDER_UNSPECIFIED,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="new_staff_admin")
        self.assertTrue(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)
        self.assertEqual(created_user.email, "new-staff@example.com")
        self.assertEqual(created_user.profile.role, UserProfile.ROLE_USER)
        self.assertTrue(created_user.has_perm("catalog.change_placereview"))
        self.assertFalse(created_user.has_perm("catalog.change_place"))

    def test_staff_creation_shows_specific_validation_errors(self):
        response = self.client.post(
            reverse("admin:catalog_staffaccessuser_add"),
            data={
                "username": "ChatGPT",
                "email": "chatgpt@example.com",
                "password1": "ChatGPT123!!",
                "password2": "ChatGPT123!!",
                "admin_role": "content_manager",
                "is_active": "on",
                "is_staff": "on",
                "profile-TOTAL_FORMS": "1",
                "profile-INITIAL_FORMS": "0",
                "profile-MIN_NUM_FORMS": "0",
                "profile-MAX_NUM_FORMS": "1",
                "profile-0-role": UserProfile.ROLE_USER,
                "profile-0-owner_role": UserProfile.OWNER_ROLE_MANAGER,
                "profile-0-owner_permissions_override": "[]",
                "profile-0-phone": "",
                "profile-0-gender": UserProfile.GENDER_UNSPECIFIED,
                "_save": "Save",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Не удалось создать сотрудника.")
        self.assertContains(response, "Пароль:")
        self.assertContains(response, "слишком похож на имя пользователя")

    def test_superadmin_can_create_content_manager_and_superadmin_roles(self):
        base_payload = {
            "email": "role-staff@example.com",
            "password1": "StrongPass123!!",
            "password2": "StrongPass123!!",
            "is_active": "on",
            "is_staff": "on",
            "profile-TOTAL_FORMS": "1",
            "profile-INITIAL_FORMS": "0",
            "profile-MIN_NUM_FORMS": "0",
            "profile-MAX_NUM_FORMS": "1",
            "profile-0-role": UserProfile.ROLE_USER,
            "profile-0-owner_role": UserProfile.OWNER_ROLE_MANAGER,
            "profile-0-owner_permissions_override": "[]",
            "profile-0-phone": "",
            "profile-0-gender": UserProfile.GENDER_UNSPECIFIED,
            "_save": "Save",
        }

        response = self.client.post(
            reverse("admin:catalog_staffaccessuser_add"),
            data={
                **base_payload,
                "username": "content_manager_admin",
                "admin_role": "content_manager",
            },
        )
        self.assertEqual(response.status_code, 302)
        content_manager = User.objects.get(username="content_manager_admin")
        self.assertTrue(content_manager.is_staff)
        self.assertFalse(content_manager.is_superuser)
        self.assertTrue(content_manager.has_perm("catalog.change_place"))
        self.assertFalse(content_manager.has_perm("catalog.change_placereview"))

        response = self.client.post(
            reverse("admin:catalog_staffaccessuser_add"),
            data={
                **base_payload,
                "username": "super_role_admin",
                "email": "super-role@example.com",
                "admin_role": "superadmin",
            },
        )
        self.assertEqual(response.status_code, 302)
        super_role = User.objects.get(username="super_role_admin")
        self.assertTrue(super_role.is_staff)
        self.assertTrue(super_role.is_superuser)

    def test_non_superuser_staff_cannot_open_user_add_form(self):
        staff_user = User.objects.create_user(
            username="limited_staff",
            email="limited-staff@example.com",
            password="password",
            is_staff=True,
        )
        self.client.force_login(staff_user)

        response = self.client.get(reverse("admin:catalog_staffaccessuser_add"))

        self.assertEqual(response.status_code, 403)

class TestAdminBulkActions(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("admin_tester", "admin@example.com", "password")
        self.client.login(username="admin_tester", password="password")

    from unittest.mock import patch

    @patch("catalog.domain_admin.place.place_quality_check")
    def test_place_make_published_action(self, mock_quality):
        mock_quality.return_value.is_ready = True
        
        place1 = create_quality_place(name="Place 1", status=Place.STATUS_DRAFT)
        place2 = create_quality_place(name="Place 2", status=Place.STATUS_DRAFT)
        
        url = reverse("admin:catalog_place_changelist")
        response = self.client.post(url, {
            "action": "mark_published",
            "_selected_action": [place1.pk, place2.pk]
        })
        
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        place2.refresh_from_db()
        self.assertEqual(place1.status, Place.STATUS_PUBLISHED)
        self.assertEqual(place2.status, Place.STATUS_PUBLISHED)

    def test_place_make_draft_action(self):
        place1 = create_quality_place(name="Place 1", status=Place.STATUS_PUBLISHED)
        
        url = reverse("admin:catalog_place_changelist")
        response = self.client.post(url, {
            "action": "mark_draft",
            "_selected_action": [place1.pk]
        })
        
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        self.assertEqual(place1.status, Place.STATUS_DRAFT)

    def test_place_mark_inactive_action(self):
        place1 = create_quality_place(name="Place 1", status=Place.STATUS_PUBLISHED)
        place1.is_active = True
        place1.save()
        
        url = reverse("admin:catalog_place_changelist")
        response = self.client.post(url, {
            "action": "mark_inactive",
            "_selected_action": [place1.pk]
        })
        
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        self.assertFalse(place1.is_active)

    def test_place_mark_pending_action(self):
        place1 = create_quality_place(name="Place 1", status=Place.STATUS_DRAFT)
        
        url = reverse("admin:catalog_place_changelist")
        response = self.client.post(url, {
            "action": "mark_pending",
            "_selected_action": [place1.pk]
        })
        
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        self.assertEqual(place1.status, Place.STATUS_PENDING)

    def test_place_move_to_deleted_and_restore(self):
        place1 = create_quality_place(name="Place 1", status=Place.STATUS_PUBLISHED)
        
        url = reverse("admin:catalog_place_changelist")
        
        # Test soft delete (requires a confirmation POST, but wait, move_selected_to_deleted checks request.POST.get("post"))
        # If "post" is not in request, it returns a TemplateResponse.
        # So we must include "post": "yes"
        response = self.client.post(url, {
            "action": "move_selected_to_deleted",
            "_selected_action": [place1.pk],
            "post": "yes",
        })
        
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        self.assertTrue(place1.is_deleted)
        self.assertIsNotNone(place1.deleted_at)
        
        # Test restore
        response = self.client.post(url, {
            "action": "restore_selected",
            "_selected_action": [place1.pk]
        })
        self.assertEqual(response.status_code, 302)
        place1.refresh_from_db()
        self.assertFalse(place1.is_deleted)
        self.assertIsNone(place1.deleted_at)
        self.assertFalse(place1.is_active) # Restored places remain inactive

    def test_review_action_approve_and_reject(self):
        place = create_quality_place(name="Review Place", status=Place.STATUS_PUBLISHED)
        review1 = PlaceReview.objects.create(place=place, status=PlaceReview.STATUS_PENDING, rating=5, text="Good", session_key="session1")
        review2 = PlaceReview.objects.create(place=place, status=PlaceReview.STATUS_PENDING, rating=1, text="Bad", session_key="session2")
        
        url = reverse("admin:catalog_placereview_changelist")
        
        # Approve review1
        response = self.client.post(url, {
            "action": "approve_selected",
            "_selected_action": [review1.pk]
        })
        self.assertEqual(response.status_code, 302)
        review1.refresh_from_db()
        self.assertEqual(review1.status, PlaceReview.STATUS_APPROVED)
        
        # Reject review2
        response = self.client.post(url, {
            "action": "reject_selected",
            "_selected_action": [review2.pk]
        })
        self.assertEqual(response.status_code, 302)
        review2.refresh_from_db()
        self.assertEqual(review2.status, PlaceReview.STATUS_REJECTED)

    def test_event_make_published_and_draft_action(self):
        place = create_quality_place(name="Event Place", status=Place.STATUS_PUBLISHED)
        event1 = Event.objects.create(name="Event 1", related_place=place, category="EDU", status=Event.STATUS_DRAFT)
        event2 = Event.objects.create(name="Event 2", related_place=place, category="EDU", status=Event.STATUS_PUBLISHED)
        
        url = reverse("admin:catalog_event_changelist")
        
        # Publish event1
        response = self.client.post(url, {
            "action": "mark_published",
            "_selected_action": [event1.pk]
        })
        self.assertEqual(response.status_code, 302)
        event1.refresh_from_db()
        self.assertEqual(event1.status, Event.STATUS_PUBLISHED)
        self.assertIsNotNone(event1.published_at)

        # Draft event2
        response = self.client.post(url, {
            "action": "mark_draft",
            "_selected_action": [event2.pk]
        })
        self.assertEqual(response.status_code, 302)
        event2.refresh_from_db()
        self.assertEqual(event2.status, Event.STATUS_DRAFT)

    def test_ownership_request_approve_and_reject_action(self):
        from catalog.models.owner import PlaceOwnershipRequest
        place1 = create_quality_place(name="Owner Place 1", status=Place.STATUS_PUBLISHED)
        place2 = create_quality_place(name="Owner Place 2", status=Place.STATUS_PUBLISHED)
        user = User.objects.create_user("applicant", "app@example.com", "pass")
        req1 = PlaceOwnershipRequest.objects.create(place=place1, applicant=user, status=PlaceOwnershipRequest.STATUS_PENDING)
        req2 = PlaceOwnershipRequest.objects.create(place=place2, applicant=user, status=PlaceOwnershipRequest.STATUS_PENDING)
        
        url = reverse("admin:catalog_placeownershiprequest_changelist")
        
        # Approve req1
        response = self.client.post(url, {
            "action": "approve_requests",
            "_selected_action": [req1.pk]
        })
        self.assertEqual(response.status_code, 302)
        req1.refresh_from_db()
        self.assertEqual(req1.status, PlaceOwnershipRequest.STATUS_APPROVED)

        # Reject req2
        response = self.client.post(url, {
            "action": "reject_requests",
            "_selected_action": [req2.pk]
        })
        self.assertEqual(response.status_code, 302)
        req2.refresh_from_db()
        self.assertEqual(req2.status, PlaceOwnershipRequest.STATUS_REJECTED)

class TestAdminChangelistUI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser("admin_ui", "admin_ui@example.com", "pass")
    
    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_shared_search_panel_rendered_in_all_models(self):
        urls = [
            reverse("admin:catalog_place_changelist"),
            reverse("admin:catalog_event_changelist"),
            reverse("admin:catalog_placereview_changelist"),
            reverse("admin:catalog_placeownershiprequest_changelist"),
            reverse("admin:catalog_siteregistereduser_changelist"),
        ]
        
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # Check for the unified row search
                self.assertContains(response, "place-admin-dashboard__row-search--unified")
                # Check for the extra filters details element
                self.assertContains(response, "place-admin-dashboard__extra-filters")
                # Check for quick filters row
                self.assertContains(response, "place-admin-dashboard__row-tabs")

    def test_quick_tabs_preserves_url_parameters(self):
        from catalog.models.review import PlaceReview
        place = create_quality_place(name="Review test place")
        user = User.objects.create_user("review_user", "review@example.com", "pass")
        PlaceReview.objects.create(place=place, user=user, text="Bad text", rating=1)
        
        url = reverse("admin:catalog_placereview_changelist") + "?q=Bad&rating=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Verify that the quick tab link contains the query parameters
        self.assertContains(response, "q=Bad")
        self.assertContains(response, "rating=1")

class TestCategoryAdminHierarchy(TestCase):
    def setUp(self):
        from catalog.models.category import Subcategory
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.force_login(self.admin)
        self.category = Category.objects.create(code="TESTCAT", name_ru="Тестовая Категория")
        self.subcategory = Subcategory.objects.create(
            category=self.category,
            code="test-subcategory",
            name_ru="Тестовая Подкатегория",
        )

    def test_changelist_view_status_and_context(self):
        url = reverse("admin:catalog_category_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовая Категория")
        self.assertContains(response, "Тестовая Подкатегория")
        self.assertTemplateUsed(response, "admin/catalog/category/change_list.html")

    def test_changelist_search_filters_and_expands_parent(self):
        url = reverse("admin:catalog_category_changelist") + "?q=Тестовая Подкатегория"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовая Категория")
        self.assertContains(response, "Тестовая Подкатегория")

    def test_place_add_form_renders_subcategory_options(self):
        url = reverse("admin:catalog_place_add")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="subcategory"', html=False)
        self.assertContains(response, f'value="{self.subcategory.pk}"', html=False)
        self.assertContains(response, 'data-category="TESTCAT"', html=False)

    def test_place_add_form_renders_metro_select_options(self):
        url = reverse("admin:catalog_place_add")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="metro"', html=False)
        self.assertContains(response, 'Выберите метро', html=False)
        self.assertNotContains(response, '<input type="text" name="metro"', html=False)


class TestAdminDeleteFlows(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin_delete", "admin_delete@example.com", "pass")
        self.client.force_login(self.admin)

    def test_can_delete_ownership_request_with_audit_entries(self):
        place = create_quality_place(name="Delete ownership request place")
        applicant = User.objects.create_user("delete_req_user", "delete_req@example.com", "pass")
        request_item = PlaceOwnershipRequest.objects.create(place=place, applicant=applicant)

        response = self.client.post(
            reverse("admin:catalog_placeownershiprequest_delete", args=[request_item.pk]),
            {"post": "yes"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(PlaceOwnershipRequest.objects.filter(pk=request_item.pk).exists())

    def test_can_delete_user_with_ownership_request_audit_history(self):
        place = create_quality_place(name="Delete user place")
        target_user = User.objects.create_user("delete_target", "delete_target@example.com", "pass")
        PlaceOwnershipRequest.objects.create(place=place, applicant=target_user)

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[target_user.pk]),
            {"post": "yes"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=target_user.pk).exists())


class TestAdminSidebarStructure(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("sidebar_admin", "sidebar@example.com", "pass")
        self.client.force_login(self.admin)
        now = timezone.now()

        Place.objects.create(
            name="Visible place",
            category="EDU",
            is_active=True,
            status=Place.STATUS_PUBLISHED,
        )
        Place.objects.create(
            name="Pending place",
            category="EDU",
            is_active=False,
            status=Place.STATUS_PENDING,
        )
        Event.objects.create(
            name="Visible event",
            category="EDU",
            status=Event.STATUS_PUBLISHED,
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=2),
        )
        Event.objects.create(
            name="Pending event",
            category="EDU",
            status=Event.STATUS_PENDING,
            start_datetime=now + timedelta(days=1),
            end_datetime=now + timedelta(days=1, hours=2),
        )
        Specialist.objects.create(
            name="Visible specialist",
            slug="visible-specialist",
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
        )
        Specialist.objects.create(
            name="Pending specialist",
            slug="pending-specialist",
            status=Specialist.STATUS_PENDING,
            is_active=False,
        )

    def test_catalog_and_moderation_use_real_admin_pages_and_metrics(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'km-admin-sidebar__access-card')
        self.assertContains(response, "Постоянные места")
        self.assertContains(response, "Временные мероприятия")
        self.assertContains(response, "Специалисты")
        self.assertContains(response, "Места на проверке")
        self.assertContains(response, "Мероприятия на проверке")
        self.assertContains(response, "Специалисты на проверке")
        self.assertContains(response, "Добавить администратора")
        self.assertContains(response, "Список администраторов")
        self.assertContains(response, 'href="/admin/catalog/place/?is_temporary__exact=0"', html=False)
        self.assertContains(response, 'href="/admin/catalog/event/"', html=False)
        self.assertContains(response, 'href="/admin/catalog/specialist/"', html=False)
        self.assertContains(response, 'href="/admin/catalog_moderation/moderationplace/"', html=False)
        self.assertContains(response, 'href="/admin/catalog_moderation/moderationevent/"', html=False)
        self.assertContains(response, 'href="/admin/catalog_moderation/moderationspecialist/"', html=False)
        self.assertContains(response, 'href="/admin/catalog_moderation/moderationreview/"', html=False)
        self.assertContains(response, 'href="/admin/catalog/staffaccessuser/add/"', html=False)
        self.assertContains(response, 'href="/admin/catalog/staffaccessuser/"', html=False)
        self.assertContains(response, '>2</span>', html=False)
        self.assertContains(response, 'class="km-admin-sidebar__badge" aria-label="0">0</span>', html=False)

    def test_moderation_items_open_separate_pending_workspaces(self):
        place_url = reverse("admin:catalog_place_changelist")
        moderation_place_url = reverse("admin:catalog_moderation_moderationplace_changelist")
        event_url = reverse("admin:catalog_event_changelist")
        moderation_event_url = reverse("admin:catalog_moderation_moderationevent_changelist")
        specialist_url = reverse("admin:catalog_specialist_changelist")
        moderation_specialist_url = reverse("admin:catalog_moderation_moderationspecialist_changelist")
        review_url = reverse("admin:catalog_placereview_changelist")
        moderation_review_url = reverse("admin:catalog_moderation_moderationreview_changelist")

        self.assertNotEqual(place_url, moderation_place_url)
        self.assertNotEqual(event_url, moderation_event_url)
        self.assertNotEqual(specialist_url, moderation_specialist_url)
        self.assertNotEqual(review_url, moderation_review_url)

        response = self.client.get(moderation_place_url)
        self.assertContains(response, "Рабочая очередь модерации")
        self.assertContains(response, "Места на проверке")
        self.assertContains(response, "Pending place")
        self.assertNotContains(response, "Visible place")
        self.assertContains(response, "Одобрить и опубликовать")
        self.assertContains(response, "Вернуть на доработку")

        response = self.client.get(moderation_event_url)
        self.assertContains(response, "Мероприятия на проверке")
        self.assertContains(response, "Pending event")
        self.assertNotContains(response, "Visible event")

        response = self.client.get(moderation_specialist_url)
        self.assertContains(response, "Специалисты на проверке")
        self.assertContains(response, "Pending specialist")
        self.assertNotContains(response, "Visible specialist")

        response = self.client.get(moderation_review_url)
        self.assertContains(response, "Нет отзывов, ожидающих проверки")

    def test_hidden_public_sections_remain_available_in_admin(self):
        site_settings = SiteSettings.get_solo()
        site_settings.events_section_enabled = False
        site_settings.specialists_section_enabled = False
        site_settings.save()

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/admin/catalog/event/"', html=False)
        self.assertContains(response, 'href="/admin/catalog/specialist/"', html=False)
        self.assertContains(response, 'title="Скрыто на сайте"', count=2, html=False)

    def test_staff_access_sidebar_marks_only_the_current_link_active(self):
        response = self.client.get(reverse("admin:catalog_staffaccessuser_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'href="/admin/catalog/staffaccessuser/add/" class="km-admin-sidebar__link"',
            html=False,
        )
        self.assertContains(
            response,
            'href="/admin/catalog/staffaccessuser/" class="km-admin-sidebar__link is-active"',
            html=False,
        )

        response = self.client.get(reverse("admin:catalog_staffaccessuser_add"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'href="/admin/catalog/staffaccessuser/add/" class="km-admin-sidebar__link is-active"',
            html=False,
        )
        self.assertContains(
            response,
            'href="/admin/catalog/staffaccessuser/" class="km-admin-sidebar__link"',
            html=False,
        )


class TestAdminSpecialistChangeList(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("specialist_list_admin", "specialist-list@example.com", "pass")
        self.client.force_login(self.admin)
        Specialist.objects.create(
            name="Published specialist",
            slug="published-specialist",
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
            is_verified=True,
        )
        Specialist.objects.create(
            name="Pending specialist",
            slug="pending-specialist-list",
            status=Specialist.STATUS_PENDING,
            is_active=False,
        )
        Specialist.objects.create(
            name="Inactive specialist",
            slug="inactive-specialist",
            status=Specialist.STATUS_DRAFT,
            is_active=False,
        )

    def test_change_list_uses_catalog_dashboard_and_real_specialist_metrics(self):
        response = self.client.get(reverse("admin:catalog_specialist_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Управляйте публикацией, проверкой")
        self.assertContains(response, "Всего специалистов")
        self.assertContains(response, "Опубликовано")
        self.assertContains(response, "На модерации")
        self.assertContains(response, "Неактивные")
        self.assertContains(response, "Без проверки")
        self.assertContains(response, "Все профили")
        self.assertContains(response, 'data-action="mark_published"', html=False)
        self.assertContains(response, 'data-action="mark_verified"', html=False)
        self.assertContains(response, 'href="?status__exact=published&amp;is_active__exact=1"', html=False)

    def test_specialist_bulk_publish_updates_public_visibility_fields(self):
        specialist = Specialist.objects.get(slug="pending-specialist-list")
        response = self.client.post(
            reverse("admin:catalog_specialist_changelist"),
            {"action": "mark_published", "_selected_action": [str(specialist.pk)], "index": "0"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        specialist.refresh_from_db()
        specialist.refresh_from_db()
        self.assertEqual(specialist.status, Specialist.STATUS_PUBLISHED)
        self.assertTrue(specialist.is_active)


class TestReviewRatingSyncAndAdminBulkActions(TestCase):
    def setUp(self):
        from catalog.models.review import PlaceReview
        from catalog.models.specialist import Specialist, SpecialistReview
        self.admin = User.objects.create_superuser("admin_reviewsync", "admin_rs@example.com", "pass")
        self.client.force_login(self.admin)
        self.place = create_quality_place(name="Rating sync test place")
        self.specialist = Specialist.objects.create(
            name="Rating sync specialist",
            slug="rating-sync-spec",
            status=Specialist.STATUS_PUBLISHED,
            is_active=True,
        )

    def test_place_review_bulk_approve_updates_place_rating_stats(self):
        from catalog.models.review import PlaceReview
        review1 = PlaceReview.objects.create(place=self.place, rating=5, text="Great place!", status=PlaceReview.STATUS_PENDING, is_approved=False)
        review2 = PlaceReview.objects.create(place=self.place, rating=4, text="Good place!", status=PlaceReview.STATUS_PENDING, is_approved=False)
        
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 0)
        self.assertEqual(self.place.rating_avg, 0.0)

        response = self.client.post(
            reverse("admin:catalog_placereview_changelist"),
            {"action": "approve_selected", "_selected_action": [str(review1.pk), str(review2.pk)], "index": "0"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 2)
        self.assertEqual(self.place.rating_avg, 4.5)

    def test_specialist_review_bulk_approve_updates_specialist_rating_stats(self):
        from catalog.models.specialist import SpecialistReview
        review = SpecialistReview.objects.create(
            specialist=self.specialist,
            author_name="Test Author",
            rating=5,
            text="Awesome specialist!",
            status=SpecialistReview.STATUS_PENDING,
            is_approved=False,
        )
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.rating_count, 0)

        response = self.client.post(
            reverse("admin:catalog_specialistreview_changelist"),
            {"action": "approve_selected", "_selected_action": [str(review.pk)], "index": "0"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.specialist.refresh_from_db()
        self.assertEqual(self.specialist.rating_count, 1)
        self.assertEqual(self.specialist.rating_avg, 5.0)

    def test_place_detail_self_heals_out_of_sync_rating_stats(self):
        from catalog.models.review import PlaceReview
        review = PlaceReview.objects.create(place=self.place, rating=5, text="Direct approved text", status=PlaceReview.STATUS_APPROVED, is_approved=True)
        # Manually force database out of sync to test self-healing
        self.place.__class__.objects.filter(pk=self.place.pk).update(rating_count=0, rating_avg=0.0)
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 0)

        response = self.client.get(self.place.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.rating_count, 1)
        self.assertEqual(self.place.rating_avg, 5.0)
