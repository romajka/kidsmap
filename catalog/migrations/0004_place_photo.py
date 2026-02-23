from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_place_catalog_improvements"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="photo",
            field=models.FileField(blank=True, null=True, upload_to="places/", verbose_name="Фото"),
        ),
    ]
