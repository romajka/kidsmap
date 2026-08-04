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
from django.core.exceptions import ValidationError
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

class TestOwnershipWorkflow(TestCase):
    def setUp(self):
        self.place = create_quality_place(
            name="Ownership Place",
            name_ru="Кружок для привязки",
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

    def test_owner_cabinet_redirects_to_places_dashboard(self):
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_places_dashboard"))

    def test_owner_cabinet_ignores_legacy_claim_search_and_redirects(self):
        Place.objects.create(
            name="Another Place",
            name_ru="Другой кружок",
            category="TECH",
            is_active=True,
        )
        self.client.login(username="owner_role_user", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"), data={"claim_q": "Другой"})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_places_dashboard"))

    def test_owner_cabinet_does_not_render_legacy_request_sections(self):
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
        response = self.client.get(reverse("owner_cabinet"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Заявки на рассмотрении")
        self.assertNotContains(response, "Принятые заявки")
        self.assertNotContains(response, "Отклоненные заявки")
        self.assertNotContains(response, "Создать заявку на управление карточкой")
        self.assertContains(response, "Мои места")

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


class TestOwnerPhoneValidation(TestCase):
    def test_owner_place_create_form_normalizes_azerbaijan_phone(self):
        form = OwnerPlaceCreateForm()
        form.cleaned_data = {"phone1": "055 123 45 67"}

        self.assertEqual(form.clean_phone1(), "+994551234567")

    def test_owner_place_create_form_accepts_possible_azerbaijan_contact_phone(self):
        form = OwnerPlaceCreateForm()
        form.cleaned_data = {"phone1": "+994 66 666 66 66"}

        self.assertEqual(form.clean_phone1(), "+994666666666")

    def test_owner_place_create_form_rejects_non_azerbaijan_phone(self):
        form = OwnerPlaceCreateForm()
        form.cleaned_data = {"phone1": "+1 202 555 0100"}

        with self.assertRaisesMessage(ValidationError, "+994 50 123 45 67"):
            form.clean_phone1()

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
        from PIL import Image

        image_bytes = BytesIO()
        Image.new("RGB", (32, 24), "#2f8f5b").save(image_bytes, format="PNG")
        return SimpleUploadedFile(name, image_bytes.getvalue(), content_type="image/png")

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

    def test_owner_can_open_published_place_for_editing(self):
        self.manager_place.status = Place.STATUS_PUBLISHED
        self.manager_place.is_active = True
        self.manager_place.save(update_fields=["status", "is_active", "updated_at"])
        self.client.login(username="owner_manager", password="StrongPass123!!")

        dashboard_response = self.client.get(reverse("owner_places_dashboard"))
        edit_response = self.client.get(reverse("owner_place_edit", args=[self.manager_place.id]))

        self.assertEqual(edit_response.status_code, 200)
        self.assertContains(
            dashboard_response,
            reverse("owner_place_edit", args=[self.manager_place.id]),
        )

    def test_owner_can_resubmit_published_place_for_moderation(self):
        self.manager_place.status = Place.STATUS_PUBLISHED
        self.manager_place.is_active = True
        self.manager_place.save(update_fields=["status", "is_active", "updated_at"])
        PlaceOwnershipRequest.objects.create(
            place=self.manager_place,
            applicant=self.manager_user,
            status=PlaceOwnershipRequest.STATUS_APPROVED,
        )
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.post(
            reverse("owner_place_submit_review", args=[self.manager_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.manager_place.refresh_from_db()
        self.assertEqual(self.manager_place.status, Place.STATUS_PENDING)
        self.assertFalse(self.manager_place.is_active)
        self.assertTrue(
            PlaceOwnershipRequest.objects.filter(
                place=self.manager_place,
                applicant=self.manager_user,
                status=PlaceOwnershipRequest.STATUS_PENDING,
            ).exists()
        )

    def test_owner_cannot_open_another_owners_place_for_editing(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.get(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse("owner_places_dashboard"))
        self.assertNotContains(response, reverse("owner_place_edit", args=[self.editor_place.id]))

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
        self.assertContains(response, "data-owner-leave-guard")
        self.assertContains(response, "Saxla və çıx")
        self.assertContains(response, 'data-owner-step="4"', html=False)
        self.assertContains(response, "owner-wizard-progressbar")
        self.assertContains(response, "owner_place_wizard.js")
        self.assertNotContains(response, '<footer class="site-footer panel">', html=False)
        self.assertNotContains(response, "Фото для шапки")

    def test_owner_edit_page_rehydrates_saved_pricing_plans(self):
        self.editor_place.pricing_plans = [
            {
                "lesson_format": "individual",
                "payment_type": "per_lesson",
                "price": "40.00",
                "currency": "AZN",
                "title_ru": "Индивидуальный",
                "is_active": True,
                "sort_order": 0,
            },
        ]
        self.editor_place.save(update_fields=["pricing_plans"])

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_edit", args=[self.editor_place.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Индивидуальный")
        self.assertContains(response, "&quot;price&quot;: &quot;40.00&quot;", html=False)
        self.assertContains(response, "owner_place_wizard.js")
        self.assertContains(response, "?v=10")

    def test_owner_edit_shows_pricing_validation_error_and_keeps_saved_plans(self):
        existing_plans = [
            {
                "lesson_format": "group",
                "payment_type": "per_month",
                "price": "120.00",
                "currency": "AZN",
                "is_active": True,
                "sort_order": 0,
            },
        ]
        self.editor_place.pricing_plans = existing_plans
        self.editor_place.save(update_fields=["pricing_plans"])

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "form_action": "save_draft",
                "name_az": "Tarif testi",
                "category": "TECH",
                "pricing_plans": json.dumps([
                    {
                        "lesson_format": "group",
                        "payment_type": "package",
                        "price": "90",
                    },
                ]),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тариф 1:")
        self.assertContains(response, "Количество и единица должны быть указаны вместе.")
        self.editor_place.refresh_from_db()
        self.assertEqual(len(self.editor_place.pricing_plans), 1)
        self.assertEqual(self.editor_place.pricing_plans[0]["price"], "120.00")

    def test_owner_editor_can_save_incomplete_edit_as_draft(self):
        self.editor_place.name_az = "Redakte qaralama"
        self.editor_place.description_az = "Ilkin tesvir"
        self.editor_place.category_id = "EDU"
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

    def test_owner_editor_can_save_draft_and_exit_to_dashboard(self):
        self.editor_place.name_az = "Redakte qaralama"
        self.editor_place.description_az = "Ilkin tesvir"
        self.editor_place.category_id = "EDU"
        self.editor_place.status = Place.STATUS_DRAFT
        self.editor_place.is_active = False
        self.editor_place.save()

        self.client.login(username="owner_editor", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "form_action": "save_draft_exit",
                "name_ru": "",
                "name_az": "Redakte qaralama cixis",
                "name_en": "",
                "description_ru": "",
                "description_az": "Yenilenmis cixis qaralamasi",
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
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_places_dashboard"))
        self.editor_place.refresh_from_db()
        self.assertEqual(self.editor_place.name_az, "Redakte qaralama cixis")
        self.assertEqual(self.editor_place.description_az, "Yenilenmis cixis qaralamasi")
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
        response = self.client.get(reverse("owner_place_create"), {"type": "permanent"})

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
        self.assertNotContains(response, "leaflet@1.9.4/dist/leaflet.css")
        self.assertNotContains(response, '<footer class="site-footer panel">', html=False)
        self.assertNotContains(response, "Фото для шапки")

    def test_owner_edit_saves_structured_schedule_and_creates_schedule_audit(self):
        self.editor_place.status = Place.STATUS_DRAFT
        self.editor_place.save(update_fields=["status", "updated_at"])
        self.client.login(username="owner_editor", password="StrongPass123!!")

        response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={
                "name_ru": "Кружок редактора",
                "name_az": "Редактор dərnəyi",
                "name_en": "",
                "description_ru": "Описание редактора",
                "description_az": "Redaktor təsviri",
                "description_en": "",
                "category": "TECH",
                "subcategory": "",
                "age_from": "7",
                "age_to": "12",
                "price_from": "50",
                "price_to": "70",
                "region": "baku",
                "district": "baku_yasamal",
                "metro": "",
                "address": "Баку, Низами 10",
                "phone1": "+994501112233",
                "instagram": "",
                "website": "",
                "schedule": "",
                "structured_schedule": build_structured_schedule_payload(),
                "lesson_duration_minutes": "60",
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
        self.assertTrue(self.editor_place.schedule_days.filter(weekday="mon", is_closed=False).exists())
        self.assertTrue(
            PlaceChangeAudit.objects.filter(
                place=self.editor_place,
                changed_by=self.editor_user,
                source=PlaceChangeAudit.SOURCE_OWNER_PANEL,
                field_name="schedule",
            ).exists()
        )

    def test_owner_place_create_opens_listing_type_choice_first(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Nə əlavə etmək istəyirsiniz?")
        self.assertContains(response, "Daimi məkan")
        self.assertContains(response, "Müvəqqəti tədbir")
        self.assertContains(response, reverse("owner_event_create"))

    def test_owner_place_create_fresh_page_uses_unique_browser_draft_key(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response_one = self.client.get(reverse("owner_place_create"), {"type": "permanent", "fresh": "1"})
        response_two = self.client.get(reverse("owner_place_create"), {"type": "permanent", "fresh": "1"})

        key_one = response_one.context["draft_client_key"]
        key_two = response_two.context["draft_client_key"]

        self.assertTrue(key_one.startswith("owner-place-create-"))
        self.assertTrue(key_two.startswith("owner-place-create-"))
        self.assertNotEqual(key_one, key_two)
        self.assertContains(response_one, f'data-owner-draft-key="{key_one}"', html=False)
        self.assertContains(response_one, f'name="draft_client_key" value="{key_one}"', html=False)

    def test_owner_place_create_invalid_post_preserves_browser_draft_key(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        draft_key = "owner-place-create-test-session"

        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "draft_client_key": draft_key,
                "name_az": "",
                "category": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["draft_client_key"], draft_key)
        self.assertContains(response, f'data-owner-draft-key="{draft_key}"', html=False)

    def test_owner_can_save_and_exit_create_draft_before_category_is_selected(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.post(
            reverse("owner_place_create"),
            data={
                "form_action": "save_draft_exit",
                "name_az": "Erkən saxlanan qaralama",
                "category": "",
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
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("owner_places_dashboard"))
        place = Place.objects.get(owner=self.manager_user, name_az="Erkən saxlanan qaralama")
        self.assertEqual(place.status, Place.STATUS_DRAFT)
        self.assertIsNotNone(place.category_id)

    @override_settings(GOOGLE_MAPS_API_KEY="test-key")
    def test_owner_create_page_uses_google_maps_when_key_is_configured(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"), {"type": "permanent"})

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
                "form_action": "save_and_publish",
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
                "gallery_images": [
                    self._image_upload("g1.png"),
                    self._image_upload("g2.png"),
                    self._image_upload("g3.png"),
                    self._image_upload("g4.png"),
                ],
            },
        )

        if response.status_code != 302:
            self.fail(response.context["form"].errors.as_text())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("owner_places_dashboard"))

        place = Place.objects.get(owner=self.manager_user, name_ru="Новая карточка владельца")
        self.assertFalse(place.is_active)
        self.assertFalse(place.is_verified)
        self.assertEqual(place.name, "Yeni owner karti")
        self.assertEqual(PlacePhoto.objects.filter(place=place).count(), 4)
        ownership_request = PlaceOwnershipRequest.objects.get(place=place, applicant=self.manager_user)
        self.assertEqual(ownership_request.status, PlaceOwnershipRequest.STATUS_PENDING)

    def test_owner_create_page_shows_disabled_publish_action_and_available_draft_save(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")

        response = self.client.get(reverse("owner_place_create"), {"type": "permanent"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-owner-publish-button', html=False)
        self.assertContains(response, 'value="save_and_publish"', html=False)
        self.assertContains(response, 'value="save_draft"', html=False)
        self.assertContains(response, 'data-owner-publish-hint', html=False)

    def test_owner_edit_publish_action_revalidates_required_fields_on_server(self):
        self.editor_place.status = Place.STATUS_DRAFT
        self.editor_place.photo = self._image_upload("saved-photo.png")
        self.editor_place.save()
        self.client.login(username="owner_editor", password="StrongPass123!!")

        response = self.client.post(
            reverse("owner_place_edit", args=[self.editor_place.id]),
            data={"form_action": "save_and_publish"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("name_az", response.context["form"].errors)
        self.assertIn("phone1", response.context["form"].errors)
        self.editor_place.refresh_from_db()
        self.assertEqual(self.editor_place.status, Place.STATUS_DRAFT)

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

    def test_owner_place_create_requires_structured_schedule_for_permanent_place(self):
        base_data = {
            "name_ru": "",
            "name_az": "Is qrafiki teleb olunur",
            "name_en": "",
            "description_ru": "",
            "description_az": "Daimi mekan ucun is qrafiki mutleq secilmelidir.",
            "description_en": "",
            "category": "EDU",
            "subcategory": "",
            "age_from": "6",
            "age_to": "12",
            "price_from": "10",
            "price_to": "20",
            "region": "baku",
            "district": "Yasamal",
            "metro": "",
            "address": "Baki, Nizami kucesi 10",
            "phone1": "+994501112233",
            "instagram": "",
            "website": "",
            "schedule": "",
            "is_temporary": "",
            "temporary_start": "",
            "temporary_end": "",
            "moderation_note": "",
        }

        form = OwnerPlaceCreateForm(
            data=base_data,
            files=MultiValueDict({"photo": [self._image_upload("main.png")]}),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("structured_schedule", form.errors)

        form = OwnerPlaceCreateForm(
            data={**base_data, "structured_schedule": build_structured_schedule_payload()},
            files=MultiValueDict({"photo": [self._image_upload("main-with-schedule.png")]}),
        )

        self.assertTrue(form.is_valid(), form.errors)

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

    def test_owner_event_create_requires_start_and_end(self):
        self.client.login(username="owner_manager", password="StrongPass123!!")
        response = self.client.post(
            reverse("owner_event_create"),
            data={
                "name_az": "Tarixsiz tədbir",
                "description_az": "Tedbir tesviri var",
                "category": "EDU",
                "age_from": "7",
                "age_to": "12",
                "price_text": "100 AZN",
                "address": "Улица 1",
                "phone": "+994501112233",
                "start_datetime": "",
                "end_datetime": "",
                "moderation_note": "Проверка обязательных дат",
                "photo": self._image_upload("main-temporary-required.png"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event_date", response.context["form"].errors)
        self.assertIn("start_time_input", response.context["form"].errors)
        self.assertIn("end_time_input", response.context["form"].errors)
        self.assertContains(response, "Müvəqqəti tədbir")
        self.assertFalse(Event.objects.filter(name_az="Tarixsiz tədbir").exists())

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

    def test_regular_user_can_open_places_dashboard(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_places_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Мои места")

    def test_regular_user_owner_cabinet_redirects_to_places_dashboard(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_cabinet"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], reverse("owner_places_dashboard"))
        self.assertNotContains(response, "Этот раздел доступен только для расширенного доступа команды.")

    def test_regular_user_can_open_place_create_flow(self):
        self.client.login(username="regular_for_owner_pages", password="StrongPass123!!")
        response = self.client.get(reverse("owner_place_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Выбор типа объявления")

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
