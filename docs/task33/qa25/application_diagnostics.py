"""Read only bounded synthetic browser diagnostics."""
import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'results.json').read_text())
terms=['Кабинет специалиста','Специалисты организации','Это мой профиль','Дипломы и сертификаты','Проверка KidsMap','Текущее сотрудничество','История сотрудничества','Подтвердить сотрудничество','Выбор публикации','Причина отклонения']
seen=set();out=[]
for row in r['rows']:
 key=(row['screen'],row['lang'])
 if row['issues'] and key not in seen:
  seen.add(key);out.append({'screen':key[0],'lang':key[1],'issues':row['issues'],'ru_terms':[t for t in terms if t in row['facts']['body']]})
print(json.dumps({'rows':r['total'],'passed':r['passed'],'checks':len(r['checks']),'checks_passed':r['checksPassed'],'representative_failures':out,'errors':r['events']['errors'],'public_bio':[(x['lang'],'QA25 synthetic biography' in x['facts']['body'])for x in r['rows']if x['screen']=='public'and x['width']==390]},ensure_ascii=False))
