"""Adapt reviewed QA06 isolation, freeze existing catalogues; no compilation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT / 'docs/qa/place-qa06-plan-2026-10-10'
scratch = ROOT / '.tmp/place-qa07-plan-20261010'
scratch.mkdir(parents=True, exist_ok=False)
manifest = []
for lang in ('ru', 'az', 'en'):
    for ext in ('po', 'mo'):
        source = ROOT / f'locale/{lang}/LC_MESSAGES/django.{ext}'
        target = scratch / f'baseline-locale/{lang}/LC_MESSAGES/django.{ext}'
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        assert digest == hashlib.sha256(source.read_bytes()).hexdigest() == hashlib.sha256(target.read_bytes()).hexdigest()
        manifest.append({'source': source.relative_to(ROOT).as_posix(),
                         'copy': target.relative_to(ROOT).as_posix(), 'sha256': digest})
(HERE / 'frozen-catalog-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
for old, new in [('qa06_settings.py','qa07_settings.py'), ('runtime.py','runtime.py'),
                 ('prepare.py','prepare.py'), ('pw.py','pw.py'),
                 ('browser.config.json','browser.config.json'), ('browser-setup.js','browser-setup.js')]:
    content = (PREVIOUS / old).read_text(encoding='utf-8')
    for before, after in [('qa06','qa07'), ('QA06','QA07'), ('55442','55444'), ('8821','8823')]:
        content = content.replace(before, after)
    if new == 'runtime.py':
        content = content.replace(".objects.create_superuser('qa07_synthetic_admin'", ".objects.create_user('qa07_synthetic_owner'")
        start = content.index("    Category.objects.create(code='QA07_LONG'")
        end = content.index('    place = Place.objects.create', start)
        content = content[:start] + content[end:]
        content = content.replace("status='draft', is_active=False", "owner=actor, created_by=actor, status='draft', is_active=False")
        content = content.replace("/admin/catalog/place/{place.pk}/change/", "/ru/account/places/{place.pk}/edit/")
        content = content.replace('synthetic admin/place', 'synthetic owner/place')
    if new == 'prepare.py':
        content = content.replace("'src/config/settings.py','Dockerfile','.github/workflows/deploy.yml','scripts/release-server.sh'", "'src/config/settings.py','src/catalog/forms.py','src/catalog/controllers/owner_places_controller.py','src/catalog/models/catalog_structure.py','src/catalog/models/place.py','src/catalog/templates/pages/owner_place_edit.html','src/catalog/templates/pages/permanent_place_form.html','src/catalog/templates/pages/includes/owner_place_continuous.html','src/catalog/templates/pages/includes/permanent_place_field.html','src/catalog/testcases/test_task33_place_continuous.py'")
        content = content.replace('place-qa0[1-5]', 'place-qa0[1-6]')
    (HERE / new).write_text(content, encoding='utf-8')
print('Created QA07 isolated owner harness; six byte-identical catalogue copies; no compilation.')
