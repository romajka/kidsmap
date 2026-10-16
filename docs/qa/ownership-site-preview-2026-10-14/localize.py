"""Append only this follow-up's exact new messages, preserving dirty catalogues."""
import json
from pathlib import Path
import polib
ROOT = Path(__file__).resolve().parents[3]
messages = {
    'Превью на сайте': ('Saytda önizləmə','Website preview'),
    'Вернуться к проверке': ('Yoxlamaya qayıt','Back to review'),
    'Так карточку увидит посетитель. Действия в превью не сохраняются.': ('Ziyarətçi kartı belə görəcək. Önizləmədəki əməliyyatlar yadda saxlanılmır.','This is how visitors will see the card. Preview actions are not saved.'),
    'Действие доступно на опубликованной странице. В превью изменения не сохраняются.': ('Bu əməliyyat dərc edilmiş səhifədə mümkündür. Önizləmədə dəyişikliklər yadda saxlanılmır.','This action is available on the published page. Preview changes are not saved.'),
}
for language,index in [('az',0),('en',1),('ru',None)]:
    path = ROOT/'locale'/language/'LC_MESSAGES/django.po'
    catalogue = polib.pofile(path)
    additions = []
    for msgid,translations in messages.items():
        if catalogue.find(msgid): continue
        assert catalogue.find(msgid,include_obsolete_entries=True) is None
        additions.append('#: catalog/place_detail_preview.html\nmsgid '+json.dumps(msgid,ensure_ascii=False)+'\nmsgstr '+json.dumps(msgid if index is None else translations[index],ensure_ascii=False))
    if additions: path.write_text(path.read_text().rstrip()+'\n\n'+'\n\n'.join(additions)+'\n')
    print(language,len(additions))
