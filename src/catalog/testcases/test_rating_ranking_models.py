from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from catalog.models import RatingRankingCalibration
from catalog.services.rating_ranking import (
    activate_rating_calibration,
    clone_and_activate_rating_calibration,
)


class RatingRankingCalibrationModelTests(TestCase):
    def setUp(self):
        self.actor = get_user_model().objects.create_superuser(
            username="calibration-admin",
            email="calibration-admin@example.test",
            password="test-password",
        )

    def proposal(self, *, version=1):
        return RatingRankingCalibration.objects.create(
            version=version,
            prior_mean=Decimal("4.00000"),
            prior_weight=Decimal("1.0000"),
            population_review_count=40,
            population_place_count=12,
            population_rating_sum=160,
            population_rating_sum_squares=640,
            population_standard_deviation=Decimal("0.00000"),
            confidence_z=Decimal("1.9600"),
            margin_stars=Decimal("0.500"),
            source_cutoff=timezone.now(),
        )

    def test_activation_retires_previous_and_records_actor(self):
        first = activate_rating_calibration(calibration=self.proposal(version=1), actor=self.actor)
        second = activate_rating_calibration(calibration=self.proposal(version=2), actor=self.actor)

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.status, RatingRankingCalibration.Status.RETIRED)
        self.assertEqual(second.status, RatingRankingCalibration.Status.ACTIVE)
        self.assertEqual(second.activated_by, self.actor)
        self.assertIsNotNone(second.activated_at)

    def test_activation_requires_an_active_superuser(self):
        ordinary_staff = get_user_model().objects.create_user(
            username="ordinary-staff", is_staff=True, password="test-password"
        )

        with self.assertRaises(PermissionError):
            activate_rating_calibration(calibration=self.proposal(), actor=ordinary_staff)

    def test_active_calibration_is_immutable(self):
        calibration = activate_rating_calibration(calibration=self.proposal(), actor=self.actor)
        calibration.prior_mean = Decimal("4.10000")

        with self.assertRaises(ValidationError):
            calibration.save()

    def test_database_allows_only_one_active_calibration(self):
        activate_rating_calibration(calibration=self.proposal(version=1), actor=self.actor)

        with self.assertRaises(IntegrityError), transaction.atomic():
            RatingRankingCalibration.objects.create(
                version=2,
                status=RatingRankingCalibration.Status.ACTIVE,
                prior_mean=Decimal("4.00000"),
                prior_weight=Decimal("1.0000"),
                population_review_count=40,
                population_place_count=12,
                population_rating_sum=160,
                population_rating_sum_squares=640,
                population_standard_deviation=Decimal("0.00000"),
                confidence_z=Decimal("1.9600"),
                margin_stars=Decimal("0.500"),
                source_cutoff=timezone.now(),
                activated_at=timezone.now(),
                activated_by=self.actor,
            )

    def test_rollback_clones_a_retired_version_without_mutating_history(self):
        first = activate_rating_calibration(calibration=self.proposal(version=1), actor=self.actor)
        activate_rating_calibration(calibration=self.proposal(version=2), actor=self.actor)

        rollback = clone_and_activate_rating_calibration(source_version=first.version, actor=self.actor)

        first.refresh_from_db()
        self.assertEqual(first.status, RatingRankingCalibration.Status.RETIRED)
        self.assertEqual(rollback.version, 3)
        self.assertEqual(rollback.status, RatingRankingCalibration.Status.ACTIVE)
        self.assertEqual(rollback.prior_mean, first.prior_mean)
        self.assertEqual(rollback.source_cutoff, first.source_cutoff)
