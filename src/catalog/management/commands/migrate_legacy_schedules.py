"""Move the old free-text ``Place.schedule`` into structured weekday rows.

Only texts the parser fully understands are converted. Anything else is listed
for manual review and left exactly as it is: a wrong opening hour on a public
card is worse than an unmigrated one. The legacy text is never deleted here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog.models import Place
from catalog.services.legacy_schedule_parser import describe_payload, parse_legacy_schedule
from catalog.services.place_schedule import is_meaningful_schedule, sync_place_schedule


@dataclass
class ScheduleOutcome:
    place: Place
    status: str
    payload: list[dict] | None = None
    reason: str = ""
    text: str = ""


class Command(BaseCommand):
    help = "Переносит текстовое расписание в редактор дней. По умолчанию — только показывает план."

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
        parser.add_argument("--examples", type=int, default=10, help="Сколько примеров показать.")
        parser.add_argument(
            "--show-manual",
            action="store_true",
            help="Показать все карточки, требующие ручной проверки.",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        if apply_changes and options["dry_run"]:
            raise CommandError("Укажите либо --apply, либо --dry-run.")

        queryset = Place.objects.filter(deleted_at__isnull=True).prefetch_related("schedule_days__intervals")
        if options.get("place_id"):
            queryset = queryset.filter(pk=options["place_id"])
            if not queryset.exists():
                raise CommandError(f"Карточка {options['place_id']} не найдена.")

        outcomes = [self._plan_for_place(place) for place in queryset.iterator(chunk_size=100)]

        migrated = [item for item in outcomes if item.status == "migrated"]
        if apply_changes and migrated:
            self._apply(migrated)

        self._report(outcomes, apply_changes=apply_changes, options=options)

    def _plan_for_place(self, place: Place) -> ScheduleOutcome:
        text = (place.schedule or "").strip()
        if place.schedule_mode != Place.SCHEDULE_MODE_REGULAR:
            return ScheduleOutcome(place=place, status="skipped", reason="режим расписания не недельный", text=text)
        if is_meaningful_schedule(_serialize(place)):
            return ScheduleOutcome(place=place, status="already_migrated", reason="дни уже заполнены", text=text)
        if not text:
            return ScheduleOutcome(place=place, status="skipped", reason="нет текстового расписания")

        payload, reason = parse_legacy_schedule(text)
        if payload is None:
            return ScheduleOutcome(place=place, status="manual_review", reason=reason, text=text)
        if not is_meaningful_schedule(payload):
            return ScheduleOutcome(
                place=place, status="manual_review", reason="разобранное расписание не содержит рабочих дней", text=text
            )
        return ScheduleOutcome(place=place, status="migrated", payload=payload, text=text)

    def _apply(self, outcomes: list[ScheduleOutcome]) -> None:
        for outcome in outcomes:
            try:
                with transaction.atomic():
                    # Re-check inside the transaction: the editor may have filled
                    # the days while the plan was being built.
                    if is_meaningful_schedule(_serialize(outcome.place)):
                        outcome.status = "already_migrated"
                        outcome.reason = "дни появились во время выполнения"
                        continue
                    sync_place_schedule(outcome.place, outcome.payload)
            except Exception as exc:  # noqa: BLE001 - reported, never silent
                outcome.status = "errors"
                outcome.reason = f"{type(exc).__name__}: {exc}"

    def _report(self, outcomes, *, apply_changes: bool, options) -> None:
        buckets: dict[str, list[ScheduleOutcome]] = {}
        for outcome in outcomes:
            buckets.setdefault(outcome.status, []).append(outcome)

        mode = "ВЫПОЛНЕНО" if apply_changes else "DRY-RUN (ничего не изменено)"
        self.stdout.write(f"=== Миграция legacy-расписаний: {mode} ===")
        for status in ("migrated", "already_migrated", "manual_review", "skipped", "errors"):
            self.stdout.write(f"{status}: {len(buckets.get(status, []))}")

        limit = options["examples"]
        migrated = buckets.get("migrated", [])
        if migrated:
            self.stdout.write(f"\n--- migrated (первые {min(limit, len(migrated))}) ---")
            for outcome in migrated[:limit]:
                self.stdout.write(f"  [{outcome.place.pk}] {outcome.text[:48]!r}")
                self.stdout.write(f"      -> {describe_payload(outcome.payload)}")

        manual = buckets.get("manual_review", [])
        if manual:
            shown = manual if options["show_manual"] else manual[:limit]
            self.stdout.write(f"\n--- manual_review ({len(shown)} из {len(manual)}) ---")
            for outcome in shown:
                self.stdout.write(f"  [{outcome.place.pk}] {outcome.reason}")
                self.stdout.write(f"      текст: {outcome.text[:70]!r}")

        errors = buckets.get("errors", [])
        if errors:
            self.stdout.write("\n--- errors ---")
            for outcome in errors:
                self.stdout.write(f"  [{outcome.place.pk}] {outcome.reason}")

        if not apply_changes and migrated:
            self.stdout.write("\nЗапустите с --apply, чтобы записать дни расписания.")


def _serialize(place: Place) -> list[dict]:
    from catalog.services.place_schedule import serialize_place_schedule

    return serialize_place_schedule(place)
