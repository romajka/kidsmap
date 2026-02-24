from django.db import migrations, models
from django.utils.text import slugify


def fill_place_slugs(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    used = set(Place.objects.exclude(slug="").values_list("slug", flat=True))

    for place in Place.objects.all().order_by("id"):
        if place.slug:
            continue

        source = place.name_ru or place.name or place.name_en or place.name_az or f"place-{place.id}"
        base = slugify(source, allow_unicode=True) or f"place-{place.id}"
        candidate = base
        idx = 2
        while candidate in used:
            candidate = f"{base}-{idx}"
            idx += 1

        place.slug = candidate
        place.save(update_fields=["slug"])
        used.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0005_place_cover_and_gallery"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="slug",
            field=models.SlugField(blank=True, db_index=True, default="", max_length=255, verbose_name="Slug"),
        ),
        migrations.RunPython(fill_place_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="place",
            name="slug",
            field=models.SlugField(blank=True, default="", max_length=255, unique=True, verbose_name="Slug"),
        ),
    ]
