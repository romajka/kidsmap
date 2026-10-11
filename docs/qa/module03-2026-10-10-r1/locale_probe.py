"""Read existing catalogs; never compile or mutate them."""
import ast, gettext, hashlib, json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
messages=['Сохранено на сервере','Личный профиль специалиста','Сохранение… Дождитесь ответа сервера.','Сохранение черновика или отправка изменений снимает этот профиль с публикации до следующей проверки KidsMap.']
def read_po(path):
    result={};key='';value='';mode=None
    for line in path.read_text(encoding='utf-8-sig').splitlines()+['']:
        if line.startswith('msgid '):key=ast.literal_eval(line[6:]);value='';mode='id'
        elif line.startswith('msgstr '):value=ast.literal_eval(line[7:]);mode='str'
        elif line.startswith('"') and mode:
            if mode=='id':key+=ast.literal_eval(line)
            else:value+=ast.literal_eval(line)
        elif not line:
            if key:result[key]=value
            mode=None
    return result
rows=[]
for lang in ('az','en','ru'):
    po=R/'locale'/lang/'LC_MESSAGES/django.po';mo=po.with_suffix('.mo');source=read_po(po)
    with mo.open('rb') as f:runtime=gettext.GNUTranslations(f)
    for message in messages:
        rows.append({'lang':lang,'msgid':message,'source_translation':source.get(message),'compiled_translation':runtime.gettext(message),'matches':source.get(message)==runtime.gettext(message)})
result={'rows':rows,'compiled_artifacts_preserved':True,'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for lang in ('az','en','ru') for p in [R/'locale'/lang/'LC_MESSAGES/django.po',R/'locale'/lang/'LC_MESSAGES/django.mo']}}
(P/'locale-probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('Catalog comparisons',len(rows),'mismatches',sum(not r['matches'] for r in rows))
