from __future__ import annotations

import json
import re
from datetime import timedelta
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, models
from django.db.models import Count, Q
from django.utils import timezone

from .migrate_legacy_database import EXCLUDED_TABLES, managed_models_by_table


class Command(BaseCommand):
    help = "Compare legacy MariaDB business data with the PostgreSQL migration target."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="legacy")
        parser.add_argument("--target", default="default")
        parser.add_argument("--analytics-days", type=int, default=180)
        parser.add_argument("--report", default="verification-report.json")

    def handle(self, *args, **options):
        source = connections[options["source"]]
        target = connections[options["target"]]
        if source.vendor != "mysql" or target.vendor != "postgresql":
            raise CommandError("Verification requires a MariaDB/MySQL source and PostgreSQL target.")

        cutoff = timezone.now() - timedelta(days=options["analytics_days"])
        source_tables = set(source.introspection.table_names())
        target_tables = set(target.introspection.table_names())
        models_by_table = managed_models_by_table()
        report = {
            "source": options["source"],
            "target": options["target"],
            "analytics_cutoff": cutoff.isoformat(),
            "tables": {},
            "relations": {},
            "duplicates": {"slugs": {}, "phones": {}},
            "missing_translations": {},
            "broken_images": {},
            "sequences": {},
            "failures": [],
        }

        checked_models = []
        for table, model in sorted(models_by_table.items()):
            if table in EXCLUDED_TABLES or table not in source_tables or table not in target_tables:
                continue
            pk = model._meta.pk.column
            source_stats = self._stats(source, table, pk, cutoff)
            target_stats = self._stats(target, table, pk, cutoff)
            matches = source_stats == target_stats
            report["tables"][table] = {
                "source": source_stats,
                "target": target_stats,
                "matches": matches,
            }
            if not matches:
                report["failures"].append(f"{table}: count or ID range differs")
            checked_models.append(model)

        for model in checked_models:
            self._check_relations(target, model, report)
            self._check_duplicates(options["target"], model, report)
            self._check_translations(options["target"], model, report)
            self._check_images(options["target"], model, report)
            self._check_sequence(target, model, report)

        output = Path(options["report"])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        if report["failures"]:
            raise CommandError(
                f"Verification failed ({len(report['failures'])} issues). Report: {output}"
            )
        self.stdout.write(self.style.SUCCESS(f"Verification passed. Report: {output}"))

    def _stats(self, connection, table, pk, cutoff):
        quote = connection.ops.quote_name
        where = ""
        params = []
        if table == "catalog_funnelevent":
            where = f" WHERE {quote('created_at')} >= %s"
            params.append(cutoff)
        sql = (
            f"SELECT COUNT(*), MIN({quote(pk)}), MAX({quote(pk)}) "
            f"FROM {quote(table)}{where}"
        )
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            count, minimum, maximum = cursor.fetchone()
        return {"count": count, "min_id": minimum, "max_id": maximum}

    def _check_relations(self, connection, model, report):
        table = model._meta.db_table
        quote = connection.ops.quote_name
        table_report = {}
        for field in model._meta.concrete_fields:
            related = getattr(field.remote_field, "model", None)
            if related is None:
                continue
            related_table = related._meta.db_table
            if related_table not in connection.introspection.table_names():
                continue
            sql = (
                f"SELECT COUNT(*) FROM {quote(table)} child "
                f"LEFT JOIN {quote(related_table)} parent "
                f"ON child.{quote(field.column)} = parent.{quote(related._meta.pk.column)} "
                f"WHERE child.{quote(field.column)} IS NOT NULL "
                f"AND parent.{quote(related._meta.pk.column)} IS NULL"
            )
            with connection.cursor() as cursor:
                cursor.execute(sql)
                orphan_count = cursor.fetchone()[0]
            missing_required = 0
            if not field.null:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM {quote(table)} "
                        f"WHERE {quote(field.column)} IS NULL"
                    )
                    missing_required = cursor.fetchone()[0]
            key = f"{field.name}->{related_table}"
            table_report[key] = {
                "orphans": orphan_count,
                "missing_required": missing_required,
            }
            if orphan_count or missing_required:
                report["failures"].append(f"{table}.{field.name}: broken relation")
        if table_report:
            report["relations"][table] = table_report

    def _check_duplicates(self, alias, model, report):
        table = model._meta.db_table
        field_names = {field.name for field in model._meta.concrete_fields}
        if "slug" in field_names:
            duplicates = list(
                model._base_manager.using(alias)
                .exclude(slug__isnull=True)
                .exclude(slug="")
                .values("slug")
                .annotate(count=Count("pk"))
                .filter(count__gt=1)[:100]
            )
            report["duplicates"]["slugs"][table] = duplicates
            if duplicates:
                report["failures"].append(f"{table}: duplicate slugs")

        phone_fields = [name for name in field_names if "phone" in name.lower()]
        phone_duplicates = {}
        for field_name in sorted(phone_fields):
            seen = {}
            duplicates = set()
            values = model._base_manager.using(alias).values_list(field_name, flat=True).iterator()
            for value in values:
                normalized = re.sub(r"\D", "", str(value or ""))
                if not normalized:
                    continue
                if normalized in seen:
                    duplicates.add(normalized)
                else:
                    seen[normalized] = True
            if duplicates:
                phone_duplicates[field_name] = sorted(duplicates)[:100]
        if phone_duplicates:
            report["duplicates"]["phones"][table] = phone_duplicates

    def _check_translations(self, alias, model, report):
        translatable = sorted(
            field.name
            for field in model._meta.concrete_fields
            if isinstance(field, (models.CharField, models.TextField))
            and field.name.endswith(("_az", "_ru", "_en"))
        )
        if not translatable:
            return
        missing = {}
        queryset = model._base_manager.using(alias)
        for field_name in translatable:
            missing[field_name] = queryset.filter(
                Q(**{f"{field_name}__isnull": True}) | Q(**{field_name: ""})
            ).count()
        report["missing_translations"][model._meta.db_table] = missing

    def _check_images(self, alias, model, report):
        file_fields = [
            field for field in model._meta.concrete_fields
            if isinstance(field, models.FileField)
        ]
        if not file_fields:
            return
        broken = []
        media_root = Path(settings.MEDIA_ROOT)
        for field in file_fields:
            values = model._base_manager.using(alias).values_list("pk", field.name).iterator()
            for pk, value in values:
                value = str(value or "").strip()
                if value and not value.startswith(("http://", "https://")):
                    candidate = Path(value)
                    if candidate.is_absolute() or ".." in candidate.parts or not (media_root / candidate).is_file():
                        broken.append({"id": pk, "field": field.name, "path": value})
                        if len(broken) >= 100:
                            break
        report["broken_images"][model._meta.db_table] = broken

    def _check_sequence(self, connection, model, report):
        pk = model._meta.pk
        if not isinstance(pk, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
            return
        table = model._meta.db_table
        quote = connection.ops.quote_name
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, pk.column])
            sequence = cursor.fetchone()[0]
            cursor.execute(f"SELECT MAX({quote(pk.column)}) FROM {quote(table)}")
            maximum = cursor.fetchone()[0] or 0
            last_value = None
            if sequence:
                cursor.execute("SELECT pg_sequence_last_value(%s::regclass)", [sequence])
                last_value = cursor.fetchone()[0]
        valid = not sequence or last_value is None or last_value >= maximum
        report["sequences"][table] = {
            "sequence": sequence,
            "last_value": last_value,
            "max_id": maximum,
            "valid": valid,
        }
        if not valid:
            report["failures"].append(f"{table}: sequence is behind max ID")
