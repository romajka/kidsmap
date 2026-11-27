from django.db import migrations


def ensure_xirdalan_city(apps, schema_editor):
    Region = apps.get_model("catalog", "Region")
    Region.objects.using(schema_editor.connection.alias).get_or_create(
        key="xirdalan",
        defaults={
            "name_ru": "Хырдалан",
            "name_az": "Xırdalan",
            "name_en": "Khirdalan",
        },
    )


class Migration(migrations.Migration):
    dependencies = [("catalog", "0149_event_price_registration")]

    # Keep a potentially referenced city on rollback; preserve existing labels.
    operations = [migrations.RunPython(ensure_xirdalan_city, migrations.RunPython.noop)]
