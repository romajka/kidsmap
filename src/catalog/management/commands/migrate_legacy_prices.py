"""Move pre-tariff ``price_*`` columns into ``PricingPlan`` rows.

Readiness counts only tariffs, so stored cards need their old scalar prices
migrated. The command never guesses: a legacy value is converted only when its
product is stated by the column it lives in. Nothing is deleted from the legacy
fields — this step only adds tariffs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Place, PricingPlan


# A legacy column states its own product; ``price_from``/``price_to`` do not,
# which is why they are ambiguous unless the operator says what they mean.
PRODUCT_BY_LEGACY_FIELD = {
    "price_per_lesson": {
        "product_type": "lesson",
        "quantity": 1,
        "quantity_unit": "lesson",
        "title_ru": "Занятие",
        "title_az": "Dərs",
        "title_en": "Lesson",
    },
    "price_per_month": {
        "product_type": "membership",
        "quantity": 1,
        "quantity_unit": "month",
        "title_ru": "Абонемент на месяц",
        "title_az": "Aylıq abonement",
        "title_en": "Monthly membership",
    },
    "price_per_8_lessons": {
        "product_type": "membership",
        "quantity": 8,
        "quantity_unit": "lesson",
        "title_ru": "Абонемент на 8 занятий",
        "title_az": "8 dərslik abonement",
        "title_en": "8-lesson membership",
    },
}

ASSUMED_PRODUCTS = {
    "lesson": {"product_type": "lesson", "quantity": 1, "quantity_unit": "lesson"},
    "month": {"product_type": "membership", "quantity": 1, "quantity_unit": "month"},
    "visit": {"product_type": "visit", "quantity": 1, "quantity_unit": "visit"},
}


@dataclass
class PlanDraft:
    source: str
    fields: dict

    def describe(self) -> str:
        kind = self.fields.get("price_kind")
        if kind == "exact":
            amount = f"{self.fields['price']} AZN"
        elif kind == "from":
            amount = f"от {self.fields['price_min']} AZN"
        elif kind == "range":
            amount = f"{self.fields['price_min']}–{self.fields['price_max']} AZN"
        else:
            amount = kind
        return f"{self.source}: {self.fields['product_type']} / {amount}"


@dataclass
class PlaceOutcome:
    place: Place
    status: str
    drafts: list[PlanDraft] = field(default_factory=list)
    reason: str = ""


def _decimal(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def build_plan_drafts(place: Place, *, assume_product: str | None = None) -> tuple[list[PlanDraft], str]:
    """Return the tariffs a legacy card unambiguously implies.

    The second value is the reason the card cannot be converted, empty when the
    drafts are usable.
    """

    drafts: list[PlanDraft] = []
    for field_name, product in PRODUCT_BY_LEGACY_FIELD.items():
        amount = _decimal(getattr(place, field_name, None))
        if amount is None:
            continue
        if amount <= 0:
            return [], f"{field_name} = {amount}: цена должна быть больше нуля"
        drafts.append(
            PlanDraft(
                source=field_name,
                fields={
                    **product,
                    "charge_role": "primary",
                    "price_kind": "exact",
                    "price": amount,
                    "currency": "AZN",
                    "is_active": True,
                },
            )
        )

    if drafts:
        # ``price_from``/``price_to`` only summarised these products for the
        # catalog badge; converting them too would double-count the price.
        return drafts, ""

    price_from = _decimal(place.price_from)
    price_to = _decimal(place.price_to)
    if price_from is None and price_to is None:
        return [], "нет legacy-цены"
    if price_from is None:
        return [], "заполнено только «цена до» — непонятно, что это за цена"
    if price_from <= 0 or (price_to is not None and price_to <= 0):
        return [], "цена меньше или равна нулю"
    if price_to is not None and price_to < price_from:
        return [], "«цена до» меньше «цены от»"
    if assume_product is None:
        return [], "есть только диапазон price_from/price_to: продукт не указан"

    product = ASSUMED_PRODUCTS[assume_product]
    if price_to is None:
        price_fields = {"price_kind": "from", "price_min": price_from}
    elif price_to == price_from:
        price_fields = {"price_kind": "exact", "price": price_from}
    else:
        price_fields = {"price_kind": "range", "price_min": price_from, "price_max": price_to}

    drafts.append(
        PlanDraft(
            source="price_from/price_to",
            fields={
                **product,
                **price_fields,
                "charge_role": "primary",
                "currency": "AZN",
                "is_active": True,
            },
        )
    )
    return drafts, ""


class Command(BaseCommand):
    help = "Переносит старые цены price_* в тарифы PricingPlan. По умолчанию — только показывает план."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Выполнить миграцию. Без этого флага команда ничего не меняет.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Явный прогон без изменений (поведение по умолчанию).",
        )
        parser.add_argument("--place-id", type=int, help="Ограничить одной карточкой.")
        parser.add_argument(
            "--assume-product",
            choices=sorted(ASSUMED_PRODUCTS),
            help=(
                "Что означает диапазон price_from/price_to. Без этого флага такие "
                "карточки считаются неоднозначными и пропускаются."
            ),
        )
        parser.add_argument("--examples", type=int, default=10, help="Сколько примеров показать.")

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        if apply_changes and options["dry_run"]:
            raise CommandError("Укажите либо --apply, либо --dry-run.")
        assume_product = options.get("assume_product")
        example_limit = options["examples"]

        queryset = Place.objects.filter(deleted_at__isnull=True).prefetch_related("pricing_plan_records")
        if options.get("place_id"):
            queryset = queryset.filter(pk=options["place_id"])
            if not queryset.exists():
                raise CommandError(f"Карточка {options['place_id']} не найдена.")

        outcomes: list[PlaceOutcome] = []
        for place in queryset.iterator(chunk_size=100):
            outcomes.append(self._plan_for_place(place, assume_product=assume_product))

        migrated = [item for item in outcomes if item.status == "migrated"]
        if apply_changes and migrated:
            self._apply(migrated)

        self._report(
            outcomes,
            apply_changes=apply_changes,
            assume_product=assume_product,
            example_limit=example_limit,
        )

    def _plan_for_place(self, place: Place, *, assume_product: str | None) -> PlaceOutcome:
        if place.pricing_plan_records.exists():
            return PlaceOutcome(place=place, status="already_migrated", reason="у карточки уже есть тарифы")

        drafts, reason = build_plan_drafts(place, assume_product=assume_product)
        if not drafts:
            if reason == "нет legacy-цены":
                return PlaceOutcome(place=place, status="skipped", reason=reason)
            return PlaceOutcome(place=place, status="ambiguous", reason=reason)
        return PlaceOutcome(place=place, status="migrated", drafts=drafts)

    def _apply(self, outcomes: list[PlaceOutcome]) -> None:
        for outcome in outcomes:
            try:
                with transaction.atomic():
                    # Re-check inside the transaction: another writer may have
                    # added tariffs since the plan was built.
                    if outcome.place.pricing_plan_records.exists():
                        outcome.status = "already_migrated"
                        outcome.reason = "тарифы появились во время выполнения"
                        continue
                    for order, draft in enumerate(outcome.drafts):
                        plan = PricingPlan(place=outcome.place, sort_order=order, **draft.fields)
                        plan.full_clean()
                        plan.save()
            except (ValidationError, ValueError) as exc:
                outcome.status = "errors"
                outcome.reason = str(exc)

    def _report(self, outcomes, *, apply_changes: bool, assume_product, example_limit: int) -> None:
        buckets: dict[str, list[PlaceOutcome]] = {}
        for outcome in outcomes:
            buckets.setdefault(outcome.status, []).append(outcome)

        mode = "ВЫПОЛНЕНО" if apply_changes else "DRY-RUN (ничего не изменено)"
        self.stdout.write(f"=== Миграция legacy-цен: {mode} ===")
        if assume_product:
            self.stdout.write(f"Диапазон price_from/price_to трактуется как: {assume_product}")
        else:
            self.stdout.write("Диапазон price_from/price_to не трактуется (нужен --assume-product)")

        for status in ("migrated", "already_migrated", "ambiguous", "skipped", "errors"):
            items = buckets.get(status, [])
            self.stdout.write(f"{status}: {len(items)}")

        for status in ("migrated", "ambiguous", "errors"):
            items = buckets.get(status, [])
            if not items:
                continue
            self.stdout.write(f"\n--- {status} (первые {min(example_limit, len(items))}) ---")
            for outcome in items[:example_limit]:
                name = outcome.place.name_az or outcome.place.name or f"#{outcome.place.pk}"
                if outcome.drafts:
                    details = "; ".join(draft.describe() for draft in outcome.drafts)
                else:
                    details = outcome.reason
                self.stdout.write(f"  [{outcome.place.pk}] {name[:40]} -> {details}")

        if not apply_changes and buckets.get("migrated"):
            self.stdout.write("\nЗапустите с --apply, чтобы создать тарифы.")
