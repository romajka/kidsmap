import json

from django.core.management.base import BaseCommand

from catalog.models import Place
from catalog.services.place_card_validation import validate_place_card


class Command(BaseCommand):
    help = "Validate place cards and print an actionable quality report."

    def add_arguments(self, parser):
        parser.add_argument("--include-temporary", action="store_true", help="Include temporary places.")
        parser.add_argument("--json", action="store_true", help="Print the complete report as JSON.")
        parser.add_argument("--only-problems", action="store_true", help="Hide cards without errors or warnings.")

    def handle(self, *args, **options):
        places = Place.objects.prefetch_related("gallery", "schedule_days__intervals", "pricing_plan_records").order_by("pk")
        if not options["include_temporary"]:
            places = places.filter(is_temporary=False)

        report = []
        clean = warnings = errors = 0
        for place in places:
            result = validate_place_card(place)
            if result.errors:
                errors += 1
            elif result.warnings:
                warnings += 1
            else:
                clean += 1
            report.append({
                "id": place.pk,
                "name": place.name_i18n("ru"),
                "errors": [issue.__dict__ for issue in result.errors],
                "warnings": [issue.__dict__ for issue in result.warnings],
            })

        summary = {"checked": len(report), "clean": clean, "warnings": warnings, "errors": errors}
        if options["json"]:
            self.stdout.write(json.dumps({"summary": summary, "places": report}, ensure_ascii=False, indent=2))
            return

        self.stdout.write(
            f"Проверено: {summary['checked']}; без ошибок: {clean}; с предупреждениями: {warnings}; с критическими ошибками: {errors}."
        )
        for item in report:
            if options["only_problems"] and not (item["errors"] or item["warnings"]):
                continue
            if item["errors"] or item["warnings"]:
                codes = [issue["code"] for issue in item["errors"] + item["warnings"]]
                self.stdout.write(f"#{item['id']} {item['name']}: {', '.join(codes)}")
