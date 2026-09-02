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
from catalog.repositories.django_repositories import DjangoPlaceRepository
from catalog.services.geocoding import PlaceGeocodingService
from catalog.services.content_quality import (
    contains_test_content,
    place_quality_check,
    place_catalog_visibility_reasons,
    public_place_queryset,
    public_review_queryset,
    review_quality_check,
)
from catalog.services.place_schedule import dump_schedule_payload
from catalog.services.slugs import PUBLIC_SLUG_MAX_LENGTH, build_ascii_slug
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


class PublicSlugTests(TestCase):
    def test_build_ascii_slug_transliterates_cyrillic_and_azerbaijani(self):
        self.assertEqual(
            build_ascii_slug("Детская школа Abşeron", fallback="place"),
            "detskaya-shkola-abseron",
        )

    def test_build_ascii_slug_is_short_and_url_safe(self):
        slug = build_ascii_slug("Очень длинное название " * 20, fallback="place")

        self.assertLessEqual(len(slug), PUBLIC_SLUG_MAX_LENGTH)
        self.assertTrue(slug.isascii())
        self.assertNotIn("%", slug)

    def test_new_place_url_does_not_contain_encoded_characters(self):
        place = create_quality_place(
            name="Детская школа дзюдо",
            name_az="",
            name_en="",
            name_ru="Детская школа дзюдо",
        )

        self.assertEqual(place.slug, "detskaya-shkola-dzyudo")
        self.assertTrue(place.get_absolute_url().isascii())


class CatalogMapQueryEfficiencyTests(TestCase):
    def test_map_uses_the_same_svg_as_museum_catalog_category(self):
        category, _ = Category.objects.update_or_create(
            code="museums-culture",
            defaults={
                "name": "Museums & culture",
                "name_ru": "Музеи и культура",
                "icon": "img/icon/cooliocns SVG/Navigation/Building_04.svg",
            },
        )
        place = create_quality_place(
            name="Museum map icon",
            category=category,
            lat=40.37,
            lng=49.84,
        )

        serialized = PlaceController.build_default()._serialize_map_places(
            DjangoPlaceRepository().map_ready_queryset(Place.objects.filter(pk=place.pk)),
            language_code="ru",
        )

        self.assertEqual(serialized[0]["category_icon_url"], category.icon_file_url)
        self.assertEqual(serialized[0]["category_icon_svg"], category.icon_svg_source)
        self.assertIn('id="Navigation / Building_04"', serialized[0]["category_icon_svg"])

    def test_map_serialization_query_count_does_not_grow_with_schedules(self):
        place_ids = []
        for index in range(2):
            place = create_quality_place(
                name=f"Map schedule {index}",
                name_ru=f"Расписание на карте {index}",
                lat=40.37 + index * 0.01,
                lng=49.84 + index * 0.01,
            )
            day = PlaceScheduleDay.objects.create(
                place=place,
                weekday="mon",
                is_closed=False,
                order=0,
            )
            PlaceScheduleInterval.objects.create(
                schedule_day=day,
                start_time="10:00",
                end_time="12:00",
                order=0,
            )
            place_ids.append(place.pk)

        repository = DjangoPlaceRepository()
        queryset = repository.map_ready_queryset(
            repository.active_queryset().filter(pk__in=place_ids)
        )

        # Main queryset + schedule days + intervals + relational tariffs.
        with self.assertNumQueries(4):
            serialized = PlaceController.build_default()._serialize_map_places(
                queryset,
                language_code="ru",
            )

        self.assertEqual(len(serialized), 2)
        self.assertTrue(all(item["schedule"] for item in serialized))


class PostgreSqlUniquenessTests(TestCase):
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

    def test_place_like_constraints_use_anonymous_session_and_nullable_user(self):
        like = PlaceLike.objects.create(place=self.place, session_key=" session-1 ")
        self.assertEqual(like.session_key, "session-1")

        blank_like = PlaceLike.objects.create(place=self.place, session_key="")
        self.assertEqual(blank_like.session_key, "")

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
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PlaceOwnershipRequest.objects.create(
                    place=self.place,
                    applicant=self.user,
                    status=PlaceOwnershipRequest.STATUS_PENDING,
                )

        request_item.status = PlaceOwnershipRequest.STATUS_APPROVED
        request_item.save(update_fields=["status", "updated_at"])
        request_item.refresh_from_db()
        self.assertEqual(request_item.status, PlaceOwnershipRequest.STATUS_APPROVED)

        PlaceOwnershipRequest.objects.create(
            place=self.place,
            applicant=self.user,
            status=PlaceOwnershipRequest.STATUS_PENDING,
        )

    def test_only_one_pending_team_invitation_per_place_and_email(self):
        invitation = OwnerTeamInvitation.objects.create(
            place=self.place,
            owner=self.owner,
            invited_by=self.owner,
            email="Member@Example.com",
            status=OwnerTeamInvitation.STATUS_PENDING,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                OwnerTeamInvitation.objects.create(
                    place=self.place,
                    owner=self.owner,
                    invited_by=self.owner,
                    email="member@example.com",
                    status=OwnerTeamInvitation.STATUS_PENDING,
                )

        invitation.status = OwnerTeamInvitation.STATUS_ACCEPTED
        invitation.save(update_fields=["status", "updated_at"])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, OwnerTeamInvitation.STATUS_ACCEPTED)

        OwnerTeamInvitation.objects.create(
            place=self.place,
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

    def test_phone_number_with_test_like_digits_does_not_hide_valid_place(self):
        place = create_quality_place(phone1="+994501234567")

        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertTrue(place.is_public)
        self.assertNotIn("test_content", place_quality_check(place).errors)

    def test_junk_tokens_are_whole_tokens_not_substrings(self):
        place = create_quality_place(name="Latest contest for children")

        self.assertFalse(contains_test_content(place.name))
        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertNotIn("test_content", place_catalog_visibility_reasons(place))

    def test_test_tokens_in_public_text_fields_hide_place_and_match_admin_check(self):
        cases = (
            ("name", "Test children club"),
            ("description_az", "Lorem " + "uşaqlar üçün faydalı dərslər və açıq qruplar. " * 4),
            ("address", "Qwerty küçəsi 10"),
        )

        for field, value in cases:
            with self.subTest(field=field):
                place = create_quality_place(**{field: value})

                self.assertTrue(contains_test_content(value))
                self.assertFalse(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
                self.assertIn("test_content", place_catalog_visibility_reasons(place))

    def test_published_active_place_is_hidden_for_every_catalog_rule(self):
        empty_category, _ = Category.objects.get_or_create(code="", defaults={"name": "Empty category"})
        cases = (
            ("missing_category", {"category": empty_category}),
            ("missing_address", {"address": ""}),
            ("missing_contact", {"phone1": "", "instagram": "", "website": ""}),
            ("missing_age", {"age_from": None, "age_to": None}),
            ("missing_price", {
                "price_from": None, "price_to": None, "price_per_lesson": None,
                "price_per_month": None, "price_per_8_lessons": None,
            }),
            ("description_too_short", {"description_az": "Коротко"}),
            ("missing_schedule", {"schedule": ""}),
            ("test_content", {"name": "test club"}),
        )

        for reason, overrides in cases:
            with self.subTest(reason=reason):
                place = create_quality_place(**overrides)
                self.assertFalse(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
                # ``is_public`` is the publication state; the catalog filter is
                # intentionally stricter and is asserted above.
                self.assertTrue(place.is_public)
                self.assertIn(reason, place_catalog_visibility_reasons(place))

    def test_price_only_in_active_pricing_plan_makes_place_public(self):
        from catalog.models import PricingPlan

        place = create_quality_place(
            price_from=None,
            price_to=None,
            price_per_lesson=None,
            price_per_month=None,
            price_per_8_lessons=None,
        )
        PricingPlan.objects.create(place=place, product_type="lesson", price_kind="exact", price=80)
        # PricingPlan signals normally keep legacy fields in sync. Clear them to
        # prove catalog visibility is granted by the relational tariff itself.
        Place.objects.filter(pk=place.pk).update(
            price_from=None, price_to=None, price_per_lesson=None,
            price_per_month=None, price_per_8_lessons=None,
        )

        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        place.refresh_from_db()
        self.assertTrue(place.is_public)

    def test_range_pricing_plan_is_a_price_for_both_quality_and_catalog(self):
        from catalog.models import PricingPlan

        place = create_quality_place(
            price_from=None,
            price_to=None,
            price_per_lesson=None,
            price_per_month=None,
            price_per_8_lessons=None,
        )
        PricingPlan.objects.create(
            place=place,
            product_type="lesson",
            price_kind="range",
            price_min=40,
            price_max=80,
        )

        self.assertTrue(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertNotIn("missing_price", place_quality_check(place).errors)

    def test_temporary_place_is_hidden_when_events_section_is_disabled(self):
        settings = SiteSettings.get_solo()
        settings.events_section_enabled = False
        settings.save(update_fields=["events_section_enabled"])
        place = create_quality_place(is_temporary=True)

        self.assertFalse(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertIn("events_section_disabled", place_catalog_visibility_reasons(place))

    def test_finished_temporary_place_is_hidden(self):
        place = create_quality_place(is_temporary=True, temporary_end=timezone.now() - timedelta(minutes=1))

        self.assertFalse(public_place_queryset(Place.objects.filter(pk=place.pk)).exists())
        self.assertIn("temporary_event_expired", place_catalog_visibility_reasons(place))

    def test_structured_schedule_counts_as_public_schedule_content(self):
        place = create_quality_place(schedule="")
        day = PlaceScheduleDay.objects.create(place=place, weekday="mon", is_closed=False, is_24_hours=False, order=0)
        PlaceScheduleInterval.objects.create(schedule_day=day, start_time="09:00", end_time="18:00", order=0)

        public_ids = list(public_place_queryset(Place.objects.all()).values_list("id", flat=True))

        self.assertIn(place.id, public_ids)

    def test_map_ready_places_prefetch_structured_schedules(self):
        place = create_quality_place(schedule="", lat=40.4093, lng=49.8671)
        day = PlaceScheduleDay.objects.create(place=place, weekday="mon", is_closed=False, is_24_hours=False, order=0)
        PlaceScheduleInterval.objects.create(schedule_day=day, start_time="09:00", end_time="18:00", order=0)

        places = list(DjangoPlaceRepository().map_ready_queryset())

        self.assertEqual([item.pk for item in places], [place.pk])
        with self.assertNumQueries(0):
            self.assertTrue(places[0].schedule_summary)

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

    def test_diagnose_place_visibility_command_is_read_only(self):
        place = create_quality_place(phone1="+994501234567")
        before_count = Place.objects.count()
        output = StringIO()

        call_command("diagnose_place_visibility", "--examples", "2", stdout=output)

        self.assertEqual(Place.objects.count(), before_count)
        self.assertIn("published+active in catalog: 1", output.getvalue())
        self.assertIn("junk false positives (old contact rule): 1", output.getvalue())
        self.assertIn(str(place.pk), output.getvalue())

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
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)
        self.assertTrue(Category.objects.filter(code="EDU").exists())
        cat = Category.objects.get(code="EDU")
        self.assertTrue(cat.icon.endswith(".svg"))
        self.assertEqual(cat.icon, "icons/categories/education.svg")
        waterpark = Category.objects.get(code="water-leisure")
        self.assertEqual(waterpark.name_ru, "Водный отдых")
        self.assertEqual(waterpark.name_az, "Su istirahəti")
        self.assertEqual(waterpark.name_en, "Water leisure")
        self.assertEqual(waterpark.icon, "icons/categories/water-leisure.svg")
        self.assertTrue(waterpark.is_active)
        self.assertTrue(waterpark.subcategories.filter(code="waterparks").exists())
        zoo = Category.objects.get(code="ZOO")
        self.assertEqual(zoo.name_ru, "Зоопарки")
        self.assertEqual(zoo.icon, "icons/categories/zoo.svg")
        self.assertTrue(zoo.is_active)
        self.assertTrue(zoo.subcategories.filter(code="aquariums-oceanariums").exists())
        self.assertEqual(Category.active.count(), 17)
        self.assertEqual(Subcategory.active.count(), 104)

    def test_taxonomy_migration_relinks_places_events_and_gallery_categories(self):
        from django.apps import apps
        from importlib import import_module

        from catalog.models import Event, Place, SiteGalleryImage

        legacy_category = Category.objects.create(
            code="WATERPARK",
            name="Аквапарки и бассейны",
            name_ru="Аквапарки и бассейны",
        )
        legacy_subcategory = Subcategory.objects.create(
            category=legacy_category,
            code="waterparks-pools",
            name="Аквапарки и бассейны для отдыха",
            name_ru="Аквапарки и бассейны для отдыха",
        )
        place = Place.objects.create(
            name="Legacy water pin",
            name_ru="Старая водная точка",
            category=legacy_category,
            subcategory=legacy_subcategory,
        )
        event = Event.objects.create(name="Legacy water event", category=legacy_category)
        gallery = SiteGalleryImage.objects.create(
            image="site/gallery/legacy-water.webp",
            category=legacy_category.code,
        )

        migration = import_module("catalog.migrations.0079_sync_public_taxonomy")
        migration.sync_taxonomy(apps, None)

        place.refresh_from_db()
        event.refresh_from_db()
        gallery.refresh_from_db()
        self.assertEqual(place.category_id, "water-leisure")
        self.assertEqual(place.subcategory.code, "waterparks")
        self.assertEqual(event.category_id, "water-leisure")
        self.assertEqual(gallery.category, "water-leisure")

    def test_taxonomy_cleanup_removes_named_duplicates_after_relinking_cards(self):
        from django.apps import apps
        from importlib import import_module

        from catalog.models import Event, Place

        duplicate_category = Category.objects.create(
            code="MUSEUM-DUP",
            name="Музеи и культура",
            name_ru="Музеи и культура",
        )
        duplicate_subcategory = Subcategory.objects.create(
            category=duplicate_category,
            code="archery-copy",
            name="Стрельба из лука",
            name_ru="Стрельба из лука",
        )
        duplicate_beach = Category.objects.create(
            code="BEACH-DUP",
            name="Пляжи",
            name_ru="Пляжи",
        )
        place = Place.objects.create(
            name="Duplicate taxonomy place",
            category=duplicate_category,
            subcategory=duplicate_subcategory,
        )
        beach_place = Place.objects.create(name="Duplicate beach place", category=duplicate_beach)
        event = Event.objects.create(name="Duplicate taxonomy event", category=duplicate_category)

        migration = import_module("catalog.migrations.0080_clean_public_taxonomy")
        migration.clean_public_taxonomy(apps, None)

        place.refresh_from_db()
        beach_place.refresh_from_db()
        event.refresh_from_db()
        self.assertEqual(place.category_id, "SPRT")
        self.assertEqual(place.subcategory.code, "archery")
        self.assertEqual(beach_place.category_id, "water-leisure")
        self.assertEqual(event.category_id, "museums-culture")
        self.assertFalse(Category.objects.filter(code="MUSEUM-DUP").exists())
        self.assertFalse(Subcategory.objects.filter(code="archery-copy").exists())

        from catalog.taxonomy_data import PUBLIC_CATEGORY_CODES, SUBCATEGORIES

        self.assertSetEqual(
            set(Category.objects.values_list("code", flat=True)),
            set(PUBLIC_CATEGORY_CODES),
        )
        self.assertSetEqual(
            set(Subcategory.objects.values_list("code", flat=True)),
            {row[1] for row in SUBCATEGORIES},
        )

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
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)
        cat = Category.objects.get(code="EDU")
        self.assertEqual(cat.icon, "custom-icon.png")

        # With flag, it should overwrite
        call_command("seed_catalog_taxonomy", "--force", update_icons=True, verbosity=0)
        cat.refresh_from_db()
        self.assertNotEqual(cat.icon, "custom-icon.png")
        self.assertTrue(cat.icon.endswith(".svg"))

class TestDependentSubcategoryValidation(TestCase):
    def test_form_validation_fails_on_mismatched_subcategory(self):
        from catalog.models.category import Subcategory
        cat1 = Category.objects.create(code="CAT1", name_ru="Cat 1")
        cat2 = Category.objects.create(code="CAT2", name_ru="Cat 2")
        sub1 = Subcategory.objects.create(category=cat1, code="cat1-sub-1", name_ru="Sub 1")
        
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
        sub1 = Subcategory.objects.create(category=cat1, code="cat1-sub-1", name_ru="Sub 1")
        
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


class TestSeedIdempotency(TestCase):
    """
    Ensures that seed_catalog_taxonomy does NOT restore categories or subcategories
    that were deactivated/archived via the production admin.

    This is the regression test for the core data loss bug:
    release-server.sh was calling seed_catalog_taxonomy on every deploy,
    causing update_or_create to overwrite admin changes.
    """

    def test_deactivated_category_stays_inactive_after_seed_without_force(self):
        """
        A category deactivated in the admin MUST remain inactive
        when seed runs WITHOUT --force (the normal deploy path).
        """
        # First run: populate the DB (simulates first deploy / empty DB init)
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        # Admin deactivates a category (simulates production admin action)
        cat = Category.objects.get(code="EDU")
        cat.is_active = False
        cat.save(update_fields=["is_active"])

        # Second run: WITHOUT --force — simulates subsequent deploys.
        # Should print a warning and return without touching data.
        out = StringIO()
        call_command("seed_catalog_taxonomy", verbosity=0, stdout=out)

        cat.refresh_from_db()
        self.assertFalse(
            cat.is_active,
            "BUG: seed_catalog_taxonomy restored is_active=True for a category "
            "that was deactivated in the admin. The seed must NEVER run without --force on production."
        )
        output = out.getvalue()
        self.assertIn("Skipping seed", output,
                      "Expected seed to print a warning when skipping due to existing data.")

    def test_deactivated_subcategory_stays_inactive_after_seed_without_force(self):
        """
        Subcategories deactivated in the admin MUST remain inactive
        when seed runs WITHOUT --force.
        """
        from catalog.models.category import Subcategory
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        sub = Subcategory.objects.get(code="football")
        sub.is_active = False
        sub.save(update_fields=["is_active"])

        call_command("seed_catalog_taxonomy", verbosity=0)

        sub.refresh_from_db()
        self.assertFalse(
            sub.is_active,
            "BUG: seed_catalog_taxonomy restored is_active=True for a subcategory "
            "that was deactivated in the admin."
        )

    def test_seed_with_force_does_not_overwrite_is_active_of_existing_categories(self):
        """
        Even with --force, the seed MUST NOT restore deactivated categories.
        --force only updates names, icons, colors — never is_active.
        """
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        cat = Category.objects.get(code="SPRT")
        cat.is_active = False
        cat.save(update_fields=["is_active"])

        # Run with --force (admin/emergency path)
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        cat.refresh_from_db()
        self.assertFalse(
            cat.is_active,
            "BUG: seed_catalog_taxonomy --force reset is_active=True for a category "
            "that was deliberately deactivated."
        )

    def test_seed_without_force_skips_when_categories_exist(self):
        """
        Without --force, the command must exit immediately if categories exist,
        printing a warning instead of modifying any data.
        """
        from catalog.models.category import Subcategory
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        initial_cat_count = Category.objects.count()
        initial_sub_count = Subcategory.objects.count()

        call_command("seed_catalog_taxonomy", verbosity=0)

        self.assertEqual(Category.objects.count(), initial_cat_count)
        self.assertEqual(Subcategory.objects.count(), initial_sub_count)

    def test_seed_force_creates_missing_categories_only(self):
        """
        With --force on a partially populated DB, seed must create missing records
        but NOT touch existing ones' is_active.
        """
        from catalog.models.category import Subcategory
        # EDU may already exist from migration 0044. Update it to simulate admin deactivation.
        Category.objects.filter(code="EDU").update(is_active=False)
        # Ensure it actually exists (migration may not have run in test DB)
        Category.objects.get_or_create(
            code="EDU",
            defaults={
                "name_ru": "Образование",
                "name_az": "Təhsil",
                "name_en": "Education",
                "name": "Образование",
                "is_active": False,
                "order": 2,
            },
        )
        # Mark EDU as inactive (simulate admin action)
        Category.objects.filter(code="EDU").update(is_active=False)

        call_command("seed_catalog_taxonomy", "--force", verbosity=0)

        edu = Category.objects.get(code="EDU")
        self.assertFalse(
            edu.is_active,
            "BUG: --force seed restored is_active=True for pre-existing record."
        )
        # Other categories should be created
        self.assertTrue(Category.objects.filter(code="SPRT").exists())


class TestCategorySoftDelete(TestCase):
    """Tests for Category.archive() and Category.restore() soft-delete methods."""

    def setUp(self):
        self.cat = Category.objects.create(
            code="TEST-CAT",
            name_ru="Тест",
            name_az="Test",
            name_en="Test",
            name="Test",
            is_active=True,
            order=99,
        )

    def test_archive_sets_is_active_false_and_deleted_at(self):
        self.cat.archive()
        self.cat.refresh_from_db()
        self.assertFalse(self.cat.is_active)
        self.assertIsNotNone(self.cat.deleted_at)
        self.assertIsNone(self.cat.deleted_by)

    def test_archive_with_user_sets_deleted_by(self):
        User = get_user_model()
        user = User.objects.create_user(username="admin_test", password="pass")
        self.cat.archive(user=user)
        self.cat.refresh_from_db()
        self.assertFalse(self.cat.is_active)
        self.assertEqual(self.cat.deleted_by, user)

    def test_restore_clears_deleted_at_and_sets_active(self):
        self.cat.archive()
        self.cat.restore()
        self.cat.refresh_from_db()
        self.assertTrue(self.cat.is_active)
        self.assertIsNone(self.cat.deleted_at)

    def test_active_manager_excludes_deleted_categories(self):
        Category.objects.create(
            code="ACTIVE-CAT", name_ru="Активная", name="Активная", order=100
        )
        self.cat.archive()
        active_codes = list(Category.active.values_list("code", flat=True))
        self.assertNotIn("TEST-CAT", active_codes)
        self.assertIn("ACTIVE-CAT", active_codes)

    def test_default_manager_includes_deleted_categories(self):
        self.cat.archive()
        self.assertIn(self.cat, Category.objects.all())

    def test_archived_category_not_restored_by_seed_without_force(self):
        """End-to-end: archive category -> run seed -> category stays archived."""
        # Populate via seed
        call_command("seed_catalog_taxonomy", "--force", verbosity=0)
        edu = Category.objects.get(code="EDU")
        edu.archive()

        # Simulate deploy: seed runs without --force
        call_command("seed_catalog_taxonomy", verbosity=0)

        edu.refresh_from_db()
        self.assertFalse(edu.is_active)
        self.assertIsNotNone(edu.deleted_at)


class CatalogSubcategoryFilterTests(TestCase):
    """Задача 22: фильтрация каталога по подкатегориям.

    Подкатегории показываются только внутри выбранной категории и только
    те, за которыми реально есть опубликованные места.
    """

    @classmethod
    def setUpTestData(cls):
        # EDU/SPRT приезжают из миграции с базовой таксономией.
        cls.edu, _ = Category.objects.get_or_create(
            code="EDU", defaults={"name": "Образование", "name_ru": "Образование", "order": 1}
        )
        cls.sport, _ = Category.objects.get_or_create(
            code="SPRT", defaults={"name": "Спорт", "name_ru": "Спорт", "order": 2}
        )

        # Коды с префиксом: часть таксономии уже засеяна миграцией, а code уникален.
        cls.robotics = Subcategory.objects.create(category=cls.edu, code="t22-robotics", name="Робототехника", name_ru="Робототехника")
        cls.languages = Subcategory.objects.create(category=cls.edu, code="t22-languages", name="Языки", name_ru="Языки")
        cls.empty_edu = Subcategory.objects.create(category=cls.edu, code="t22-chess", name="Шахматы", name_ru="Шахматы")
        cls.judo = Subcategory.objects.create(category=cls.sport, code="t22-judo", name="Дзюдо", name_ru="Дзюдо")

        cls.robotics_place = create_quality_place(name="Robotics club", category="EDU", subcategory=cls.robotics)
        cls.languages_place = create_quality_place(name="Language school", category="EDU", subcategory=cls.languages)
        cls.judo_place = create_quality_place(name="Judo academy", category="SPRT", subcategory=cls.judo)

    def _names(self, response):
        return {place.name for place in response.context["places"]}

    def test_selected_subcategory_actually_filters_the_catalog(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU", "subcategory": str(self.robotics.pk)})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._names(response), {"Robotics club"})

    def test_subcategories_are_offered_only_for_the_selected_category(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU"})

        offered = {option["value"] for option in response.context["subcategory_options_for_category"]}
        self.assertIn(str(self.robotics.pk), offered)
        self.assertIn(str(self.languages.pk), offered)
        self.assertNotIn(str(self.judo.pk), offered, "подкатегория чужой категории")

    def test_empty_subcategories_are_not_offered(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU"})

        offered = {option["value"] for option in response.context["subcategory_options_for_category"]}
        self.assertNotIn(str(self.empty_edu.pk), offered, "подкатегория без мест не должна предлагаться")

    def test_block_is_hidden_until_a_category_is_chosen(self):
        response = self.client.get(reverse("place_list"))

        self.assertEqual(response.context["subcategory_options_for_category"], [])
        self.assertNotContains(response, "filter-subcategory")

    def test_block_is_rendered_once_a_category_is_chosen(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU"})

        self.assertContains(response, "filter-subcategory")
        self.assertContains(response, 'data-select-target="subcategory"')

    def test_subcategory_from_a_foreign_category_is_dropped(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU", "subcategory": str(self.judo.pk)})

        self.assertEqual(response.context["selected"]["subcategory"], "")
        self.assertEqual(self._names(response), {"Robotics club", "Language school"})

    def test_subcategory_without_category_selects_its_parent(self):
        """Ссылкой можно поделиться — фильтр должен остаться видимым в сайдбаре."""
        response = self.client.get(reverse("place_list"), {"subcategory": str(self.judo.pk)})

        self.assertEqual(response.context["selected"]["category"], "SPRT")
        self.assertEqual(response.context["selected"]["subcategory"], str(self.judo.pk))
        self.assertEqual(self._names(response), {"Judo academy"})

    def test_garbage_subcategory_is_ignored(self):
        for value in ("abc", "0", "999999"):
            with self.subTest(value=value):
                response = self.client.get(reverse("place_list"), {"category": "EDU", "subcategory": value})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context["selected"]["subcategory"], "")

    def test_subcategory_combines_with_other_filters(self):
        create_quality_place(name="Robotics in Ganja", category="EDU", subcategory=self.robotics, district="Gəncə", age_from=10, age_to=14)

        response = self.client.get(
            reverse("place_list"),
            {"category": "EDU", "subcategory": str(self.robotics.pk), "district": "baku"},
        )

        self.assertEqual(self._names(response), {"Robotics club"}, "район должен сужать выдачу вместе с подкатегорией")

        by_age = self.client.get(
            reverse("place_list"),
            {"category": "EDU", "subcategory": str(self.robotics.pk), "age_from": "13", "age_to": "14"},
        )
        self.assertEqual(self._names(by_age), {"Robotics in Ganja"}, "возраст должен сужать выдачу вместе с подкатегорией")

    def test_subcategory_survives_in_normalized_url_and_has_a_removable_chip(self):
        response = self.client.get(reverse("place_list"), {"category": "EDU", "subcategory": str(self.robotics.pk)})

        self.assertIn(f"subcategory={self.robotics.pk}", response.context["query_without_page"])

        # Метки чипов зависят от языка, поэтому опознаём их по ссылке снятия.
        chips = response.context["active_filter_chips"]
        subcategory_chips = [chip for chip in chips if "Робототехника" in chip["label"]]
        self.assertEqual(len(subcategory_chips), 1)
        self.assertNotIn("subcategory=", subcategory_chips[0]["remove_url"])
        self.assertIn("category=EDU", subcategory_chips[0]["remove_url"], "категория остаётся")

        category_chips = [chip for chip in chips if "category=EDU" not in chip["remove_url"]]
        self.assertTrue(category_chips, "чип категории не найден")
        self.assertNotIn(
            "subcategory=",
            category_chips[0]["remove_url"],
            "снимая категорию, надо снимать и подкатегорию",
        )
