from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0063_event_location_contacts")]

    operations = [
        migrations.AddField(
            model_name="event",
            name="district",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Регион / район"),
        ),
        migrations.AddField(
            model_name="event",
            name="metro",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Метро"),
        ),
    ]
