from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0103_place_review_cooldown"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="home_recommendations_limit",
            field=models.PositiveSmallIntegerField(
                default=4,
                help_text="От 1 до 24. Сначала уберите лишние места из карусели, затем уменьшайте число.",
                validators=[MinValueValidator(1), MaxValueValidator(24)],
                verbose_name="Количество мест в карусели главной",
            ),
        ),
    ]
