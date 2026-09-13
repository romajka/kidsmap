import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0111_analytics_ingress_daily"),
    ]

    operations = [
        migrations.CreateModel(
            name="RatingRankingCalibration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("version", models.PositiveIntegerField(unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Черновик"), ("active", "Активна"), ("retired", "Архивная")],
                        db_index=True,
                        default="draft",
                        max_length=16,
                    ),
                ),
                ("prior_mean", models.DecimalField(decimal_places=5, max_digits=7)),
                ("prior_weight", models.DecimalField(decimal_places=4, max_digits=9)),
                ("population_review_count", models.PositiveIntegerField()),
                ("population_place_count", models.PositiveIntegerField()),
                ("population_rating_sum", models.PositiveBigIntegerField()),
                ("population_rating_sum_squares", models.PositiveBigIntegerField()),
                ("population_standard_deviation", models.DecimalField(decimal_places=5, max_digits=7)),
                ("confidence_z", models.DecimalField(decimal_places=4, max_digits=6)),
                ("margin_stars", models.DecimalField(decimal_places=3, max_digits=5)),
                ("source_cutoff", models.DateTimeField()),
                ("calculated_at", models.DateTimeField(auto_now_add=True)),
                ("activated_at", models.DateTimeField(blank=True, null=True)),
                (
                    "activated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="activated_rating_calibrations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Калибровка сортировки по рейтингу",
                "verbose_name_plural": "Калибровки сортировки по рейтингу",
                "ordering": ("-version",),
                "constraints": [
                    models.UniqueConstraint(
                        condition=models.Q(("status", "active")),
                        fields=("status",),
                        name="unique_active_rating_calibration",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("prior_mean__gte", 1), ("prior_mean__lte", 5)),
                        name="rating_calibration_mean_range",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("prior_weight__gt", 0)),
                        name="rating_calibration_weight_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("population_review_count__gte", 30), ("population_place_count__gte", 10)),
                        name="rating_calibration_population_minimum",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("population_rating_sum__gt", 0), ("population_rating_sum_squares__gt", 0)),
                        name="rating_calibration_sums_positive",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("population_standard_deviation__gte", 0)),
                        name="rating_calibration_stddev_nonnegative",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("confidence_z__gt", 0), ("margin_stars__gt", 0)),
                        name="rating_calibration_policy_positive",
                    ),
                    models.CheckConstraint(
                        condition=(
                            models.Q(("activated_at__isnull", True), ("status", "draft"))
                            | models.Q(("activated_at__isnull", False), ("status__in", ("active", "retired")))
                        ),
                        name="rating_calibration_activation_time",
                    ),
                ],
            },
        ),
    ]
