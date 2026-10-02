import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied

from catalog.models import Category, Place


class Command(BaseCommand):
    help = "Import places from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")
        parser.add_argument("--actor-id",type=int,required=True,help="Active platform editor account")
        parser.add_argument("--schema-version",type=int,required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model
        from catalog.services import publication
        actor=get_user_model().objects.filter(pk=options["actor_id"],is_active=True).first()
        from catalog.services.business_team import platform_has_action
        if actor is None or not platform_has_action(user=actor,action="place.publish"):
            raise CommandError("Active platform publication permission required.")
        if options["schema_version"] != publication.SCHEMA_VERSION:
            raise CommandError("Publication schema conflict.")
        csv_file = Path(options["csv_file"])
        if not csv_file.exists():
            raise CommandError(f"File not found: {csv_file}")

        required_columns = {
            "category",
            "district",
            "metro",
            "address",
            "age_from",
            "age_to",
            "price_from",
            "price_to",
            "phone1",
            "instagram",
            "website",
            "name_ru",
            "name_en",
            "name_az",
            "description_ru",
            "description_en",
            "description_az",
        }

        created = 0
        updated = 0

        with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV has no header")

            missing = sorted(required_columns - set(reader.fieldnames))
            if missing:
                raise CommandError(f"Missing CSV columns: {', '.join(missing)}")

            for row_num, row in enumerate(reader, start=2):
                try:
                    data = self._normalize_row(row)
                except ValueError as exc:
                    raise CommandError(f"Row {row_num}: {exc}") from exc

                # Existing objects require explicit identity/base: name+address
                # is not a safe update key across branches/businesses.
                raw_id=(row.get("place_id") or "").strip()
                try:
                    if raw_id:
                        place=publication.locked_target('place',int(raw_id));is_created=False
                        expected=int(row.get("base_content_version") or 0)
                        revision_version=int(row.get("revision_version") or 0)
                    else:
                        if Place.objects.filter(name_ru=data["name_ru"],address=data["address"]).exists():
                            raise ValidationError("Existing/ambiguous row requires place_id and base_content_version.")
                        place=Place.objects.create(name=data["name"],category_id=data["category"],created_by=actor,status='draft',is_active=False)
                        is_created=True;expected=place.content_version;revision_version=0
                    patch={k:v for k,v in data.items() if k in publication.fields_for('place')}
                    publication.propose(actor=actor,target_type='place',target_id=place.pk,patch=patch,schema_version=options['schema_version'],expected_version=expected,revision_version=revision_version,submit=True,explicit_save=True)
                except (ValueError,ValidationError,PermissionDenied) as exc:
                    raise CommandError(f"Row {row_num}: publication validation/conflict; import rolled back.") from exc
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Created: {created}, Updated: {updated}"
            )
        )

    def _normalize_row(self, row):
        def to_int(value):
            value = (value or "").strip()
            return int(value) if value else None

        def clean(value):
            return (value or "").strip()

        data = {
            "category": clean(row.get("category")),
            "district": clean(row.get("district")),
            "metro": clean(row.get("metro")),
            "address": clean(row.get("address")),
            "age_from": to_int(row.get("age_from")),
            "age_to": to_int(row.get("age_to")),
            "price_from": to_int(row.get("price_from")),
            "price_to": to_int(row.get("price_to")),
            "phone1": clean(row.get("phone1")),
            "instagram": clean(row.get("instagram")),
            "website": clean(row.get("website")),
            "name_ru": clean(row.get("name_ru")),
            "name_en": clean(row.get("name_en")),
            "name_az": clean(row.get("name_az")),
            "description_ru": clean(row.get("description_ru")),
            "description_en": clean(row.get("description_en")),
            "description_az": clean(row.get("description_az")),
            "name": clean(row.get("name_ru")) or clean(row.get("name_en")) or clean(row.get("name_az")),

        }

        if not data["category"]:
            raise ValueError("category is required")
        if not Category.active.filter(code=data["category"]).exists():
            raise ValueError(f"unknown category code: {data['category']}")
        if not data["name_ru"] and not data["name_en"] and not data["name_az"]:
            raise ValueError("at least one of name_ru/name_en/name_az is required")

        return data
