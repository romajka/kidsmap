from django.db import migrations, models, transaction


CATEGORY_MOVES = {
    "BEACH": "water-leisure",
    "WATERPARK": "water-leisure",
    "PARK": "parks-playgrounds",
}

CATEGORY_NAME_MOVES = {
    "пляжи": "water-leisure",
    "çimərliklər": "water-leisure",
    "beaches": "water-leisure",
    "аквапарки и бассейны": "water-leisure",
    "akvaparklar və hovuzlar": "water-leisure",
    "waterparks & pools": "water-leisure",
    "парки": "parks-playgrounds",
    "parklar": "parks-playgrounds",
    "parks": "parks-playgrounds",
}


def _normalized(value):
    return " ".join(str(value or "").casefold().split())


def clean_public_taxonomy(apps, schema_editor):
    from catalog.taxonomy_data import category_seed_rows, subcategory_seed_rows

    Category = apps.get_model("catalog", "Category")
    Subcategory = apps.get_model("catalog", "Subcategory")
    Place = apps.get_model("catalog", "Place")
    Event = apps.get_model("catalog", "Event")
    SiteGalleryImage = apps.get_model("catalog", "SiteGalleryImage")

    category_rows = category_seed_rows()
    subcategory_rows = subcategory_seed_rows()
    category_codes = {row["code"] for row in category_rows}
    subcategory_codes = {row["code"] for row in subcategory_rows}

    category_by_name = {}
    for row in category_rows:
        for field in ("name", "name_ru", "name_az", "name_en"):
            value = _normalized(row.get(field))
            if value:
                category_by_name[value] = row["code"]

    subcategory_by_name = {}
    for row in subcategory_rows:
        for field in ("ru", "az", "en"):
            value = _normalized(row.get(field))
            if value:
                subcategory_by_name[value] = row["code"]

    with transaction.atomic():
        # Duplicate names can have different codes. Move every linked card to
        # the canonical row before removing the duplicate.
        for duplicate in Subcategory.objects.exclude(code__in=subcategory_codes).iterator():
            target_code = None
            for value in (duplicate.name, duplicate.name_ru, duplicate.name_az, duplicate.name_en):
                target_code = subcategory_by_name.get(_normalized(value))
                if target_code:
                    break
            target = Subcategory.objects.filter(code=target_code).first() if target_code else None
            if target:
                Place.objects.filter(subcategory_id=duplicate.pk).update(
                    subcategory_id=target.pk,
                    category_id=target.category_id,
                )
            else:
                # The category remains on the card and is normalized below.
                Place.objects.filter(subcategory_id=duplicate.pk).update(subcategory_id=None)
            duplicate.delete()

        for duplicate in Category.objects.exclude(code__in=category_codes).iterator():
            target_code = CATEGORY_MOVES.get(duplicate.code)
            if not target_code:
                for value in (duplicate.name, duplicate.name_ru, duplicate.name_az, duplicate.name_en):
                    normalized_name = _normalized(value)
                    target_code = CATEGORY_NAME_MOVES.get(normalized_name) or category_by_name.get(normalized_name)
                    if target_code:
                        break

            # Unknown retired categories cannot remain because the public
            # taxonomy is closed. FUN is the least destructive generic bucket;
            # no card or event is deleted.
            target_code = target_code or "FUN"
            Place.objects.filter(category_id=duplicate.pk).update(category_id=target_code)
            Event.objects.filter(category_id=duplicate.pk).update(category_id=target_code)
            SiteGalleryImage.objects.filter(category=duplicate.pk).update(category=target_code)
            duplicate.delete()

        # Canonical metadata, order and active status are authoritative for the
        # approved structure. This also restores rows previously only archived.
        for row in category_rows:
            Category.objects.filter(code=row["code"]).update(
                name=row["name"],
                name_ru=row["name_ru"],
                name_az=row["name_az"],
                name_en=row["name_en"],
                order=row["order"],
                is_active=True,
                deleted_at=None,
                deleted_by_id=None,
            )
        for row in subcategory_rows:
            Subcategory.objects.filter(code=row["code"]).update(
                category_id=row["cat"],
                name=row["ru"],
                name_ru=row["ru"],
                name_az=row["az"],
                name_en=row["en"],
                order=row["order"],
                is_active=True,
                deleted_at=None,
                deleted_by_id=None,
            )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0079_sync_public_taxonomy"),
    ]

    operations = [
        migrations.RunPython(clean_public_taxonomy, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="subcategory",
            name="code",
            field=models.CharField(max_length=50, unique=True, verbose_name="Код"),
        ),
    ]
