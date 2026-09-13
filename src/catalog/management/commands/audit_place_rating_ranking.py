import math

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg, Count
from django.utils import timezone

from catalog.models import Place, PlaceReview, RatingRankingCalibration
from catalog.services.content_quality import public_place_queryset, public_review_queryset
from catalog.services.rating_ranking import validate_rating_calibration


class Command(BaseCommand):
    help = "Read-only aggregate integrity audit for Bayesian Place-rating sorting."

    def handle(self, *args, **options):
        active = list(
            RatingRankingCalibration.objects.filter(
                status=RatingRankingCalibration.Status.ACTIVE
            )[:2]
        )
        active_count = len(active)
        self.stdout.write(f"active_calibration_count={active_count}")
        problems = []
        if active_count != 1:
            problems.append("exactly one active calibration is required")

        calibration = active[0] if active_count == 1 else None
        calibration_valid = False
        if calibration is not None:
            try:
                validate_rating_calibration(calibration)
                calibration_valid = True
            except (TypeError, ValueError):
                problems.append("active calibration values are invalid")
        self.stdout.write(f"active_calibration_valid={str(calibration_valid).lower()}")

        public_places = list(
            public_place_queryset(Place.objects.all())
            .order_by()
            .values("pk", "rating_avg", "rating_count")
        )
        place_ids = [row["pk"] for row in public_places]
        review_stats = {
            row["place_id"]: row
            for row in public_review_queryset(PlaceReview.objects.filter(place_id__in=place_ids))
            .values("place_id")
            .annotate(expected_count=Count("pk"), expected_average=Avg("rating"))
        }
        mismatch_count = 0
        for place in public_places:
            expected = review_stats.get(place["pk"], {})
            expected_count = int(expected.get("expected_count") or 0)
            expected_average = float(expected.get("expected_average") or 0)
            if int(place["rating_count"] or 0) != expected_count or not math.isclose(
                float(place["rating_avg"] or 0), expected_average, abs_tol=0.00001
            ):
                mismatch_count += 1
        self.stdout.write(f"rating_aggregate_mismatch_count={mismatch_count}")
        if mismatch_count:
            problems.append("stored Place rating aggregates are stale")

        eligible_review_count = public_review_queryset(
            PlaceReview.objects.filter(place_id__in=place_ids)
        ).count()
        self.stdout.write(f"eligible_review_count={eligible_review_count}")
        if calibration is not None:
            growth = max(eligible_review_count - calibration.population_review_count, 0)
            growth_percent = (
                growth * 100 / calibration.population_review_count
                if calibration.population_review_count
                else 0
            )
            age_days = max((timezone.now() - calibration.source_cutoff).days, 0)
            self.stdout.write(f"active_calibration_age_days={age_days}")
            self.stdout.write(f"eligible_population_growth_percent={growth_percent:.2f}")
            self.stdout.write(
                f"recalibration_recommended={str(growth_percent >= 20 or age_days >= 92).lower()}"
            )

        if problems:
            raise CommandError("; ".join(problems))
        self.stdout.write(self.style.SUCCESS("rating_ranking_integrity=ok"))
