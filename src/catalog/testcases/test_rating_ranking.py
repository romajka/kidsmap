from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Place, RatingRankingCalibration
from catalog.services.filtering import PlaceListFilters
from catalog.services.rating_ranking import (
    RatingCalibrationValues,
    calculate_weighted_rating,
    derive_rating_calibration,
)
from catalog.testcases.utils import create_quality_place


class RatingRankingMathTests(TestCase):
    def test_small_perfect_sample_is_below_large_stable_sample(self):
        calibration = RatingCalibrationValues(prior_mean=4.0, prior_weight=15.0)

        one_review = calculate_weighted_rating(
            rating_avg=5.0,
            rating_count=1,
            calibration=calibration,
        )
        stable_rating = calculate_weighted_rating(
            rating_avg=4.3,
            rating_count=100,
            calibration=calibration,
        )

        self.assertAlmostEqual(one_review, 4.0625)
        self.assertAlmostEqual(stable_rating, 4.2608695652)
        self.assertLess(one_review, stable_rating)

    def test_unrated_place_has_no_internal_score(self):
        calibration = RatingCalibrationValues(prior_mean=4.0, prior_weight=15.0)
        self.assertIsNone(
            calculate_weighted_rating(
                rating_avg=0.0,
                rating_count=0,
                calibration=calibration,
            )
        )

    def test_invalid_formula_inputs_are_rejected(self):
        calibration = RatingCalibrationValues(prior_mean=4.0, prior_weight=15.0)
        for rating_avg, rating_count in ((0, 1), (6, 1), (4, -1), (float("nan"), 1)):
            with self.subTest(rating_avg=rating_avg, rating_count=rating_count):
                with self.assertRaises(ValueError):
                    calculate_weighted_rating(
                        rating_avg=rating_avg,
                        rating_count=rating_count,
                        calibration=calibration,
                    )

    def test_calibration_derivation_uses_population_variance(self):
        values = derive_rating_calibration(
            rating_count=40,
            rating_sum=160,
            rating_sum_squares=680,
            rated_place_count=12,
            confidence_z=1.96,
            margin_stars=0.5,
        )

        self.assertEqual(values.prior_mean, 4.0)
        self.assertEqual(values.prior_weight, 16.0)
        self.assertEqual(values.population_standard_deviation, 1.0)

    def test_calibration_requires_a_meaningful_population(self):
        with self.assertRaises(ValueError):
            derive_rating_calibration(
                rating_count=29,
                rating_sum=116,
                rating_sum_squares=500,
                rated_place_count=10,
                confidence_z=1.96,
                margin_stars=0.5,
            )


class RatingRankingCatalogueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = get_user_model().objects.create_superuser(
            username="rating-calibration-owner",
            email="rating-owner@example.test",
            password="test-password",
        )
        cls.calibration = RatingRankingCalibration.objects.create(
            version=1,
            status=RatingRankingCalibration.Status.ACTIVE,
            prior_mean="4.00000",
            prior_weight="15.0000",
            population_review_count=100,
            population_place_count=20,
            population_rating_sum=400,
            population_rating_sum_squares=1696,
            population_standard_deviation="0.97980",
            confidence_z="1.9600",
            margin_stars="0.500",
            source_cutoff=timezone.now(),
            activated_at=timezone.now(),
            activated_by=cls.actor,
        )
        now = timezone.now()
        cls.single = create_quality_place(
            name="Single 5.0", rating_avg=5.0, rating_count=1, created_at=now - timedelta(days=1)
        )
        cls.stable = create_quality_place(
            name="Stable 4.3", rating_avg=4.3, rating_count=100, created_at=now - timedelta(days=2)
        )
        cls.supported = create_quality_place(
            name="Supported 4.8", rating_avg=4.8, rating_count=20, created_at=now - timedelta(days=3)
        )
        cls.unrated = create_quality_place(
            name="Unrated", rating_avg=0, rating_count=0, created_at=now
        )

    def test_rating_sort_uses_bayesian_order_and_keeps_real_values(self):
        response = self.client.get(reverse("place_list"), {"sort": "rating"})

        self.assertEqual(response.status_code, 200)
        names = [place.name for place in response.context["places"]]
        self.assertLess(names.index(self.supported.name), names.index(self.stable.name))
        self.assertLess(names.index(self.stable.name), names.index(self.single.name))
        self.assertLess(names.index(self.single.name), names.index(self.unrated.name))
        ranked_single = next(place for place in response.context["places"] if place.pk == self.single.pk)
        self.assertEqual(ranked_single.rating_avg, 5.0)
        self.assertEqual(ranked_single.rating_count, 1)
        self.assertContains(response, "5.0")
        self.assertNotContains(response, "4.0625")
        self.assertNotContains(response, "rating_rank_score")
        self.assertIn("sort=rating", response.context["query_without_page"])
        map_item = next(item for item in response.context["catalog_map_places"] if item["id"] == self.single.pk)
        self.assertEqual(map_item["rating"], 5.0)
        self.assertEqual(map_item["reviews_count"], 1)
        self.assertNotIn("rating_rank_score", map_item)

    def test_rating_sort_option_is_localized_and_selected(self):
        expected = {
            "az": "Reytinq üzrə",
            "ru": "По рейтингу",
            "en": "Highest rated",
        }

        for language_code, label in expected.items():
            with self.subTest(language_code=language_code), override(language_code):
                response = self.client.get(reverse("place_list"), {"sort": "rating"})
                self.assertContains(response, label)
                self.assertContains(response, '<option value="rating" selected>', html=False)

    def test_azerbaijani_review_count_sort_is_not_called_popularity(self):
        with override("az"):
            response = self.client.get(reverse("place_list"))

        self.assertContains(response, "Ən çox rəy alanlar")
        self.assertNotContains(response, "Əvvəlcə populyar")

    def test_rating_sort_has_deterministic_tie_breakers(self):
        first = create_quality_place(name="Tie older", rating_avg=4.5, rating_count=10)
        second = create_quality_place(name="Tie newer", rating_avg=4.5, rating_count=10)
        Place.objects.filter(pk=first.pk).update(created_at=timezone.now() - timedelta(hours=1))
        Place.objects.filter(pk=second.pk).update(created_at=timezone.now())

        qs = PlaceListFilters(sort="rating").apply(Place.objects.filter(pk__in=[first.pk, second.pk]))

        self.assertEqual(list(qs.values_list("pk", flat=True)), [second.pk, first.pk])

    def test_rating_sort_reads_calibration_once_without_per_place_queries(self):
        filters = PlaceListFilters(sort="rating")

        with CaptureQueriesContext(connection) as queries:
            list(filters.apply(Place.objects.all()))

        calibration_queries = [
            query for query in queries.captured_queries
            if "catalog_ratingrankingcalibration" in query["sql"].lower()
        ]
        self.assertEqual(len(calibration_queries), 1)

    def test_missing_calibration_normalizes_rating_to_new(self):
        RatingRankingCalibration.objects.all().delete()

        response = self.client.get(reverse("place_list"), {"sort": "rating"})

        self.assertEqual(response.context["selected"]["sort"], "new")
        self.assertFalse(response.context["rating_sort_available"])
        self.assertNotContains(response, '<option value="rating"', html=False)

    def test_invalid_active_calibration_disables_rating_sort(self):
        RatingRankingCalibration.objects.filter(pk=self.calibration.pk).update(prior_weight="14.0000")

        response = self.client.get(reverse("place_list"), {"sort": "rating"})

        self.assertEqual(response.context["selected"]["sort"], "new")
        self.assertFalse(response.context["rating_sort_available"])
