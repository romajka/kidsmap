"""Read only the exact nature keys in PO and MO; report missing source entries."""
import ast
import gettext
import hashlib
import json
import os
import re
from pathlib import Path

os.environ['DJANGO_TESTING'] = '1'
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXPECTED = {'ru': ['Бизнес','Общественное место'],
            'az': ['Biznes','İctimai məkan'], 'en': ['Business','Public space']}
KEYS = EXPECTED['ru']
rows, hashes = [], {}
for lang in ('ru','az','en'):
    po = ROOT / f'locale/{lang}/LC_MESSAGES/django.po'
    mo = po.with_suffix('.mo')
    for path in (po, mo):
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    found = {}
    for block in re.split(r'\r?\n\s*\r?\n', po.read_text(encoding='utf-8-sig')):
        fields, active = {}, None
        for line in block.splitlines():
            match = re.match(r'^(msgid|msgstr|msgctxt)\s+(".*")$', line)
            if match:
                active = match.group(1)
                fields[active] = ast.literal_eval(match.group(2))
            elif line.startswith('"') and active:
                fields[active] += ast.literal_eval(line)
            else:
                active = None
        if fields.get('msgid') in KEYS and 'msgctxt' not in fields:
            assert fields['msgid'] not in found
            found[fields['msgid']] = fields.get('msgstr','')
    with mo.open('rb') as file:
        translations = gettext.GNUTranslations(file)
    for key, expected in zip(KEYS, EXPECTED[lang]):
        rows.append({'language': lang, 'msgid': key, 'source_present': key in found,
                     'source_translation': found.get(key), 'compiled_present': key in translations._catalog,
                     'compiled_value': translations.gettext(key), 'proposed_expected': expected,
                     'pass': translations.gettext(key) == expected})
result = {'rows': rows, 'hashes': hashes, 'total': len(rows),
          'passed': sum(row['pass'] for row in rows), 'failed': sum(not row['pass'] for row in rows),
          'compilation_performed': False, 'application_changes': False}
(HERE / 'catalog-comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({key:value for key,value in result.items() if key not in ('rows','hashes')}))
raise SystemExit(1 if result['failed'] else 0)
