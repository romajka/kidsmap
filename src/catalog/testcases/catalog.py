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

class MariaDbCompatibleUniquenessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="mariadb_unique_user",
            email="mariadb_unique_user@example.com",
            password="StrongPass123!!",
        )
        self.owner = User.objects.create_user(
            username="mariadb_unique_owner",
            email="owner@example.com",
            password="StrongPass123!!",
        )
        self.place = create_quality_place(name="MariaDB Unique Place", name_ru="MariaDB Unique Place")

    def test_place_like_constraints_use_normalized_session_and_nullable_user(self):
        like = PlaceLike.objects.create(place=self.place, session_key="session-1")
        self.assertEqual(like.session_key_unique, "session-1")

        blank_like = PlaceLike.objects.create(place=self.place, session_key="")
        self.assertIsNone(blank_like.session_key_unique)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceLike.objects.create(place=self.place, session_key="session-1")

        PlaceLike.objects.create(place=self.place, user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceLike.objects.create(place=self.place, user=self.user)

    def test_review_constraints_enforce_single_authenticated_author(self):
        PlaceReview.objects.create(place=self.place, user=self.user, rating=5, text="First")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceReview.objects.create(place=self.place, user=self.user, rating=4, text="Second")

        SiteReview.objects.create(user=self.user, rating=5, text="Site first")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SiteReview.objects.create(user=self.user, rating=3, text="Site second")

    def test_reaction_constraints_enforce_unique_user_and_session(self):
        place_review = PlaceReview.objects.create(place=self.place, rating=5, text="Review")
        site_review = SiteReview.objects.create(author_name="Guest", rating=5, text="Site review")

        PlaceReviewReaction.objects.create(review=place_review, session_key="session-r")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceReviewReaction.objects.create(review=place_review, session_key="session-r")

        PlaceReviewReaction.objects.create(review=place_review, user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceReviewReaction.objects.create(review=place_review, user=self.user)

        SiteReviewReaction.objects.create(review=site_review, session_key="session-s")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SiteReviewReaction.objects.create(review=site_review, session_key="session-s")

        SiteReviewReaction.objects.create(review=site_review, user=self.user)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SiteReviewReaction.objects.create(review=site_review, user=self.user)

    def test_only_one_pending_ownership_request_per_place_and_applicant(self):
        request_item = PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )
        self.assertEqual(request_item.pending_constraint_key, PlaceOwnershipRequest.STATUS_PENDING)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceOwnershipRequest.objects.create(
                    place=self.place,
                    applicant=self.user,
                    status=PlaceOwnershipRequest.STATUS_PENDING,
                )

        request_item.status = PlaceOwnershipRequest.STATUS_APPROVED
        request_item.save(update_fields=["status", "pending_constraint_key", "updated_at"])
        request_item.refresh_from_db()
        self.assertIsNone(request_item.pending_constraint_key)

        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )

    def test_only_one_pending_team_invitation_per_owner_and_email(self):
        invitation = OwnerTeamInvitation.objects.create(
            owner=self.owner,
            invited_by=self.owner,
            email="Member@Example.com",
            status=OwnerTeamInvitation.STATUS_PENDING,
        )
        self.assertEqual(invitation.pending_email, "member@example.com")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OwnerTeamInvitation.objects.create(
                    owner=self.owner,
                    invited_by=self.owner,
                    email="member@example.com",
                    status=OwnerTeamInvitation.STATUS_PENDING,
                )

        invitation.status = OwnerTeamInvitation.STATUS_ACCEPTED
        invitation.save(update_fields=["status", "pending_email", "updated_at"])
        invitation.refresh_from_db()
        self.assertIsNone(invitation.pending_email)

        OwnerTeamInvitation.objects.create(
            owner=self.owner,
            invited_by=self.owner,
            email="member@example.com",
            status=OwnerTeamInvitation.STATUS_PENDING,
        )

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

    def test_structured_schedule_counts_as_public_schedule_content(self):
        place = create_quality_place(schedule="")
        day = PlaceScheduleDay.objects.create(place=place, weekday="mon", is_closed=False, is_24_hours=False, order=0)
        PlaceScheduleInterval.objects.create(schedule_day=day, start_time="09:00", end_time="18:00", order=0)

        public_ids = list(public_place_queryset(Place.objects.all()).values_list("id", flat=True))

        self.assertIn(place.id, public_ids)

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
        self.assertIn("baku_yasamal", repository.queries[0])
        self.assertIn("метро Ичеришехер", repository.queries[0])
        self.assertIn("Баку", repository.queries[0])

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

class TestSeedCatalogTaxonomyCommand(TestCase):
    def test_seeds_taxonomy_with_svg_paths(self):
        call_command("seed_catalog_taxonomy", verbosity=0)
        self.assertTrue(Category.objects.filter(code="EDU").exists())
        cat = Category.objects.get(code="EDU")
        self.assertTrue(cat.icon.endswith(".svg"))
        self.assertIn("img/icon/cooliocns SVG/Interface/Book_Open.svg", cat.icon)

    def test_update_icons_flag_overwrites_existing_custom_icon(self):
        Category.objects.update_or_create(
            code="EDU",
            defaults={
                "name": "Образование",
                "name_az": "Təhsil",
                "name_ru": "Образование",
                "name_en": "Education",
                "icon": "custom-icon.png",
                "order": 2,
            }
        )
        
        # Without flag, it should not overwrite custom-icon.png since it doesn't start with fas fa-
        call_command("seed_catalog_taxonomy", verbosity=0)
        cat = Category.objects.get(code="EDU")
        self.assertEqual(cat.icon, "custom-icon.png")

        # With flag, it should overwrite
        call_command("seed_catalog_taxonomy", update_icons=True, verbosity=0)
        cat.refresh_from_db()
        self.assertNotEqual(cat.icon, "custom-icon.png")
        self.assertTrue(cat.icon.endswith(".svg"))

class TestDependentSubcategoryValidation(TestCase):
    def test_form_validation_fails_on_mismatched_subcategory(self):
        from catalog.models.category import Subcategory
        cat1 = Category.objects.create(code="CAT1", name_ru="Cat 1")
        cat2 = Category.objects.create(code="CAT2", name_ru="Cat 2")
        sub1 = Subcategory.objects.create(category=cat1, name_ru="Sub 1")
        
        from catalog.forms import OwnerPlaceEditForm
        form = OwnerPlaceEditForm(data={
            "name_ru": "Test Place",
            "category": cat2.code,
            "subcategory": sub1.id,
            "lat": "40.0",
            "lng": "40.0"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("subcategory", form.errors)
        self.assertEqual(form.errors["subcategory"][0], "Выбранная подкатегория не принадлежит к указанной категории.")

    def test_form_validation_succeeds_on_matched_subcategory(self):
        from catalog.models.category import Subcategory
        cat1 = Category.objects.create(code="CAT1", name_ru="Cat 1")
        sub1 = Subcategory.objects.create(category=cat1, name_ru="Sub 1")
        
        from catalog.forms import OwnerPlaceEditForm
        form = OwnerPlaceEditForm(data={
            "name_ru": "Test Place",
            "category": cat1.code,
            "subcategory": sub1.id,
            "lat": "40.0",
            "lng": "40.0"
        })
        # Note: missing other required fields might make it invalid, 
        # but subcategory shouldn't be in errors
        form.is_valid()
        self.assertNotIn("subcategory", form.errors)
