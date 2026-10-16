import json,polib
from pathlib import Path
from django.utils.translation import gettext,override
P=Path('/home/ramin/kidsmap/docs/qa/offer-qa06-recheck-2026-10-14-r1');R=P.parents[2]
keys=['Публикация занятия: %(status)s','Условия подтверждены','Условия не подтверждены','Отдельный статус проверки не установлен','Владелец назначен','Владелец не назначен','Владение проверено','Владение не проверено','Основной','Дополнительный','Регистрационный взнос','Депозит','Разовая оплата','Регулярная оплата','Оплата частями'];rows=[]
for lang in ['ru','az','en']:
 po=polib.pofile(str(R/'locale'/lang/'LC_MESSAGES/django.po'))
 with override(lang):
  for key in keys:
   e=po.find(key);rows.append({'lang':lang,'msgid':key,'po':e.msgstr if e else None,'flags':e.flags if e else [],'runtime':gettext(key),'runtime_falls_back_to_msgid':gettext(key)==key})
(P/'gettext-evidence.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));print('Current isolated gettext/PO rows:',len(rows))
