import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Place
from catalog.services.pricing_plans import normalize_pricing_plans, replace_place_pricing_plans


class Command(BaseCommand):
    help = "Migrate legacy Place pricing data to relational PricingPlan rows"

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument("--dry-run", action="store_true")
        mode.add_argument("--apply", action="store_true")
        parser.add_argument("--report", type=str)

    def handle(self, *args, **options):
        report = {"processed": 0, "created": 0, "skipped": 0, "conflicts": 0, "ambiguous": []}
        for place in Place.objects.order_by("pk").iterator(chunk_size=100):
            report["processed"] += 1
            payload = []
            if place.pricing_plans_legacy:
                try:
                    payload.extend(normalize_pricing_plans(place.pricing_plans_legacy))
                except Exception as exc:
                    report["conflicts"] += 1
                    report["ambiguous"].append({"place_id": place.pk, "reason": str(exc)})

            legacy = [
                (place.price_per_lesson, {"product_type": "lesson", "billing_mode": "one_time", "quantity": 1, "quantity_unit": "lesson", "title_ru": "Одно занятие"}),
                (place.price_per_month, {"product_type": "membership", "billing_mode": "recurring", "billing_interval": "month", "billing_interval_count": 1, "title_ru": "Месячный абонемент"}),
                (place.price_per_8_lessons, {"product_type": "lesson", "billing_mode": "one_time", "quantity": 8, "quantity_unit": "lesson", "title_ru": "Пакет из 8 занятий"}),
            ]
            fingerprints = {(item.get("product_type"), item.get("billing_mode"), item.get("billing_interval"), item.get("quantity"), item.get("quantity_unit")) for item in payload}
            for amount, base in legacy:
                fingerprint = (base.get("product_type"), base.get("billing_mode"), base.get("billing_interval"), base.get("quantity"), base.get("quantity_unit"))
                if amount is None or fingerprint in fingerprints:
                    continue
                payload.append({**base, "price_kind": "free" if amount == 0 else "exact", "price": str(amount), "currency": "AZN", "charge_role": "primary", "is_active": True})
                fingerprints.add(fingerprint)

            if not payload:
                report["skipped"] += 1
                if place.price_from is not None or place.price_to is not None:
                    report["ambiguous"].append({"place_id": place.pk, "reason": "only price_from/price_to"})
                continue
            try:
                normalized = normalize_pricing_plans(payload)
            except Exception as exc:
                report["conflicts"] += 1
                report["ambiguous"].append({"place_id": place.pk, "reason": str(exc)})
                continue
            existing = place.pricing_plan_records.count()
            if options["apply"]:
                with transaction.atomic():
                    saved = replace_place_pricing_plans(place, normalized, allow_verified=True)
                report["created"] += max(0, len(saved) - existing)
            else:
                report["created"] += max(0, len(normalized) - existing)

        output = json.dumps(report, ensure_ascii=False, indent=2, default=str)
        self.stdout.write(output)
        if options.get("report"):
            path = Path(options["report"]).expanduser().resolve()
            try:
                path.write_text(output + "\n", encoding="utf-8")
            except OSError as exc:
                raise CommandError(str(exc)) from exc
