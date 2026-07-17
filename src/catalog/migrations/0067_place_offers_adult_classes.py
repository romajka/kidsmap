from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0066_sitesettings_events_section_enabled"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="offers_adult_classes",
            field=models.BooleanField(default=False, verbose_name="Также есть занятия для взрослых"),
        ),
    ]
