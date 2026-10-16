"""Add exact review messages; preserve existing dirty catalogues byte-for-byte."""
import json
from pathlib import Path
import polib
root=Path(__file__).resolve().parents[3]
messages={
'Полный текст':('Tam mətn','Full text'),
'Сводка карточки':('Kartın xülasəsi','Card summary'),
'Обязательные данные':('Məcburi məlumatlar','Required information'),
'Заполненность, а не результат проверки':('Doldurulma, yoxlamanın nəticəsi deyil','Completeness, not a review result'),
'Доступно':('Əlçatandır','Available'),
'Языки карточки':('Kartın dilləri','Card languages'),
'Название и описание заполнены':('Ad və təsvir doldurulub','Name and description provided'),
'Заполнено':('Doldurulub','Provided'),
'Направления / группы':('İstiqamətlər / qruplar','Activities / groups'),
'Что изменилось':('Nə dəyişib','What changed'),
'По сравнению с текущей карточкой':('Cari kartla müqayisədə','Compared with the current card'),
'Поле':('Sahə','Field'),
'Сейчас':('Hazırda','Current'),
'Отправлено':('Göndərilib','Submitted'),
'Изменён блок данных — откройте раздел для проверки':('Məlumat bloku dəyişib — yoxlamaq üçün bölməni açın','Data block changed — open the section to review'),
'Значение удалено':('Dəyər silinib','Value removed'),
'Отличий от текущей карточки нет':('Cari kartdan fərq yoxdur','No differences from the current card'),
'Свернуть все условия':('Bütün şərtləri yığ','Collapse all conditions'),
'Решение модератора':('Moderatorun qərarı','Moderator decision'),
'Расписание по дням':('Günlər üzrə cədvəl','Schedule by day'),
}
for lang,index in [('ru',None),('az',0),('en',1)]:
 path=root/'locale'/lang/'LC_MESSAGES/django.po';catalog=polib.pofile(path);add=[]
 for msgid,text in messages.items():
  if catalog.find(msgid):continue
  assert catalog.find(msgid,include_obsolete_entries=True) is None
  add.append('#: catalog/placeownershiprequest/preview.html\nmsgid '+json.dumps(msgid,ensure_ascii=False)+'\nmsgstr '+json.dumps(msgid if index is None else text[index],ensure_ascii=False))
 if add:path.write_text(path.read_text().rstrip()+'\n\n'+'\n\n'.join(add)+'\n')
 print(lang,len(add))
