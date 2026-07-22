from __future__ import annotations

import json

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print deterministic row counts for validating a database transfer"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to inspect (default: default)",
        )
        parser.add_argument(
            "--exclude",
            action="append",
            default=[],
            metavar="APP_LABEL.MODEL",
            help="Model label to omit; may be supplied more than once",
        )

    def handle(self, *args, **options):
        database = options["database"]
        excluded = {label.strip().lower() for label in options["exclude"]}
        counts: dict[str, int] = {}

        for model in apps.get_models():
            opts = model._meta
            if opts.proxy or not opts.managed:
                continue
            label = opts.label_lower
            if label in excluded:
                continue
            counts[label] = model._default_manager.using(database).count()

        payload = {
            "database": database,
            "models": dict(sorted(counts.items())),
            "total_rows": sum(counts.values()),
        }
        self.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
