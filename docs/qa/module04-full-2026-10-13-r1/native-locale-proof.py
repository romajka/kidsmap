import json
from pathlib import Path
from django.conf import settings
from django.utils.translation import override,gettext,ngettext
P=Path(__file__).resolve().parent
messages=['Редактирование мероприятия','Шаги формы мероприятия','Вперёд','Тип организатора','Нельзя опубликовать мероприятие. Обязательны для заполнения: {}']
singular='\n                Исправьте проблему ниже и сохраните мероприятие ещё раз.\n              '
plural='\n                Исправьте проблемы ниже и сохраните мероприятие ещё раз.\n              '
values={}
for lang in ['ru','az','en']:
 with override(lang):values[lang]={**{m:gettext(m) for m in messages},'instruction_single':ngettext(singular,plural,1),'instruction_plural':ngettext(singular,plural,2)}
d={'default_language':settings.LANGUAGE_CODE,'values':values};(P/'native-locale-proof.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps(d,ensure_ascii=False))
