from django.db import migrations


def ensure_absheron_region(apps, schema_editor):
    Region = apps.get_model("catalog", "Region")
    Region.objects.update_or_create(
        key="absheron",
        defaults={
            "name_ru": "Абшерон",
            "name_az": "Abşeron",
            "name_en": "Absheron",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0073_postgresql_native_constraints"),
    ]

    operations = [
        migrations.RunPython(ensure_absheron_region, migrations.RunPython.noop),
    ]
