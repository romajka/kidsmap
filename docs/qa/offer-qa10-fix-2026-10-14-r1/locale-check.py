import json
from pathlib import Path
from django.db import connection,transaction
from django.utils.translation import override,gettext
from catalog.models import Place
from catalog.services.pricing_plans import offering_editor_choices
P=Path(__file__).resolve().parent
ids=['Абонемент','Лагерь','Тур','Дополнительная услуга','Точная цена','Диапазон','По запросу','Год','Индивидуальный']
values={'ru':ids,'az':['Abunə','Düşərgə','Tur','Əlavə xidmət','Dəqiq qiymət','Qiymət aralığı','Sorğu əsasında','İl','Fərdi'],'en':['Membership','Camp','Tour','Additional service','Exact price','Price range','On request','Year','Individual']}
keys=[('product_types','membership'),('product_types','camp'),('product_types','tour'),('product_types','addon'),('price_kinds','exact'),('price_kinds','range'),('price_kinds','on_request'),('billing_intervals','year'),('lesson_formats','individual')]
old=['Условия подтверждены','Условия не подтверждены','Отдельный статус проверки не установлен','Основной','Дополнительный','Регистрационный взнос','Разовая оплата','Регулярная оплата','Оплата частями','На проверке']
rows=[];codes=None
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 place=Place.objects.get(pk=2)
 for lang in ['ru','az','en']:
  with override(lang):
   choices=offering_editor_choices(place)
   for i,(family,code) in enumerate(keys):
    actual=dict(choices[family])[code];assert actual==values[lang][i],(lang,code,actual)
    assert gettext(ids[i])==values[lang][i]
    rows.append({'lang':lang,'code':code,'label':actual,'status':'PASS'})
   actual={k:[x[0] for x in choices[k]] for k in sorted({x[0] for x in keys})}
   if codes is not None:assert codes==actual
   codes=actual
   for msgid in old:
    actual=gettext(msgid);assert actual and (lang=='ru' or not any('А'<=x<='я' or x in 'Ёё' for x in actual)),(lang,msgid,actual)
(P/'locale-check.json').write_text(json.dumps({'transaction':'READ ONLY','rows':rows,'target_checks':54,'prior_caption_checks':30,'enum_codes_unchanged':True},ensure_ascii=False,indent=2));print('PASS:54target labels/gettext checks,30prior captions, identical enum codes')
