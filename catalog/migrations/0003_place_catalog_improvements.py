from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_place_i18n_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Активно"),
        ),
        migrations.AddField(
            model_name="place",
            name="lat",
            field=models.FloatField(blank=True, null=True, verbose_name="Широта"),
        ),
        migrations.AddField(
            model_name="place",
            name="lng",
            field=models.FloatField(blank=True, null=True, verbose_name="Долгота"),
        ),
        migrations.AddField(
            model_name="place",
            name="schedule",
            field=models.TextField(blank=True, verbose_name="Расписание"),
        ),
        migrations.AddField(
            model_name="place",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Обновлено"),
        ),
        migrations.AddField(
            model_name="place",
            name="website",
            field=models.URLField(blank=True, verbose_name="Сайт"),
        ),
    ]
