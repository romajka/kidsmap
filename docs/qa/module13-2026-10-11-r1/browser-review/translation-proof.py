import gettext
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
keys = ['Карта пока не активна', 'Геокодирование не настроено. Заполните GOOGLE_MAPS_API_KEY, чтобы рассчитывать координаты прямо из формы.', 'Выберите район']
result = {'source_only_support_for_fresh_rendered_locale_checks': True, 'languages': {}}
for lang in ['ru', 'az', 'en']:
    folder = REPO / 'locale' / lang / 'LC_MESSAGES'
    mo = folder / 'django.mo'
    po = folder / 'django.po'
    with mo.open('rb') as f:
        compiled = gettext.GNUTranslations(f)
    result['languages'][lang] = {'po_sha256': hashlib.sha256(po.read_bytes()).hexdigest(), 'mo_sha256': hashlib.sha256(mo.read_bytes()).hexdigest(), 'keys': [{'msgid': key, 'in_compiled_catalog': key in compiled._catalog, 'compiled_translation': compiled.gettext(key)} for key in keys]}
(HERE / 'translation-proof.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({lang: [{'key': k['msgid'], 'compiled': k['in_compiled_catalog']} for k in value['keys']] for lang, value in result['languages'].items()}, ensure_ascii=True))
