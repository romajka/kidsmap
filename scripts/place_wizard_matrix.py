"""Refresh ONLY the ORM inventory in the field matrix; never infer workflow rules.

Run with the project's Python environment. --check is read-only. No database
connection is needed: migrations are loaded from disk with MigrationLoader(None).
The manually reviewed architecture sections outside the markers are preserved.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / 'docs/PERMANENT_PLACE_FIELD_MATRIX.md'
START = '<!-- BEGIN AUTO-GENERATED MODEL FACTS -->'
END = '<!-- END AUTO-GENERATED MODEL FACTS -->'
MODEL_NAMES = ('Place', 'PricingPlan', 'PlaceScheduleDay', 'PlaceScheduleInterval', 'PlacePhoto')


def cell(value):
    return str(value).replace('|', '&#124;').replace('\n', ' ')


def field_facts(field):
    from django.db.models import NOT_PROVIDED
    default = field.default
    if default is NOT_PROVIDED:
        default = '—'
    elif callable(default):
        default = f'{default.__module__}.{default.__qualname__}()'
    else:
        default = repr(default)
    facts = [f'blank={field.blank}', f'null={field.null}', f'default={default}']
    for name in ('max_length', 'max_digits', 'decimal_places', 'primary_key', 'unique', 'auto_now', 'auto_now_add', 'db_column'):
        value = getattr(field, name, None)
        if value is not None and value is not False:
            facts.append(f'{name}={value}')
    if field.remote_field:
        remote = field.remote_field
        facts += [f'to={remote.model._meta.label}', f'target={field.target_field.name}',
                  f'on_delete={remote.on_delete.__name__}', f'related_name={remote.related_name}']
    if field.choices:
        facts.append('choices=' + ', '.join(repr(value) for value, _label in field.flatchoices))
    return '; '.join(facts)


def generate():
    sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from django.apps import apps
    from django.db.migrations.loader import MigrationLoader
    from django.utils.translation import override
    from catalog.forms import OwnerPlaceEditForm
    from catalog.domain_admin.place import PlaceAdminForm, PlaceAdmin

    def flatten_fields(fieldsets):
        def flatten(items):
            for item in items:
                if isinstance(item, (tuple, list)):
                    yield from flatten(item)
                else:
                    yield item
        return {field for _title, options in fieldsets for field in flatten(options.get('fields', ())) }

    admin_add = flatten_fields(PlaceAdmin.ADD_FIELDSETS)
    admin_edit = flatten_fields(PlaceAdmin.fieldsets)

    loader = MigrationLoader(None)
    migration_apps = loader.project_state().apps
    lines = [START, '', '## AUTO-GENERATED FACTS: полная структура моделей', '',
             'Источник: Django `_meta.local_fields`, `base_fields` форм и конечное состояние миграций на диске. '
             'Это не требования публикации. `blank=False` не равнозначно обязательности в черновике. '
             '«Owner / Admin form» означает наличие в базовом классе формы, а не видимость в шаблоне, '
             'доступность по правам или принятие HTTP POST после обработки view. '
             '«Admin add/edit» — присутствие в штатных fieldsets (дополнительные редакторы/шаблоны описаны вручную). Автоматический `id` включён.', '',
             'Листья графа миграций catalog: ' + ', '.join(f'`{name}`' for app, name in loader.graph.leaf_nodes('catalog')) + '.', '']
    mismatches = []
    with override('ru'):
        for name in MODEL_NAMES:
            model = apps.get_model('catalog', name)
            migrated = migration_apps.get_model('catalog', name)
            runtime_fields = {field.name: field for field in model._meta.local_fields}
            migrated_fields = {field.name: field for field in migrated._meta.local_fields}
            for key in sorted(runtime_fields.keys() | migrated_fields.keys()):
                left, right = runtime_fields.get(key), migrated_fields.get(key)
                if left is None or right is None or (left.get_internal_type(), field_facts(left)) != (right.get_internal_type(), field_facts(right)):
                    mismatches.append(f'{name}.{key}')
            lines += [f'### {name} — {len(runtime_fields)} полей', '',
                      '| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |',
                      '|---|---|---|---|---|']
            for field in runtime_fields.values():
                inclusion = '— (связанная модель)'
                if name == 'Place':
                    inclusion = f'{"да" if field.name in OwnerPlaceEditForm.base_fields else "нет"} / {"да" if field.name in PlaceAdminForm.base_fields else "нет"}'
                visibility = f'{"да" if field.name in admin_add else "нет"} / {"да" if field.name in admin_edit else "нет"}' if name == 'Place' else 'связанный редактор'
                lines.append(f'| `{field.name}` | {field.get_internal_type()} | {cell(field_facts(field))} | {inclusion} | {visibility} |')
            lines += ['', 'Model ordering: `' + cell(repr(model._meta.ordering)) + '`.', '']
            for constraint in model._meta.constraints:
                lines.append(f'- DB constraint `{constraint.name}`: `{cell(repr(constraint))}`.')
            lines.append('')
    lines += ['Сверка перечисленных типов полей, defaults, choices и параметров с конечным состоянием миграций: '
              + ('совпадает.' if not mismatches else '**расхождения**: ' + ', '.join(mismatches)), '', END]
    return '\n'.join(lines), mismatches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the generated block is stale; do not write files.')
    args = parser.parse_args()
    current = DOCUMENT.read_text(encoding='utf-8')
    if current.count(START) != 1 or current.count(END) != 1 or current.index(START) >= current.index(END):
        parser.error('Expected exactly one ordered pair of inventory markers; manual document is never overwritten.')
    generated, mismatches = generate()
    start, end = current.index(START), current.index(END) + len(END)
    result = current[:start] + generated + current[end:]
    if args.check:
        if result != current or mismatches:
            print('FAIL: inventory is stale or migration facts differ. Review and regenerate.')
            return 1
        print('PASS: inventory matches ORM and disk migrations. Manual rules require a separate code review.')
    else:
        DOCUMENT.write_text(result, encoding='utf-8')
        print('Updated generated model facts only; manual architecture sections preserved.')
        if mismatches:
            print('Migration differences: ' + ', '.join(mismatches))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
