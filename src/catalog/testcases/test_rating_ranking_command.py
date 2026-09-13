from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalog.models import Place, PlaceReview, RatingRankingCalibration
from catalog.testcases.utils import create_quality_place


class RatingRankingCalibrationCommandTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser(
            username="rating-command-admin",
            email="rating-command@example.test",
            password="test-password",
        )
        self.places = []
        for place_index in range(10):
            place = create_quality_place(name=f"Calibration place {place_index}")
            self.places.append(place)
            for review_index in range(3):
                PlaceReview.objects.create(
                    place=place,
                    author_name=f"Reviewer {place_index}-{review_index}",
                    rating=4 if review_index else 5,
                    text="A detailed and useful family review.",
                    status=PlaceReview.STATUS_APPROVED,
                    is_approved=True,
                )

    def test_dry_run_outputs_only_aggregate_proposal_and_writes_nothing(self):
        public_place = self.places[0]
        PlaceReview.objects.create(
            place=public_place,
            author_name="Pending reviewer",
            rating=5,
            text="Pending review text.",
            status=PlaceReview.STATUS_PENDING,
            is_approved=False,
        )
        PlaceReview.objects.create(
            place=public_place,
            author_name="Junk reviewer",
            rating=5,
            text="test",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )
        private_place = create_quality_place(name="Private calibration place", status=Place.STATUS_DRAFT)
        PlaceReview.objects.create(
            place=private_place,
            author_name="Private reviewer",
            rating=5,
            text="A valid review on a non-public Place.",
            status=PlaceReview.STATUS_APPROVED,
            is_approved=True,
        )
        output = StringIO()

        call_command(
            "calibrate_place_rating_ranking",
            "--confidence-z=1.96",
            "--margin-stars=0.5",
            "--dry-run",
            stdout=output,
        )

        rendered = output.getvalue()
        self.assertIn("population_review_count=30", rendered)
        self.assertIn("population_place_count=10", rendered)
        self.assertNotIn("Reviewer", rendered)
        self.assertFalse(RatingRankingCalibration.objects.exists())

    def test_activate_creates_an_active_version(self):
        call_command(
            "calibrate_place_rating_ranking",
            "--confidence-z=1.96",
            "--margin-stars=0.5",
            "--activate",
            f"--actor-user-id={self.actor.pk}",
            stdout=StringIO(),
        )

        calibration = RatingRankingCalibration.objects.get()
        self.assertEqual(calibration.status, RatingRankingCalibration.Status.ACTIVE)
        self.assertEqual(calibration.activated_by, self.actor)

    def test_rollback_command_clones_the_requested_version(self):
        for _ in range(2):
            call_command(
                "calibrate_place_rating_ranking",
                "--confidence-z=1.96",
                "--margin-stars=0.5",
                "--activate",
                f"--actor-user-id={self.actor.pk}",
                stdout=StringIO(),
            )
        output = StringIO()

        call_command(
            "rollback_place_rating_ranking",
            "--to-version=1",
            f"--actor-user-id={self.actor.pk}",
            stdout=output,
        )

        active = RatingRankingCalibration.objects.get(status=RatingRankingCalibration.Status.ACTIVE)
        self.assertEqual(active.version, 3)
        self.assertIn("rollback_source_version=1 activated_version=3", output.getvalue())
