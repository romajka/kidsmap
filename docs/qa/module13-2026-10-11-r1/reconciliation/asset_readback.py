"""Read shared WORKTREE catalogs without Django.setup, DB or writes to locales."""
import ast, gettext, hashlib, json
from pathlib import Path
ROOT=Path('C:/kidsmap');OUT=Path(__file__).resolve().parent
def po_entry(path,key):
    text=path.read_text(encoding='utf-8-sig');blocks=text.split('\n\n')
    for block in blocks:
        lines=block.splitlines();msgid='';value='';mode=None
        for line in lines:
            if line.startswith('msgid '):mode='id';msgid=ast.literal_eval(line[6:])
            elif line.startswith('msgstr '):mode='value';value=ast.literal_eval(line[7:])
            elif line.startswith('"') and mode=='id':msgid+=ast.literal_eval(line)
            elif line.startswith('"') and mode=='value':value+=ast.literal_eval(line)
            elif line.startswith('msgctxt') or line.startswith('msgid_plural'):mode=None
        if msgid==key:return {'present':True,'value':value,'fuzzy':any(l.startswith('#,') and 'fuzzy' in l for l in lines)}
    return {'present':False,'value':None,'fuzzy':None}
keys=['Описание','Описание (AZ)','Описание (RU)','Описание (EN)','Карта пока не активна','Владелец мероприятия','Связанное место','Показывать «Афишу»','Показывать «Педагогов и специалистов»','Показывать «Организации»']
rows=[]
for lang in ['ru','az','en']:
    po=ROOT/'locale'/lang/'LC_MESSAGES/django.po';mo=po.with_suffix('.mo')
    with mo.open('rb') as f:translations=gettext.GNUTranslations(f)
    for key in keys:rows.append({'language':lang,'msgid':key,'current_shared_mo_gettext':translations.gettext(key),'current_po':po_entry(po,key),
        'po_sha256':hashlib.sha256(po.read_bytes()).hexdigest(),'mo_sha256':hashlib.sha256(mo.read_bytes()).hexdigest()})
payload={'scope':'Fresh direct asset read only; shared ignored WORKTREE MO. This is not native browser proof or effective module13 Django LOCALE_PATHS attestation.',
    'rows':rows,'external_calls':0,'django_setup':False,'db_connections':0,'locale_writes':0}
(OUT/'current-shared-locale-readback.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rows':len(rows),'unfuzzy_po_mo_mismatches':sum(r['current_po']['present'] and not r['current_po']['fuzzy'] and r['current_po']['value']!=r['current_shared_mo_gettext'] for r in rows),'scope':'asset only'},ensure_ascii=False))
