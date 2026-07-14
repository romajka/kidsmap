from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0062_place_lesson_details_and_pricing_plans")]

    operations = [
        migrations.AddField(
            model_name="event",
            name="lat",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Широта"),
        ),
        migrations.AddField(
            model_name="event",
            name="lng",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True, verbose_name="Долгота"),
        ),
        migrations.AddField(
            model_name="event",
            name="website",
            field=models.URLField(blank=True, default="", max_length=255, verbose_name="Сайт"),
        ),
    ]
