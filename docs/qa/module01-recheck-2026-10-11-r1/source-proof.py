"""Read-only compiler comparisons; no graph cache or credentials exported."""
import gettext,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
manifest=json.loads((R/'.tmp/module01-recheck-20261011-r1/locales/manifest.json').read_text())
out={'source':'current WORKTREE PO compiled by existing helper, not shared MO','compiler':manifest.get('compiler'),'entries':[]}
keys=['Бизнес','Общественное место','Описание (RU)','Выберите район','Карта пока не активна','Геокодирование не настроено.']
for lang in ['ru','az','en']:
 po=R/'locale'/lang/'LC_MESSAGES/django.po';mo=Path(manifest['locale_root'])/lang/'LC_MESSAGES/django.mo';shared=R/'locale'/lang/'LC_MESSAGES/django.mo'
 with mo.open('rb') as f:tr=gettext.GNUTranslations(f)
 with shared.open('rb') as f:old=gettext.GNUTranslations(f)
 out['entries'].append({'language':lang,'po_sha256':hashlib.sha256(po.read_bytes()).hexdigest(),'isolated_mo_sha256':hashlib.sha256(mo.read_bytes()).hexdigest(),'shared_mo_sha256':hashlib.sha256(shared.read_bytes()).hexdigest(),'shared_equals_isolated':mo.read_bytes()==shared.read_bytes(),'translation_keys':{k:{'active_isolated':k in tr._catalog,'isolated':tr.gettext(k),'active_shared':k in old._catalog,'shared':old.gettext(k)} for k in keys}})
(P/'compiled-locales-proof.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Current PO / isolated MO / untouched shared MO proof saved')
