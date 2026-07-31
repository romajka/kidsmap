import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from catalog.models import Category, Place


class Command(BaseCommand):
    help = "Import places from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to CSV file")

    def handle(self, *args, **options):
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

                place, is_created = Place.objects.update_or_create(
                    name_ru=data["name_ru"],
                    address=data["address"],
                    defaults=data,
                )
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
            "is_active": True,
        }

        if not data["category"]:
            raise ValueError("category is required")
        if not Category.active.filter(code=data["category"]).exists():
            raise ValueError(f"unknown category code: {data['category']}")
        if not data["name_ru"] and not data["name_en"] and not data["name_az"]:
            raise ValueError("at least one of name_ru/name_en/name_az is required")

        return data
