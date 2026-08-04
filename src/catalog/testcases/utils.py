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
        "photo": "places/quality_test.jpg",
        "is_active": True,
        "status": Place.STATUS_PUBLISHED,
    }
    defaults.update(overrides)
    return Place.objects.create(**defaults)

def build_structured_schedule_payload():
    return dump_schedule_payload(
        [
            {"weekday": "mon", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "18:00"}]},
            {"weekday": "tue", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "18:00"}]},
            {"weekday": "wed", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "18:00"}]},
            {"weekday": "thu", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "18:00"}]},
            {"weekday": "fri", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "09:00", "end": "18:00"}]},
            {"weekday": "sat", "is_closed": False, "is_24_hours": False, "intervals": [{"start": "10:00", "end": "16:00"}]},
            {"weekday": "sun", "is_closed": True, "is_24_hours": False, "intervals": []},
        ]
    )
