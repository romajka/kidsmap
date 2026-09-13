from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [("catalog", "0110_public_favorites_activation_constraint")]

    operations = [
        migrations.CreateModel(
            name="AnalyticsIngressDaily",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day", models.DateField(default=django.utils.timezone.localdate, unique=True)),
                ("accepted_count", models.PositiveBigIntegerField(default=0)),
                ("rejected_count", models.PositiveBigIntegerField(default=0)),
                ("rate_limited_count", models.PositiveBigIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Дневное качество аналитики", "verbose_name_plural": "Дневное качество аналитики"},
        )
    ]
