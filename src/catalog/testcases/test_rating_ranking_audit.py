from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import PlaceReview
from catalog.services.rating_ranking import (
    activate_rating_calibration,
    build_place_rating_calibration_proposal,
)
from catalog.testcases.utils import create_quality_place


class RatingRankingAuditTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser(
            username="rating-audit-admin",
            email="rating-audit@example.test",
            password="test-password",
        )
        self.places = []
        for place_index in range(10):
            place = create_quality_place(name=f"Audit place {place_index}")
            self.places.append(place)
            for review_index in range(3):
                PlaceReview.objects.create(
                    place=place,
                    author_name=f"Audit reviewer {place_index}-{review_index}",
                    rating=4,
                    text="Useful review for aggregate validation.",
                    status=PlaceReview.STATUS_APPROVED,
                    is_approved=True,
                )
        activate_rating_calibration(
            calibration=build_place_rating_calibration_proposal(
                confidence_z=1.96,
                margin_stars=0.5,
            ),
            actor=self.actor,
        )

    def test_audit_reports_aggregate_health(self):
        output = StringIO()

        call_command("audit_place_rating_ranking", stdout=output)

        rendered = output.getvalue()
        self.assertIn("active_calibration_count=1", rendered)
        self.assertIn("rating_aggregate_mismatch_count=0", rendered)
        self.assertNotIn("Audit reviewer", rendered)

    def test_audit_fails_when_a_place_aggregate_is_stale(self):
        type(self.places[0]).objects.filter(pk=self.places[0].pk).update(
            rating_avg=1.0,
            rating_count=99,
        )

        with self.assertRaises(CommandError):
            call_command("audit_place_rating_ranking", stdout=StringIO())
