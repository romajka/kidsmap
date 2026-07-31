from django.conf import settings
from django.db import migrations, models


def fill_place_creator_from_first_audit(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    PlaceChangeAudit = apps.get_model("catalog", "PlaceChangeAudit")

    for place in Place.objects.filter(created_by__isnull=True).iterator():
        creator_id = (
            PlaceChangeAudit.objects.filter(place_id=place.pk, changed_by__isnull=False)
            .order_by("created_at", "pk")
            .values_list("changed_by_id", flat=True)
            .first()
        )
        if creator_id:
            Place.objects.filter(pk=place.pk, created_by__isnull=True).update(created_by_id=creator_id)


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0077_place_age_open_ended"),
    ]

    operations = [
        migrations.AddField(
            model_name="place",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name="created_places",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Кто добавил",
            ),
        ),
        migrations.RunPython(fill_place_creator_from_first_audit, migrations.RunPython.noop),
    ]
