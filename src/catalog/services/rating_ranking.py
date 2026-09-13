from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import (
    Count,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    QuerySet,
    Sum,
    Value,
    Case,
    When,
)
from django.utils import timezone


@dataclass(frozen=True, slots=True)
class RatingCalibrationValues:
    prior_mean: float
    prior_weight: float
    population_standard_deviation: float = 0.0

    def __post_init__(self):
        values = (self.prior_mean, self.prior_weight, self.population_standard_deviation)
        if not all(math.isfinite(float(value)) for value in values):
            raise ValueError("Calibration values must be finite.")
        if not 1 <= float(self.prior_mean) <= 5:
            raise ValueError("Prior mean must be between 1 and 5.")
        if float(self.prior_weight) <= 0:
            raise ValueError("Prior weight must be positive.")
        if float(self.population_standard_deviation) < 0:
            raise ValueError("Population standard deviation cannot be negative.")


def calculate_weighted_rating(
    *,
    rating_avg: float,
    rating_count: int,
    calibration: RatingCalibrationValues,
) -> float | None:
    count = int(rating_count)
    average = float(rating_avg)
    if count < 0:
        raise ValueError("Rating count cannot be negative.")
    if count == 0:
        return None
    if not math.isfinite(average) or not 1 <= average <= 5:
        raise ValueError("Rating average must be finite and between 1 and 5.")
    numerator = math.fsum((count * average, calibration.prior_weight * calibration.prior_mean))
    return numerator / (count + calibration.prior_weight)


def derive_rating_calibration(
    *,
    rating_count: int,
    rating_sum: int,
    rating_sum_squares: int,
    rated_place_count: int,
    confidence_z: float,
    margin_stars: float,
) -> RatingCalibrationValues:
    count = int(rating_count)
    place_count = int(rated_place_count)
    rating_total = int(rating_sum)
    square_total = int(rating_sum_squares)
    z_value = float(confidence_z)
    margin = float(margin_stars)
    if count < 30 or place_count < 10:
        raise ValueError("Calibration requires at least 30 reviews across 10 public Places.")
    if not math.isfinite(z_value) or not math.isfinite(margin) or z_value <= 0 or margin <= 0:
        raise ValueError("Confidence and margin must be positive finite values.")
    prior_mean = rating_total / count
    variance = max(0.0, square_total / count - prior_mean**2)
    standard_deviation = math.sqrt(variance)
    prior_weight = max(1, math.ceil((z_value * standard_deviation / margin) ** 2))
    return RatingCalibrationValues(
        prior_mean=prior_mean,
        prior_weight=float(prior_weight),
        population_standard_deviation=standard_deviation,
    )


def _values_from_calibration(calibration, *, verify_derivation: bool = False) -> RatingCalibrationValues:
    values = RatingCalibrationValues(
        prior_mean=float(calibration.prior_mean),
        prior_weight=float(calibration.prior_weight),
        population_standard_deviation=float(calibration.population_standard_deviation),
    )
    if verify_derivation:
        derived = derive_rating_calibration(
            rating_count=calibration.population_review_count,
            rating_sum=calibration.population_rating_sum,
            rating_sum_squares=calibration.population_rating_sum_squares,
            rated_place_count=calibration.population_place_count,
            confidence_z=float(calibration.confidence_z),
            margin_stars=float(calibration.margin_stars),
        )
        if not math.isclose(values.prior_mean, derived.prior_mean, abs_tol=0.00001):
            raise ValueError("Stored prior mean does not match its population.")
        if not math.isclose(values.prior_weight, derived.prior_weight, abs_tol=0.0001):
            raise ValueError("Stored prior weight does not match its population.")
        if not math.isclose(
            values.population_standard_deviation,
            derived.population_standard_deviation,
            abs_tol=0.00001,
        ):
            raise ValueError("Stored standard deviation does not match its population.")
    return values


def validate_rating_calibration(calibration) -> RatingCalibrationValues:
    return _values_from_calibration(calibration, verify_derivation=True)


def get_active_rating_calibration():
    from catalog.models import RatingRankingCalibration

    calibration = RatingRankingCalibration.objects.filter(
        status=RatingRankingCalibration.Status.ACTIVE
    ).first()
    if calibration is None:
        return None
    try:
        _values_from_calibration(calibration, verify_derivation=True)
    except (TypeError, ValueError):
        return None
    return calibration


def rating_sort_is_available() -> bool:
    return get_active_rating_calibration() is not None


def apply_weighted_rating_ordering(queryset: QuerySet, calibration) -> QuerySet:
    values = _values_from_calibration(calibration)
    prior_weight = float(values.prior_weight)
    prior_total = prior_weight * float(values.prior_mean)
    score = ExpressionWrapper(
        (F("rating_count") * F("rating_avg") + Value(prior_total))
        / (F("rating_count") + Value(prior_weight)),
        output_field=FloatField(),
    )
    return queryset.annotate(
        rating_rank_has_reviews=Case(
            When(rating_count__gt=0, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        ),
        rating_rank_score=Case(
            When(rating_count__gt=0, then=score),
            default=Value(None),
            output_field=FloatField(),
        ),
    ).order_by(
        "-rating_rank_has_reviews",
        "-rating_rank_score",
        "-rating_count",
        "-rating_avg",
        "-created_at",
        "-pk",
    )


def build_place_rating_calibration_proposal(
    *,
    confidence_z: float,
    margin_stars: float,
    source_cutoff=None,
):
    from catalog.models import Place, PlaceReview, RatingRankingCalibration
    from catalog.services.content_quality import public_place_queryset, public_review_queryset

    cutoff = source_cutoff or timezone.now()
    public_place_ids = public_place_queryset(Place.objects.all()).order_by().values("pk")
    square = ExpressionWrapper(F("rating") * F("rating"), output_field=IntegerField())
    population = public_review_queryset(
        PlaceReview.objects.filter(place_id__in=public_place_ids, created_at__lte=cutoff)
    ).aggregate(
        review_count=Count("pk"),
        place_count=Count("place_id", distinct=True),
        rating_sum=Sum("rating"),
        rating_sum_squares=Sum(square),
    )
    values = derive_rating_calibration(
        rating_count=int(population["review_count"] or 0),
        rating_sum=int(population["rating_sum"] or 0),
        rating_sum_squares=int(population["rating_sum_squares"] or 0),
        rated_place_count=int(population["place_count"] or 0),
        confidence_z=confidence_z,
        margin_stars=margin_stars,
    )
    next_version = (RatingRankingCalibration.objects.aggregate(value=Max("version"))["value"] or 0) + 1
    return RatingRankingCalibration(
        version=next_version,
        prior_mean=Decimal(f"{values.prior_mean:.5f}"),
        prior_weight=Decimal(f"{values.prior_weight:.4f}"),
        population_review_count=int(population["review_count"]),
        population_place_count=int(population["place_count"]),
        population_rating_sum=int(population["rating_sum"]),
        population_rating_sum_squares=int(population["rating_sum_squares"]),
        population_standard_deviation=Decimal(f"{values.population_standard_deviation:.5f}"),
        confidence_z=Decimal(f"{float(confidence_z):.4f}"),
        margin_stars=Decimal(f"{float(margin_stars):.3f}"),
        source_cutoff=cutoff,
    )


@transaction.atomic
def activate_rating_calibration(*, calibration, actor, now=None):
    from catalog.models import RatingRankingCalibration

    if not actor or not actor.is_active or not actor.is_staff or not actor.is_superuser:
        raise PermissionError("An active superuser must activate rating calibration.")
    _values_from_calibration(calibration, verify_derivation=True)
    if calibration.pk is None:
        calibration.save()
    calibration = RatingRankingCalibration.objects.select_for_update().get(pk=calibration.pk)
    if calibration.status != RatingRankingCalibration.Status.DRAFT:
        raise ValueError("Only a draft calibration can be activated.")
    active_rows = list(
        RatingRankingCalibration.objects.select_for_update().filter(
            status=RatingRankingCalibration.Status.ACTIVE
        )
    )
    for active in active_rows:
        active.status = RatingRankingCalibration.Status.RETIRED
        active._allow_calibration_transition = True
        active.save(update_fields=("status",))
        del active._allow_calibration_transition
    calibration.status = RatingRankingCalibration.Status.ACTIVE
    calibration.activated_at = now or timezone.now()
    calibration.activated_by = actor
    calibration._allow_calibration_transition = True
    calibration.save(update_fields=("status", "activated_at", "activated_by"))
    del calibration._allow_calibration_transition
    return calibration


@transaction.atomic
def clone_and_activate_rating_calibration(*, source_version: int, actor, now=None):
    """Rollback by activating a new immutable version copied from a prior snapshot."""

    from catalog.models import RatingRankingCalibration

    source = RatingRankingCalibration.objects.select_for_update().filter(
        version=source_version,
        status__in=(
            RatingRankingCalibration.Status.ACTIVE,
            RatingRankingCalibration.Status.RETIRED,
        ),
    ).first()
    if source is None:
        raise ValueError("Rollback source must be an active or retired calibration version.")
    next_version = (RatingRankingCalibration.objects.aggregate(value=Max("version"))["value"] or 0) + 1
    clone = RatingRankingCalibration(
        version=next_version,
        prior_mean=source.prior_mean,
        prior_weight=source.prior_weight,
        population_review_count=source.population_review_count,
        population_place_count=source.population_place_count,
        population_rating_sum=source.population_rating_sum,
        population_rating_sum_squares=source.population_rating_sum_squares,
        population_standard_deviation=source.population_standard_deviation,
        confidence_z=source.confidence_z,
        margin_stars=source.margin_stars,
        source_cutoff=source.source_cutoff,
    )
    return activate_rating_calibration(calibration=clone, actor=actor, now=now)
