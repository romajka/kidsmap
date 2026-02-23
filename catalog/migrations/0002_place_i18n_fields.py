from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="description_az",
            field=models.TextField(blank=True, default="", verbose_name="Описание (AZ)"),
        ),
        migrations.AddField(
            model_name="place",
            name="description_en",
            field=models.TextField(blank=True, default="", verbose_name="Описание (EN)"),
        ),
        migrations.AddField(
            model_name="place",
            name="description_ru",
            field=models.TextField(blank=True, default="", verbose_name="Описание (RU)"),
        ),
        migrations.AddField(
            model_name="place",
            name="name_az",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Название (AZ)"),
        ),
        migrations.AddField(
            model_name="place",
            name="name_en",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Название (EN)"),
        ),
        migrations.AddField(
            model_name="place",
            name="name_ru",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Название (RU)"),
        ),
    ]
