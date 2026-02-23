from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_place_photo"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="cover_photo",
            field=models.FileField(blank=True, null=True, upload_to="places/covers/", verbose_name="Фото для шапки"),
        ),
        migrations.CreateModel(
            name="PlacePhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.FileField(upload_to="places/gallery/", verbose_name="Фото")),
                ("caption", models.CharField(blank=True, max_length=255, verbose_name="Подпись")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Порядок")),
                (
                    "place",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="gallery", to="catalog.place", verbose_name="Место"),
                ),
            ],
            options={
                "verbose_name": "Фото галереи",
                "verbose_name_plural": "Фото галереи",
                "ordering": ("order", "id"),
            },
        ),
    ]
