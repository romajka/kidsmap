import gettext,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
messages=['Владелец мероприятия','Связанное место','Редактирование мероприятия','Есть несохранённая копия в этой вкладке','Восстановить ввод','Оставить серверные данные','Название и описание сохраняются на азербайджанском (AZ). Язык интерфейса не создаёт переводы.','Черновику нужны организатор и категория. Даты можно оставить пустыми целиком; если начать ввод, заполните весь интервал. Отправка требует всех отмеченных полей и фото. Карта необязательна.']
result={}
for lang in ['ru','az','en']:
 with (R/f'locale/{lang}/LC_MESSAGES/django.mo').open('rb') as f:t=gettext.GNUTranslations(f)
 result[lang]={x:{'rendered':t.gettext(x),'same_as_RU_msgid':t.gettext(x)==x} for x in messages}
(P/'translation-proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Read compiled WORKTREE catalogs; no compilation.')
