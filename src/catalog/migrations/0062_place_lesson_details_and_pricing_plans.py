from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0061_sitevisibilitysettings")]

    operations = [
        migrations.AddField(
            model_name="place",
            name="lesson_format",
            field=models.CharField(blank=True, default="", max_length=16, choices=[("group", "Групповые"), ("individual", "Индивидуальные")], verbose_name="Формат занятий"),
        ),
        migrations.AddField(
            model_name="place",
            name="lessons_per_week",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Занятий в неделю"),
        ),
        migrations.AddField(
            model_name="place",
            name="lessons_per_month",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Занятий в месяц"),
        ),
        migrations.AddField(
            model_name="place",
            name="pricing_plans",
            field=models.JSONField(blank=True, default=list, verbose_name="Тарифы"),
        ),
    ]
