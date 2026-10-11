"""Read-only targeted PO/MO comparison. Does not compile or change catalogues."""
import ast
import gettext
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ['DJANGO_TESTING'] = '1'
KEYS = [f'Описание ({language})' for language in ['AZ','RU','EN']] + [
    'Карта пока не активна',
    'Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY, чтобы рассчитывать координаты прямо из формы.']


def target_entries(path):
    # Parse only singular, non-context target messages, including wrapped strings.
    entries = {}
    for block in re.split(r'\r?\n\s*\r?\n', path.read_text(encoding='utf-8-sig')):
        fields, flags, field = {}, [], None
        for line in block.splitlines():
            if line.startswith('#,'):
                flags += [item.strip() for item in line[2:].split(',')]
            if line.startswith('#'):
                continue
            match = re.match(r'^(msgid|msgstr|msgctxt|msgid_plural)\s+(".*")$', line)
            if match:
                field = match.group(1)
                fields[field] = ast.literal_eval(match.group(2))
            elif line.startswith('"') and field:
                fields[field] += ast.literal_eval(line)
            else:
                field = None
        key = fields.get('msgid')
        if key in KEYS and 'msgctxt' not in fields:
            assert key not in entries, ('duplicate target',key)
            assert 'msgid_plural' not in fields
            entries[key] = {'translation':fields.get('msgstr',''),'flags':flags}
    assert set(entries)==set(KEYS), (path,set(KEYS)-set(entries))
    return entries


rows, hashes = [], {}
for language in ['ru','az','en']:
    po = ROOT/f'locale/{language}/LC_MESSAGES/django.po'
    mo = po.with_suffix('.mo')
    for path in (po,mo):
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    entries = target_entries(po)
    with mo.open('rb') as file:
        translations = gettext.GNUTranslations(file)
    for key in KEYS:
        entry = entries[key]
        expected = entry['translation'] or key
        assert 'fuzzy' not in entry['flags'], ('target is fuzzy',language,key)
        actual = translations.gettext(key)
        rows.append({'language':language,'msgid':key,'source_translation':entry['translation'],
            'flags':entry['flags'],'compiled_value':actual,'key_present':key in translations._catalog,
            'matches_source':actual==expected})
result = {'rows':rows,'hashes':hashes,'checks':len(rows),
          'matches':sum(r['matches_source'] for r in rows),
          'mismatches':sum(not r['matches_source'] for r in rows),'compiled_assets_written':False}
(HERE/'catalog-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','hashes']}))
raise SystemExit(1 if result['mismatches'] else 0)
