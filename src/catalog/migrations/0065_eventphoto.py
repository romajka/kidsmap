import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0064_event_location_filters")]

    operations = [
        migrations.CreateModel(
            name="EventPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.FileField(upload_to="events/gallery/", verbose_name="Фото")),
                ("caption", models.CharField(blank=True, max_length=255, verbose_name="Подпись")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="gallery", to="catalog.event", verbose_name="Мероприятие")),
            ],
            options={"verbose_name": "Фото мероприятия", "verbose_name_plural": "Фотографии мероприятия", "ordering": ("order", "id")},
        ),
    ]
